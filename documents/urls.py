from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.client_list, name='client_list'),  # Главная страница
    path('clients/', views.client_list, name='client_list'),
    path('client/create/', views.client_create, name='client_create'),  # Создание клиента
    path('client/<int:pk>/edit/', views.client_edit, name='client_edit'),  # Редактирование клиента
    path('client/<int:pk>/delete/', views.client_delete, name='client_delete'),  # Удаление клиента
    path('documents/', views.document_list, name='document_list'),  # Список всех документов
    path('document/create/', views.document_create, name='document_create'),  # Создание нового документа
    path('document/create-for-client/<int:client_pk>/', views.document_create_for_client, name='document_create_for_client'),
    path('document/<int:pk>/', views.document_detail, name='document_detail'),
    path('document/<int:pk>/edit/', views.document_edit, name='document_edit'),
    path('document/<int:pk>/delete/', views.document_delete, name='document_delete'),
    path('client-base/', views.client_base, name='client_base'),
    path('templates/', views.template_list, name='template_list'),
    path('templates/<int:template_pk>/create/', views.document_create_from_template, name='document_create_from_template'),
    path('get-client-data/<int:client_pk>/', views.get_client_data, name='get_client_data'),
    path('cases/', views.case_list, name='case_list'),
    path('cases/create/', views.case_create, name='case_create'),
    path('cases/<int:pk>/edit/', views.case_edit, name='case_edit'),
    path('cases/<int:pk>/delete/', views.case_delete, name='case_delete'),
    path('get-documents-by-clients/', views.get_documents_by_clients, name='get_documents_by_clients'),
    path('cases/<int:pk>/view/', views.case_view, name='case_view'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)