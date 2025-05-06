import logging
from rest_framework import viewsets, filters, parsers
from rest_framework.exceptions import PermissionDenied
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.http import Http404

# Import RBAC components
from core.viewsets.mixins import OrganizationScopedViewSetMixin
from core.rbac.drf_permissions import HasModelPermissionInOrg
from core.rbac.permissions import has_perm_in_org

from api.v1.base_models.common.fileStorage.models import FileStorage
from .models import Document
from .serializers import DocumentSerializer

logger = logging.getLogger(__name__)


class DocumentViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint for managing Documents with organization scoping.
    Requires appropriate permissions in the document's organization context.
    """
    serializer_class = DocumentSerializer
    # queryset automatically filtered by OrganizationScopedViewSetMixin.get_queryset()
    queryset = Document.objects.select_related(
        'organization', 'document_type', 'file', 'content_type'
    ).prefetch_related('tags').all()

    # Permissions handled by HasModelPermissionInOrg
    permission_classes = [HasModelPermissionInOrg]
    
    # Add support for file uploads
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    # Filtering and search
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'tags__name', 'file__original_filename']
    ordering_fields = ['title', 'created_at', 'updated_at', 'version', 'status']
    ordering = ['-created_at']
    
    # Can add django_filters.DjangoFilterBackend and filterset_class if needed
    
    def perform_create(self, serializer):
        """
        Handle organization assignment, file uploads, and GFK linking when creating a document.
        """
        # Extract data from serializer
        data = serializer.validated_data
        uploaded_file = data.pop('uploaded_file', None)
        parent_ctype_id = data.pop('parent_content_type_id', None)
        parent_object_id = data.pop('parent_object_id', None)
        
        # Handle file upload if provided
        if uploaded_file:
            # Create FileStorage record for the uploaded file
            file_storage = FileStorage(
                file=uploaded_file,
                original_filename=uploaded_file.name,
                mime_type=uploaded_file.content_type if hasattr(uploaded_file, 'content_type') else '',
                file_size=uploaded_file.size if hasattr(uploaded_file, 'size') else 0,
                uploaded_by=self.request.user,
                organization=self.get_organization()  # Get organization from RBAC context
            )
            file_storage.save()
            
            # Set the file field to the newly created FileStorage
            data['file'] = file_storage

        # Call super() to let OrganizationScopedViewSetMixin handle org and permission check
        super().perform_create(serializer)

        # Now link the GFK if data was provided
        instance = serializer.instance
        if parent_ctype_id and parent_object_id:
            try:
                parent_content_type = get_object_or_404(ContentType, pk=parent_ctype_id)
                instance.content_type = parent_content_type
                instance.object_id = parent_object_id
                instance.save(update_fields=['content_type', 'object_id'])
            except Http404:
                logger.error(f"Failed to link document {instance.id} to content type {parent_ctype_id}, object {parent_object_id}")
                # We already validated in serializer, so this shouldn't happen
                # But if it does, the document is still created, just not linked

    def perform_update(self, serializer):
        """
        Handle updates to a document, including file uploads, GFK linking and version increments.
        """
        # Extract data from serializer
        data = serializer.validated_data
        uploaded_file = data.pop('uploaded_file', None)
        parent_ctype_id = data.pop('parent_content_type_id', None)
        parent_object_id = data.pop('parent_object_id', None)
        
        # Handle file upload if provided
        if uploaded_file:
            # Create FileStorage record for the uploaded file
            file_storage = FileStorage(
                file=uploaded_file,
                original_filename=uploaded_file.name,
                mime_type=uploaded_file.content_type if hasattr(uploaded_file, 'content_type') else '',
                file_size=uploaded_file.size if hasattr(uploaded_file, 'size') else 0,
                uploaded_by=self.request.user,
                organization=self.get_organization()  # Get organization from RBAC context
            )
            file_storage.save()
            
            # Set the file field to the newly created FileStorage
            data['file'] = file_storage
            
            # Increment version since we're updating the file
            instance = self.get_object()
            data['version'] = instance.version + 1
        # Check if there's a change of file (existing FileStorage ID)
        elif 'file' in data and data['file'] != self.get_object().file:
            # New file reference, increment version
            instance = self.get_object()
            data['version'] = instance.version + 1

        # Call super() to let OrganizationScopedViewSetMixin handle org and permission check
        super().perform_update(serializer)

        # Now link the GFK if data was provided
        instance = serializer.instance
        if parent_ctype_id and parent_object_id:
            try:
                parent_content_type = get_object_or_404(ContentType, pk=parent_ctype_id)
                instance.content_type = parent_content_type
                instance.object_id = parent_object_id
                instance.save(update_fields=['content_type', 'object_id'])
            except Http404:
                logger.error(f"Failed to link document {instance.id} to content type {parent_ctype_id}, object {parent_object_id}") 