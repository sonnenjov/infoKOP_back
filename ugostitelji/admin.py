from django.contrib import admin
from .models import MenuItem, MenuCategory

@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display  = ['name', 'company', 'category', 'price', 'is_available']
    list_filter   = ['is_available', 'category', 'company']
    search_fields = ['name', 'company__company_name']