"""
Admin configuration for the products app.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin configuration for the Product model."""
    list_display = [
        'sku', 'name', 'organization', 'product_type', 'status',
        'is_inventory_tracked', 'is_purchasable', 'is_sellable', 'created_at'
    ]
    list_filter = [
        'organization', 'product_type', 'status',
        'is_inventory_tracked', 'is_purchasable', 'is_sellable',
        'created_at', 'updated_at'
    ]
    search_fields = [
        'name', 'sku', 'description',
        'organization__name', 'category__name'
    ]
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    fieldsets = [
        (
            'Basic Information', {
                'fields': [
                    'name', 'sku', 'description', 'organization', 
                    'product_type', 'category', 'status', 'base_uom',
                    'tags'
                ]
            }
        ),
        (
            'Settings', {
                'fields': [
                    'is_inventory_tracked', 'is_purchasable', 'is_sellable'
                ]
            }
        ),
        (
            'Custom Data', {
                'fields': ['attributes', 'custom_fields'],
                'classes': ['collapse']
            }
        ),
        (
            'Audit', {
                'fields': [
                    'created_at', 'updated_at', 'created_by', 'updated_by'
                ],
                'classes': ['collapse']
            }
        )
    ] 