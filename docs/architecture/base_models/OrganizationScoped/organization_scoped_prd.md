

# OrganizationScoped Mechanism - Product Requirements Document (PRD)

## 1. Overview

*   **Purpose**: To define the standard mechanism (`OrganizationScoped` abstract base model and associated filtering logic) for ensuring data segregation and multi-tenancy across the ERP system. This mechanism links various data models to the `Organization` entity and automatically filters data access based on the user's organizational context derived from `OrganizationMembership`.
*   **Scope**: Definition of the `OrganizationScoped` **Abstract Base Model**, the implementation of the automatic queryset filtering logic (enforcement) via a **ViewSet Mixin**, integration with the Org-Aware RBAC system for permission checking during data modification, and requirements related to applying and testing this mechanism.
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
    *   Example: `organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name='%(app_label)s_%(class)s_set', db_index=True)`
    *   `on_delete=models.PROTECT` recommended to prevent accidental data loss if an Organization is deleted.
*   **Purpose**: Structurally link inheriting models to a specific `Organization`.

### 3.2 Automatic Scoping Enforcement Logic (ViewSet Mixin)
*   **Goal**: Automatically filter querysets in API list/retrieve views so users only see records belonging to the organization(s) they are members of (via `OrganizationMembership`). Also, validate creation/modification permissions within the correct organizational context.
*   **Primary Implementation**: A **base API ViewSet Mixin** (e.g., `OrganizationScopedViewSetMixin`).
    *   **QuerySet Filtering (`get_queryset`)**:
        1. Access `request.user`. Handle unauthenticated users.
        2. Bypass filtering for Superusers.
        3. Get user's accessible organizations via `user.get_organizations()`.
        4. Filter the ViewSet's base queryset using `queryset.filter(organization__in=user_organizations)`.
    *   **Creation Validation (`perform_create`)**:
        1. Determine the target `organization` for the new record (e.g., from request data or URL).
        2. Verify the `request.user` has the necessary **model-level `add_modelname` permission *within the context of the target organization*** using the **Organization-Aware RBAC check function**.
        3. If permitted, call `serializer.save(organization=target_organization)`.
    *   **Update/Delete Validation:** Relies on standard DRF permission checks (`permission_classes` on the ViewSet) which **must** use the Organization-Aware RBAC checker to verify `change_modelname` or `delete_modelname` permission on the specific object being modified/deleted (within its `organization`).

## 4. Functional Requirements

### 4.1 Applying the Scope
*   **Model Inheritance**: Models needing org segregation **must** inherit `OrganizationScoped`.
*   **API View Inheritance**: ViewSets for scoped models **must** inherit the `OrganizationScopedViewSetMixin`.
*   **Data Creation (`perform_create` / Serializer `create`):**
    *   The `organization` field **must** be set when creating instances of scoped models.
    *   The source of the target `organization` must be determined (request data, URL context).
    *   The permission check (using Org-Aware RBAC) against the target organization **must** pass before saving.

### 4.2 Scoped Data Handling
*   **Default Filtering**: `GET` requests (List/Retrieve) are automatically filtered by the user's organization memberships via the ViewSet mixin's `get_queryset`.
*   **Permission Integration (Org-Aware RBAC):**
    *   All access control checks (View, Add, Change, Delete) performed by DRF `permission_classes` or within views/mixins **must** use the **organization-aware permission checking mechanism**.
    *   This check verifies if the user has the required Django model permission (`view_product`, `change_product`, etc.) granted via a role associated with their `OrganizationMembership` for the *specific organization* context of the data being accessed or created/modified.
    *   **No field-level permission checks** are implemented; access to all serializer fields is determined by the model-level permission for the action within the organization context.

## 5. Technical Requirements

### 5.1 Data Management & Performance
*   **Indexing:** The `organization` ForeignKey **must be indexed** on all inheriting concrete model tables.
*   **Query Efficiency:** The `queryset.filter(organization__in=...)` must be performant. `user.get_organizations()` must be efficient (likely involving caching strategies later).

### 5.2 Security
*   **Multi-Tenancy Enforcement:** The `get_queryset` filtering logic is the primary control for reads.
*   **Create/Update Security:** Validation within `perform_create` (and standard permission checks for update/delete) must ensure users can only modify data in organizations where they have appropriate model-level permissions (checked via Org-Aware RBAC). Users should generally not be able to change the `organization` field on update.
*   **Superuser Bypass:** Clearly implemented and tested.
*   **Auditability:** Audit logs for scoped data should include the `organization` context.

### 5.3 Integration
*   **User/Membership:** Relies on `User.get_organizations()` method querying `OrganizationMembership`.
*   **Base API Views:** Relies on developers using the `OrganizationScopedViewSetMixin`.
*   **Organization Model:** Dependency for the ForeignKey.
*   **RBAC System:** Relies heavily on the Org-Aware permission checking function being implemented and used by permission classes.

## 6. Non-Functional Requirements
*   Scalability (especially query performance), Reliability (filtering/permission checks must be correct), Availability, Testability.

## 7. API Documentation Requirements
*   Document `OrganizationScoped` inheritance requirement for developers creating new models.
*   State that relevant API endpoints are automatically filtered by user's organization memberships for read operations.
*   Document how the target `organization` is determined/provided during `POST` requests for creating scoped objects.
*   Explain that `add`/`change`/`delete` operations require appropriate model-level permissions within the specific organization context.
*   Document superuser behavior (bypasses filtering).

## 8. Testing Requirements
*   **Unit Tests**: Test `OrganizationScoped` abstract model definition. Test `user.get_organizations()` helper (already done).
*   **Integration Tests (ViewSet Mixin Logic - Mocking RBAC):** Test the `get_queryset` override in the base ViewSet Mixin for users in zero/one/multiple orgs. Test the `perform_create` logic by mocking the Org-Aware `has_perm` function to verify correct org determination, permission check call, and serializer save/denial.
*   **Integration Tests (Full Enforcement - After RBAC Implementation):**
    *   Test concrete scoped ViewSets (inheriting the mixin).
    *   **Data Isolation**: Verify User A (Org A) cannot see/access Org B data via LIST or RETRIEVE API calls.
    *   **Superuser Bypass**: Verify superuser sees data from all orgs.
    *   **Create Operations**: Test `POST` requests using the *real* Org-Aware permission check: verify success/failure based on user's actual role/permissions in the target organization.
    *   **Update/Delete Operations:** Verify standard model permissions (`change`/`delete`) are checked *using the real Org-Aware RBAC function* against the object's organization.
*   **Performance Tests**: Measure `organization__in` filter performance with many users/orgs/memberships.
*   **Security Tests**: Attempt to bypass org scoping filters. Attempt to create/modify data in unauthorized organizations.

## 9. Deployment Requirements
*   Migrations add `organization_id` column and index to inheriting models.
*   `OrganizationScopedViewSetMixin` deployed and used by relevant views.
*   **Org-Aware RBAC permission checking mechanism must be deployed and integrated into permission classes.**

## 10. Consumer Requirements (Developers)
*   Inherit `OrganizationScoped` abstract model for org-specific data.
*   Inherit `OrganizationScopedViewSetMixin` for associated API ViewSets.
*   Ensure creation logic correctly determines and provides the target `organization` (often via serializer `perform_create` will handle validation if serializer passes `organization` field).
*   Use standard DRF permission classes that have been configured to use the Org-Aware RBAC backend/checker.
