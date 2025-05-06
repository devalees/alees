from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import TaxJurisdiction, TaxCategory, TaxRate


@admin.register(TaxJurisdiction)
class TaxJurisdictionAdmin(MPTTModelAdmin):
    list_display = ('code', 'name', 'jurisdiction_type', 'parent', 'is_active')
    list_filter = ('jurisdiction_type', 'is_active')
    search_fields = ('code', 'name')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    fieldsets = (
        (None, {
            'fields': ('code', 'name', 'jurisdiction_type', 'parent', 'is_active')
        }),
        ('Custom Fields', {
            'fields': ('custom_fields',),
            'classes': ('collapse',),
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )


@admin.register(TaxCategory)
class TaxCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    fieldsets = (
        (None, {
            'fields': ('code', 'name', 'description', 'is_active')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ('name', 'jurisdiction', 'tax_category', 'rate', 'tax_type', 'is_compound', 'priority', 'valid_from', 'valid_to', 'is_active')
    list_filter = ('jurisdiction', 'tax_category', 'tax_type', 'is_compound', 'is_active')
    search_fields = ('name', 'jurisdiction__name', 'jurisdiction__code', 'tax_category__name')
    list_editable = ('rate', 'is_active', 'valid_to')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    fieldsets = (
        (None, {
            'fields': ('jurisdiction', 'tax_category', 'name', 'rate', 'tax_type')
        }),
        ('Calculation Options', {
            'fields': ('is_compound', 'priority'),
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_to', 'is_active'),
        }),
        ('Custom Fields', {
            'fields': ('custom_fields',),
            'classes': ('collapse',),
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    ) 