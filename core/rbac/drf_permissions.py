from functools import wraps
import logging # <-- Use standard logging
from rest_framework import permissions
from django.core.exceptions import PermissionDenied, ValidationError # Import exceptions

from .permissions import has_perm_in_org # Import core permission helper
# Import utility helpers
from .utils import get_user_request_context, get_validated_request_org_id
# from django.utils.log import logger # <-- Remove incorrect import
from api.v1.base_models.organization.models import OrganizationMembership # Corrected import path

# Instantiate logger for this module
logger = logging.getLogger(__name__)

class HasModelPermissionInOrg(permissions.BasePermission):
     """
     Checks if user has the required model-level permission within the
     organization context.

     - For list actions: Checks if user has 'view' perm in *any* active org.
     - For create actions: Validates provided/inferred org and checks 'add' perm in that specific org.
     - For object actions (retrieve, update, delete): Checks perm against the object's org.
     
     Note: Superusers bypass all permission checks.
     """
     # Optional: map actions to required permissions if not using convention
     # action_perm_map = {'list': 'view', 'retrieve': 'view', ...}

     # Keep this helper method inside the class
     def get_required_permission(self, request, view, obj=None):
         """
         Determine the required permission codename based on action and model.
         Uses the object's model if provided (for object permissions),
         otherwise tries to get the model from the view.
         """
         model_cls = None
         if obj:
             model_cls = obj.__class__
         else:
             # Try getting model from viewset queryset or serializer
             # Make this more robust
             if hasattr(view, 'queryset') and view.queryset is not None:
                 model_cls = view.queryset.model
             elif hasattr(view, 'get_queryset'): # Call get_queryset if it exists
                 try:
                     queryset = view.get_queryset()
                     if queryset is not None:
                         model_cls = queryset.model
                 except Exception as e: # Catch potential errors in get_queryset
                      logger.warning("Error calling get_queryset on view %s: %s", view.__class__.__name__, e)
             
             # Fallback to serializer if model not found via queryset
             if not model_cls and hasattr(view, 'get_serializer_class'):
                 try:
                     serializer_cls = view.get_serializer_class()
                     if hasattr(serializer_cls, 'Meta') and hasattr(serializer_cls.Meta, 'model'):
                         model_cls = serializer_cls.Meta.model
                 except Exception as e: # Catch potential errors in get_serializer_class
                     logger.warning("Error calling get_serializer_class on view %s: %s", view.__class__.__name__, e)

         if not model_cls:
             logger.warning("[PermClass] Cannot determine model from view %s or object %s for permission check", view.__class__.__name__, obj)
             return None

         # Default mapping from DRF/Django conventions
         action_map = {
             'list': 'view',
             'retrieve': 'view',
             'create': 'add',
             'update': 'change',
             'partial_update': 'change',
             'destroy': 'delete',
         }

         # Determine required action prefix (view, add, change, delete)
         action_prefix = action_map.get(view.action)
         if not action_prefix:
             # Allow custom actions or OPTIONS by default
             logger.debug("[PermClass] No standard permission prefix for action: %s", view.action)
             return None

         # Construct the permission codename
         perm_codename = f'{action_prefix}_{model_cls._meta.model_name}'
         # Return the full codename including app_label
         return f'{model_cls._meta.app_label}.{perm_codename}'

     def has_permission(self, request, view):
         """Check permissions for view-level actions (list, create)."""
         # CRITICAL: Superusers bypass all permission checks immediately
         if request.user and request.user.is_superuser:
             logger.debug("[PermClass] Superuser granted permission automatically")
             return True
             
         # Authentication check
         user = request.user
         if not user or not user.is_authenticated: 
             logger.debug("[PermClass] User not authenticated")
             return False
         
         # For standard options/metadata requests (like schema generation)
         if view.action in ['metadata', 'options']:
             logger.debug("[PermClass] Allowing standard action %s without specific permission.", view.action)
             return True
         
         # Determine required permission codename using the view
         perm_codename = self.get_required_permission(request, view) # No obj here
         logger.debug("[PermClass] Required perm for %s: %s", view.action, perm_codename)
         
         # If perm_codename is None, deny permission
         if not perm_codename:
             logger.warning("[PermClass] Denying action %s because required permission could not be determined.", view.action)
             return False
             
         if view.action == 'list':
             # For list, check if user has view permission in *any* of their orgs
             active_org_ids, _ = get_user_request_context(user)
             if not active_org_ids:
                 logger.debug("[PermClass] Denying List: User has no active organizations")
                 return False # User isn't in any active org, can't list anything

             # Check if the user has the view perm in at least one of their orgs
             has_view_perm_somewhere = any(
                 has_perm_in_org(user, perm_codename, org_id)
                 for org_id in active_org_ids
             )
             logger.debug("[PermClass] List permission check (has_view_perm_somewhere): %s", has_view_perm_somewhere)
             return has_view_perm_somewhere

         elif view.action == 'create':
             # For create, validate the target organization and check permission there.
             try:
                 # This helper validates single/multi org context and request data
                 target_org_id = get_validated_request_org_id(request, required_for_action=True)
                 # If validation passes, target_org_id will be an integer

                 if target_org_id is None:
                     # This case *shouldn't* happen with required_for_action=True,
                     # but handle defensively. Maybe the user has no orgs.
                     logger.warning("[PermClass] get_validated_request_org_id returned None unexpectedly for create action.")
                     return False

                 # Check permission in the specific target organization
                 has_create_perm = has_perm_in_org(user, perm_codename, target_org_id)
                 logger.debug("[PermClass] Create permission check in org %s: %s", target_org_id, has_create_perm)
                 return has_create_perm

             except (ValidationError, PermissionDenied) as e:
                 # get_validated_request_org_id raises these if:
                 # - Org ID format invalid (ValidationError)
                 # - Org ID required but not provided for multi-org user (ValidationError)
                 # - Provided org ID invalid for single-org user (ValidationError)
                 # - User has no active orgs (PermissionDenied)
                 # - Provided org ID not in user's active list (PermissionDenied)
                 logger.info("[PermClass] Denying Create due to validation/permission error from helper: %s", e)
                 return False

         else:
             # For other non-object-level actions (like custom actions mapped at the viewset level)
             # or potentially for detail views before the object is fetched,
             # DRF might call has_permission. We should allow the request to proceed
             # so that has_object_permission can handle the specific object check later.
             logger.debug("[PermClass] Allowing non-list/create action '%s' in has_permission, deferring to has_object_permission if applicable.", view.action)
             return True # Allow request to proceed

     def has_object_permission(self, request, view, obj):
         """Check permissions for object-level actions (retrieve, update, delete)."""
         # CRITICAL: Superusers bypass all permission checks immediately
         if request.user and request.user.is_superuser:
             logger.debug("[PermClass] Superuser granted object permission automatically")
             return True
         
         # Authentication check
         user = request.user
         if not user or not user.is_authenticated:
             logger.debug("[PermClass] User not authenticated") 
             return False
         
         # Use the unified method to get permission, passing the object
         required_perm = self.get_required_permission(request, view, obj=obj)
         logger.debug("[PermClass] Required perm for obj action: %s", required_perm)

         if not required_perm:
             # If no specific permission mapped, deny access by default for safety
             logger.warning("[PermClass] Denying object action '%s' because required permission could not be determined.", view.action)
             return False

         # Use the org-aware helper function with the specific object
         has_perm = has_perm_in_org(user, required_perm, obj)
         logger.debug("[PermClass] has_object_permission result: %s", has_perm)
         return has_perm


class HasGeneralModelPermission(permissions.DjangoModelPermissions):
    """
    Permission class for general, non-organization-scoped models.
    
    This class uses Django's standard permission system without organization context,
    making it suitable for models that are not organization-scoped and should be
    accessible across organizations (e.g., UoM, Currency).
    
    This class is a slight extension of DjangoModelPermissions with additional
    support for view_* permissions and special handling for superusers.
    """
    
    # Add view permission support that may not be in base class
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }
    
    def has_permission(self, request, view):
        # Superusers bypass all permission checks
        if request.user and request.user.is_superuser:
            return True
            
        # Fall back to standard DjangoModelPermissions behavior
        return super().has_permission(request, view)
        
    def has_object_permission(self, request, view, obj):
        # Superusers bypass all permission checks
        if request.user and request.user.is_superuser:
            return True
            
        # Check if user has appropriate model-level permissions
        # DjangoModelPermissions doesn't have object-level checks, so we'll add basic support
        if not self.has_permission(request, view):
            return False
            
        # If user has model-level permissions and we're not checking object-specific permissions,
        # allow access. For true object-level permissions, subclass should override this method.
        return True