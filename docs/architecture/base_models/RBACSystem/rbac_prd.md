
## Updated: `rbac_prd.md` (Org-Aware Model-Level Permissions Only)

# Role-Based Access Control (RBAC) System - Product Requirements Document (PRD)

## 1. Overview

*   **Purpose**: To define a flexible Role-Based Access Control (RBAC) system for the ERP, enabling control over user actions based on assigned roles **within specific organizational contexts**. The system focuses on managing standard Django **model-level permissions**.
*   **Scope**: Definition of Role (`Group`) usage, standard `Permission` usage, assignment of Roles to Users **via `OrganizationMembership`**, mechanisms for checking model-level permissions within an organization context, and integration with core ERP modules. **Excludes field-level permission control.**
*   **Relationship to Django Auth**: This system **utilizes and extends** Django's built-in authentication and authorization framework (`User`, `Group`, `Permission`). Django `Group` will be used to represent Roles. Django `Permission` will handle model-level access (`add`, `change`, `view`, `delete`). `OrganizationMembership` provides the link between User, Organization, and Role.
*   **Target Users**: System Administrators, Security Managers, Application Developers.

## 2. Business Requirements

*   Assign permissions to users based on defined business roles, applied **within the context of specific organizations** they belong to.
*   Control access to view, create, modify, and delete data across different modules (Model-Level CRUD via standard Django permissions).
*   Control access to specific custom actions within modules (Model-Level via custom Django permissions).
*   *(Future)* Optionally support hierarchical roles where permissions can be inherited. *(Initial implementation assumes flat roles/groups per organization membership)*.
*   Ensure access control is enforced consistently across APIs, respecting organizational boundaries.
*   Provide audit trails for role/permission assignments.

## 3. Core RBAC Models & Structures

### 3.1 `Role` Model (`django.contrib.auth.models.Group`)
*   **Implementation**: Use Django's built-in `django.contrib.auth.models.Group`.
*   **Conceptual Name**: Treat `Group` as `Role` within the application context.
*   **Fields Used**: `name`, `permissions` (ManyToManyField to `django.contrib.auth.models.Permission`).
*   **Scoping**: Django Groups are global. A Role definition applies system-wide. Assignment to a user *within an organization* is handled by `OrganizationMembership`.

### 3.2 `Permission` Model (`django.contrib.auth.models.Permission`)
*   **Implementation**: Use Django's built-in `django.contrib.auth.models.Permission`.
*   **Usage**: Handles **model-level** permissions (e.g., `app_label.add_modelname`, `app_label.change_modelname`, `app_label.delete_modelname`, `app_label.view_modelname`).
*   **Custom Permissions**: Custom model-level actions defined via model `Meta.permissions`.

### 3.3 User-Organization-Role Assignment (`OrganizationMembership` Model)
*   **Implementation**: Use the previously defined `OrganizationMembership` model.
*   **Purpose**: Links a specific `User` to a specific `Organization` and assigns them **one** `Role` (`Group`) **for that specific organizational context**. This is the core of org-aware permissions.

## 4. Functional Requirements

### 4.1 Role Management (Admin/API)
*   Utilize standard mechanisms (e.g., Django Admin, potentially dedicated API) for managing Groups (Roles) and assigning model-level `Permission` objects to them.
*   Utilize standard mechanisms (Admin, API) for managing `OrganizationMembership` records, which includes assigning the user's Role (`Group`) for that specific organization.

### 4.2 Permission Definition
*   Model-level permissions defined via Django standard mechanisms (auto-generated + custom in `Meta`).

### 4.3 Organization-Aware Access Control Check Mechanism
*   **Requirement**: A mechanism is needed to check if a `user` has a specific `permission_codename` (e.g., `products.change_product`) *within the context of a specific `organization` or org-scoped `object`*.
*   **Implementation Approach**: Either:
    *   **A) Helper Function:** A function like `has_perm_in_org(user, permission_codename, organization_or_object)` which performs the check.
    *   **B) Custom Auth Backend:** A custom Django Authentication Backend that overrides the default `has_perm` method to incorporate the organization context (more complex integration).
    *(Decision: Assume **Helper Function (A)** initially for clarity unless Backend (B) proves necessary)*.
