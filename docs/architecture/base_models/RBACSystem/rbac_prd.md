# Role-Based Access Control (RBAC) System - Product Requirements Document (PRD) - Refined (Field-Level CRUD)

## 1. Overview

*   **Purpose**: To define a flexible Role-Based Access Control (RBAC) system for the ERP, enabling granular control over user actions based on assigned roles and permissions. The system will manage **model-level permissions** and extend functionality to support **field-level Create, Read, and Update permissions**.
*   **Scope**: Definition of Role (`Group`) usage, standard `Permission` usage, a new `FieldPermission` model, assignment of Roles to Users (within organizational contexts), mechanisms for checking permissions (model and field level), and integration with core ERP modules.
*   **Relationship to Django Auth**: This system **extends** Django's built-in authentication and authorization framework (`User`, `Group`, `Permission`). Django `Group` will be used to represent Roles. Django `Permission` will handle model-level access. A custom `FieldPermission` model will handle field-level access.
*   **Target Users**: System Administrators, Security Managers, Application Developers.

## 2. Business Requirements

*   Assign permissions to users based on defined business roles, rather than individually.
*   Control access to view, create, modify, and delete data across different modules (Model-Level via standard Django permissions).
*   Control access to specific custom actions within modules (Model-Level via custom Django permissions).
*   *(Future)* Optionally support hierarchical roles where permissions can be inherited. *(Initial implementation assumes flat roles/groups)*.
*   **Control access to view specific fields within a model (Field-Level Read).**
*   **Control ability to provide values for specific fields during record creation (Field-Level Create).**
*   **Control ability to modify specific fields on existing records (Field-Level Update).**
*   Ensure access control is enforced consistently across APIs.
*   Integrate permission checks with organizational scoping (multi-tenancy).
*   Provide audit trails for role/permission assignments and potentially access decisions.

## 3. Core RBAC Models & Structures

### 3.1 `Role` Model (`django.contrib.auth.models.Group`)
*   **Implementation**: Use Django's built-in `django.contrib.auth.models.Group`.
*   **Conceptual Name**: Treat `Group` as `Role` within the application context.
*   **Fields Used**: `name`, `permissions` (ManyToManyField to `django.contrib.auth.models.Permission`).
*   **Scoping**: Django Groups are global by default. **If Roles need to be scoped per organization, a custom Role model OR a linking model between User, Group, and Organization would be required.** *(Decision: Assume global Roles/Groups initially unless Org-scoping is explicitly required)*.

### 3.2 `Permission` Model (`django.contrib.auth.models.Permission`)
*   **Implementation**: Use Django's built-in `django.contrib.auth.models.Permission`.
*   **Usage**: Handles **model-level** permissions (e.g., `app_label.add_modelname`, `app_label.change_modelname`, `app_label.delete_modelname`, `app_label.view_modelname`).
*   **Custom Permissions**: Custom model-level actions defined via model `Meta.permissions`.

### 3.3 User Role Assignment (`User.groups`)
*   **Implementation**: Use Django's standard `User.groups` ManyToManyField to assign users to Roles (`Group`s). *(If Org-scoped roles were needed, this would change to use a linking model like `UserOrganizationRole`)*.

### 3.4 `FieldPermission` Model (NEW)
*   **Purpose**: To explicitly grant Create, Read, or Update access to a specific model field for a specific Role (`Group`).
*   **Location**: Defined within the permissions/RBAC app (e.g., `rbac/models.py`).
*   **Inheritance**: Inherits `Timestamped`, `Auditable`.
*   **Fields**:
    *   `group`: (ForeignKey to `django.contrib.auth.models.Group`, on_delete=models.CASCADE, related_name='field_permissions') The Role receiving the permission.
    *   `content_type`: (ForeignKey to `django.contrib.contenttypes.models.ContentType`, on_delete=models.CASCADE) The model this permission applies to.
    *   `field_name`: (CharField, max_length=255) The name of the field on the model identified by `content_type`.
    *   `can_create`: (BooleanField, default=False) Can provide a value for this field during record **creation**?
    *   `can_read`: (BooleanField, default=False) Can **read** (view) the value of this field?
    *   `can_update`: (BooleanField, default=False) Can **update** (change) the value of this field on an existing record?
