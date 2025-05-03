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
         print(f"[PermClass] has_permission called for action: {view.action}") # DEBUG
         user = request.user
         if not user or not user.is_authenticated: return False
         if user.is_superuser: return True

         # Need model to determine permission codename
         model_meta = None
         if hasattr(view, 'get_queryset'):
             queryset = view.get_queryset()
             if queryset is not None:
                 model_meta = queryset.model._meta
         elif hasattr(view, 'get_serializer'):
             serializer = view.get_serializer()
             if hasattr(serializer.Meta, 'model'):
                 model_meta = serializer.Meta.model._meta
         
         if not model_meta:
             print("[PermClass] Cannot determine model from view") # DEBUG
             return False # Cannot determine model

         required_perm = _get_required_permission(view.action, model_meta)
         print(f"[PermClass] Required perm for {view.action}: {required_perm}") # DEBUG

         if not required_perm: 
             print("[PermClass] No standard permission required for action") # DEBUG
             return False # Action doesn't map to a standard perm

         # For List/Create, the check is primarily done by get_queryset filtering
         # or perform_create. We allow the view to proceed if authenticated.
         # The actual org-specific permission check happens later.
         print("[PermClass] Allowing base permission for List/Create, deferring org check") # DEBUG
         return True 

     def has_object_permission(self, request, view, obj):
         # For RETRIEVE, UPDATE, PARTIAL_UPDATE, DESTROY
         print(f"[PermClass] has_object_permission called for action: {view.action} on obj {obj}") # DEBUG
         user = request.user
         if not user or not user.is_authenticated: return False
         if user.is_superuser: return True

         model_meta = obj._meta
         required_perm = _get_required_permission(view.action, model_meta)
         print(f"[PermClass] Required perm for obj action: {required_perm}") # DEBUG

         if not required_perm: return False

         # Use the org-aware helper function with the specific object
         has_perm = has_perm_in_org(user, required_perm, obj)
         print(f"[PermClass] has_object_permission result: {has_perm}") # DEBUG
         return has_perm 