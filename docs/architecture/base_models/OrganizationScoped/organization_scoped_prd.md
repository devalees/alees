

# OrganizationScoped Mechanism - Product Requirements Document (PRD) (Revised for Simple Org-Aware RBAC)

## 1. Overview

*   **Purpose**: To define the standard mechanism (`OrganizationScoped` abstract base model and associated filtering logic) for ensuring data segregation and multi-tenancy across the ERP system. This mechanism links various data models to the `Organization` entity and automatically filters data access based on the user's organizational context derived from `OrganizationMembership`.
*   **Scope**: Definition of the `OrganizationScoped` **Abstract Base Model**, the implementation of the automatic queryset filtering logic (enforcement), integration with the Org-Aware RBAC system, and requirements related to applying and testing this mechanism.
*   **Target Users**: System Developers (implementing models that inherit this abstract model), System Architects (designing data segregation), Security Auditors (verifying multi-tenancy).

## 2. Business Requirements

*   **Mandatory Data Segregation**: Ensure data associated with one organization is not accessible by users unless they have membership/permissions within that specific organization.
*   **Consistent Scoping Implementation**: Provide a single, reusable pattern for organization-level data isolation.
*   **Transparency for End-Users**: Standard data access automatically applies organizational filters based on the user's memberships.

## 3. Core Scoping Mechanism Implementation

### 3.1 Abstract Base Model Definition (`OrganizationScoped`)
*   **Implementation**: Defined as a Django **Abstract Base Model** (inherits `models.Model`, `Meta: abstract = True`).
*   **Location**: Shared location (e.g., `core/models.py`).
*   **Core Field**: Contains a non-nullable `ForeignKey` to `Organization`.
    *   Example: `organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name='%(app_label)s_%(class)s_set', db_index=True)` *(Added `db_index=True`)*
    *   `on_delete=models.PROTECT` recommended.
*   **Purpose**: Structurally link inheriting models to a specific `Organization`.

### 3.2 Automatic Scoping Enforcement Logic (QuerySet Filtering)
*   **Goal**: Automatically filter querysets so users only retrieve records belonging to the organization(s) they are members of (via `OrganizationMembership`).
*   **Primary Implementation**: Override `get_queryset` method within a **base API ViewSet Mixin** (e.g., `OrganizationScopedViewSetMixin`).
    *   **Logic**:
        1. Access `request.user`.
        2. Handle unauthenticated users (return `queryset.none()` or raise error).
        3. **Bypass for Superusers:** If `user.is_superuser`, return `super().get_queryset()`.
        4. **Get User Orgs:** Call `user.get_organizations()` (which queries `OrganizationMembership`).
        5. If no organizations returned, return `queryset.none()`.
        6. **Filter Queryset:** Return `super().get_queryset().filter(organization__in=user_organizations)`.
*   **Rationale**: Centralizes filtering logic, uses request context.

## 4. Functional Requirements

### 4.1 Applying the Scope
*   **Model Inheritance**: Models needing org segregation **must** inherit `OrganizationScoped`.
*   **API View Inheritance**: ViewSets for scoped models **must** inherit the `OrganizationScopedViewSetMixin`.
*   **Data Creation (`perform_create` / Serializer `create`):**
    *   The `organization` field **must** be set when creating instances of scoped models.
    *   **Source of Organization:** The target `organization` for new records **must** be determined, typically from:
        *   **Explicit Request Data:** An `organization` field in the API request payload (e.g., `{"name": "...", "organization": "<org_pk>"}`).
        *   **URL Context:** If using nested URLs like `/organizations/{org_pk}/products/`.
        *   **(Less Ideal)** User's "default" or "current active" organization context (requires additional state management).
    *   **Permission Check:** Before saving, the logic **must** verify the `request.user` has the necessary **model-level `add_modelname` permission *within the context of the target organization*** (using the Org-Aware RBAC check function).