*   **Meta**:
    *   `unique_together = ('group', 'content_type', 'field_name')` Ensures only one field permission entry per group/model/field.
    *   `verbose_name = "Field Permission"`
    *   `verbose_name_plural = "Field Permissions"`
    *   `indexes`: Index on `group`, `content_type`, `field_name`.

### 3.5 Management of Field Permission Records
*   **Requirement**: A mechanism must exist for authorized administrators to perform CRUD operations (Create, Read, Update, Delete) on `FieldPermission` model instances. This allows defining the specific field-level access (`can_create`, `can_read`, `can_update`) granted to different Roles (`Group`s) for various model fields.
*   **Access**: This management capability must be restricted to designated administrative roles.

## 4. Functional Requirements

### 4.1 Role Management (Admin/API)
*   Utilize standard mechanisms (e.g., Django Admin, dedicated API) for managing Groups (Roles) and assigning model-level `Permission` objects to them.
*   Utilize the mechanism defined in 3.5 for managing `FieldPermission` records.
*   Utilize standard mechanisms for assigning Users to Groups.

### 4.2 Permission Definition
*   Model-level permissions defined via Django standard mechanisms (auto-generated + custom in `Meta`).
*   Field-level C/R/U permissions defined by creating/managing `FieldPermission` instances via the mechanism in 3.5.

### 4.3 Access Control Check Mechanism
*   **Model-Level Check Function**: Use standard `user.has_perm('app_label.codename', obj)`. Must return `True` before field-level checks are relevant for a specific action.
*   **Field-Level Check Function**:
    *   `has_field_permission(user, action, model_or_instance, field_name)` where `action` is 'create', 'read', or 'update'.
    *   **Logic**:
        1. Check for superuser bypass -> return `True`.
        2. **Check necessary model-level permission:** (Crucial prerequisite)
           *   If `action == 'read'`, check corresponding model `view` permission. If `False`, return `False`.
           *   If `action == 'create'`, check corresponding model `add` permission. If `False`, return `False`.
           *   If `action == 'update'`, check corresponding model `change` permission. If `False`, return `False`.
        3. **Check for explicit field-level grant:**
           *   Get user's `groups`.
           *   Get `ContentType` for `model_or_instance`.
           *   Query `FieldPermission` cache/database: `FieldPermission.objects.filter(group__in=user_groups, content_type=ctype, field_name=field_name)`
           *   Check the relevant flag on the retrieved `FieldPermission` record(s) based on the `action`:
               *   If `action == 'read'`, check if any record has `can_read=True`.
               *   If `action == 'create'`, check if any record has `can_create=True`.
               *   If `action == 'update'`, check if any record has `can_update=True`.
           *   Return `True` if the specific field access is granted (and model access was granted), `False` otherwise.
    *   **Caching**: Implement aggressive caching for the results of `FieldPermission` queries per user/model.

### 4.4 Integration with Application Code
*   **API Serializers (Primary Enforcement Point for Field-Level)**:
    *   **Read Enforcement (`to_representation` / `get_fields`):** Dynamically determine readable fields using `has_field_permission(..., 'read', ...)` and only include those in the output.
    *   **Create Enforcement (`validate` / `create`):** Check `has_field_permission(..., 'create', ...)` for all fields provided in input data. Reject if any field lacks permission.
    *   **Update Enforcement (`validate` / `update`):** Check `has_field_permission(..., 'update', ...)` for all fields provided in input data. Reject if any field lacks permission.
*   **API Views (Model-Level Enforcement)**: Use DRF `permission_classes` checking standard Django model-level permissions (`add`, `change`, `view`, `delete`) for overall access to the view/action.
*   **Organization Scoping Integration**: `has_field_permission` checks (and the underlying `user.has_perm`) must operate within the correct organization context if roles/permissions eventually become org-scoped. Initially assumes global roles/permissions checked after data scoping.

### 4.5 Audit Logging
*   Changes to `Group` memberships (`User.groups`), `Group` permissions (`Group.permissions`), and `FieldPermission` instances must be logged via the `Audit Logging System`.
*   *(Optional)* Log significant permission check failures (access denied) if needed.

## 5. Technical Requirements

### 5.1 Data Management
*   Efficient storage for `FieldPermission`.
*   **Indexing**: Critical indexes on `FieldPermission` (`group`, `content_type`, `field_name`).
*   **Permission Caching**: Implement robust caching for resolved user permissions (model-level) and field-level permissions (e.g., `user_id -> {model_key: {'read_fields': set(), 'create_fields': set(), 'update_fields': set()}}`). Invalidate caches appropriately on changes to Group membership, Group permissions, or `FieldPermission` records.

### 5.2 Security
*   Prevent unauthorized modification of Groups, Permissions, `FieldPermission` records, and assignments.
*   Ensure permission checking logic (model and field level) is secure and consistently applied.
*   Secure the management capability for `FieldPermission` records (defined in 3.5).
*   Audit logging of all relevant security/permission changes.

### 5.3 Performance
*   **Permission Checks**: Model and field-level checks must be extremely fast. Heavy reliance on caching.
*   **Serialization Overhead**: Acknowledge and optimize the performance impact of checking permissions per field during serialization and validation.
*   Minimize database queries during checks.

### 5.4 Integration
*   Integrates with `User`, `Group`, `Permission`, `ContentType`, `Organization` (for context), `Audit Logging System`.
*   Requires integration into base API Serializers to enforce field-level rules.
*   Provides checking mechanism (`has_field_permission`) for potential use elsewhere (e.g., UI rendering logic).
*   Requires a mechanism (Admin, API, other) for administrators to manage `FieldPermission` records.

## 6. Non-Functional Requirements

*   **Scalability**: Handle large numbers of users, roles, permissions (model & field), and frequent checks.
*   **Availability**: Permission checking is critical infrastructure.
*   **Consistency**: Ensure permission data is consistent; cache invalidation must be reliable.
*   **Maintainability**: Permission logic and management mechanisms should be maintainable.

## 7. Success Metrics

*   Successful enforcement of model and field-level access control.
*   Low rate of incorrect access grants/denials.
*   Performance of checks meets targets.
*   Ease of administration for managing Roles and Field Permissions.

## 8. Testing Requirements

*   **Unit Tests**: Test `FieldPermission` model. Test `has_field_permission` logic thoroughly for read/create/update actions, including interaction with model permissions and superuser bypass. Test caching mechanisms (set, get, invalidate).
*   **Integration Tests**:
    *   Test permission enforcement in API views (model-level) and serializers (field-level).
    *   Test API LIST/RETRIEVE: Verify fields excluded based on `can_read=False`.
    *   Test API CREATE: Verify requests fail if input contains fields where `can_create=False`. Verify successful creation with permitted fields.
    *   Test API UPDATE/PATCH: Verify requests fail if input contains fields where `can_update=False`. Verify successful updates with permitted fields.
    *   Test the administrative mechanism for managing field permissions (e.g., via Admin UI or dedicated API).
    *   Test cache invalidation scenarios.
*   **Security Tests**: Attempt to bypass model and field-level checks, escalate privileges.
*   **Performance Tests**: Measure overhead of permission checks (model and field) under load, especially during serialization.

## 9. Deployment Requirements

*   Migrations for `FieldPermission` model and indexes.
*   Initial setup of essential Roles (`Group`s) and appropriate model/field permission assignments.
*   Configuration and deployment of caching backend (e.g., Redis).
*   Deployment of the administrative mechanism for managing `FieldPermission` records.

## 10. Maintenance Requirements

*   Ongoing management of Roles, Permissions, FieldPermissions, and User assignments by administrators via the designated mechanism.
*   Monitoring cache performance, hit rates, and invalidation effectiveness.
*   Regular security reviews of permission logic and assignments.
