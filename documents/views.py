import json
from django.core.files.base import ContentFile
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Client, Document, ChatMessage, Template, Case
from .forms import AssignUsersForm, DocumentForm, ClientForm, TransferClientForm, TemplateEditorForm, CaseForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout
from django.utils.timezone import now, timedelta
from docx import Document as DocxDocument
import subprocess
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from reportlab.pdfgen import canvas
from io import BytesIO
import logging
from pikepdf import Pdf, Page

logger = logging.getLogger(__name__)

@login_required
def assign_users_to_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = AssignUsersForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('client_list')
    else:
        form = AssignUsersForm(instance=client)
    return render(request, 'documents/assign_users.html', {'form': form, 'client': client})



@login_required
def document_list(request):
    clients_with_documents = Client.objects.prefetch_related('documents').all()
    return render(request, 'documents/document_list.html', {
        'clients_with_documents': clients_with_documents,
    })

@login_required
def client_list(request):
    # Клиенты текущего пользователя
    clients = Client.objects.filter(created_by=request.user).prefetch_related('documents')

    # Фильтрация по имени клиента (если передан параметр query)
    query = request.GET.get('query', '')
    if query:
        clients = clients.filter(name__icontains=query)  # Поиск без учета регистра

    # Пагинация
    paginator = Paginator(clients, 5)  # 5 клиентов на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Документы с приближающимися дедлайнами
    upcoming_documents = Document.objects.filter(
        created_by=request.user,
        deadline__lte=now().date() + timedelta(days=7),
        status='in_progress'
    )

    # Все пользователи с индикатором онлайн/оффлайн
    users = User.objects.all()

    return render(request, 'documents/client_list.html', {
        'page_obj': page_obj,  # Передаем объект пагинации вместо clients
        'upcoming_documents': upcoming_documents,
        'users': users,
        'query': query,  # Передаем запрос для сохранения фильтра
    })

@login_required
def document_edit(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            return redirect('client_list')
    else:
        form = DocumentForm(instance=document)
    return render(request, 'documents/document_form.html', {'form': form, 'document': document})

@login_required
def document_delete(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        document.delete()
        return redirect('client_list')
    return render(request, 'documents/document_confirm_delete.html', {'document': document})

@login_required
def document_detail(request, pk):
    document = get_object_or_404(Document, pk=pk)
    return render(request, 'documents/document_detail.html', {'document': document})

@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        return redirect('client_list')
    return render(request, 'documents/client_confirm_delete.html', {'client': client})

def register(request):
    if request.user.is_authenticated:
        return redirect('client_list')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('client_list')
    else:
        form = UserCreationForm()
    return render(request, 'documents/register.html', {'form': form})

def custom_logout(request):
    logout(request)
    return redirect('login')

@login_required
def document_create(request):
    return redirect('document_list')

@login_required
def document_create_for_client(request, client_pk):
    client = get_object_or_404(Client, pk=client_pk, created_by=request.user)
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.client = client  # Устанавливаем клиента
            document.created_by = request.user  # Устанавливаем текущего пользователя
            document.save()
            return redirect('client_list')
    else:
        form = DocumentForm(initial={'client': client})  # Передаем client через initial
    return render(request, 'documents/document_form.html', {'form': form, 'client': client})

@login_required
def client_base(request):
    # Все клиенты (независимо от создателя)
    clients = Client.objects.all().prefetch_related('documents')

    # Фильтрация по имени клиента (если передан параметр query)
    query = request.GET.get('query', '')
    if query:
        clients = clients.filter(
            Q(name__icontains=query) |  # Поиск по имени
            Q(inn__icontains=query) |   # Поиск по ИНН
            Q(address__icontains=query) # Поиск по адресу
        )

    # Пагинация
    paginator = Paginator(clients, 10)  # 10 клиентов на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Передача клиента другому пользователю
    if request.method == 'POST' and 'transfer_client' in request.POST:
        client_pk = request.POST.get('client_pk')
        client = get_object_or_404(Client, pk=client_pk)
        form = TransferClientForm(request.POST)
        if form.is_valid():
            new_owner = form.cleaned_data['new_owner']
            client.created_by = new_owner  # Изменяем владельца
            client.save()
            return redirect('client_base')
    else:
        form = TransferClientForm()

    return render(request, 'documents/client_base.html', {
        'page_obj': page_obj,
        'query': query,
        'form': form,
    })


@login_required
def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.created_by = request.user
            client.save()
            return redirect('client_list')
    else:
        form = ClientForm()
    return render(request, 'documents/client_form.html', {'form': form})

@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)  # Получаем клиента без проверки created_by
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('client_base')
    else:
        form = ClientForm(instance=client)
    return render(request, 'documents/client_form.html', {'form': form})

@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk, created_by=request.user)
    if request.method == 'POST':
        client.delete()
        return redirect('client_list')
    return render(request, 'documents/client_confirm_delete.html', {'client': client})

