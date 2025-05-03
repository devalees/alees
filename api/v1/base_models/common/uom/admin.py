from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import UomType, UnitOfMeasure

__all__ = ['UomTypeAdmin', 'UnitOfMeasureAdmin']

@admin.register(UomType)
class UomTypeAdmin(admin.ModelAdmin):
    """Admin configuration for the UomType model."""
    list_display = ('code', 'name', 'is_active', 'created_at', 'updated_at') # Added timestamps
    search_fields = ('code', 'name', 'description')
    list_filter = ('is_active',)
    readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
    fieldsets = (
        (None, {'fields': ('code', 'name', 'description', 'is_active')}),
        (_("Customization"), {'fields': ('custom_fields',), 'classes': ('collapse',)}),
        (_("Audit Information"), {'fields': readonly_fields, 'classes': ('collapse',)}),
    )

@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    """Admin configuration for the UnitOfMeasure model."""
    list_display = ('code', 'name', 'uom_type', 'symbol', 'is_active', 'updated_at')
    search_fields = ('code', 'name', 'symbol', 'uom_type__code', 'uom_type__name') # Search by type fields
    list_filter = ('uom_type', 'is_active')
    list_select_related = ('uom_type',) # Optimize query for list view
    readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
    autocomplete_fields = ['uom_type'] # Use autocomplete for FK selection
    fieldsets = (
        (None, {'fields': ('code', 'name', 'uom_type', 'symbol', 'is_active')}),
        (_("Customization"), {'fields': ('custom_fields',), 'classes': ('collapse',)}),
        (_("Audit Information"), {'fields': readonly_fields, 'classes': ('collapse',)}),
    )

    # Optimize Autocomplete Query (optional but good practice)
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('uom_type') 