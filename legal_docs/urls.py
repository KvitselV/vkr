from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from documents.views import register
from documents.views import custom_logout

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('documents.urls')),  # Маршруты приложения
    path('login/', auth_views.LoginView.as_view(template_name='documents/login.html'), name='login'),
    path('logout/', custom_logout, name='logout'),  # Используем собственное представление
    path('register/', register, name='register'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)