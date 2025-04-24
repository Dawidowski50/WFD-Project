from django.contrib import admin
from .models import Category, Item, Maintenance

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'daily_rate', 'condition', 'is_available', 'last_maintained')
    list_filter = ('category', 'condition', 'is_available')
    search_fields = ('name', 'description')

@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ('item', 'staff', 'maintenance_date', 'status', 'created_at')
    list_filter = ('status', 'maintenance_date')
    search_fields = ('item__name', 'description')
