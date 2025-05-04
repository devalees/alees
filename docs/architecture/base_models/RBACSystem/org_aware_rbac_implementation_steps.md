# Organization-Aware RBAC - Implementation Steps

## 1. Overview

**Goal:**
Implement an RBAC system that integrates tightly with organization scoping. Users belonging to a single active organization should have their organization context handled automatically. Users in multiple active organizations must explicitly specify the target organization for relevant operations. The system relies on caching user organization affiliations and permissions for performance.

**Depends On:**
`OrganizationMembership`, `User.get_organizations`, `core.rbac` (base RBAC functions like `has_perm_in_org`), Django Caching framework, `rest_framework_simplejwt` (for login hook).

**Key Features:**
*   Automatic organization scoping for single-org users.
*   Explicit organization selection enforcement for multi-org users.
*   Cached user organization lists (`active_org_ids`) and permissions (`rbac:perms:user:X:org:Y`).
*   Centralized permission checking respecting the user's selected or inferred organization context.
*   Secure and efficient queryset filtering based on user's accessible organizations.

**Primary Location(s):**
Modifications span across `core/rbac/`, `core/models.py` (`OrganizationScoped`), `api/v1/base_models/common/auth/` (login view/serializer), `api/v1/base_models/user/` (helper method), potentially base serializer/viewset mixins, and specific ViewSets like `OrganizationViewSet`.

## 2. Prerequisites

[ ] Verify `OrganizationMembership` model and related components (serializer, view) are implemented.
[ ] Verify `User.get_organizations()` method exists and functions correctly (filtering active memberships).
[ ] Verify `core.rbac.permissions.has_perm_in_org` function exists.
[ ] Verify `core.rbac.signals` exist for basic permission cache invalidation.
[ ] Verify Django Caching is configured (`settings.CACHES`), including 'default' and 'rbac' aliases.
[ ] Verify JWT authentication (`rest_framework_simplejwt`) is configured.
[ ] Identify all models that inherit or should inherit from `core.models.OrganizationScoped`.
[ ] Identify all ViewSets managing `OrganizationScoped` models.

## 3. Implementation Steps (TDD Workflow)

### 3.1 RBAC Cache Configuration

[ ] **(Verify)** Confirm `settings.CACHES` defines 'default' and 'rbac' backends (e.g., Redis).
[ ] **(Verify)** Confirm `settings.RBAC_CACHE_TIMEOUT` exists or set a default value.

### 3.2 RBAC Helper Functions (`core/rbac/utils.py` or `permissions.py`)

[ ] **(Test First)** Write unit tests for `get_user_request_context`. Test scenarios: authenticated user (cache hit/miss, single/multi/no orgs), unauthenticated user.
[ ] **(Implement)** Create `get_user_request_context(user)` function to retrieve `active_org_ids` from cache (with DB fallback/rebuild on miss).
[ ] **(Test First)** Write unit tests for `get_validated_request_org_id`. Test scenarios: single/multi-org user, org ID provided/not provided, invalid ID provided, action requires/doesn't require ID.
[ ] **(Implement)** Create `get_validated_request_org_id(request, required_for_action)` function to determine the target org ID based on context and request data, raising appropriate errors (`ValidationError`, `PermissionDenied`).
[ ] Run helper tests; expect pass. Refactor.

### 3.3 Login Cache Population (`common/auth/views.py` or `serializers.py`)

[ ] **(Test First)** Write integration/API test for login. After successful login, assert that cache keys `user:<pk>:active_org_ids` and `rbac:perms:user:<pk>:org:<org_pk>` (for each active org) are populated correctly.
[ ] **(Implement)** Modify `CustomTokenObtainPairView.post` or `CustomTokenObtainPairSerializer.validate`/`get_token` method.
    *   After successful authentication, get the `user`.
    *   Call `user.get_organizations()`.
    *   Cache the list of `active_org_ids`.
    *   Iterate active memberships, fetch permissions per role, and cache them using the `rbac:perms:user:X:org:Y` key format.
