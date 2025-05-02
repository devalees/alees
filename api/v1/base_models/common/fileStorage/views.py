from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from .models import FileStorage
# Use the full FileStorageSerializer for the response, but FileUploadSerializer for input
from .serializers import FileStorageSerializer, FileUploadSerializer 
from api.v1.base_models.organization.models import Organization, OrganizationMembership

# Assume this permission checking function exists elsewhere and can be imported
# from core.permissions import has_perm_in_org 
# For now, we'll mock it in tests
def has_perm_in_org(user, perm, organization):
    # Placeholder/Mock implementation for initial setup
    print(f"Permission check mock: User {user}, Perm {perm}, Org {organization}")
    # Default to True for upload view tests for now, will be properly mocked
    return True 

# --- Placeholder Permission Class ---
class HasModelPermissionInOrgPlaceholder(permissions.BasePermission):
    """Placeholder: Checks standard Django model perms, NOT org-aware yet."""
    # Maps view actions to required Django permission codenames
    action_perms_map = {
        'list': '%(app_label)s.view_%(model_name)s',
        'retrieve': '%(app_label)s.view_%(model_name)s',
        'destroy': '%(app_label)s.delete_%(model_name)s',
        # Add 'create', 'update', 'partial_update' if needed
    }

    def has_permission(self, request, view):
        # Get the required permission string for the current action
        # Uses the view's queryset model to determine app_label/model_name
        model_cls = view.queryset.model
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': model_cls._meta.model_name
        }
        perm_code = self.action_perms_map.get(view.action) % kwargs if view.action in self.action_perms_map else None
        
        if not perm_code:
            # No permission defined for this action, allow (or deny based on policy)
            return True 

        # Check if the authenticated user has the standard Django permission
        return request.user and request.user.is_authenticated and request.user.has_perm(perm_code)

    def has_object_permission(self, request, view, obj):
        # For detail views, check the same permission again (redundant with above but safe)
        # A real org-aware check would use the 'obj.organization' here.
        model_cls = view.queryset.model
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': model_cls._meta.model_name
        }
        perm_code = self.action_perms_map.get(view.action) % kwargs if view.action in self.action_perms_map else None
        
        if not perm_code:
            return True
            
        # Check if the authenticated user has the standard Django permission
        return request.user and request.user.is_authenticated and request.user.has_perm(perm_code)

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
        
        if not organization:
            # Handle case where organization wasn't provided or validated
            # This depends on whether organization is required in FileUploadSerializer
            raise PermissionDenied(_("Organization must be specified for upload."))

        # --- Organization-Aware Permission Check --- 
        perm_code = 'file_storage.add_filestorage' # Use the correct permission codename
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

# Assuming this mixin exists and correctly filters by request.user.organization
# TODO: Verify or implement OrganizationScopedViewSetMixin if it doesn't exist
# from core.views import OrganizationScopedViewSetMixin 
class OrganizationScopedViewSetMixin: # Placeholder implementation
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        if user.is_authenticated:
            # Attempt to get the user's primary/first active organization membership
            membership = OrganizationMembership.objects.filter(
                user=user, 
                is_active=True
            ).select_related('organization').first()
            
            if membership and membership.organization:
                # Filter the main queryset by the user's organization
                return qs.filter(organization=membership.organization)
        
        # If no organization found or user not authenticated, return empty queryset
        return qs.none() 

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
    # TODO: Add org-aware permission class (e.g., from core.permissions)
    permission_classes = [
        permissions.IsAuthenticated, 
        HasModelPermissionInOrgPlaceholder # Add the placeholder permission check
    ] 
    filterset_fields = ['mime_type', 'tags__name'] # Requires django-filter setup
    search_fields = ['original_filename', 'uploaded_by__username'] # Requires SearchFilter

    # Override perform_destroy for physical file deletion
    def perform_destroy(self, instance):
        # TODO: Enhance permission check here if needed (e.g., check delete_filestorage)
        # The main check should ideally be handled by permission_classes
        perm_code = 'file_storage.delete_filestorage'
        if not has_perm_in_org(self.request.user, perm_code, instance.organization):
             raise PermissionDenied(_("You do not have permission to delete this file."))
        
        # Delete the physical file first
        instance.file.delete(save=False)
        # Then delete the database record
        super().perform_destroy(instance)
