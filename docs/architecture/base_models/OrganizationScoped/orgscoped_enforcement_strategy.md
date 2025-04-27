

This document will focus on *how* the `OrganizationScopedViewSetMixin` (or similar base class) will achieve the automatic filtering and creation control, integrating with the multi-organization setup (`OrganizationMembership`) and the simplified Org-Aware RBAC.

--- START OF FILE orgscoped_enforcement_strategy.md ---

# Organization Scoped Enforcement - Strategy & Plan

## 1. Overview

*   **Purpose**: To outline the strategy for implementing the runtime enforcement logic for Organization Scoping (Multi-Tenancy) within API ViewSets.
*   **Scope**: Focuses on the design and implementation of a reusable base class or mixin (`OrganizationScopedViewSetMixin`) that automatically filters querysets and controls object creation based on the requesting user's organization memberships and permissions.
*   **Context**: This follows the definition of the `OrganizationScoped` abstract base model (which adds the `organization` ForeignKey) and the implementation of the `OrganizationMembership` model (linking Users to Organizations with Roles). It assumes an Org-Aware RBAC mechanism exists (`has_perm_in_org`).

## 2. Core Requirements

1.  **Automatic QuerySet Filtering**: `GET` requests (List/Retrieve) for resources inheriting `OrganizationScoped` must automatically return only objects belonging to the organization(s) the authenticated user is an active member of (via `OrganizationMembership`). Superusers should bypass this filtering.
2.  **Controlled Creation**: `POST` requests creating `OrganizationScoped` objects must ensure the object is assigned to a valid `Organization`. The system must verify the authenticated user has the necessary `add_model` permission *within that specific target Organization*.
3.  **Prevent Scope Change (Default):** By default, users should not be able to change the `organization` field of an existing scoped object via `PUT`/`PATCH` unless specifically allowed by fine-grained permissions (which are currently out of scope with the simplified RBAC).
4.  **Reusability**: The enforcement logic should be implemented in a reusable mixin or base class inherited by all ViewSets managing `OrganizationScoped` models.
5.  **Performance**: The filtering and permission checks must be performant, leveraging database indexes and caching where appropriate.

## 3. Implementation Strategy

### 3.1. Base ViewSet Mixin (`OrganizationScopedViewSetMixin`)

*   **Location:** `core/views.py` or `api/v1/base_views.py` (or similar shared location).
*   **Inheritance:** ViewSets for `OrganizationScoped` models (e.g., `ProductViewSet`, `WarehouseViewSet`, `DocumentViewSet`) will inherit from this mixin *in addition* to their standard DRF base (e.g., `viewsets.ModelViewSet`).
    ```python
    # Example:
    from core.views import OrganizationScopedViewSetMixin
    from rest_framework import viewsets

    class ProductViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
        # ... queryset, serializer_class, permissions ...
    ```

### 3.2. QuerySet Filtering (`get_queryset` Override)

*   The `OrganizationScopedViewSetMixin` will override the `get_queryset` method.
*   **Logic:**
    1.  Call `super().get_queryset()` to get the base queryset defined in the inheriting ViewSet.
    2.  Get `request.user`. Handle unauthenticated users (return `queryset.none()`).
    3.  Check `if user.is_superuser`: return the unfiltered base queryset.
    4.  Call `orgs = user.get_organizations()` (this helper queries `OrganizationMembership` and returns a QuerySet or list of active `Organization` instances the user belongs to).
    5.  If `orgs` is empty, return `queryset.none()`.
    6.  Filter the base queryset: `queryset.filter(organization__in=orgs)`.
*   **Dependencies:** `User.get_organizations()` method, `Organization` model.

### 3.3. Creation Control (`perform_create` Override)

*   The `OrganizationScopedViewSetMixin` will override the `perform_create` method.
*   **Logic:**
    1.  Get `request.user`. Handle unauthenticated (usually prevented by higher-level permissions).
    2.  **Determine Target Organization:**
        *   The target `organization` (PK) **must** be provided in the `serializer.validated_data` (meaning it was included in the request body and validated by the serializer). *Rationale: If a user belongs to multiple orgs, the system cannot guess where the new object should belong.*
        *   Fetch the `target_org = Organization.objects.get(pk=org_pk)`. Handle `DoesNotExist`.
    3.  **Check User Membership (Optional but Recommended):** Verify that the `target_org` is actually one of the organizations the `request.user` belongs to (i.e., it's in `user.get_organizations()`). This prevents users from creating data in orgs they aren't members of, even if they somehow bypass other permission checks.
    4.  **Check Permission:**
        *   Determine the required permission codename (e.g., `f"{serializer.Meta.model._meta.app_label}.add_{serializer.Meta.model._meta.model_name}"`).
        *   Call the Org-Aware RBAC function: `has_perm_in_org(user, add_perm, target_org)`.
        *   If `False`, raise `PermissionDenied`.
    5.  **Save:** Call `serializer.save(organization=target_organization)`. Pass the validated `target_organization` instance to the serializer's `save` method so it gets set on the model instance.
*   **Serializer Requirement:** The serializer used by the ViewSet (e.g., `ProductSerializer`) needs an `organization` field that is writable (e.g., `serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all(), write_only=True)`) so the target organization PK can be accepted and validated in the request payload.

### 3.4. Update/Delete Control

*   **Organization Field:** The `organization` field in serializers for scoped models should generally be `read_only=True` to prevent changing an object's scope after creation.
*   **Permission Checks:** Standard `permission_classes` on the ViewSet, using the Org-Aware RBAC check, will handle `change_model` and `delete_model` permissions. The `get_object()` method (which implicitly uses `get_queryset`) ensures the user can only retrieve (and thus attempt to update/delete) objects within their allowed scope *before* the permission check even runs.

### 3.5. Caching Considerations

*   The results of `user.get_organizations()` can be cached per-request or longer-term (with proper invalidation) to improve performance of `get_queryset`.
*   The results of the Org-Aware `has_perm_in_org` check should also be cached aggressively (as per the RBAC strategy).

## 4. Implementation Plan Integration

*   The **Mixin Definition** (`OrganizationScoped` abstract model) is implemented early (Phase 1, Step 11).
*   Models start inheriting the abstract model as they are implemented (e.g., `Product`, `Warehouse` in Phase 3). Migrations add the `organization_id` column.
*   The **Enforcement Logic** (`OrganizationScopedViewSetMixin` implementation) is deferred until **Phase 2 (Step 21)** *after* `OrganizationMembership` and the Org-Aware RBAC checks are implemented, as the mixin relies on these components.
*   Once the mixin is implemented, existing and future ViewSets for scoped models will inherit it.

## 5. Testing Plan

*   Focus integration tests (as outlined in the `OrganizationScoped` PRD's testing section) on verifying the `get_queryset` filtering and the `perform_create` logic within the context of the `OrganizationScopedViewSetMixin` applied to test ViewSets. Ensure data isolation, correct organization assignment on create, and proper permission checks against the target organization.

--- END OF FILE orgscoped_enforcement_strategy.md ---

This document provides the high-level plan for implementing the enforcement part, clarifying the dependencies and the expected logic within the ViewSet mixin, setting the stage for the detailed implementation steps later.