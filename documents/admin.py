from django.contrib import admin
from .models import Client, Document, Template

class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'inn', 'ogrn', 'address')
    search_fields = ('name', 'inn', 'ogrn')

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'category', 'deadline', 'status')
    list_filter = ('category', 'status', 'deadline')
    search_fields = ('title', 'client__name')

@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')  # Отображаемые поля в списке
    search_fields = ('name',)  # Поиск по названию шаблона

admin.site.register(Client, ClientAdmin)
admin.site.register(Document, DocumentAdmin)
