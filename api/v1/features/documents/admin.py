from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.safestring import mark_safe
from django.urls import reverse
from django import forms
from django.db import transaction

from api.v1.base_models.common.fileStorage.models import FileStorage
from .models import Document


class DocumentAdminForm(forms.ModelForm):
    """Custom form for Document admin to handle file uploads."""
    uploaded_file = forms.FileField(required=False, help_text="Upload a file to associate with this document")
    
    class Meta:
        model = Document
        fields = '__all__'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Document model."""
    form = DocumentAdminForm
    list_display = (
        'title', 'version', 'document_type', 'status', 'organization',
        'content_object_link', 'file_link', 'updated_at'
    )
    list_filter = ('organization', 'document_type', 'status', 'created_at')
    search_fields = ('title', 'description', 'file__original_filename', 'object_id')
    list_select_related = ('organization', 'document_type', 'file', 'content_type')
    readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
    autocomplete_fields = ['document_type']
    fieldsets = (
        (None, {'fields': ('organization', 'title', 'status', 'version')}),
        ('File', {'fields': ('file', 'uploaded_file')}),
        ('Content & Type', {'fields': ('description', 'document_type', 'tags')}),
        ('Related Object', {'fields': ('content_type', 'object_id')}),
        ('Custom Data', {'classes': ('collapse',), 'fields': ('custom_fields',)}),
        ('Audit Info', {'classes': ('collapse',), 'fields': ('created_at', 'created_by', 'updated_at', 'updated_by')}),
    )

    @admin.display(description='Related Object')
    def content_object_link(self, obj):
        """Display a link to the related object, if any."""
        if not obj.content_object:
            return "-"
        
        try:
            if hasattr(obj.content_object, 'get_admin_url'):
                url = obj.content_object.get_admin_url()
            else:
                app_label = obj.content_type.app_label
                model_name = obj.content_type.model
                url = reverse(f'admin:{app_label}_{model_name}_change', args=[obj.object_id])
            
            return mark_safe(f'<a href="{url}">{obj.content_object}</a>')
        except Exception:
            return str(obj.content_object)

    @admin.display(description='File')
    def file_link(self, obj):
        """Display a link to the file storage record."""
        if not obj.file:
            return "-"
        
        try:
            # Correct admin URL for FileStorage
            url = reverse('admin:fileStorage_filestorage_change', args=[obj.file.id])
            
            # Try alternative URL format if the first one fails
            if not url:
                url = reverse('admin:api_v1_base_models_common_filestorage_filestorage_change', args=[obj.file.id])
                
            return mark_safe(f'<a href="{url}">{obj.file.original_filename}</a>')
        except Exception as e:
            # Fallback to just showing the filename if URL generation fails
            return f"{obj.file.original_filename} (ID: {obj.file.id})"
            
    def save_model(self, request, obj, form, change):
        """Handle file uploads and create FileStorage records."""
        uploaded_file = form.cleaned_data.get('uploaded_file')
        
        # Handle file upload if provided
        if uploaded_file:
            with transaction.atomic():
                # Create FileStorage record for the uploaded file
                file_storage = FileStorage(
                    file=uploaded_file,
                    original_filename=uploaded_file.name,
                    mime_type=uploaded_file.content_type if hasattr(uploaded_file, 'content_type') else '',
                    file_size=uploaded_file.size if hasattr(uploaded_file, 'size') else 0,
                    uploaded_by=request.user,
                    organization=obj.organization
                )
                file_storage.save()
                
                # Set the file field to the newly created FileStorage
                obj.file = file_storage
                
                # Increment version if this is an update
                if change:
                    obj.version += 1
        
        super().save_model(request, obj, form, change) 