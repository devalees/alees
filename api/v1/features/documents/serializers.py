from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

# Import the RBAC mixin
from core.serializers.mixins import OrganizationScopedSerializerMixin
from api.v1.base_models.common.fileStorage.models import FileStorage
from api.v1.base_models.common.fileStorage.serializers import FileStorageSerializer
from api.v1.base_models.common.category.models import Category
from api.v1.base_models.common.category.serializers import CategorySerializer

from .models import Document


class DocumentSerializer(OrganizationScopedSerializerMixin, TaggitSerializer, serializers.ModelSerializer):
    """Serializer for Document model with Organization scoping and tag support."""
    
    tags = TagListSerializerField(required=False)
    file_details = FileStorageSerializer(source='file', read_only=True)
    
    # Add a file upload field that will be used to create a FileStorage record
    uploaded_file = serializers.FileField(write_only=True, required=False)
    
    # Make the file field optional, as it will be set automatically when using uploaded_file
    file = serializers.PrimaryKeyRelatedField(
        queryset=FileStorage.objects.all(),
        required=False
    )

    # Document type representation
    document_type_slug = serializers.SlugRelatedField(
        slug_field='slug', source='document_type', read_only=True, allow_null=True
    )
    document_type = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(category_type='DOCUMENT_TYPE'),
        allow_null=True, required=False
    )
    document_type_details = CategorySerializer(source='document_type', read_only=True)

    # GFK Representation (Read-only)
    content_type_app_label = serializers.CharField(source='content_type.app_label', read_only=True, allow_null=True)
    content_type_model = serializers.CharField(source='content_type.model', read_only=True, allow_null=True)
    content_object_id_display = serializers.CharField(source='object_id', read_only=True, allow_null=True)

    # GFK Write fields (handled by view's perform_create)
    parent_content_type_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    parent_object_id = serializers.CharField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Document
        fields = [
            'id', 'title', 'document_type', 'document_type_slug', 'document_type_details', 'status',
            'file', 'file_details', 'uploaded_file',
            'version', 'description', 'tags', 'custom_fields',
            'content_type', 'object_id',  # Read-only representation of GFK link
            'content_type_app_label', 'content_type_model', 'content_object_id_display',
            'parent_content_type_id', 'parent_object_id',  # Write-only for linking
            'organization',  # Handled by OrganizationScopedSerializerMixin
            'created_at', 'updated_at',
        ]
        read_only_fields = (
            'id', 'version', 'created_at', 'updated_at',
            'file_details', 'content_type', 'object_id',  # Read-only for GFK after creation
            'content_type_app_label', 'content_type_model', 'content_object_id_display',
            'document_type_slug', 'document_type_details',
        )

    def validate(self, data):
        """Validate the data, particularly the custom_fields and GFK inputs."""
        # Ensure that either 'file' or 'uploaded_file' is provided
        if not data.get('file') and not data.get('uploaded_file'):
            raise ValidationError({
                "file": "Either a file ID or an uploaded file must be provided."
            })
            
        # Validate GFK inputs if provided
        parent_content_type_id = data.get('parent_content_type_id')
        parent_object_id = data.get('parent_object_id')

        if (parent_content_type_id is not None) != (parent_object_id is not None):
            raise ValidationError({
                "parent_content_type_id": "Both parent_content_type_id and parent_object_id must be provided together."
            })

        if parent_content_type_id is not None:
            try:
                content_type = ContentType.objects.get(pk=parent_content_type_id)
                model_class = content_type.model_class()
                if model_class is None:
                    raise ValidationError({
                        "parent_content_type_id": f"ContentType with ID {parent_content_type_id} does not have a valid model."
                    })
                
                # Try to get the instance to verify it exists
                try:
                    model_class.objects.get(pk=parent_object_id)
                except (model_class.DoesNotExist, ValueError):
                    raise ValidationError({
                        "parent_object_id": f"Object with ID {parent_object_id} does not exist for the given content type."
                    })
            except ContentType.DoesNotExist:
                raise ValidationError({
                    "parent_content_type_id": f"ContentType with ID {parent_content_type_id} does not exist."
                })

        # Validate custom_fields if necessary (implementation depends on any schema validation logic)
        # if 'custom_fields' in data and data['custom_fields']:
        #     # Implement custom field validation logic if needed
        #     pass

        return data 