*   **Helper Function Logic (`has_perm_in_org`)**:
    1. Check for superuser bypass -> return `True`.
    2. Determine the relevant `organization` (either passed directly or extracted from `organization_or_object`). If no organization context, return `False` (or handle based on global role assignment if that's ever needed).
    3. Find the user's active `OrganizationMembership` for that specific `organization`. If none exists, return `False`.
    4. Get the `role` (`Group`) associated with that specific membership. If no role assigned, return `False`.
    5. Check if the `role` (`Group`) has the required `permission_codename` assigned via its `permissions` M2M field. Return `True` if found, `False` otherwise.
*   **Caching**: Implement caching for the results of permission checks per user/permission/organization combination.

### 4.4 Integration with Application Code
*   **API Views (Primary Enforcement Point)**:
    *   ViewSet `permission_classes` **must use custom `BasePermission` classes** that leverage the `has_perm_in_org` helper function.
    *   `has_permission` (for list/create views): Checks the required model-level permission (e.g., `view_model`, `add_model`) generally within *any* of the user's organizations (for list) or the *target* organization (for create, determined from request data/URL).
    *   `has_object_permission` (for retrieve/update/delete views): Checks the required model-level permission (`view_model`, `change_model`, `delete_model`) using `has_perm_in_org` with the specific `obj.organization` as the context.
*   **API Serializers**: **Do not perform permission checks.** They serialize all fields available on the model. Field visibility is implicitly controlled by whether the user has the necessary model-level permission (e.g., `view_model` to see any fields, `change_model` to update any writable fields) checked at the View level.
*   **OrganizationScoped Mixin**: The `perform_create` method within the `OrganizationScopedViewSetMixin` **must** use the `has_perm_in_org` helper to verify `add_model` permission in the target organization before saving.

### 4.5 Audit Logging
*   Changes to `Group` memberships (`User.groups` - if global roles used), `Group` permissions (`Group.permissions`), and `OrganizationMembership` instances (including `role` changes) must be logged via the `Audit Logging System`.

## 5. Technical Requirements

### 5.1 Data Management
*   Relies on efficient querying of `OrganizationMembership` and `Group.permissions`.
*   **Permission Caching**: Implement robust caching for resolved user permissions per organization (e.g., `user_id -> org_id -> {set of permission codenames}`). Invalidate caches appropriately on changes to `OrganizationMembership` or `Group.permissions`.

### 5.2 Security
*   Prevent unauthorized modification of Groups, Permissions, and `OrganizationMembership` records.
*   Ensure Org-Aware permission checking logic is secure and consistently applied in ViewSets via custom permission classes.
*   Audit logging of all relevant security/permission changes.

### 5.3 Performance
*   **Permission Checks**: Org-Aware checks must be extremely fast. Heavy reliance on caching. Minimize database queries during checks.

### 5.4 Integration
*   Integrates with `User`, `Group`, `Permission`, `ContentType`, `Organization`, `OrganizationMembership`, `Audit Logging System`, Caching Backend.
*   Requires integration into DRF `permission_classes` and potentially the `OrganizationScopedViewSetMixin`.

## 6. Non-Functional Requirements

*   **Scalability**: Handle large numbers of users, roles, permissions, organizations, memberships, and frequent checks. Caching is key.
*   **Availability**: Permission checking is critical infrastructure.
*   **Consistency**: Ensure permission data is consistent; cache invalidation must be reliable.
*   **Maintainability**: Permission logic and management mechanisms should be maintainable.

## 7. Success Metrics

*   Successful enforcement of model-level access control within the correct organizational context.
*   Low rate of incorrect access grants/denials.
*   Performance of Org-Aware checks meets targets.
*   Ease of administration for managing Roles, Permissions, and Organization Memberships.

## 8. Testing Requirements

*   **Unit Tests**: Test the `has_perm_in_org` helper function thoroughly. Test caching mechanisms (set, get, invalidate).
*   **Integration Tests**:
    *   Test custom DRF permission classes (`HasModelPermissionInOrg`) using the helper function.
    *   Test API ViewSets (List, Create, Retrieve, Update, Delete) with different users, organizations, and roles. Verify access is correctly granted/denied based on model-level permissions assigned via `OrganizationMembership`.
    *   Test the `OrganizationScopedViewSetMixin`'s `perform_create` integration with the real `has_perm_in_org` check.
    *   Test cache invalidation scenarios when memberships or role permissions change.
*   **Security Tests**: Attempt to bypass organizational scope checks, escalate privileges.

## 9. Deployment Requirements

*   Migrations for prerequisite models.
*   Initial setup of essential Roles (`Group`s) and assignment of standard model Permissions to these Roles.
*   Configuration and deployment of caching backend (e.g., Redis).
*   Deployment of the `has_perm_in_org` helper and custom DRF permission classes.

## 10. Maintenance Requirements

*   Ongoing management of Roles, Permissions, and User `OrganizationMembership` assignments by administrators.
*   Monitoring cache performance, hit rates, and invalidation effectiveness.
*   Regular security reviews of permission logic and assignments.
