from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from django.template.defaultfilters import filesizeformat

from .models import FileStorage
from api.v1.base_models.user.serializers import UserSimpleSerializer
from api.v1.base_models.organization.serializers import OrganizationSimpleSerializer

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

class FileStorageSerializer(TaggitSerializer, serializers.ModelSerializer):
    """Serializer for the FileStorage model."""
    
    tags = TagListSerializerField(required=False)
    uploaded_by = UserSimpleSerializer(read_only=True)
    organization = OrganizationSimpleSerializer(read_only=True)
    
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
        # Permission check using the (mocked or real) function
        # Adjust permission codename as needed (e.g., 'file_storage.view_filestorage')
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
