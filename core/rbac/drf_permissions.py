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

     # Restore the helper method to get permission codename
     def get_required_permission(self, request, view):
         # Default mapping from DRF/Django conventions
         action_map = {
             'list': 'view',
             'retrieve': 'view',
             'create': 'add',
             'update': 'change',
             'partial_update': 'change',
             'destroy': 'delete',
         }
         # Get the model from the view
         model_cls = None
         if hasattr(view, 'get_queryset'):
             queryset = view.get_queryset()
             if queryset is not None:
                 model_cls = queryset.model
         elif hasattr(view, 'get_serializer_class'):
             serializer_cls = view.get_serializer_class()
             if hasattr(serializer_cls, 'Meta') and hasattr(serializer_cls.Meta, 'model'):
                 model_cls = serializer_cls.Meta.model
         
         if not model_cls:
             print("[PermClass] Cannot determine model from view for permission check") # DEBUG
             return None

         # Determine required action prefix (view, add, change, delete)
         action_prefix = action_map.get(view.action)
         if not action_prefix:
             # Allow custom actions or OPTIONS by default
             print(f"[PermClass] No standard permission prefix for action: {view.action}") # DEBUG
             return None

         # Construct the permission codename
         perm_codename = f'{action_prefix}_{model_cls._meta.model_name}'
         # Return the full codename including app_label
         return f'{model_cls._meta.app_label}.{perm_codename}'

     def has_permission(self, request, view):
         # For LIST and CREATE (no specific object yet)
         print(f"[PermClass] has_permission called for action: {view.action}") # DEBUG
         user = request.user
         if not user or not user.is_authenticated: return False
         if user.is_superuser: return True

         # Determine required permission codename
         perm_codename = self.get_required_permission(request, view)
         print(f"[PermClass] Required perm for {view.action}: {perm_codename}") # DEBUG
         if not perm_codename:
             # No specific permission needed for this action (e.g., OPTIONS)
             return True

         if view.action == 'create':
             # For create, permission is checked against the target org in perform_create
             # Allow the request to proceed to the view's perform_create
             print("[PermClass] Allowing base permission for Create, deferring org check") # DEBUG
             return True 
         elif view.action == 'list':
             # For list, check if user has view permission in *any* of their orgs
             # The queryset filtering will handle showing only accessible data
             user_orgs = user.get_organizations()
             if not user_orgs.exists():
                 print("[PermClass] Denying List: User has no organizations") # DEBUG
                 return False # User isn't in any org, can't list anything
             
             # Check if the user has the view perm in at least one of their orgs
             # This prevents users without view perms anywhere from hitting the list endpoint
             # Note: has_perm_in_org uses caching
             has_view_perm_somewhere = any(
                 has_perm_in_org(user, perm_codename, org) 
                 for org in user_orgs
             )
             print(f"[PermClass] List permission check (has_view_perm_somewhere): {has_view_perm_somewhere}") # DEBUG
             return has_view_perm_somewhere
         else:
             # For other non-object actions (if any), default deny?
             # Or assume permission if it reaches here? Let's default allow for now.
             print(f"[PermClass] Allowing non-list/create action '{view.action}' by default") # DEBUG
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

         if not required_perm:
             # If no specific permission mapped, deny access by default for safety
             # unless it's a known safe action (like OPTIONS)
             # Revisit if specific custom actions need permission bypass
             return False # Deny if permission cannot be determined

         # Use the org-aware helper function with the specific object
         has_perm = has_perm_in_org(user, required_perm, obj)
         print(f"[PermClass] has_object_permission result: {has_perm}") # DEBUG
         return has_perm 