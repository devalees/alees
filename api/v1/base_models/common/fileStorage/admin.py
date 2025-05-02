from django.contrib import admin
from .models import FileStorage

@admin.register(FileStorage)
class FileStorageAdmin(admin.ModelAdmin):
    """Admin configuration for FileStorage model."""
    list_display = (
        'original_filename', 
        'organization', 
        'uploaded_by', 
        'mime_type', 
        'file_size', 
        'created_at',
        'id', # Included for easy reference
    )
    list_filter = ('organization', 'mime_type', 'created_at')
    search_fields = ('original_filename', 'uploaded_by__username', 'tags__name')
    
    # Make most fields read-only as per the spec
    readonly_fields = (
        'id',
        'organization',
        'uploaded_by',
        'file', # Prevent direct file manipulation here
        'original_filename',
        'mime_type',
        'file_size',
        'created_by',
        'updated_by',
        'created_at',
        'updated_at',
    )
    
    fieldsets = (
        (None, {
            'fields': ('organization', 'uploaded_by', 'original_filename', 'file')
        }),
        ('Metadata', {
            'fields': ('mime_type', 'file_size', 'tags', 'metadata', 'custom_fields')
        }),
        ('Audit', {
            'fields': ('id', 'created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',) # Collapse audit fields by default
        }),
    )
    
    # Allow adding tags in the admin
    filter_horizontal = () # Use default widget for TaggableManager

    def get_queryset(self, request):
        # Prefetch related users and organization for efficiency
        return super().get_queryset(request).select_related(
            'organization', 'uploaded_by', 'created_by', 'updated_by'
        ).prefetch_related('tags') 