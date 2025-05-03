# RBAC System (Org-Aware Model-Level) - Implementation Steps

## 1. Overview

**Component Name:**
Organization-Aware RBAC System

**Corresponding PRD:**
`rbac_prd.md` (Org-Aware Model-Level Permissions Only)

**Depends On:**
`Timestamped`, `Auditable`, Django `auth` app (`User`, `Group`, `Permission`), `ContentType` framework, `Organization`, `OrganizationMembership`, Caching strategy (`cache_redis.md`).

**Key Features:**
Implements organization-aware checking for standard Django model-level permissions using Roles (`Group`) assigned via `OrganizationMembership`. Focuses on a helper function and custom DRF permission classes.

**Primary Location(s):**
`rbac/` (New dedicated app) or potentially `core/`

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `User`, `Group`, `Permission`, `ContentType`, `Organization`, `OrganizationMembership`) are implemented and migrated.
[ ] **Create new Django app (if not done):** `python manage.py startapp rbac`. Add `'rbac'` to `INSTALLED_APPS`.
[ ] Ensure caching backend (Redis) and strategy are configured.
[ ] Ensure `factory-boy` is set up. Factories for `User`, `Group`, `Organization`, `OrganizationMembership` exist.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Org-Aware Permission Check Function (`rbac/permissions.py`)

  [ ] **(Test First)**
      Write **Unit Tests** (`rbac/tests/unit/test_permissions.py`) for the `has_perm_in_org` function.
      *   Setup: User, OrgA, OrgB, RoleAdmin (with `change_product`), RoleViewer (with `view_product`). Create OrgMemberships assigning User to OrgA as Admin, OrgB as Viewer.
      *   Mock `OrganizationMembership.objects.filter()` and `group.permissions.filter()` if needed for pure unit testing, or use `@pytest.mark.django_db` for integration testing of the helper.
      *   Test superuser -> always `True`.
      *   Test user `has_perm_in_org('products.change_product', org_a)` -> `True`.
      *   Test user `has_perm_in_org('products.view_product', org_a)` -> `True` (implicitly granted by change).
      *   Test user `has_perm_in_org('products.delete_product', org_a)` -> `False`.
      *   Test user `has_perm_in_org('products.change_product', org_b)` -> `False`.
      *   Test user `has_perm_in_org('products.view_product', org_b)` -> `True`.
      *   Test user with no membership in `org_a` -> `False` for any perm in `org_a`.
      *   Test user with membership but no role assigned in `org_a` -> `False`.
      *   Test passing an object instance instead of org -> verify org is extracted correctly.
      *   **(Optional - Caching)** Test cache gets/sets/invalidations if implementing caching here.
      Run; expect failure (`has_perm_in_org` doesn't exist or is incorrect).
  [ ] Create `rbac/permissions.py`. Define the `has_perm_in_org` function:
      ```python
      # rbac/permissions.py
      from functools import lru_cache
      from django.core.cache import caches
      from api.v1.base_models.organization.models import OrganizationMembership, Organization # Adjust path

      permission_cache = caches['permissions'] # Ensure 'permissions' cache configured

      # @lru_cache(maxsize=...) # Simple in-memory cache (per process)
      def has_perm_in_org(user, perm_codename, org_or_obj):
          """
          Checks if a user has a specific model-level permission within the
          context of a given organization or org-scoped object.
          """
          if not user or not user.is_authenticated:
              return False
          if user.is_superuser:
              return True

          # Determine the organization
          organization = None
          if isinstance(org_or_obj, Organization):
              organization = org_or_obj
          elif hasattr(org_or_obj, 'organization') and isinstance(getattr(org_or_obj, 'organization'), Organization):
              organization = org_or_obj.organization
          else:
              # Cannot determine organization context
              return False

          # --- Check Cache ---
          # cache_key = f'rbac:perms:user:{user.pk}:org:{organization.pk}'
          # cached_perms = permission_cache.get(cache_key)
          # if cached_perms is not None:
          #     return perm_codename in cached_perms
          # --- End Cache Check ---

          # Find active membership for this specific org
          try:
              membership = OrganizationMembership.objects.select_related('role__permissions')\
                                                 .get(user=user, organization=organization, is_active=True)
          except OrganizationMembership.DoesNotExist:
              # permission_cache.set(cache_key, set(), timeout=...) # Cache empty set
              return False

          if not membership.role:
              # permission_cache.set(cache_key, set(), timeout=...) # Cache empty set
              return False # No role assigned for this org

          # Check if the assigned role has the required permission
          has_perm = membership.role.permissions.filter(codename=perm_codename.split('.')[-1]).exists()

          # --- Set Cache (More complex: cache the *set* of perms for the role/org) ---
          # all_perms_for_role = set(membership.role.permissions.values_list('codename', flat=True))
          # permission_cache.set(cache_key, all_perms_for_role, timeout=...)
          # --- End Set Cache ---

          return has_perm

      # --- Cache Invalidation (Simplified Example - needs refinement) ---
      # Connect signals for OrganizationMembership save/delete and Group.permissions m2m_changed
      # In signal handler:
      # def invalidate_user_org_perm_cache(user_pk, org_pk):
      #     cache_key = f'rbac:perms:user:{user_pk}:org:{org_pk}'
      #     permission_cache.delete(cache_key)
      # --- End Cache Invalidation ---
      ```
      *(Note: Caching implementation details (key structure, invalidation) need careful design and testing)*.
  [ ] Run tests; expect pass. Refactor for clarity, performance, and robust caching.

  ### 3.2 Custom DRF Permission Classes (`rbac/drf_permissions.py`)

  [ ] **(Test First)**
      Write **Integration Tests** (`rbac/tests/integration/test_drf_permissions.py`) using `APIRequestFactory` and a sample ViewSet/View.
      *   Instantiate the custom permission classes (e.g., `HasModelPermissionInOrg`).
      *   Call `.has_permission(request, view)` and `.has_object_permission(request, view, obj)`.
      *   Mock the `has_perm_in_org` helper function.
      *   Test various scenarios: list/create (no obj), retrieve/update/delete (with obj), different required permissions (`view`, `add`, `change`, `delete`), user having/lacking permission according to the mock. Assert `True`/`False` return values.
      Run; expect failure.
  [ ] Create `rbac/drf_permissions.py`. Define custom DRF permission classes:
      ```python
      # rbac/drf_permissions.py
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
               user = request.user
               if not user or not user.is_authenticated: return False
               if user.is_superuser: return True

               queryset = view.get_queryset() # Get model info from view's queryset
               model_meta = queryset.model._meta
               required_perm = _get_required_permission(view.action, model_meta)

               if not required_perm: return False # Action doesn't map to a standard perm

               if view.action == 'list':
                   # Check if user has view permission in *any* of their orgs
                   # Optimization: Could check globally first user.has_perm(required_perm)
                   # More accurate: Check if get_queryset() after scoping returns anything
                   # Simplest: Allow list view if authenticated, rely on get_queryset filtering
                   return True # Rely on OrganizationScopedViewSetMixin filtering
               elif view.action == 'create':
                   # Permission checked more accurately in perform_create against target org
                   # Check if user has global add perm as a basic check?
                   # return user.has_perm(required_perm)
                   # Better: Defer definitive check to perform_create, allow view access here
                   return True # Let perform_create handle org-specific check
               else:
                   # Should not happen for standard view actions without an object
                   return False

           def has_object_permission(self, request, view, obj):
               # For RETRIEVE, UPDATE, PARTIAL_UPDATE, DESTROY
               user = request.user
               if not user or not user.is_authenticated: return False
               if user.is_superuser: return True

               model_meta = obj._meta
               required_perm = _get_required_permission(view.action, model_meta)

               if not required_perm: return False

               # Use the org-aware helper function with the specific object
               return has_perm_in_org(user, required_perm, obj)
      ```
  [ ] Run DRF permission tests; expect pass. Refactor permission classes.

  ### 3.3 ViewSet Permission Integration

  [x] **(Test First)** Write full API tests for sample ViewSets (e.g., `ProductViewSet`, `WarehouseViewSet`) that inherit `OrganizationScopedViewSetMixin`.
      *   Ensure the ViewSet's `permission_classes` includes the custom `HasModelPermissionInOrg` (or equivalent).
      *   Test LIST (ensure results are filtered by org *and* user has view perm).
      *   Test CREATE (ensure `perform_create` checks `add` perm in target org).
      *   Test RETRIEVE/UPDATE/DELETE (ensure `has_object_permission` checks `view`/`change`/`delete` perm against the object's org).
      *   Test with users in different roles/orgs.
  [x] Apply the custom permission classes to base ViewSets or specific ViewSets:
      ```python
      # api/v1/features/products/views.py (Example)
      from rbac.drf_permissions import HasModelPermissionInOrg # Adjust import

      class ProductViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
          # ... queryset, serializer_class ...
          permission_classes = [permissions.IsAuthenticated, HasModelPermissionInOrg] # Apply custom class
          # ...
      ```
  [x] **Crucially:** Ensure the `perform_create` method in `OrganizationScopedViewSetMixin` is now using the *real* `has_perm_in_org` function (update the import if it was using a placeholder).
  [ ] Run full API tests for scoped models; expect pass. Refactor integration points.

  ### 3.4 Define Roles & Assign Permissions (Admin/Data Migration)

  [ ] **(Manual/Data Migration)**
      *   Define necessary Roles (`Group` instances) via Django Admin or a data migration (e.g., 'Admin', 'Manager', 'Viewer', 'Sales Rep').
      *   Assign appropriate standard model permissions (`view_product`, `add_product`, `change_organization`, etc.) to these Roles using the standard Django Admin interface for Groups.

  ### 3.5 Assign Users to Roles in Orgs (Admin/API)

  [ ] **(Manual/API/Admin)** Use the existing `OrganizationMembership` management tools (Admin or API, if built) to assign users to organizations with specific roles.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`). Verify all permission-related tests (unit, integration, API) pass for various user/role/org combinations.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=rbac`). Review uncovered lines in permission logic, helpers, DRF classes.
[ ] Manually test API interactions with different user roles logged in. Verify they can/cannot perform expected actions (CRUD) on org-scoped data based on their assigned role via `OrganizationMembership`.
[ ] Review RBAC documentation (PRD, API docs).

## 5. Follow-up Actions

[ ] Address TODOs (e.g., Refine caching strategy, implement cache invalidation).
[ ] Create Pull Request(s).
[ ] Update API documentation explaining how permissions are checked based on roles assigned per organization.
[ ] Document the standard Roles created and their intended permission sets.

---