@login_required
def document_create_for_client(request, client_pk):
    client = get_object_or_404(Client, pk=client_pk, created_by=request.user)
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.client = client
            document.created_by = request.user
            document.save()
            return redirect('client_list')
    else:
        form = DocumentForm()
    return render(request, 'documents/document_form.html', {'form': form, 'client': client})

@login_required
def template_list(request):
    templates = Template.objects.all()
    return render(request, 'documents/template_list.html', {'templates': templates})

@login_required
def document_create_from_template(request, template_pk):
    template = get_object_or_404(Template, pk=template_pk)
    print(f"Template file URL: {template.file.url}")  # Логирование URL файла
    clients = Client.objects.filter(created_by=request.user)

    if request.method == 'POST':
        form = TemplateEditorForm(request.POST, user=request.user)
        if form.is_valid():
            client = form.cleaned_data['client']
            text_fields = form.cleaned_data.get('text_fields', {})

            # Создаем PDF на основе шаблона
            buffer = BytesIO()
            p = canvas.Canvas(buffer)

            # Пример добавления текста в PDF
            p.drawString(100, 750, f"Имя клиента: {client.name}")
            p.drawString(100, 730, f"ИНН: {client.inn}")
            p.drawString(100, 710, f"Адрес: {client.address}")

            # Добавляем пользовательские поля
            y_position = 690
            for key, value in text_fields.items():
                p.drawString(100, y_position, f"{key}: {value}")
                y_position -= 20

            p.showPage()
            p.save()

            # Получаем готовый PDF
            pdf = buffer.getvalue()
            buffer.close()

            # Отправляем PDF как ответ
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{template.name}.pdf"'
            response.write(pdf)
            return response
    else:
        form = TemplateEditorForm(user=request.user)

    return render(request, 'documents/document_editor.html', {
        'template': template,
        'clients': clients,
        'form': form,
    })

def get_client_data(request, client_pk):
    try:
        client = Client.objects.get(pk=client_pk)
        data = {
            'name': client.name,
            'inn': client.inn or '',
            'address': client.address or '',
        }
        return JsonResponse(data)
    except Client.DoesNotExist:
        return JsonResponse({'error': 'Клиент не найден'}, status=404)

def case_list(request):
    cases = Case.objects.all()
    return render(request, 'documents/case_list.html', {'cases': cases})

def case_create(request):
    if request.method == 'POST':
        form = CaseForm(request.POST)
        if form.is_valid():
            case = form.save()
            return redirect('case_list')
    else:
        form = CaseForm()
    return render(request, 'documents/case_form.html', {'form': form})

def case_edit(request, pk):
    case = get_object_or_404(Case, pk=pk)
    if request.method == 'POST':
        form = CaseForm(request.POST, instance=case)
        if form.is_valid():
            form.save()
            return redirect('case_list')
    else:
        form = CaseForm(instance=case)
    return render(request, 'documents/case_form.html', {'form': form})

def case_delete(request, pk):
    case = get_object_or_404(Case, pk=pk)
    if request.method == 'POST':
        case.delete()
        return redirect('case_list')
    return render(request, 'documents/case_confirm_delete.html', {'case': case})

def get_documents_by_clients(request):
    client_ids = request.GET.getlist('client_ids[]')  # Получаем ID выбранных клиентов
    if client_ids:
        documents = Document.objects.filter(client_id__in=client_ids).values('id', 'title')
        return JsonResponse(list(documents), safe=False)
    return JsonResponse([], safe=False)

def case_view(request, pk):
    case = get_object_or_404(Case, pk=pk)
    return render(request, 'documents/case_view.html', {'case': case})