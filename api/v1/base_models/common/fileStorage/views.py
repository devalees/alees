from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from .models import FileStorage
# Use the full FileStorageSerializer for the response, but FileUploadSerializer for input
from .serializers import FileStorageSerializer, FileUploadSerializer 
from api.v1.base_models.organization.models import Organization, OrganizationMembership

# Import core viewset mixin and permission class
from core.viewsets.mixins import OrganizationScopedViewSetMixin
from core.rbac.drf_permissions import HasModelPermissionInOrg
from core.rbac.permissions import has_perm_in_org

# --- FileUploadView Definition ---
class FileUploadView(generics.CreateAPIView):
    """
    Handles file uploads. Requires authentication.
    Checks `add_filestorage` permission for the target organization.
    Sets `uploaded_by` automatically.
    """
    queryset = FileStorage.objects.all() 
    # Use the full serializer for the response representation
    serializer_class = FileStorageSerializer 
    permission_classes = [permissions.IsAuthenticated] # Basic auth check first
    
    # Override get_serializer_class to use the simpler upload serializer for input
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FileUploadSerializer
        return FileStorageSerializer # Use full for response schema generation

    def perform_create(self, serializer):
        """Perform permission checks and set automatic fields before saving."""
        user = self.request.user
        # Get the target organization from the validated data
        organization = serializer.validated_data.get('organization')
        
        # If organization is not provided, try to determine it from user context
        if not organization:
            from core.rbac.utils import get_user_request_context
            
            # Get user's active organizations
            active_org_ids, is_single_org = get_user_request_context(user)
            
            if not active_org_ids:
                raise PermissionDenied(_("You do not belong to any active organizations."))
            
            # For single-org users: use their only organization
            if is_single_org:
                try:
                    organization = Organization.objects.get(pk=active_org_ids[0])
                    serializer.validated_data['organization'] = organization
                except Organization.DoesNotExist:
                    raise PermissionDenied(_("Your organization could not be found."))
            else:
                # Multi-org users must explicitly specify an organization
                raise PermissionDenied(_("Organization must be specified for upload when you belong to multiple organizations."))

        # --- Organization-Aware Permission Check --- 
        perm_code = 'add_filestorage' # Use the correct permission codename
        if not has_perm_in_org(user, perm_code, organization):
            raise PermissionDenied(_("You do not have permission to upload files to this organization."))

        # Permission granted, add additional data to be saved
        uploaded_file = serializer.validated_data.get('file')
        serializer.validated_data['uploaded_by'] = user
        # Organization is already in validated_data from the serializer
        # serializer.validated_data['organization'] = organization 
        serializer.validated_data['original_filename'] = uploaded_file.name if uploaded_file else 'unknown'
        serializer.validated_data['mime_type'] = uploaded_file.content_type if uploaded_file else ''
        # REMOVED: Explicit save call is removed
        # serializer.save(...)

    def create(self, request, *args, **kwargs):
        """Override create to ensure perform_create adds data before default save."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer) # Modifies serializer.validated_data
        # Let the default CreateModelMixin handle the actual save using the modified validated_data
        instance = serializer.save() 
        
        # Return response using the full FileStorageSerializer for the created instance
        # instance = serializer.instance # instance is now returned by save()
        response_serializer = FileStorageSerializer(instance, context=self.get_serializer_context())
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

# --- FileStorageViewSet Definition ---
from rest_framework import viewsets, mixins

class FileStorageViewSet(OrganizationScopedViewSetMixin, 
                         mixins.RetrieveModelMixin, 
                         mixins.ListModelMixin, 
                         mixins.DestroyModelMixin,
                         viewsets.GenericViewSet):
    """
    Provides LIST, RETRIEVE, DELETE operations for FileStorage, scoped by organization.
    Requires 'view_filestorage' for list/retrieve, 'delete_filestorage' for delete.
    """
    queryset = FileStorage.objects.select_related('organization', 'uploaded_by').prefetch_related('tags').all()
    serializer_class = FileStorageSerializer
    permission_classes = [
        permissions.IsAuthenticated, 
        HasModelPermissionInOrg # Use RBAC permission class
    ] 
    filterset_fields = ['mime_type', 'tags__name'] # Requires django-filter setup
    search_fields = ['original_filename', 'uploaded_by__username'] # Requires SearchFilter

    # Override perform_destroy for physical file deletion
    def perform_destroy(self, instance):
        """Delete the physical file before deleting the database record."""
        # Permission check should be handled by permission_classes
        # Delete the physical file from storage
        if instance.file:
            instance.file.delete(save=False)
        
        # Proceed with deleting the database record
        super().perform_destroy(instance)
