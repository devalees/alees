from django.contrib import admin
from .models import Status

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name', 'category', 'color', 'updated_at')
    search_fields = ('slug', 'name', 'description', 'category')
    list_filter = ('category',)
    prepopulated_fields = {'slug': ('name',)} # Auto-populate slug from name
    # Assuming Timestamped/Auditable provides these fields automatically
    # If not, adjust readonly_fields accordingly
    readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
    fieldsets = (
        (None, {'fields': ('slug', 'name', 'description')}),
        ('Categorization', {'fields': ('category', 'color')}),
        ('Custom Data', {'fields': ('custom_fields',)}),
        ('Audit Info', {'classes': ('collapse',), 'fields': readonly_fields}),
    ) 