from rest_framework import permissions
from .permissions import has_perm_in_org # Import helper

def _get_required_permission(view_action, model_meta):
     """ Determine the required model permission based on view action """
     if view_action == 'list' or view_action == 'retrieve':
         return f'{model_meta.app_label}.view_{model_meta.model_name}'
     elif view_action == 'create':
         return f'{model_meta.app_label}.add_{model_meta.model_name}'
     elif view_action in ('update', 'partial_update'):
         return f'{model_meta.app_label}.change_{model_meta.model_name}'
     elif view_action == 'destroy':
         return f'{model_meta.app_label}.delete_{model_meta.model_name}'
     # Handle custom actions based on mapping or convention if needed
     return None

class HasModelPermissionInOrg(permissions.BasePermission):
     """
     Checks if user has the required model-level permission within the
     organization context (derived from object or target org for create).
     """
     # Optional: map actions to required permissions if not using convention
     # action_perm_map = {'list': 'view', 'retrieve': 'view', ...}

     def has_permission(self, request, view):
         # For LIST and CREATE (no specific object yet)
         # Check authentication first
         if not request.user or not request.user.is_authenticated:
              return False
         # Superuser bypass
         if request.user.is_superuser:
              return True

         # Ensure the view has a queryset to derive the model from
         if not hasattr(view, 'get_queryset'):
              return False
         
         queryset = view.get_queryset()
         model_meta = queryset.model._meta
         required_perm = _get_required_permission(view.action, model_meta)

         if not required_perm: 
              return False 

         if view.action == 'list':
             return True # Rely on OrganizationScopedViewSetMixin filtering
         elif view.action == 'create':
             return True # Let perform_create handle org-specific check
         else:
             return False

     def has_object_permission(self, request, view, obj):
         # For RETRIEVE, UPDATE, PARTIAL_UPDATE, DESTROY
         # Check authentication first
         if not request.user or not request.user.is_authenticated:
              return False
         # Superuser bypass
         if request.user.is_superuser:
              return True

         model_meta = obj._meta
         required_perm = _get_required_permission(view.action, model_meta)

         if not required_perm: return False # Action doesn't map to a standard permission

         # Use the org-aware helper function with the specific object
         return has_perm_in_org(request.user, required_perm, obj) 