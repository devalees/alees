
--- START OF FILE OrganizationMembership_prd.md ---

# OrganizationMembership Model - Product Requirements Document (PRD)

## 1. Overview

*   **Purpose**: To define the linking model that establishes a relationship between a `User` and an `Organization`, assigning a specific `Role` (represented by a Django `Group`) to the user within the context of that organization. This enables multi-organization membership and organization-specific roles.
*   **Scope**: Definition of the `OrganizationMembership` data model, its fields, relationships, constraints, and basic management operations.
*   **Implementation**: Defined as a concrete Django Model. It **must** inherit `Timestamped` and `Auditable`.
*   **Target Users**: System Administrators (managing memberships), Developers (querying memberships for permissions/scoping), potentially Organization Managers (if delegated permissions).

## 2. Business Requirements

*   **Multi-Organization Users**: Allow a single `User` account to be associated with multiple `Organization` records simultaneously.
*   **Organization-Specific Roles**: Assign distinct roles (permissions) to a user for each organization they belong to (e.g., 'Admin' in Org A, 'Viewer' in Org B).
*   **Foundation for Org-Aware Access Control**: Provide the necessary data structure for the RBAC system to determine a user's permissions within a specific organizational context.
*   **Clear Membership Tracking**: Maintain a clear record of which users belong to which organizations and in what capacity (role).

## 3. Functional Requirements

### 3.1 `OrganizationMembership` Model Definition
*   **Inheritance**: Must inherit `Timestamped`, `Auditable`.
*   **Fields**:
    *   `user`: (ForeignKey to `User` (`settings.AUTH_USER_MODEL`), on_delete=models.CASCADE, related_name='organization_memberships') **Required**. The user who is a member.
    *   `organization`: (ForeignKey to `Organization`, on_delete=models.CASCADE, related_name='memberships') **Required**. The organization the user is a member of.
    *   `role`: (ForeignKey to `django.contrib.auth.models.Group`, on_delete=models.PROTECT, related_name='organization_memberships') **Required**. The Role (Group) assigned to the user *specifically within this organization*. Use `PROTECT` to prevent deleting a Role that's actively assigned.
    *   `is_active`: (BooleanField, default=True, db_index=True) Flag to activate/deactivate the membership link without deleting it.
    *   *(Optional Fields)*:
        *   `join_date`: (DateField, auto_now_add=True or nullable) Date the membership was created.
        *   `is_default`: (BooleanField, default=False) Flag to indicate a user's "primary" or default organization context if needed (e.g., for creating new org-scoped data when context isn't specified). Requires logic to ensure only one default per user.
*   **Meta**:
    *   `verbose_name = "Organization Membership"`
    *   `verbose_name_plural = "Organization Memberships"`
    *   `unique_together = ('user', 'organization')` (A user has only one direct membership/role definition per organization).
    *   `ordering = ['organization__name', 'user__username']`
*   **String Representation**: `__str__` method should return a clear representation (e.g., `f"{self.user.username} in {self.organization.name} as {self.role.name}"`).

### 3.2 Data Management & Operations
*   **CRUD**: Primarily managed by Administrators via Admin UI or dedicated API endpoints.
    *   **Create**: Assign a user to an organization with a specific role.
    *   **Read/List**: View memberships for a user or an organization.
    *   **Update**: Change the `role` or `is_active` status for an existing membership.
    *   **Delete**: Remove a user's membership from an organization.
*   **Validation**: Enforce `unique_together`. Ensure valid `User`, `Organization`, and `Role` (Group) are selected.

### 3.3 Relationship with Other Models
*   Links `User`, `Organization`, and `Group` (Role).
*   Is queried by the RBAC system (`has_perm` logic) to determine permissions within an organization.
*   Is queried by the `User.get_organizations()` helper method to determine which organizations a user belongs to.

### 3.4 Out of Scope
*   Defining the Roles (`Group`) or Permissions themselves (handled by standard Django auth).
*   Complex invitation/approval workflows for joining organizations (can be built later).

## 4. Technical Requirements

### 4.1 Data Management
*   **Storage**: Standard database storage for the model.
*   **Indexing**: Indexes on `user`, `organization`, `role`, `is_active`. Composite index for `unique_together`.

### 4.2 Security
*   **Access Control**: Permissions (`add_organizationmembership`, `change_organizationmembership`, `delete_organizationmembership`, `view_organizationmembership`) must be strictly controlled, typically restricted to System Administrators or potentially Organization Managers for their own org.
*   **Audit Logging**: CRUD operations on `OrganizationMembership` records **must** be logged via the `Audit Logging System`, capturing user, organization, role, and the admin performing the change.

### 4.3 Performance
*   Efficient querying by `user` (to find all orgs/roles for a user) and by `organization` (to find all members/roles in an org). Relies on standard ForeignKey indexing. Caching might be applied to user's roles/orgs within the RBAC check function.

### 4.4 Integration
*   **Core Integration**: Provides the link between User, Organization, and Role for the Org-Aware RBAC system.
*   **API Endpoint (Admin Focused)**: Provide RESTful API endpoints (e.g., `/api/v1/organization-memberships/` or nested under users/organizations) for managing memberships, secured for administrators.
*   **User Integration**: `User` model needs `get_organizations()` method implemented to query this model.

## 5. Non-Functional Requirements

*   **Scalability**: Support large numbers of users and organizations, resulting in potentially many membership records. Query performance is key.
*   **Availability**: Membership data needed for almost every permission check, must be available.
*   **Data Consistency**: Maintain `unique_together` constraints and FK integrity.

## 6. Success Metrics

*   Users can be successfully assigned roles within specific organizations.
*   Org-aware permission checks correctly utilize membership data.
*   Administrators can efficiently manage user memberships.

## 7. API Documentation Requirements (If Admin API Endpoint is implemented)

*   Document `OrganizationMembership` model fields.
*   Document API endpoints for CRUD operations on memberships.
*   Specify required administrative permissions.

## 8. Testing Requirements

*   **Unit Tests**: Test `OrganizationMembership` model creation, `unique_together` constraint, `__str__`.
*   **Integration Tests**:
    *   Test creating/updating/deleting memberships via Admin/API.
    *   Test permission checks for managing memberships.
    *   **Crucially**, test the `User.get_organizations()` method returns the correct set of organizations based on membership records.
    *   Test that the Org-Aware RBAC `has_perm` logic correctly identifies permissions granted via a role in a specific `OrganizationMembership`.
*   **Data Tests**: Ensure `on_delete=PROTECT` works correctly for the `role` field. Test `on_delete=CASCADE` for `user` and `organization`.

## 9. Deployment Requirements

*   Migrations for `OrganizationMembership` table and indexes.
*   Dependencies on `User`, `Organization`, `Group` models/migrations.
*   Initial assignment of roles/memberships if needed during setup.
*   Assignment of permissions to manage memberships to appropriate admin roles.

## 10. Maintenance Requirements

*   Ongoing management of user memberships as roles/responsibilities change.
*   Standard database backups. Monitoring query performance related to memberships.

--- END OF FILE OrganizationMembership_prd.md ---