from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from .models import Category

@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    """Admin configuration for the Category model using MPTT drag-drop."""
    list_display = (
        'tree_actions',
        'indented_title',
        'slug',
        'category_type',
        'is_active'
    )
    list_display_links = ('indented_title',)
    list_filter = ('category_type', 'is_active', 'level') # Added level filter
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('id', 'created_at', 'created_by', 'updated_at', 'updated_by')

    # MPTT admin handles hierarchy display/editing via drag-drop
    # Add fieldsets for better organization if needed
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'parent', 'category_type', 'description', 'is_active')
        }),
        ('Custom Fields', {
            'fields': ('custom_fields',),
            'classes': ('collapse',), # Make collapsible
        }),
        ('Audit Information', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',), # Make collapsible
        }),
    ) 