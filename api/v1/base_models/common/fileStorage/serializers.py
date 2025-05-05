from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from django.template.defaultfilters import filesizeformat

from .models import FileStorage
from api.v1.base_models.user.serializers import UserSimpleSerializer
from api.v1.base_models.organization.models import Organization
from api.v1.base_models.organization.serializers import OrganizationSimpleSerializer
# Import OrganizationScopedSerializerMixin
from core.serializers.mixins import OrganizationScopedSerializerMixin
# Import has_perm_in_org from core.rbac.permissions
from core.rbac.permissions import has_perm_in_org

# Assume this permission checking function exists elsewhere and can be imported
# from core.permissions import has_perm_in_org 
# For now, we'll mock it in tests
def has_perm_in_org(user, perm, organization):
    # Placeholder/Mock implementation for initial setup
    # In real scenario, this would call the actual RBAC logic
    print(f"Permission check mock: User {user}, Perm {perm}, Org {organization}")
    # Default to False for safety until real function is integrated and tested
    # Tests will specifically mock this to return True/False as needed.
    return False 

class FileUploadSerializer(serializers.ModelSerializer):
    """Serializer specifically for handling file uploads."""
    # We need to accept organization ID during upload
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(), 
        write_only=True # Usually we don't show the full org details on upload response
    )
    file = serializers.FileField(write_only=True, required=True)

    class Meta:
        model = FileStorage
        fields = ('file', 'organization') # Fields required for upload
        # Note: uploaded_by will be set in the view
        # Other fields like original_filename, mime_type, size are set by model/storage


class FileStorageSerializer(OrganizationScopedSerializerMixin, TaggitSerializer, serializers.ModelSerializer):
    """Serializer for the FileStorage model."""
    
    tags = TagListSerializerField(required=False)
    uploaded_by = UserSimpleSerializer(read_only=True)
    # We inherit organization field from OrganizationScopedSerializerMixin
    # But we customize it to use OrganizationSimpleSerializer for read responses
    organization = OrganizationSimpleSerializer(read_only=True)
    # Add writeable organization_id field for tests
    organization_id = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        source='organization',
        required=False,
        write_only=True
    )
    
    # Custom method fields
    download_url = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()

    class Meta:
        model = FileStorage
        fields = (
            'id', 
            'file', # FileField will typically return the path/URL
            'original_filename', 
            'file_size', 
            'mime_type', 
            'uploaded_by', 
            'tags', 
            'custom_fields',
            'organization',
            'organization_id', 
            'created_at',
            'updated_at',
            # Added fields
            'download_url',
            'file_size_display',
        )
        read_only_fields = (
            'id',
            'file', # Don't allow changing the file itself via this serializer
            'original_filename',
            'file_size',
            'mime_type',
            'uploaded_by',
            'organization',
            'created_at',
            'updated_at',
            'download_url',
            'file_size_display',
        )

    def get_download_url(self, obj):
        """Generate a download URL only if the user has permission."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None

        user = request.user
        # Permission check using has_perm_in_org from the RBAC system
        perm_code = 'file_storage.view_filestorage' 
        if has_perm_in_org(user, perm_code, obj.organization):
            if obj.file:
                try:
                    return request.build_absolute_uri(obj.file.url)
                except ValueError:
                    # Handle cases where file URL cannot be generated
                    return None
        return None

    def get_file_size_display(self, obj):
        """Return a human-readable file size."""
        if obj.file_size is not None:
            return filesizeformat(obj.file_size)
        return None

    # Optional: Add validation for custom_fields if needed
    def validate_custom_fields(self, value):
        """Ensure custom_fields is a dictionary."""
        if value is None: # Allow null
            return value
        if not isinstance(value, dict):
            raise serializers.ValidationError("Custom fields must be a valid JSON object (dictionary).")
        # Add more specific validation rules here if necessary
        # e.g., check for specific keys, value types, lengths etc.
        return value