### 4.2 Scoped Data Handling
*   **Default Filtering**: `GET` requests (List/Retrieve) are automatically filtered by the user's organization memberships via the ViewSet mixin.
*   **Permission Integration (Org-Aware RBAC):**
    *   All access control checks (View, Add, Change, Delete) performed by DRF `permission_classes` or within views **must** use the **organization-aware permission checking mechanism** defined in the `rbac_strategy_org_aware.md`.
    *   This check verifies if the user has the required Django model permission (`view_product`, `change_product`, etc.) granted via a role associated with their `OrganizationMembership` for the *specific organization* context of the data being accessed or created.
    *   **Field-level permission checks are removed.** Access to fields is granted if the user has the relevant model-level permission (e.g., `change_model`) for that organization.

## 5. Technical Requirements

### 5.1 Data Management & Performance
*   **Indexing:** The `organization` ForeignKey **must be indexed** on all inheriting concrete model tables. *(This is now default on the abstract model's FK definition)*.
*   **Query Efficiency:** The `queryset.filter(organization__in=...)` must be performant. `user.get_organizations()` (querying `OrganizationMembership`) must be efficient.

### 5.2 Security
*   **Multi-Tenancy Enforcement:** The `get_queryset` filtering logic is the core control.
*   **Create/Update Security:** Validation within `perform_create`/serializers must ensure users can only assign data to organizations where they have appropriate `add_model` permissions (checked via Org-Aware RBAC). Users should not be able to change the `organization` field on update unless specifically permitted.
*   **Superuser Bypass:** Clearly implemented and tested.
*   **Auditability:** Audit logs for scoped data should include the `organization` context.

### 5.3 Integration
*   **User/Membership:** Relies on `User.get_organizations()` method querying `OrganizationMembership`.
*   **Base API Views:** Relies on developers using the `OrganizationScopedViewSetMixin`.
*   **Organization Model:** Dependency for the ForeignKey.
*   **RBAC System:** Relies on the Org-Aware permission checking function (`has_perm_in_org(...)` or similar).

## 6. Non-Functional Requirements
*   Scalability, Performance, Reliability, Testability (as before).

## 7. API Documentation Requirements
*   Document `OrganizationScoped` inheritance requirement for developers.
*   State that relevant API endpoints are automatically filtered by user's organization memberships.
*   Document how the target `organization` is determined/provided during `POST` requests for creating scoped objects.
*   Document superuser behavior.

## 8. Testing Requirements
*   **Unit Tests**: Test `OrganizationScoped` abstract model definition. Test `user.get_organizations()` helper.
*   **Integration Tests**:
    *   **Core Logic Verification**: Test the `get_queryset` override in the base ViewSet Mixin for users in zero/one/multiple orgs.
    *   **Data Isolation**: Verify User A (Org A) cannot see/access Org B data via LIST or RETRIEVE API calls for scoped models.
    *   **Superuser Bypass**: Verify superuser sees data from all orgs.
    *   **Create Operations**: Test `POST` requests:
        *   Verify `organization` field is correctly set based on request data/context.
        *   Verify user without `add_model` permission *in the target organization* gets 403 Forbidden.
        *   Verify user *with* `add_model` permission *in the target organization* gets 201 Created.
    *   **Update/Delete Operations:** Verify standard model permissions are checked *within the organization scope* of the object being modified/deleted.
*   **Performance Tests**: Measure `organization__in` filter performance.
*   **Security Tests**: Attempt to bypass org scoping filters. Attempt to create/modify data in unauthorized organizations.

## 9. Deployment Requirements
*   Migrations add `organization_id` column and index to inheriting models.
*   `OrganizationScopedViewSetMixin` deployed and used by relevant views.
*   Org-Aware RBAC permission checking mechanism must be deployed.

## 10. Consumer Requirements (Developers)
*   Inherit `OrganizationScoped` abstract model for org-specific data.
*   Inherit `OrganizationScopedViewSetMixin` for associated API ViewSets.
*   Ensure creation logic correctly determines and validates the target `organization` based on request context and Org-Aware permissions.
*   Use the Org-Aware permission checking functions for any manual authorization logic.