[ ] Run login cache tests; expect pass. Refactor.

### 3.4 Enhance Cache Invalidation Signals (`core/rbac/signals.py`)

[ ] **(Test First)** Write tests ensuring that saving/deleting an `OrganizationMembership` invalidates *both* the specific `rbac:perms:user:X:org:Y` key *and* the user's `user:X:active_org_ids` list key.
[ ] **(Implement)** Modify `invalidate_on_membership_save` and `invalidate_on_membership_delete` signals to delete the `user:X:active_org_ids` cache key in addition to the permission cache key.
[ ] Run signal tests; expect pass. Refactor.

### 3.5 Refine Permission Check Function (`core/rbac/permissions.py`)

[ ] **(Test First)** Update tests for `has_perm_in_org` to verify it works correctly when passed an integer `organization_id` instead of an object.
[ ] **(Implement)** Modify `has_perm_in_org` to handle an integer `org_or_obj` argument, using it directly as the `organization_id` for cache keys and DB lookups.
[ ] Run `has_perm_in_org` tests; expect pass. Refactor.

### 3.6 Refine DRF Permission Class (`core/rbac/drf_permissions.py`)

[ ] **(Test First)** Write/update API tests for `list` and `create` actions on a sample `OrganizationScoped` ViewSet protected by `HasModelPermissionInOrg`.
    *   Test single-org user: Auto-scoping works, providing org ID fails.
    *   Test multi-org user: Providing valid org ID works, not providing org ID fails (for `create`), providing invalid org ID fails.
    *   Test permission denial based on role in the target org.
[ ] **(Implement)** Modify `HasModelPermissionInOrg.has_permission`:
    *   Use `get_user_request_context` to get user's org status.
    *   For `create` and potentially `list` actions, use `get_validated_request_org_id` to determine the target organization.
    *   Check permission using `has_perm_in_org(user, perm_codename, target_org_id)`. Adjust `list` logic based on desired behavior (filter by one requested org or allow if perm exists in *any* org).
[ ] **(Implement)** Remove the redundant `CanAccessOrganizationObject` class.
[ ] Run relevant API tests; expect pass. Refactor.

### 3.7 Organization-Scoped Serializer Logic (Mixin or Base Class)

[ ] **(Test First)** Write unit tests for serializer validation logic. Test single/multi-org user creating an object, providing/not providing organization field.
[ ] **(Implement)** Create `OrganizationScopedSerializerMixin` (or modify a base serializer).
    *   Implement `validate` method to check `organization` field based on `get_user_request_context`: enforce not provided for single-org, require valid for multi-org (on create).
    *   Implement `create` method to automatically set `validated_data['organization_id']` for single-org users using `get_user_request_context`.
[ ] Run serializer tests; expect pass. Refactor.

### 3.8 Organization-Scoped ViewSet Queryset Filtering (Mixin or Base Class)

[ ] **(Test First)** Write API tests for `list` actions on sample `OrganizationScoped` ViewSets. Verify superusers see all, regular users only see objects from their `active_org_ids`.
[ ] **(Implement)** Create `OrganizationScopedViewSetMixin` (or modify a base ViewSet).
    *   Override `get_queryset`.
    *   Filter the base queryset by `organization_id__in=active_org_ids` (obtained via `get_user_request_context`) for non-superusers. Handle users with no active orgs (return `queryset.none()`).
[ ] Run relevant list API tests; expect pass. Refactor.

### 3.9 Integrate Mixins/Base Classes

[ ] **(Implement)** Identify all ViewSets managing `OrganizationScoped` models. Inherit from `OrganizationScopedViewSetMixin` and ensure `permission_classes` includes `HasModelPermissionInOrg`.
[ ] **(Implement)** Identify all Serializers for `OrganizationScoped` models. Inherit from `OrganizationScopedSerializerMixin`. Adjust `organization` field definition (e.g., `read_only=True`, `required=False/True`).
[ ] **(Test)** Rerun API tests for affected ViewSets (CRUD, list).

