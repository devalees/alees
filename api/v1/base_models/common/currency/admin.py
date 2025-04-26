from django.contrib import admin
from .models import Currency

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'symbol', 'decimal_places', 'is_active', 'numeric_code')
    search_fields = ('code', 'name', 'numeric_code')
    list_filter = ('is_active',)
    # Add custom_fields if needed/useful in admin list/form
