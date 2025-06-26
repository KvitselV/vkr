from django import forms
from .models import Client, Document, Case
from django.contrib.auth.models import User
class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'inn', 'ogrn', 'address']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите наименование организации'
            }),
            'inn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ИНН'
            }),
            'ogrn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ОГРН'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите юридический адрес'
            }),
        }

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['client', 'title', 'file', 'category', 'deadline', 'status']  # Исключаем created_by
        widgets = {
            'client': forms.HiddenInput(attrs={'id': 'clientId'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_title',
                'placeholder': 'Введите название документа'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'id': 'id_file'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_category'
            }),
            'deadline': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'id_deadline'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_status'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Извлекаем пользователя из kwargs
        super(DocumentForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['created_by'].initial = user  # Устанавливаем текущего пользователя

class AssignUsersForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['users']
        widgets = {
            'users': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }

class TransferClientForm(forms.Form):
    new_owner = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="Новый владелец",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    class Meta:
        model = Client
        fields = ['new_owner']

class TemplateEditorForm(forms.Form):
    client = forms.ModelChoiceField(
        queryset=Client.objects.none(),  # Изначально пустой queryset
        label="Клиент",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    text_fields = forms.JSONField(
        required=False,
        label="Поля для заполнения",
        widget=forms.HiddenInput()
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Получаем пользователя из kwargs
        super(TemplateEditorForm, self).__init__(*args, **kwargs)
        if user:
            # Фильтруем клиентов по текущему пользователю
            self.fields['client'].queryset = Client.objects.filter(created_by=user)


class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = ['title', 'description', 'category', 'status', 'clients', 'documents', 'notes']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }