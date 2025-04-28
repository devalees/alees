# User & UserProfile Models - Product Requirements Document (PRD) - Refined (Username Login + Custom Fields)

## 1. Overview

*   **Purpose**: To define the user representation within the ERP system, extending Django's built-in `User` model with a dedicated `UserProfile` model for additional attributes, preferences, relationships, and **dynamic custom fields**. **Login will be based on `username`**.
*   **Scope**: Definition of the `UserProfile` model, its relationship to the core Django `User` model, management of user profiles including custom fields, integration with authentication/authorization systems, and linkage to organizational structures.
*   **Technical Approach**: Utilizes Django's built-in `User` model for core authentication. A separate `UserProfile` model, linked via a `OneToOneField` to `User`, stores ERP-specific attributes, relationships, and custom data via a `JSONField`.
*   **Target Users**: All system users, System Administrators, HR Managers, Department Managers.

## 2. Business Requirements

*   Maintain comprehensive user profile information, including adaptable custom attributes.
*   Support different classifications of users.
*   Integrate users seamlessly with the organizational structure.
*   Provide a foundation for RBAC within organizational contexts.
*   Allow users to manage personal preferences.
*   Enable administrators to manage user accounts, profiles, and custom fields relevant to users.
*   **Require users to log in using their unique `username`**.

## 3. Functional Requirements

### 3.1 Core User Model (`django.contrib.auth.models.User`)
*   Leverage standard fields: `username` (unique login identifier), `password`, `email`, `first_name`, `last_name`.
*   Utilize standard status/permission fields: `is_active`, `is_staff`, `is_superuser`, `groups`, `user_permissions`, `last_login`, `date_joined`.

### 3.2 `UserProfile` Model Definition
*   **Relationship**: `user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')`.
*   **Inheritance**: Should inherit `Timestamped`, `Auditable`.
*   **Fields (Examples)**:
    *   `job_title`, `employee_id`, `phone_number`, `profile_picture`, `manager`, `date_of_birth`, `employment_start_date`, `employment_end_date`, `employment_type`, etc.
*   **Preferences Fields**:
    *   `language`, `timezone`, `notification_preferences` (JSONField).
*   **Custom Fields**:
    *   `custom_fields`: (JSONField, default=dict, blank=True) Stores values for dynamically defined custom fields relevant to user profiles.

### 3.3 Custom Field Schema Definition (External Mechanism)
*   **Requirement**: A separate mechanism (e.g., a `CustomFieldDefinition` model, potentially linked to user type/role/organization type) is needed to define the schema for custom fields applicable to `UserProfile`.
*   **Schema Attributes**: Defines key, label, field type, validation rules, choices, help text, etc. *(Refer to `organization_prd.md` Section 3.4 for detail)*.

### 3.4 User/Profile Management Operations
*   **Admin Interface**: Comprehensive management via Django Admin (User + inline UserProfile).
*   **API**: Endpoints for User/Profile CRUD, activation/deactivation, group/permission/org assignments.
*   **Custom Field Value Management**: API/Admin interfaces should allow viewing and updating the `custom_fields` JSON object on a `UserProfile`, subject to permissions.
*   **User Self-Service**: Allow users to view/update own profile data (including permitted custom fields). Users typically cannot change their `username`.

### 3.5 Authentication & Authorization Integration
*   **Authentication**: Default internal method uses `username`/password. External methods (SSO, Social, 2FA) via library integrations.
*   **Authorization**: Leverage Django permissions + custom logic for Org/Dept/Team context based on relationships (defined in 3.2). Access to view/edit specific `custom_fields` may require specific permissions.

### 3.6 History & Status
*   **Current Status**: `User.is_active`.
*   **Historical Data**: Captured by the `Audit Logging System` (logins, profile changes including `custom_fields` diffs, permission changes).

### 3.7 Custom Field Validation
*   **Requirement**: Data saved to the `UserProfile.custom_fields` field must be validated against the corresponding `CustomFieldDefinition` schema.
*   **Implementation**: Logic typically resides in API Serializers or Forms used for updating the `UserProfile`.

## 4. Technical Requirements

### 4.1 Security
*   Password/Username/Session security as standard. API security via Auth/Permissions.
*   **Profile Data Security**: Control access to sensitive profile fields and `custom_fields`.
*   **Audit Logging**: Log changes to User, UserProfile, and `custom_fields`. Log permission/group changes.

### 4.2 Performance
*   Optimize User/Profile queries (`select_related`).
*   Efficient permission checks.
*   **Custom Field Queries**: Requires appropriate DB support (e.g., PostgreSQL GIN index on `custom_fields` JSONField) if frequent querying on custom field values is needed.

### 4.3 Integration
*   Authentication Backend configured for `username`.
*   Signal for auto-creating `UserProfile`.
*   Admin integration (inline profile).
*   Chosen Org/Membership integration pattern.
*   Audit System integration.
*   External Auth library integration points.
*   Integration with the `CustomFieldDefinition` mechanism for schema lookup during validation/display.

## 5. Non-Functional Requirements

*   Scalability, Availability, Consistency, Backup/Recovery, Compliance (PII).

## 6. Success Metrics

*   High auth success rate. Efficient API responses. User satisfaction. Successful RBAC. Security/Compliance adherence. Successful implementation and use of custom fields for user profiles.

## 7. API Documentation Requirements

*   Document User/Profile models/fields (incl. `username` login, `custom_fields` structure).
*   Document User/Profile/Relationship API endpoints.
*   Provide examples (creating users, updating profiles, handling `custom_fields` data).
*   Document auth/permission requirements.
*   Document how to discover available custom field schemas for users (if applicable via API).

## 8. Testing Requirements

*   Unit Tests (Profile model, signal, custom field validation logic if separated).
*   Integration Tests (API CRUD, login via `username`, permissions, **saving/validating `custom_fields` data via API**, self-service).
*   Security Tests (auth, permissions, PII access, custom field access).
*   Authentication Integration Tests.

## 9. Deployment Requirements

*   Migrations (`UserProfile`, relationship models). Secure initial user setup. Auth config.
*   Deployment of `CustomFieldDefinition` mechanism and potential initial schemas.

## 10. Maintenance Requirements

*   User admin (passwords, status). Audit log monitoring. Auth library updates.
*   Management of custom field schemas via `CustomFieldDefinition` interface.