### 3.10 Refactor `OrganizationViewSet` (`organization/views.py`)

[ ] **(Test First)** Update API tests for `OrganizationViewSet` to ensure permissions and listing adhere to the new RBAC logic.
[ ] **(Implement)** Replace `permissions.DjangoModelPermissions` with `HasModelPermissionInOrg` in `get_permissions`.
[ ] **(Implement)** Modify `get_queryset` to filter by user's `active_org_ids` using `get_user_request_context`.
[ ] Run `OrganizationViewSet` API tests; expect pass. Refactor.

### 3.11 Refactor `OrganizationMembershipViewSet` (Optional) (`organization/views.py`)

[ ] **(Decide)** Determine if membership management remains admin/self-service (`IsAdminOrReadOwnMemberships`) or uses granular RBAC (`HasModelPermissionInOrg`).
[ ] **(Implement)** If using granular RBAC:
    *   Define necessary permissions (`add/change/delete/view_organizationmembership`).
    *   Assign permissions to appropriate Roles (Groups).
    *   Replace `IsAdminOrReadOwnMemberships` with `HasModelPermissionInOrg`.
    *   Update `get_queryset` if necessary (though filtering by user's orgs might still be relevant).
[ ] **(Test)** Update/write API tests based on the chosen permission strategy.

### 3.12 Refactor `OrganizationMembershipSerializer` (`organization/serializers.py`)

[ ] **(Test First)** Update serializer tests to specifically check validation against the `(user, organization)` uniqueness constraint.
[ ] **(Implement)** Modify the `validate` method in `OrganizationMembershipSerializer` to check `OrganizationMembership.objects.filter(user=attrs['user'], organization=attrs['organization'])`.
[ ] Run serializer tests; expect pass. Refactor.

### 3.13 Refactor `OrganizationScoped.save` (`core/models.py`)

[ ] **(Test First)** Ensure model tests verify organization immutability on update.
[ ] **(Implement)** Simplify the `save` method, potentially removing auto-population logic if serializers handle it reliably. Focus on the immutability check for updates.
[ ] Run model tests; expect pass. Refactor.


## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`). Address any failures.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov`). Aim for high coverage in modified areas (`core/rbac`, mixins, etc.).
[ ] Manually test key workflows:
    *   Login as single-org user -> Create/List/View scoped objects (org field hidden/auto).
    *   Login as multi-org user -> Create/List/View scoped objects (org field required/validated). Test switching org context if applicable.
    *   Test permission denial scenarios.
    *   Test cache invalidation (e.g., deactivate membership, check access changes).
[ ] Review API documentation for changes (e.g., required 'organization' field for multi-org users).

## 5. Follow-up Actions

[ ] Address any TODOs left in the code.
[ ] Create Pull Request(s) for review.
[ ] Update project documentation (Architecture diagrams, READMEs).
[ ] Monitor application performance and cache hit rates after deployment.

## 6. Implementation Notes

### 6.1 Key Decisions Made

*   Centralized organization context retrieval via `get_user_request_context`.
*   Centralized organization validation/determination via `get_validated_request_org_id`.
*   Leveraging cache for user's active organizations and permissions per organization.
*   Enforcing org specification differences between single/multi-org users primarily at the Permission and Serializer layers.
*   Using Mixins/Base Classes for reusable ViewSet (queryset filtering) and Serializer (validation/population) logic for `OrganizationScoped` models.

### 6.2 Testing Strategy

*   Unit tests for helper functions, model methods, serializer validation, signal handlers.
*   Integration/API tests for login flow (cache population), permission class behavior (view/object level), ViewSet CRUD operations, and queryset filtering. Focus on testing both single-org and multi-org user scenarios.

### 6.3 Current Status

*   Planning phase complete. Implementation steps defined.

### 6.4 Next Steps

*   Begin implementation following the steps outlined above, adhering to the TDD workflow.

--- END OF FILE org_aware_rbac_implementation_steps.md --- 