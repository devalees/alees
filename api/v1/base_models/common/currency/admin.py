from django.contrib import admin
from .models import Currency

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = (
        'code', 
        'name', 
        'symbol', 
        'decimal_places', 
        'is_active', 
        'numeric_code',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by'
    )
    search_fields = ('code', 'name', 'numeric_code')
    list_filter = ('is_active', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    fieldsets = (
        ('Currency Information', {
            'fields': ('code', 'name', 'symbol', 'numeric_code', 'decimal_places', 'is_active', 'custom_fields')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    # Add custom_fields if needed/useful in admin list/form
