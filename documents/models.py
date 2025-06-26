from django.db import models
from django.contrib.auth.models import User

from django.contrib.auth.models import User

from django.db import models
from django.contrib.auth.models import User
from django.template.defaulttags import now


class Client(models.Model):
    name = models.CharField(max_length=100, verbose_name="Наименование организации")
    inn = models.CharField(max_length=12, verbose_name="ИНН", blank=True, null=True)
    ogrn = models.CharField(max_length=15, verbose_name="ОГРН", blank=True, null=True)
    address = models.CharField(max_length=255, verbose_name="Юридический адрес", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='clients',
        verbose_name="Создан пользователем",
        default=1
    )
    users = models.ManyToManyField(
        User,
        related_name='assigned_clients',
        blank=True,
        verbose_name="Назначенные пользователи"
    )

    def __str__(self):
        return self.name


class Document(models.Model):
    CATEGORY_CHOICES = [
        ('contract', 'Договор'),
        ('claim', 'Исковое заявление'),
        ('act', 'Акт'),
        ('custom', 'Пользовательский'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('in_progress', 'На рассмотрении'),
        ('approved', 'Утвержден'),
        ('rejected', 'Отклонен'),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='documents',
        blank=True,
        null=True,
        verbose_name="Клиент"
    )
    title = models.CharField(max_length=255, verbose_name="Название документа")
    file = models.FileField(upload_to='documents/', blank=True, null=True, verbose_name="Файл документа")
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='custom',
        verbose_name="Категория"
    )
    deadline = models.DateField(blank=True, null=True, verbose_name="Срок")
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Статус"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_documents',
        null=True,
        blank=True,
        verbose_name="Создан пользователем"
    )

    def __str__(self):
        return self.title


class Case(models.Model):
    CATEGORY_CHOICES = [
        ('litigation', 'Судебное дело'),
        ('consultation', 'Консультация'),
        ('contract_review', 'Проверка договора'),
        ('other', 'Другое'),
    ]

    STATUS_CHOICES = [
        ('open', 'Открыто'),
        ('in_progress', 'В работе'),
        ('closed', 'Закрыто'),
    ]

    title = models.CharField(max_length=255, verbose_name="Название дела")
    description = models.TextField(blank=True, null=True, verbose_name="Описание дела")
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='other',
        verbose_name="Категория дела"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        verbose_name="Статус дела"
    )
    clients = models.ManyToManyField(
        Client,
        related_name='cases',
        verbose_name="Клиенты"
    )
    documents = models.ManyToManyField(
        Document,
        related_name='cases',
        blank=True,
        verbose_name="Документы"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Заметки по делу")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return self.title


class UpdateLastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.user.userprofile.last_seen = now()
            request.user.userprofile.save()
        response = self.get_response(request)
        return response

class Template(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название шаблона")
    file = models.FileField(upload_to='templates/', verbose_name="Файл шаблона")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")

    def __str__(self):
        return self.name