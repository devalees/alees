# Base Models Product Requirements Document (PRD)

## Table of Contents

1. [Core Models](#core-models)
   - [Organization](#organization)
   - [Organization Type](#organization-type)
   - [User Profile](#user-profile)
   - [Contact](#contact)
   - [Address](#address)

2. [System Models](#system-models)
   - [Audit Logging](#audit-logging)
   - [Auditable](#auditable)
   - [Timestamped](#timestamped)
   - [Status](#status)

3. [Authentication & Authorization](#authentication--authorization)
   - [Auth API](#auth-api)
   - [Organization Membership](#organization-membership)
   - [Organization Scoped](#organization-scoped)

4. [Business Models](#business-models)
   - [Product](#product)
   - [Category](#category)
   - [Tax](#tax)
   - [Currency](#currency)
   - [Unit of Measure](#unit-of-measure)
   - [Warehouse](#warehouse)
   - [Stock Location](#stock-location)

5. [Communication & Collaboration](#communication--collaboration)
   - [Chat](#chat)
   - [Comment](#comment)
   - [Notification](#notification)
   - [Video Meeting](#video-meeting)

6. [Document Management](#document-management)
   - [Document System](#document-system)
   - [File Storage](#file-storage)
   - [Export/Import](#exportimport)

7. [System Features](#system-features)
   - [Search](#search)
   - [Filtering](#filtering)
   - [Tagging](#tagging)
   - [Workflow](#workflow)
   - [Automation](#automation)

---

## Core Models


### Organization

# Organization Base Model - Product Requirements Document (PRD)

## 1. Overview
- **Purpose**: To define the core `Organization` entity, providing a flexible and scalable foundation for managing organizational units, their structures, attributes, and relationships within the ERP system.
- **Scope**: Definition, attributes, hierarchy, relationships, custom fields, and management of `Organization` entities. This model serves as the anchor point for the `OrganizationScoped` multi-tenancy mechanism.
- **Implementation**: Defined as a concrete Django Model. It **must** inherit the `Timestamped` and `Auditable` Abstract Base Models. It will also utilize `django-mptt` for hierarchy and potentially `django-taggit` for tags.
- **Target Users**: System administrators, HR managers, department heads, finance managers, users needing to view/manage organizational structures.

## 2. Business Requirements
- Represent diverse organizational structures (hierarchical, matrix, flat, project-based).
- Serve as the central entity for multi-tenant data segregation (via the separate `OrganizationScoped` mechanism linking other models to this one).
- Support international organizations (multiple locations, currencies, timezones, languages).
- Allow for organizational changes, restructuring, and history tracking.
- Provide flexibility through configurable types and dynamic custom fields.

## 3. Functional Requirements

### 3.1 Organization Information & Attributes
- **Inheritance**: Must inherit `Timestamped` and `Auditable` abstract base models. Must inherit `mptt.models.MPTTModel`.
- **Core Fields**:
    - `name`: (CharField) The display name of the organizational unit. (Indexed)
    - `code`: (CharField) A unique identifier/code for the organization. (Unique, Indexed)
    - `organization_type`: (ForeignKey to `OrganizationType` model) Defines the kind of unit (e.g., Company, Department). `on_delete=PROTECT`.
    - `status`: (CharField with choices) e.g., 'Active', 'Inactive', 'Archived'. (Indexed)
    - `parent`: (TreeForeignKey to `self`, managed by `django-mptt`) Defines the primary hierarchical parent. `on_delete=PROTECT`.
    - `effective_date`: (DateField/DateTimeField, null=True, blank=True) Date the organization unit becomes active/valid.
    - `end_date`: (DateField/DateTimeField, null=True, blank=True) Date the organization unit ceases to be active/valid.
- **Contact Information**: (ForeignKey to `Contact` model, `on_delete=models.SET_NULL`, null=True, blank=True, related_name='primary_for_organizations') Primary contact person.
- **Address Details**: (ForeignKey to `Address` model, `on_delete=models.SET_NULL`, null=True, blank=True, related_name='primary_for_organizations') Primary address. *(Consider dedicated fields/FKs for Billing/Shipping addresses if needed)*.
- **Localization**:
    - `timezone`: (CharField, using standard timezone names) Default timezone.
    - `currency`: (ForeignKey to `Currency` model, `on_delete=models.PROTECT`, null=True, blank=True) Default operating currency.
    - `language`: (CharField with choices) Default language preference.
- **Metadata & Classification**:
    - `tags`: (TaggableManager via `django-taggit`, blank=True) For flexible categorization.
    - `metadata`: (JSONField, default=dict, blank=True) For storing other structured or unstructured metadata specific to the organization.

### 3.2 Organization Types (Reference)
- Relies on the separate `OrganizationType` model via the `organization_type` ForeignKey.

### 3.3 Organization Structure & Relationships
- **Primary Hierarchy**: Managed via the `parent` TreeForeignKey and `django-mptt`. Provides parent-child relationships and efficient hierarchy queries.
- **Other Relationships** (Out of Scope for this model): Matrix reporting, cross-functional teams, partnerships, specific Customer/Supplier links should be handled by separate dedicated linking models if required beyond basic OrgType classification.

### 3.4 Custom Fields
- **Implementation**: Use a `custom_fields` **JSONField** on the `Organization` model (default=dict, blank=True).
- **Schema Definition**: Requires a separate mechanism (e.g., `CustomFieldDefinition` model, possibly linked to `OrganizationType`) to define schema (key, label, type, validation, choices, help text).
- **Functionality**:
    - Store and retrieve custom field values.
    - Validate custom field data against the defined schema (logic likely in Serializers/Forms).
    - Allow querying/filtering based on custom field values (requires specific DB support like PostgreSQL GIN index).

### 3.5 History Tracking & Auditing
- **Requirement**: Track significant changes to `Organization` records.
- **Implementation**: Changes captured via the `Auditable` mixin (`updated_by`/`at`) and logged historically by the central **`Audit Logging System`**. The Audit Log should record changes to key fields (name, status, parent, type) and potentially `custom_fields` diffs.

### 3.6 Operations
- **CRUD**: API endpoints/Admin UI for CRUD (soft delete via `status`).
- **Hierarchy Management**: API actions/Admin UI for moving organizations (changing `parent`).
- **Type Management**: Handled via the separate `OrganizationType` CRUD interfaces.
- **Custom Field Schema Management**: API/Admin for the separate `CustomFieldDefinition` model.

## 4. Technical Requirements

### 4.1 Performance
- **Hierarchy Queries**: Leverage `django-mptt` indexing and methods.
- **Attribute Queries**: Index core fields (`code`, `name`, `status`, `organization_type`).
- **Custom Field Queries**: Requires DB support (e.g., PostgreSQL GIN index on `custom_fields` JSONField).
- **Scalability**: Support thousands of records and deep hierarchies.
- **Caching**: Cache static/infrequently changing data (org details, types).

### 4.2 Security
- **Access Control**: Implement RBAC for managing `Organization` entities via the `Permission` system. Define roles/permissions (CRUD, change_hierarchy, manage_custom_fields_values). Permissions can be global or scoped (e.g., manage descendants).
- **Audit Logging**: Ensure changes trigger logs in the central `Audit Logging System`.
- **Custom Field Security**: Evaluate need for field-level security on specific custom fields.

### 4.3 Integration
- **API Endpoints**: Comprehensive RESTful APIs for `/organizations/` (CRUD), hierarchy actions (`/descendants/`, `/ancestors/`, move), potentially endpoints for managing custom field *values*.
- **Dependency APIs**: Relies on APIs for `/organization-types/`, `/custom-field-definitions/`.
- **Webhook Support**: Trigger webhooks on Organization lifecycle events.
- **Import/Export**: Mechanisms for bulk import/export (CSV, JSON).
- **Module Integration**: Serve as target for ForeignKeys from `OrganizationScoped` models, `User`, `Contact`, etc.

## 5. Non-Functional Requirements
- **Scalability**: Handle growth in organizations and data.
- **High Availability**: Critical model, requires HA infrastructure.
- **Data Consistency**: Use transactions for complex updates (hierarchy changes). Maintain FK integrity.
- **Backup and Recovery**: Define RPO/RTO. Test procedures.
- **Compliance**: Address data protection regulations for contact/address info linked.

## 6. Success Metrics
- **API Performance**: Meet defined SLAs.
- **Data Integrity**: Low inconsistency rate. Successful validation.
- **User Satisfaction**: Positive feedback on managing organizations/custom fields.
- **Scalability**: Maintains performance under growth.
- **Adoption**: Used effectively as the scoping foundation.

### Organization Type

# OrganizationType Base Model - Product Requirements Document (PRD)

## 1. Overview

*   **Purpose**: To define and manage the distinct classifications or categories of `Organization` entities within the ERP system. This model provides a controlled vocabulary for describing the nature of different organizational units.
*   **Scope**: Definition of the `OrganizationType` data model, its attributes, management operations (CRUD), relationship with the `Organization` model, and basic API exposure.
*   **Implementation**: Defined as a concrete Django Model. It **must** inherit the `Timestamped` and `Auditable` Abstract Base Models.
*   **Target Users**: System Administrators (managing the types), Developers (referencing types in logic), Business Analysts (defining necessary types).

## 2. Business Requirements

*   **Standardized Classification**: Provide a consistent and predefined set of categories to classify all `Organization` records.
*   **Extensibility**: Allow administrators to define new organization types as business needs evolve.
*   **Clarity & Reporting**: Enable clear identification and reporting based on the nature of an organization (e.g., filter all "Customers", count all "Departments").
*   **Foundation for Rules**: Serve as a basis for potential future business rules or conditional logic that may vary depending on the type of organization (e.g., different required fields, different allowed relationships).

## 3. Functional Requirements

### 3.1 Model Definition (`OrganizationType`)
*   **Inheritance**: Must inherit `Timestamped` and `Auditable` abstract base models.
*   **Fields**:
    *   `name`: (CharField, max_length=100) The unique, human-readable name of the type (e.g., "Company", "Department", "Customer", "Supplier", "Location/Branch"). Must be unique. (Indexed)
    *   `description`: (TextField, blank=True) An optional description explaining the purpose or characteristics of this organization type.
    *   *(Consider adding `is_internal` or `category` flags later if needed for grouping types, but keep simple initially).*
*   **Meta**:
    *   `verbose_name = "Organization Type"`
    *   `verbose_name_plural = "Organization Types"`
    *   `ordering = ['name']`
*   **String Representation**: `__str__` method should return the `name`.

### 3.2 Data Management & Operations
*   **CRUD Operations**:
    *   Ability to Create new Organization Types (via Admin UI, potentially simple API).
    *   Ability to Read/List existing Organization Types.
    *   Ability to Update existing Organization Types (primarily `description`). Changing `name` might be restricted or require careful handling due to its use as an identifier.
    *   Ability to Delete Organization Types *only if* they are not currently referenced by any `Organization` record (enforced by `on_delete=models.PROTECT` on the `Organization.organization_type` ForeignKey).
*   **Validation**:
    *   The `name` field must be unique and non-empty.
*   **Initial Data**: A predefined set of essential organization types should be created during initial system setup or migration (e.g., "Company", "Department", "Customer", "Supplier").

### 3.3 Relationship with `Organization`
*   The `Organization` model *must* have a non-nullable ForeignKey (`organization_type`) pointing to this `OrganizationType` model.
*   The `on_delete` behavior for this ForeignKey on the `Organization` model should be `models.PROTECT` to prevent accidental deletion of a type that is in use.

### 3.4 Examples of Types
*   Internal Structure: Company, Division, Department, Team, Location/Branch
*   External Relationships: Customer, Supplier, Partner, Vendor
*   Other: Project, Subsidiary

## 4. Technical Requirements

### 4.1 Performance
*   Queries retrieving `OrganizationType` by name or ID should be highly performant (it acts as a lookup table). Simple database indexing on `name` (already specified as unique) and the primary key is sufficient.
*   Listing all types should be efficient (expected low number of records).

### 4.2 Security
*   **Access Control**: Managing `OrganizationType` records (Create, Update, Delete) should be restricted to specific administrative roles (e.g., System Administrator). Requires standard Django model permissions (`add_organizationtype`, `change_organizationtype`, `delete_organizationtype`).
*   **Audit Logging**: Changes (Create, Update, Delete) to `OrganizationType` records should be logged in the central `Audit` system (leveraging the `Auditable` mixin for user/timestamp and potentially explicit logging for delete/create).

### 4.3 Integration
*   **Primary Integration**: Serves as the target for the `Organization.organization_type` ForeignKey.
*   **API Endpoint (Optional but Recommended)**: Provide a simple RESTful API endpoint (e.g., `/api/v1/organization-types/`) for listing and potentially managing types, protected by appropriate administrative permissions. This allows other services or UI components to fetch the available types.

## 5. Non-Functional Requirements

*   **Scalability**: Should easily handle hundreds of distinct organization types without performance issues.
*   **Availability**: As a dependency for creating `Organization` records, the types must be reliably available.
*   **Data Consistency**: Unique name constraint must be enforced. Referential integrity with `Organization` must be maintained via `on_delete=PROTECT`.
*   **Maintainability**: The model and its management interface should be simple and easy to maintain.

## 6. API Documentation Requirements (If API Endpoint is implemented)

*   OpenAPI/Swagger documentation for the `/organization-types/` endpoint.
*   Endpoint descriptions (List, Retrieve, potentially Create/Update/Delete).
*   Request/response examples.
*   Authentication/Authorization documentation (Admin role required).
*   Error code documentation (e.g., for unique constraint violation, deletion protection error).

## 7. Testing Requirements

*   **Unit Tests**:
    *   Test `OrganizationType` model creation and `__str__`.
    *   Test unique constraint validation on `name`.
    *   Test inheritance of `Timestamped`/`Auditable` fields.
*   **Integration Tests**:
    *   Test CRUD operations via Admin UI or API (if implemented).
    *   **Crucially**, test the deletion protection: Attempt to delete an `OrganizationType` that is currently assigned to an `Organization` and verify it fails with the expected `ProtectedError`.
    *   Test deleting an unused `OrganizationType` succeeds.
    *   Test permission checks for managing types.
*   **API Tests** (If API Endpoint is implemented):
    *   Test LIST, RETRIEVE, CREATE, UPDATE, DELETE operations via HTTP requests.
    *   Test authentication and permission enforcement on the API endpoint.

## 8. Deployment Requirements

*   **Migrations**: Standard Django migration for creating the `OrganizationType` table.
*   **Initial Data Population**: A data migration (`migrations.RunPython`) should be created to populate the initial, essential set of `OrganizationType` records upon first deployment.

## 9. Maintenance Requirements

*   Regular backup according to standard database procedures.
*   Administrators may need to add or occasionally update descriptions of types via the Admin UI/API. Deletion is rare due to protection constraints.

## 10. Success Metrics

*   Successful creation and classification of `Organization` records using defined types.
*   Low error rate related to `OrganizationType` lookup or management.
*   Administrator satisfaction with the ease of managing types.
*   No reported issues related to accidental deletion of types in use.

### User Profile

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

### Contact

# Contact Model - Product Requirements Document (PRD) - Simplified (with Custom Fields)

## 1. Overview

*   **Purpose**: To define a centralized model for storing information about **individual people** (contacts), potentially extended with **dynamic custom fields**, relevant to the ERP system.
*   **Scope**: Definition of the `Contact` data model, its core attributes, links to communication channels, relationships with Organizations, and custom field capability. Excludes interaction history and complex relationships.
*   **Implementation**: Defined as a concrete Django Model. Inherits `Timestamped`, `Auditable`. Uses a `JSONField` for custom fields. Related models for communication channels.
*   **Target Users**: Sales, Procurement, Support Teams, Admins.

## 2. Business Requirements

*   Centralized contact info for individuals.
*   Represent different types of external contacts.
*   Link contacts to Organizations.
*   Manage multiple communication methods.
*   Allow adding specific, dynamic attributes to contacts (via Custom Fields).
*   Foundation for CRM/Communication features.

## 3. Functional Requirements

### 3.1 `Contact` Model Definition
*   **Inheritance**: Inherit `Timestamped`, `Auditable`.
*   **Fields**:
    *   `first_name`, `last_name`, `title`.
    *   `organization_name` (CharField, denormalized).
    *   `linked_organization` (ForeignKey to `Organization`, SET_NULL, nullable, blank).
    *   `contact_type` (CharField w/ choices).
    *   `status` (CharField w/ choices).
    *   `source` (CharField, blank).
    *   `notes` (TextField, blank).
    *   `tags` (TaggableManager, blank).
    *   **`custom_fields`**: (JSONField, default=dict, blank=True) Stores values for dynamically defined custom fields relevant to contacts.
*   **Meta**: `verbose_name`, `plural`, `ordering`, indexes.
*   **String Representation**: Full name.

### 3.2 Communication Channel Models (Separate Related Models)
*   Required separate models: `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress` (linking to `Address`), optional `ContactSocialProfile`.
*   Each linked via ForeignKey to `Contact`.
*   Each includes `type` (Work/Home) and `is_primary` (Boolean) fields.
*   Each inherits `Timestamped`/`Auditable`.

### 3.3 Custom Field Schema Definition (External Mechanism)
*   **Requirement**: A separate mechanism (e.g., `CustomFieldDefinition` model) is needed to define the schema for custom fields applicable to `Contact`.
*   **Schema Attributes**: Defines key, label, type, validation, choices, etc.

### 3.4 Contact Management Operations
*   **CRUD**: Standard operations for `Contact` and related communication channels (Admin/API).
*   **Inline Editing**: Manage communication channels inline in Contact admin.
*   **Primary Flag Logic**: Enforce single primary per type per contact.
*   **Custom Field Value Management**: API/Admin to view/update `custom_fields` JSON object.

### 3.5 Validation
*   Standard field validation. Email/Phone format validation (on channel models). Custom field validation against schema (in Serializer/Form). *Duplicate detection is separate.*

### 3.6 Custom Field Validation
*   **Requirement**: Data saved to `Contact.custom_fields` must be validated against the corresponding schema.
*   **Implementation**: Logic in API Serializers or Forms.

### 3.7 Out of Scope for this Model/PRD
*   Contact-Contact relationships, Interaction History (use separate Activity/Log systems), User model duplication.

## 4. Technical Requirements

### 4.1 Data Management
*   Storage: Standard fields + JSONField. Appropriate types for channels.
*   Indexing: Key Contact fields (`last_name`, `linked_organization`, `status`, `type`). Communication channel FKs, `is_primary`. Email if unique. **Requires DB support (e.g., GIN index) for efficient querying on `custom_fields`**.
*   Search: API filtering on key fields + potentially primary channel + custom fields.

### 4.2 Security
*   Access Control: Permissions (`add_contact`, etc.). Access possibly scoped by Org or role. PII handling. Custom field access control.
*   Audit Logging: Log CRUD on Contact/Channels, including `custom_fields` changes, via Audit System.

### 4.3 Performance
*   Efficient contact queries. Efficient retrieval of primary channels (`prefetch_related`). Efficient querying on `custom_fields` (needs indexing).

### 4.4 Integration
*   Core data for CRM/Sales/Support. Links to `Organization`, `Address`. Linked from channel models.
*   API Endpoints for Contact and related channels. Define `custom_fields` handling.
*   Integrates with `CustomFieldDefinition` mechanism.
*   Optional external sync.

## 5. Non-Functional Requirements

*   Scalability (millions of contacts), Availability, Consistency (incl. primary flags), Backup/Recovery.

## 6. Success Metrics

*   Data accuracy/completeness. Ease of management. Successful integration. Compliance. Successful use of custom fields.

## 7. API Documentation Requirements

*   Document Contact/Channel models/fields (incl. `custom_fields`).
*   Document APIs for managing Contact and Channels, including `custom_fields`.
*   Examples for creating contacts with channels, `custom_fields`.
*   Permissions documentation.
*   Document how to discover custom field schemas (if applicable).

## 8. Testing Requirements

*   Unit Tests (Models, primary flag logic, custom field validation logic).
*   Integration Tests (API CRUD for Contact/Channels, **saving/validating `custom_fields`**, filtering, permissions, org linking).
*   Data Validation Tests (Email/Phone formats).
*   Security Tests (PII access, custom field access).

## 9. Deployment Requirements

*   Migrations (Contact, Channels, indexes incl. JSONField if needed).
*   Initial data import considerations.
*   Deployment of `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements

*   Backups. Data cleansing/deduplication processes (separate).
*   Management of custom field schemas.

### Address

# Address Model - Product Requirements Document (PRD) - Simplified (with Custom Fields)

## 1. Overview

*   **Purpose**: To define a standardized model for storing and managing **physical postal addresses**, potentially extended with **dynamic custom fields**, within the ERP system.
*   **Scope**: Definition of the `Address` data model structure for physical addresses, its core fields, basic validation, and custom field capability. Excludes digital addresses, external validation/geocoding services, and detailed history.
*   **Implementation**: Defined as a concrete Django Model. It should inherit `Timestamped`, `Auditable`. Uses a `JSONField` for custom fields.
*   **Target Users**: Systems/Modules needing addresses (UserProfile, Organization, Contact, Warehouse), Admins, Users entering address data.

## 2. Business Requirements

*   Store physical locations accurately.
*   Support international address formats.
*   Provide a standardized, reusable address structure.
*   Allow adding specific, dynamic attributes to addresses as needed per implementation requirements (via Custom Fields).

## 3. Functional Requirements

### 3.1 `Address` Model Definition
*   **Inheritance**: Should inherit `Timestamped`, `Auditable`.
*   **Fields**:
    *   `street_address_1`, `street_address_2`, `city`, `state_province`, `postal_code`.
    *   `country`: (CharField, max_length=2) **Required**. ISO 3166-1 alpha-2 code. (Indexed).
    *   `latitude`, `longitude`: (DecimalField, nullable, blank=True).
    *   `status`: (CharField with choices, optional).
    *   **`custom_fields`**: (JSONField, default=dict, blank=True) Stores values for dynamically defined custom fields relevant to addresses.
*   **Meta**: `verbose_name`, `verbose_name_plural`, potential indexes.
*   **String Representation**: Concise address string.

### 3.2 Custom Field Schema Definition (External Mechanism)
*   **Requirement**: A separate mechanism (e.g., `CustomFieldDefinition` model) is needed to define the schema for custom fields applicable to `Address`.
*   **Schema Attributes**: Defines key, label, type, validation, choices, etc.

### 3.3 Data Management & Operations
*   **CRUD**: Standard operations via Admin/API.
*   **Validation**: Basic format/length validation. Country code validation. Custom field validation against schema (in Serializer/Form). *External validation out of scope.*
*   **Uniqueness**: Not typically unique system-wide.

### 3.4 Relationship with Other Models
*   Linked *to* by other models (UserProfile, Organization, Warehouse) via `ForeignKey`. Define `on_delete` behavior (SET_NULL, PROTECT).

### 3.5 Custom Field Validation
*   **Requirement**: Data saved to `Address.custom_fields` must be validated against the corresponding schema defined externally.
*   **Implementation**: Logic in API Serializers or Forms.

### 3.6 Out of Scope for this Model
*   Digital Addresses, External Validation/Geocoding Services, Address History (Audit Log), Complex Address-Address relationships.

## 4. Technical Requirements

### 4.1 Data Management
*   Storage: Standard fields + JSONField.
*   Indexing: Key address components (`city`, `state_province`, `postal_code`, `country`). **Requires DB support (e.g., GIN index) for efficient querying on `custom_fields`**.
*   Search: Basic filtering + potential filtering on custom fields.

### 4.2 Security
*   Access Control: Permissions (`add_address`, etc.). Access often implicit via owning record. Consider custom field access.
*   Data Privacy: PII handling according to regulations.
*   Audit Logging: Log CRUD operations, including changes to `custom_fields`, via Audit System.

### 4.3 Performance
*   Efficient querying on standard fields and potentially `custom_fields` (needs indexing). Efficient retrieval via FK using `select_related`.

### 4.4 Integration
*   Primary target for ForeignKeys.
*   Optional dedicated API endpoints, or manage via owning entity's API. Define how `custom_fields` are managed via API.
*   Integrates with `CustomFieldDefinition` mechanism.
*   Separate integration for External Services (validation/geocoding).

## 5. Non-Functional Requirements

*   Scalability (millions of addresses), Availability, Consistency, Backup/Recovery, Accuracy.

## 6. Success Metrics

*   Successful storage/retrieval. Ability to filter. Low data errors. Successful use of custom fields where needed.

## 7. API Documentation Requirements (If API Endpoint is implemented)

*   Document Address model fields (incl. `custom_fields`). Country code standard.
*   Document API endpoints and how `custom_fields` are handled.
*   Auth/Permission requirements.
*   Document how to discover available custom field schemas for addresses (if applicable).

## 8. Testing Requirements

*   Unit Tests (Model, basic validation, `custom_fields` handling logic if any).
*   Integration Tests (CRUD via owning model, FK constraints, API tests including **saving/validating `custom_fields`**).
*   Security Tests (PII access, custom field access).

## 9. Deployment Requirements

*   Migrations (Address table, indexes including for JSONField if needed).
*   Country data validation/choices mechanism.
*   Deployment of `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements

*   Backups. Data quality monitoring.
*   Management of custom field schemas.
## System Models


### Audit Logging



# Audit Logging System - Product Requirements Document (PRD) - Refined

## 1. Overview

*   **Purpose**: To define the requirements for a standardized **Audit Logging System** responsible for creating and storing an immutable trail of significant activities and data changes within the ERP system.
*   **Scope**: Definition of the central `AuditLog` model, the mechanisms for capturing auditable events, basic requirements for accessing/querying the logs, and related technical considerations. This system provides historical tracking and accountability.
*   **Target Users**: System Administrators, Auditors, Compliance Officers, potentially Support Staff (with specific, limited query permissions).

## 2. Business Requirements

*   **Accountability**: Track user actions and system events to determine who did what, when.
*   **Change History**: Provide a historical record of modifications to critical data entities.
*   **Compliance**: Support internal and external audit requirements by providing verifiable logs.
*   **Security Monitoring**: Aid in detecting suspicious activities or unauthorized changes.
*   **Troubleshooting**: Assist in diagnosing issues by reviewing the sequence of events leading up to a problem.

## 3. Functional Requirements

### 3.1 Audit Log Entry (`AuditLog` Model Definition)
*   A dedicated concrete model (e.g., `AuditLog` likely in `core` or a dedicated `audit` app) will store individual audit records.
*   **Inheritance**: Should inherit `Timestamped` (provides `created_at` which serves as the primary event timestamp). Does *not* typically inherit `Auditable` (as it logs actions *by* users, not actions *on* the log itself) and is *not* typically `OrganizationScoped` directly (it logs events *within* orgs, identified by the `organization` FK).
*   **Required Fields for each Log Entry**:
    *   `timestamp`: (DateTimeField, default=timezone.now, db_index=True) Explicit timestamp, defaulting to now (can override if logging past events). Often `Timestamped.created_at` is sufficient and this field might be omitted if `Timestamped` is inherited. *(Decision: Use `Timestamped.created_at` or separate `timestamp` field? Using `Timestamped.created_at` is simpler)*. Let's assume use of `Timestamped.created_at`.
    *   `user`: (ForeignKey to `User` (`settings.AUTH_USER_MODEL`), on_delete=models.SET_NULL, null=True, blank=True, db_index=True) The user who performed the action. Null/blank if system-initiated or user deleted.
    *   `organization`: (ForeignKey to `Organization`, on_delete=models.SET_NULL, null=True, blank=True, db_index=True) The organization context in which the action occurred. Essential for filtering logs in a multi-tenant system.
    *   `action_type`: (CharField with choices, max_length=50, db_index=True) The type of action performed (e.g., 'CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'LOGIN_FAILED', 'PERMISSION_ASSIGN', 'PERMISSION_REVOKE', 'ROLE_CHANGE', 'SYSTEM_EVENT', 'ORDER_PLACED'). Needs a well-defined set of choices.
    *   `content_type`: (ForeignKey to `django.contrib.contenttypes.models.ContentType`, null=True, blank=True, db_index=True) The model/type of the primary resource affected by the action (if applicable).
    *   `object_id`: (CharField, max_length=255, null=True, blank=True, db_index=True) The primary key (as string to support UUIDs/Ints) of the specific resource instance affected (if applicable).
    *   `object_repr`: (CharField, max_length=255, blank=True) A human-readable representation of the affected object *at the time of the event* (e.g., Organization name, User username, Product SKU). Useful for quick identification in logs.
    *   `changes`: (JSONField, null=True, blank=True) Stores details of data changes, primarily for 'UPDATE' actions. Structure: `{"field_name": {"old": "old_value", "new": "new_value"}, ...}`. Store only changed fields. Sensitive fields should be masked or excluded based on policy.
    *   `context`: (JSONField, null=True, blank=True) Additional contextual information (e.g., `{"ip_address": "1.2.3.4", "session_key": "abc"}` for logins, `{"source": "api_v1"}` for API actions).
*   **Meta**: `verbose_name`, `plural`, `ordering = ['-created_at']`, relevant `indexes` (e.g., composite on `content_type`, `object_id`).

### 3.2 Event Categories to Audit (Action Types & Triggers)
*   The system must capture and log events for at least the following categories (defining corresponding `action_type` choices):
    *   **Data Changes (CRUD on Key Models)**: Trigger on `post_save` (distinguish CREATE/UPDATE via `created` flag), `post_delete`. Populate `changes` for UPDATEs. Key models include `Organization`, `UserProfile` (and potentially sensitive `User` fields if changed via admin), `Product`, `Category`, `Contact`, `Address`, `Warehouse`, `Document`, `Invoice`, `Order`, `Payment`, `Role`/`Group`, `Permission` assignments, `FieldPermission`, `AutomationRule`, etc. *(Maintain a list of explicitly audited models)*.
    *   **User Authentication**: Trigger on `user_logged_in`, `user_logged_out`, `user_login_failed` signals. Populate `context` with IP Address. `action_type` examples: 'LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGOUT'.
    *   **Permission/Role Changes**: Trigger on `m2m_changed` for `User.groups`, `Group.permissions`, or via explicit logging when `FieldPermission` or `UserOrganizationRole` records are changed. `action_type` examples: 'USER_ROLE_ADDED', 'USER_ROLE_REMOVED', 'ROLE_PERMISSION_CHANGED'.
    *   **Key System Events**: Explicit logging for critical actions like initiating major data imports/exports (`DataJob` status changes), running critical maintenance tasks. `action_type` examples: 'EXPORT_JOB_STARTED', 'IMPORT_JOB_COMPLETED'.

### 3.3 Event Capturing Mechanism
*   **Primary Method**: Utilize **Django Signals** (`post_save`, `post_delete`, auth signals, `m2m_changed`, potentially custom signals) connected to receiver functions.
*   **Signal Receivers**: Implement efficient receiver functions (ideally in `signals.py` per app or a central `audit/receivers.py`).
    *   Receivers extract context (user from request middleware like `django-crum`, instance data, `created`/`update_fields` flags).
    *   Determine `action_type`.
    *   For UPDATEs, calculate the `changes` dictionary (comparing `instance` fields to previous state, possibly requiring fetching the object pre-save or using a library like `django-simple-history`'s tracking). Handle related fields carefully. Mask sensitive fields.
    *   Determine `organization` context.
    *   Create and save the `AuditLog` instance.
    *   **Consider Asynchronicity:** If calculating `changes` is complex or saving the `AuditLog` adds noticeable latency to critical operations, consider queuing an asynchronous Celery task from the signal receiver to create the `AuditLog` entry. This adds complexity but improves primary request performance. *(Decision: Sync vs Async logging? Start with Sync, optimize later if needed)*.
*   **Helper Function**: Create a central helper function `log_audit_event(user, organization, action_type, content_object=None, changes=None, context=None)` to standardize log creation.

### 3.4 Log Access & Querying
*   **Admin Interface**: Provide a read-only Django Admin interface for `AuditLog`.
    *   Use `list_display` to show key fields (timestamp, user, org, action, object repr).
    *   Implement `list_filter` for filtering by `user`, `organization`, `action_type`, `content_type`, date range (`timestamp`).
    *   Implement `search_fields` for searching `object_repr`, potentially `user__username`.
    *   Display `changes` and `context` JSON nicely (perhaps using `django-json-widget`).
*   **API (Restricted)**: Provide a read-only API endpoint (e.g., `/api/v1/audit-logs/`) secured for Admin/Auditor roles.
    *   Support filtering similar to the Admin interface via query parameters.
    *   Implement pagination.

## 4. Technical Requirements

### 4.1 Data Management (`AuditLog` Model)
*   **Storage**: Standard DB storage. `JSONB` in PostgreSQL is crucial for efficient querying/indexing of `changes` and `context` fields.
*   **Indexing**: Critical indexes on fields used for filtering: `created_at` (timestamp), `user`, `organization`, `action_type`, `content_type`, `object_id`. Composite index on `(content_type, object_id)` is essential for finding history for a specific object. Consider GIN indexes on `changes` and `context` JSONB fields in PostgreSQL if querying within them is required.
*   **Data Volume & Archiving/Purging**: The `AuditLog` table **will grow very large**. A strategy for managing this size is **essential**:
    *   Define a data retention policy (e.g., keep active logs for 90 days, archive up to 1 year, purge older).
    *   Implement regular (e.g., nightly/weekly) archiving (moving data to slower/cheaper storage or separate tables) or purging (deletion) based on the retention policy. This typically requires custom management commands or database procedures.
*   **Immutability**: Design to prevent modification of log entries after creation (enforce via application logic/permissions).

### 4.2 Security
*   **Access Control**: Use Django permissions (`view_auditlog`) assigned to specific Admin/Auditor roles to strictly control who can view logs via Admin/API. No standard user access.
*   **Data Masking**: Implement logic (e.g., within the signal receiver or `log_audit_event` helper) to mask or exclude sensitive fields (passwords, tokens, PII based on policy) before saving them in the `changes` JSON field.
*   **Integrity**: Protect against tampering (standard DB security).

### 4.3 Performance
*   **Log Creation**: Minimize performance impact of signal receivers/logging calls on primary operations. Use efficient methods for detecting changes. Consider async logging if needed.
*   **Log Querying**: Ensure queries (Admin filters, API) are highly performant using appropriate indexes. Avoid slow queries on the potentially massive `AuditLog` table.

### 4.4 Integration
*   **Signal Registration**: Connect receivers to relevant signals from audited models and auth system.
*   **User/Organization Context**: Requires reliable access to the current user and organization context (e.g., via middleware like `django-crum` or passing context explicitly).
*   **ContentType Framework**: Relies heavily on `django.contrib.contenttypes`.

## 5. Non-Functional Requirements

*   **Scalability**: Handle high volume of log entries. Database performance for writes and reads must scale. Archiving/Purging essential for long-term scalability.
*   **Reliability**: Logging mechanism should be reliable; minimize loss of audit records.
*   **Availability**: Viewing interface/API should be available for authorized users.
*   **Data Consistency**: Ensure logged data (user, object refs, changes) is accurate at the time of the event.

## 6. Success Metrics

*   Comprehensive coverage of critical events as defined.
*   Ability to successfully retrieve audit history for specific objects or users.
*   Performance of log creation has negligible impact on user operations.
*   Performance of log querying meets requirements for administrators/auditors.
*   Compliance requirements related to audit trails are met.

## 7. API Documentation Requirements (If Log Query API is implemented)

*   Document the `/audit-logs/` endpoint.
*   Detail available query parameters for filtering.
*   Describe the `AuditLog` response structure, including `changes` and `context` formats.
*   Specify required Admin/Auditor permissions.

## 8. Testing Requirements

*   **Unit Tests**: Test signal receiver logic (parsing args, calculating changes, calling log creation helper - requires mocking). Test `log_audit_event` helper function. Test data masking logic.
*   **Integration Tests**:
    *   Trigger audited actions (create/update/delete models, login/logout) and verify `AuditLog` entries are created with the correct `user`, `organization`, `action_type`, `content_object`, `changes`, and `context`.
    *   Test filtering logs via Admin interface or API with various parameters.
    *   Test access control for viewing logs.
    *   Test archiving/purging scripts/commands (requires careful test setup).
*   **Performance Tests**: Measure write throughput and query performance on a large, populated `AuditLog` table in a staging environment.

## 9. Deployment Requirements

*   Migrations for `AuditLog` model and crucial indexes.
*   Ensure signal receivers are connected in production.
*   Deploy and schedule archiving/purging jobs/commands.
*   Assign `view_auditlog` permissions to appropriate roles.
*   Configure data masking rules for sensitive fields.

## 10. Maintenance Requirements

*   Monitor `AuditLog` table growth and query performance.
*   Ensure archiving/purging jobs run successfully.
*   Update audited models list and signal receivers as application evolves.
*   Regular database maintenance (indexing, vacuuming) on the `AuditLog` table.

--- END OF FILE audit_logging_system_prd.md ---
### Auditable


# Auditable Abstract Base Model - Product Requirements Document (PRD)

## 1. Overview

*   **Purpose**: To provide a standardized, automatic mechanism for tracking the user who created and the user who last modified model instances across the ERP system using an **Abstract Base Model**.
*   **Scope**: Definition and implementation of an **Abstract Base Model** that adds `created_by` and `updated_by` foreign key fields to inheriting models.
*   **Target Users**: System (automatically populating fields), Developers (inheriting the abstract model), Audit Log system (referencing these fields).

## 2. Business Requirements

*   **Accountability**: Know which user initially created any given record.
*   **Change Tracking**: Know which user last modified any given record.
*   **Consistency**: Ensure a uniform way of tracking basic user attribution across all relevant models.
*   **Foundation for Auditing**: Provide essential user context for more detailed audit logs.

## 3. Functional Requirements

### 3.1 Abstract Base Model Definition (`Auditable`)
*   **Implementation**: Defined as a Django **Abstract Base Model** (inherits from `models.Model` and includes `class Meta: abstract = True`).
*   **Location**: Defined in a shared location (e.g., `core/models.py` or `common/models.py`).
*   **Dependencies**: Requires the `User` model (`settings.AUTH_USER_MODEL`) to be defined.
*   **Fields**:
    *   `created_by`: (`models.ForeignKey`)
        *   Links to `settings.AUTH_USER_MODEL`.
        *   Set automatically when the record is first created to the user performing the action.
        *   Should not be editable after creation.
        *   `related_name`: Use `"+"` to avoid creating a reverse relation from User back to every auditable model, or use a pattern like `created_%(app_label)s_%(class)s_set`. `related_name="+"` is common for purely tracking fields.
        *   `on_delete=models.SET_NULL`: **Crucial**. If the creating user is deleted, we want to keep the record but set the `created_by` field to NULL, preserving the historical fact that *someone* created it without breaking referential integrity.
        *   `null=True`, `blank=True`: Necessary to allow `SET_NULL`. Also allows creation by system processes where no user is logged in (though ideally, a dedicated 'system' user is used).
        *   `editable=False`: Prevent modification via standard forms/admin.
    *   `updated_by`: (`models.ForeignKey`)
        *   Links to `settings.AUTH_USER_MODEL`.
        *   Set automatically every time the record is saved to the user performing the action.
        *   `related_name="+"`.
        *   `on_delete=models.SET_NULL`.
        *   `null=True`, `blank=True`.
        *   `editable=False`.
*   **Automation**: Requires logic (typically via overriding model `save()` method or potentially using signals, though `save()` override is common for this) to automatically populate these fields based on the currently authenticated user. This logic needs access to the user performing the request/action.

### 3.2 Model Inheritance
*   All concrete models requiring user tracking *must* inherit from this `Auditable` **Abstract Base Model**.
*   Example Inheritance: `class MyModel(Timestamped, Auditable): ...` (Often used together).
*   Target Models: `Organization`, `Product`, `Contact`, `Address`, `Invoice`, etc.

### 3.3 Data Population (Automatic)
*   **Challenge:** Unlike `auto_now*` for timestamps, Django doesn't have built-in `auto_set_user` fields. This requires custom implementation.
*   **Recommended Implementation:**
    1.  Use middleware (e.g., `django-crum` - Current Request User Middleware) or thread-local storage to make the current `request.user` globally accessible within the request cycle *in a safe way*.
    2.  Override the `save()` method in the `Auditable` abstract model (or potentially a common concrete base model that inherits the mixins).
    3.  In the overridden `save()`:
        *   Get the current user using the chosen method (e.g., `get_current_user()` from `django-crum`).
        *   If the user is authenticated:
            *   If `self.pk` is `None` (creating), set `self.created_by = current_user`.
            *   Always set `self.updated_by = current_user`.
        *   Call `super().save(*args, **kwargs)`.

## 4. Technical Requirements

### 4.1 Implementation
*   Define the `Auditable` abstract base model with the `ForeignKey` fields (`created_by`, `updated_by`) linked to `settings.AUTH_USER_MODEL` using `on_delete=models.SET_NULL`.
*   Implement the mechanism (middleware + `save()` override recommended) to automatically populate these fields. Ensure this mechanism handles unauthenticated users or system processes gracefully (leaves fields NULL or uses a designated system user).

### 4.2 Database
*   Database foreign key constraints will be created linking to the User table.
*   Indexes on `created_by_id` and `updated_by_id` might be beneficial if frequently filtering by user, but likely not essential initially.

### 4.3 Performance
*   Getting the current user on every save adds minimal overhead if using an efficient middleware/thread-local approach like `django-crum`. Avoid complex lookups in the `save()` method.

### 4.4 Integration
*   Depends on `settings.AUTH_USER_MODEL`.
*   Requires integration with the request cycle (via middleware or similar) to identify the current user.

## 5. Non-Functional Requirements

*   **Reliability**: Automatic population must work consistently for all inheriting models and handle anonymous users correctly.
*   **Maintainability**: The abstract model and user-fetching logic should be simple.
*   **Consistency**: Provides a standard way to identify creators/updaters.

## 6. API/Serialization

*   When models inheriting `Auditable` are serialized, `created_by` and `updated_by` fields might be included (read-only) and potentially nested to show user details (e.g., username). Requires careful consideration of performance and data exposure. Often just the IDs are sufficient.

## 7. Testing Requirements

*   **Unit Tests**:
    *   Define a simple concrete test model inheriting `Auditable` (and `Timestamped`).
    *   **Requires mocking the current user:** Use tools like `override_settings` (if user is stored in settings context, less common), mock the middleware function (`mock.patch`), or set thread-local storage directly within the test setup.
    *   Test creating an instance with a mocked user: Verify `created_by` and `updated_by` are set to the mocked user.
    *   Test updating the instance with a *different* mocked user: Verify `created_by` remains the same, and `updated_by` changes to the new user.
    *   Test saving without an authenticated user (if applicable): Verify fields remain NULL or are set to a system user if that pattern is used.
*   **Integration Tests**:
    *   When creating/updating models via API endpoints with an authenticated user, verify `created_by` / `updated_by` are correctly populated (though often not directly exposed in API responses, check the database record).

## 8. Deployment Requirements

*   **Migrations**: Migrations will add the `created_by_id` and `updated_by_id` columns (with foreign key constraints) when concrete models inherit `Auditable`. Handle default values/nullability correctly if adding to existing models with data (similar to `Timestamped`).
*   **Middleware**: Ensure the chosen middleware (like `django-crum`) for tracking the current user is added to `settings.MIDDLEWARE`.

## 9. Maintenance Requirements

*   Minimal maintenance for the abstract model itself. Ensure the user-fetching mechanism remains reliable.

--- END OF FILE auditable_prd.md ---

This PRD now specifically defines the `Auditable` abstract base model for `created_by`/`updated_by` fields, including the crucial implementation detail about needing a mechanism (like middleware + save override) to automatically populate them. It slots correctly into Phase 1 of our implementation plan right after `User` and `Timestamped`.
### Timestamped

# Timestamped Abstract Base Model - Product Requirements Document (PRD) - Simplified & Specified

## 1. Overview

*   **Purpose**: To provide a standardized, automatic mechanism for tracking the creation and last modification time of model instances across the ERP system using an **Abstract Base Model**.
*   **Scope**: Definition and implementation of an **Abstract Base Model** that adds `created_at` and `updated_at` timestamp fields to inheriting models.
*   **Target Users**: Developers (inheriting the abstract model), System (automatically populating fields).

## 2. Business Requirements

*   **Basic Audit Trail**: Know when any given record was initially created.
*   **Modification Tracking**: Know when any given record was last updated.
*   **Consistency**: Ensure a uniform way of tracking these basic timestamps across all relevant models.

## 3. Functional Requirements

### 3.1 Abstract Base Model Definition (`Timestamped`)
*   **Implementation**: Defined as a Django **Abstract Base Model** (inherits from `models.Model` and includes `class Meta: abstract = True`).
*   **Location**: Defined in a shared location (e.g., `core/models.py` or `common/models.py`).
*   **Fields**:
    *   `created_at`: (`models.DateTimeField`)
        *   Automatically set to the current date and time when the record is first created.
        *   Should not be editable after creation.
        *   Implementation Detail: Use `auto_now_add=True`.
    *   `updated_at`: (`models.DateTimeField`)
        *   Automatically set to the current date and time every time the record is saved (including creation).
        *   Implementation Detail: Use `auto_now=True`.
*   **Timezone Handling**:
    *   Timestamps must be timezone-aware.
    *   Project Requirement: Django's `USE_TZ = True` setting must be enabled in `settings.py`.
    *   Storage Detail: Timestamps will be stored in the database in UTC (standard Django behavior with `USE_TZ=True`).

### 3.2 Model Inheritance
*   All concrete models requiring basic creation/update timestamps *must* inherit from this `Timestamped` **Abstract Base Model**.
*   Example Inheritance: `class MyModel(Timestamped): ...`
*   Target Models: `Organization`, `OrganizationType`, `User`, `Product`, `Contact`, `Address`, etc.

### 3.3 Data Population
*   The `created_at` and `updated_at` fields must be populated automatically by Django's ORM during the `save()` process via the `auto_now_add` and `auto_now` options. No manual setting of these fields is required in standard application code.

## 4. Technical Requirements

### 4.1 Implementation
*   Use standard Django `DateTimeField` with `auto_now_add=True` and `auto_now=True` arguments within the `Timestamped` abstract base model definition.
*   Ensure `USE_TZ = True` is set in the project's `settings.py`.

### 4.2 Database
*   Database field types used by Django for `DateTimeField` when `USE_TZ=True` must correctly store timezone-aware timestamps (e.g., `TIMESTAMP WITH TIME ZONE` in PostgreSQL).
*   Consider adding database indexes to `created_at` and `updated_at` fields on the *concrete* model tables if they are frequently used for filtering or ordering large datasets, but this is not mandatory initially for the abstract model definition itself.

### 4.3 Performance
*   Negligible performance impact, as field population is handled efficiently by the ORM.

## 5. Non-Functional Requirements

*   **Reliability**: The automatic timestamp population must work reliably for all inheriting models.
*   **Maintainability**: The abstract base model should be simple and require minimal maintenance.
*   **Consistency**: Provides a consistent way to access creation/update times across different models inheriting it.

## 6. API/Serialization

*   When concrete models inheriting `Timestamped` are serialized (e.g., via DRF serializers), the `created_at` and `updated_at` fields should typically be included as read-only fields in the serializer definition for the concrete model.
*   API responses should ideally represent these timestamps in a standard format, preferably ISO 8601 with timezone information (e.g., `2023-10-27T10:30:00Z`). Timezone conversion for display is handled outside this model's scope (e.g., serializers, frontend).

## 7. Testing Requirements

*   **Unit Tests**:
    *   Define a simple concrete test model inheriting `Timestamped`.
    *   Create an instance of the test model. Verify `created_at` and `updated_at` are set and approximately equal after initial save.
    *   Update the instance and save again. Verify `created_at` remains unchanged and `updated_at` is updated.
    *   Verify the stored values are timezone-aware (`is_aware` is True).
*   **Integration Tests**:
    *   When creating/updating concrete models (like `Organization`) via API endpoints, verify the `created_at` and `updated_at` fields are present and correctly populated in the API response and database.

## 8. Deployment Requirements

*   **Migrations**: When a concrete model inherits `Timestamped` for the first time or the abstract model itself is added/changed, Django's `makemigrations` command will generate the necessary migration(s) to add the `created_at` and `updated_at` columns to the concrete model's table. Handle default values appropriately for existing rows if adding to models with data.
*   **Settings**: Ensure `USE_TZ = True` is active in all deployment environments.

## 9. Maintenance Requirements

*   Minimal maintenance expected for the abstract base model itself. Primarily relates to standard Django and database upkeep.

### Status

# Status Model - Product Requirements Document (PRD) - Simplified (with Custom Fields)

## 1. Overview

*   **Purpose**: To define a standardized set of status values, potentially extended with **dynamic custom fields**, that can be consistently applied to various entities across the ERP system, providing a controlled vocabulary for states.
*   **Scope**: Definition of the `Status` data model for representing distinct status values (e.g., 'Active', 'Pending', 'Approved'), its core attributes, basic management, and custom field capability. Excludes transition logic, workflow rules, and detailed history.
*   **Implementation**: Defined as a concrete Django Model. It should inherit standard base models like `Timestamped`, `Auditable`. Uses a `JSONField` for custom fields.
*   **Target Users**: Developers (referencing statuses), System Administrators (managing statuses and custom fields), Business Analysts (defining statuses).

## 2. Business Requirements

*   **Standardized States**: Provide a consistent set of terms for describing the state of different entities.
*   **Clarity & Reporting**: Enable clear identification, filtering, and reporting based on entity status.
*   **Foundation for Workflows**: Serve as the reference points (nodes/states) for future workflow implementations.
*   **Extensibility**: Allow administrators to define new status values and add specific dynamic attributes to status definitions as needed (via Custom Fields).

## 3. Functional Requirements

### 3.1 `Status` Model Definition
*   **Inheritance**: Should inherit `Timestamped`, `Auditable`.
*   **Fields**:
    *   `slug`: (SlugField or CharField, max_length=50, primary_key=True) Unique, machine-readable identifier (e.g., 'active', 'pending_approval'). **Primary Key**.
    *   `name`: (CharField, max_length=100, unique=True) Human-readable name (e.g., "Active", "Pending Approval").
    *   `description`: (TextField, blank=True) Optional explanation.
    *   `category`: (CharField, max_length=50, blank=True, db_index=True) Optional grouping category (e.g., 'General', 'Order Lifecycle').
    *   `color`: (CharField, max_length=7, blank=True) Optional hex color code for UI.
    *   **`custom_fields`**: (JSONField, default=dict, blank=True) Stores values for dynamically defined custom fields relevant to the status definition itself (e.g., UI flags, workflow configuration hints).
*   **Meta**:
    *   `verbose_name = "Status"`
    *   `verbose_name_plural = "Statuses"`
    *   `ordering = ['category', 'name']`
*   **String Representation**: `__str__` method should return the `name`.

### 3.2 Custom Field Schema Definition (External Mechanism)
*   **Requirement**: If custom fields are used, a separate mechanism (e.g., `CustomFieldDefinition` model, possibly filtered by a 'Status' context) is needed to define their schema (key, label, type, validation, etc.).
*   **Schema Attributes**: Defines key, label, type, validation, choices, help text, etc.

### 3.3 Data Management & Operations
*   **CRUD Operations**: Ability to Create, Read, Update, Delete Status records (via Admin UI, potentially API). Includes managing `custom_fields` data.
*   **Deletion Constraint**: Deletion should be restricted if the status `slug` is referenced (e.g., in CharField choices or FKs). Consider using an `is_active` flag instead of deletion.
*   **Custom Field Value Management**: API/Admin interfaces should allow viewing and updating the `custom_fields` JSON object on a `Status` record.
*   **Validation**: Unique constraints (`slug`, `name`). Custom field validation against schema (in Serializer/Form).
*   **Initial Data**: Populate common status values via data migration.

### 3.4 Relationship with Other Models
*   Typically referenced by `status` fields (usually `CharField`) on other models using the `Status.slug` value. Less commonly uses a direct `ForeignKey`.

### 3.5 Custom Field Validation
*   **Requirement**: Data saved to `Status.custom_fields` must be validated against the corresponding schema.
*   **Implementation**: Logic in API Serializers or Forms.

### 3.6 Out of Scope for this Model/PRD
*   **State Transition Logic/Rules**: Handled by a separate `Workflow`/`StateMachine` system.
*   **Transition Conditions/Actions**: Handled by the `Workflow`/`StateMachine` system.
*   **Status History (of other entities)**: Handled by the central `Audit Logging System`.

## 4. Technical Requirements

### 4.1 Data Management
*   **Storage**: Standard fields + JSONField.
*   **Indexing**: PK (`slug`), `name`, `category`. **Requires DB support (e.g., GIN index) for efficient querying on `custom_fields`** if needed.
*   **Initial Population**: Data migration required.
*   **Search**: Basic filtering/search on core fields, potentially `custom_fields`.

### 4.2 Security
*   **Access Control**: Restrict management of `Status` records (including `custom_fields`) to Admin roles.
*   **Audit Logging**: Log CRUD operations and changes to `custom_fields` via Audit System.

### 4.3 Performance
*   High performance for lookups by `slug`. Efficient listing. Efficient `custom_fields` querying (needs indexing).

### 4.4 Integration
*   **Primary Integration**: Provides reference values for status fields elsewhere.
*   **API Endpoint (Optional)**: Read-only API (`/api/v1/statuses/`) to list statuses (incl. `custom_fields`). Management API restricted.
*   **Workflow Integration (Future)**: Workflow system references `Status.slug`. Might read `custom_fields` for configuration.
*   **Custom Field Schema Integration**: Integrates with `CustomFieldDefinition` mechanism.

## 5. Non-Functional Requirements

*   **Availability**: Status definitions must be reliably available.
*   **Data Consistency**: `slug`/`name` uniqueness. Referential integrity if FKs used.
*   **Maintainability**: Simple model, plus management of custom field schemas.

## 6. Success Metrics

*   Consistent use of status values. Ease of admin. Successful use in workflows. Successful use of custom fields if implemented.

## 7. API Documentation Requirements (If API Endpoint is implemented)

*   Document Status model fields (incl. `custom_fields`).
*   Document API endpoints, `custom_fields` handling.
*   Auth/Permission requirements.
*   Document how to discover custom field schemas (if applicable).

## 8. Testing Requirements

*   **Unit Tests**: Test `Status` model, unique constraints, `custom_fields` logic if any.
*   **Data Tests**: Verify initial population.
*   **Integration Tests**: Test CRUD via Admin/API (incl. **saving/validating `custom_fields`**). Test deletion constraints. Test permissions.

## 9. Deployment Requirements

*   **Migrations**: Standard migration for `Status` table, indexes (incl. JSONField if needed).
*   **Initial Data Population**: Execute data migration.
*   **Custom Field Schema Deployment**: Deploy `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements

*   Admin management of statuses and custom field schemas. Backups.

## Authentication & Authorization


### Auth API



--- START OF FILE auth_api_prd.md ---

# Authentication API - Product Requirements Document (PRD)

## 1. Overview

*   **Purpose**: To define the requirements for the API-based authentication system, enabling users to securely log in via credentials (username/password), manage authentication tokens (JWT), use API keys for programmatic access, and manage Two-Factor Authentication (2FA) settings.
*   **Scope**: Covers user login (JWT obtain/refresh), API key authentication, and initial 2FA setup/management (specifically TOTP). Excludes user self-registration, the 2FA verification step during login (deferred), and the full password reset workflow (deferred).
*   **Technical Approach**: Leverages Django's built-in `User` model, `djangorestframework-simplejwt` for JWT, `djangorestframework-api-key` for API keys, and `django-otp` (with `otp_totp`) for 2FA.
*   **Target Users**: End users (logging in, managing 2FA), API Clients (using JWT or API Keys), System Administrators (managing API Keys).

## 2. Business Requirements

*   **Secure User Login**: Provide a standard and secure method for users to authenticate using their `username` and password via the API.
*   **Session Management (API)**: Manage user sessions effectively for API clients using industry-standard JWT (Access and Refresh tokens).
*   **Programmatic Access**: Enable secure server-to-server or third-party integrations using manageable, expirable API keys.
*   **Enhanced Security (2FA)**: Allow users to optionally enable Time-based One-Time Password (TOTP) 2FA for increased account security.
*   **Basic Account Management**: Allow authenticated users to change their own password.

## 3. Functional Requirements

### 3.1 Core Authentication (Django `User` Model)
*   Utilize Django's `auth.User` model for storing user credentials (`username`, hashed `password`, `email`, etc.) and core status fields (`is_active`, `is_staff`, `is_superuser`).
*   Authentication attempts will validate against the hashed password stored in this model.
*   User creation is handled outside this scope (e.g., Admin UI). No self-registration API.

### 3.2 JWT Token Management (`djangorestframework-simplejwt`)
*   **Token Obtain Endpoint**:
    *   URL: `POST /api/v1/auth/token/obtain/`
    *   Input: `username`, `password`.
    *   Output (Success): JSON containing `access` token (short-lived) and `refresh` token (longer-lived). HTTP 200 OK.
    *   Output (Failure): Standard API error response (e.g., 401 Unauthorized for bad credentials/inactive user).
    *   *Deferred*: This endpoint will need modification later to handle the 2FA verification step if 2FA is enabled for the user. Initially, it grants tokens directly upon valid password authentication.
*   **Token Refresh Endpoint**:
    *   URL: `POST /api/v1/auth/token/refresh/`
    *   Input: `refresh` token.
    *   Output (Success): JSON containing a new `access` token. HTTP 200 OK. Optionally rotate refresh tokens.
    *   Output (Failure): Standard API error response (e.g., 401 Unauthorized for invalid/expired refresh token).
*   **Token Verification Endpoint (Optional but Recommended)**:
    *   URL: `POST /api/v1/auth/token/verify/`
    *   Input: `token` (access token).
    *   Output (Success): HTTP 200 OK (empty body).
    *   Output (Failure): Standard API error response (e.g., 401 Unauthorized for invalid/expired token).
*   **Token Usage**: Clients must send the `access` token in the `Authorization: Bearer <access_token>` header for subsequent authenticated requests.

### 3.3 API Key Authentication (`djangorestframework-api-key`)
*   **Purpose**: Authenticate non-user programmatic clients.
*   **Generation & Management**:
    *   API Keys (`APIKey` model provided by library) are generated, managed (revoked, expiry set), and permissions assigned **only** via the Django Admin interface by administrators.
    *   Keys must have an expiry date.
    *   Keys store a hashed version; the original key is shown only once upon creation.
*   **Usage**: API clients must send their valid, unhashed API key in the **`X-API-Key`** HTTP header.
*   **Authentication Backend**: DRF's `APIKeyAuthentication` backend (configured as default) will validate the key provided in the `X-API-Key` header against the hashed keys in the database, checking for expiry and revocation status.
*   **Authorization**: Permissions for API key requests are determined by the permissions assigned *directly to the specific `APIKey` object* in the Django Admin, enforced using the library's `HasAPIKey` permission class (or custom logic referencing key permissions).

### 3.4 Two-Factor Authentication (2FA - TOTP Setup via `django-otp`)
*   **Scope**: Initial implementation focuses only on enabling/disabling TOTP via authenticator apps. The login flow modification to *verify* the 2FA code is deferred.
*   **Device Model**: Utilizes `django_otp.plugins.otp_totp.models.TOTPDevice` to store TOTP configuration linked to a User.
*   **Enablement Flow:**
    *   **Initiate Setup Endpoint**:
        *   URL: `POST /api/v1/auth/2fa/totp/setup/`
        *   Permissions: User must be authenticated (JWT).
        *   Action: Deletes any previous *unconfirmed* TOTP devices for the user. Creates a new, *unconfirmed* `TOTPDevice`.
        *   Output: JSON containing `setup_key` (secret key for manual entry) and `qr_code` (SVG or PNG data URI for authenticator app scanning). HTTP 200 OK.
    *   **Verify Setup Endpoint**:
        *   URL: `POST /api/v1/auth/2fa/totp/verify/`
        *   Permissions: User must be authenticated (JWT).
        *   Input: `token` (the 6-digit code from the authenticator app).
        *   Action: Finds the user's *unconfirmed* `TOTPDevice`. Verifies the provided `token` against the device. If valid, marks the device as `confirmed=True`. Optionally generates and returns one-time backup codes (`StaticDevice`/`StaticToken`).
        *   Output (Success): Success message, potentially backup codes. HTTP 200 OK.
        *   Output (Failure): Standard API error (400 Bad Request for invalid token or no setup found).
*   **Disable Endpoint**:
    *   URL: `POST /api/v1/auth/2fa/totp/disable/`
    *   Permissions: User must be authenticated (JWT).
    *   Input: User's current `password` (for confirmation).
    *   Action: Verifies password. If correct, deletes all `TOTPDevice` (and potentially other OTP devices like `StaticDevice`) records associated with the user.
    *   Output (Success): Success message. HTTP 200 OK.
    *   Output (Failure): Standard API error (400 Bad Request for wrong password).

### 3.5 Password Management (Basic)
*   **Password Change Endpoint**:
    *   URL: `POST /api/v1/auth/password/change/`
    *   Permissions: User must be authenticated (JWT).
    *   Input: `old_password`, `new_password1`, `new_password2`.
    *   Action: Validates old password against user's current hash. Validates new passwords match and meet complexity requirements (via Django settings/validators). If valid, updates the user's password hash using `user.set_password()`.
    *   Output (Success): Success message. HTTP 200 OK.
    *   Output (Failure): Standard API error (400 Bad Request for validation errors).
*   **Password Reset Flow (Deferred)**: Full flow (request reset email -> confirm via token -> set new password) is not included initially.

### 3.6 Out of Scope (Initial Implementation)
*   User Self-Registration API.
*   2FA Code Verification *during* the actual login (`/token/obtain/`) flow.
*   Full Password Reset workflow.
*   Management of API Keys via API endpoints (Admin only).
*   Support for other 2FA methods (SMS, HOTP, etc.).
*   Social Login / SSO integration.
*   Token Blacklisting / Advanced Logout for JWT.

## 4. Technical Requirements

### 4.1 Libraries & Configuration
*   Install and configure `djangorestframework-simplejwt`, `django-otp`, `django-otp.plugins.otp_totp`, `qrcode[pil]`, `djangorestframework-api-key`.
*   Configure required `INSTALLED_APPS`, `MIDDLEWARE`.
*   Configure `REST_FRAMEWORK` settings (`DEFAULT_AUTHENTICATION_CLASSES`).
*   Configure `SIMPLE_JWT` settings (lifetimes, etc.).
*   Configure `OTP_TOTP_ISSUER`.
*   Configure `REST_FRAMEWORK_API_KEY` setting (`HEADER_NAME`).

### 4.2 Security
*   JWT signing key must be kept secret.
*   Password hashing follows Django defaults (secure).
*   API Keys are hashed in the database.
*   TOTP secrets are stored securely by `django-otp`.
*   API endpoints must use appropriate permission classes (`IsAuthenticated`, `IsAdminUser`, potentially custom ones).
*   Rate limiting should be applied to login and potentially 2FA verification endpoints.
*   Password complexity rules enforced by Django settings.
*   Webhook validation needed if external services trigger auth events (not planned initially).

### 4.3 Integration
*   Integrates with Django `User` model.
*   Provides authentication backends for DRF.
*   Relies on secure storage for secrets/keys.
*   `django-otp` integrates with `User`.
*   `djangorestframework-api-key` integrates with DRF and Django Admin.

## 5. Non-Functional Requirements

*   **Security**: Paramount for all authentication operations.
*   **Reliability**: Login, token refresh, 2FA setup must be reliable.
*   **Performance**: Authentication checks and token generation should be fast.
*   **Usability**: API responses (especially errors) should be clear. 2FA setup flow should be understandable.

## 6. Success Metrics

*   Successful user login via JWT.
*   Successful token refresh.
*   Successful API authentication using API Keys.
*   Successful user enablement and disabling of TOTP 2FA.
*   Low rate of authentication-related errors/lockouts.
*   Security audits pass relevant authentication checks.

## 7. API Documentation Requirements

*   Document all Authentication API endpoints (`/auth/token/obtain/`, `/refresh/`, `/2fa/totp/setup/`, `/verify/`, `/disable/`, `/password/change/`).
*   Specify request methods, required headers (e.g., `Authorization: Bearer`, `X-API-Key`), request body formats, and response formats (success and error).
*   Explain the JWT obtain/refresh flow.
*   Explain how to use API Keys (header + key value).
*   Explain the TOTP setup/verify/disable flow.
*   Document permission requirements for each endpoint.

## 8. Testing Requirements

*   **Unit Tests**: Test any custom logic in views or serializers (e.g., password validation if customized). Mock external calls if any.
*   **Integration Tests / API Tests**:
    *   Test JWT obtain/refresh with valid/invalid credentials/tokens.
    *   Test API Key authentication with valid/invalid/expired/revoked keys using the `X-API-Key` header.
    *   Test full TOTP setup flow (initiate, verify with valid/invalid codes).
    *   Test TOTP disable flow (with correct/incorrect password).
    *   Test password change flow (with correct/incorrect old password, validation).
    *   Test permission enforcement on all endpoints.
*   **Security Tests**: Attempt common authentication attacks (e.g., brute force on login - check rate limiting, credential stuffing). Check for information leakage in error messages.

## 9. Deployment Requirements

*   Install required libraries in production environment.
*   Run all library migrations (`simplejwt`, `otp`, `api_key`).
*   Securely configure `SECRET_KEY`, `SIMPLE_JWT['SIGNING_KEY']`, database passwords, and external service keys (if any) via environment variables/secrets management.
*   Configure appropriate token lifetimes for production.
*   Administrators need access to Django Admin to manage API Keys.

## 10. Maintenance Requirements

*   Keep authentication libraries (`simplejwt`, `otp`, `api_key`) updated with security patches.
*   Monitor for authentication failures or suspicious activity (via logs).
*   Administrators manage API Keys lifecycle (creation, revocation, expiry). Rotate JWT signing key periodically.

--- END OF FILE auth_api_prd.md ---
### Organization Membership


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
### Organization Scoped



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

## Business Models


### Product

# Product Model - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To define the core model representing products, services, or other sellable/purchasable items within the ERP system.
*   **Scope**: Definition of the `Product` data model, its essential attributes (identification, type, category, status), basic configuration flags (e.g., inventory tracking), link to UoM, and custom field capability. Excludes detailed pricing, inventory level tracking, complex variants/bundles, and lifecycle history.
*   **Implementation**: Defined as a concrete Django Model. It **must** inherit `Timestamped`, `Auditable`, and `OrganizationScoped`. Uses a `JSONField` for custom fields.
*   **Target Users**: Product Managers, Inventory Managers, Sales Teams, Purchasing Teams, System Administrators.

## 2. Business Requirements

*   **Central Product Catalog**: Provide a single source of truth for all products and services offered or managed.
*   **Support Diverse Offerings**: Represent physical goods, services, digital items, raw materials, etc.
*   **Categorization**: Allow products to be classified using the defined category structures.
*   **Foundation for Operations**: Provide the core product reference needed by Sales, Purchasing, Inventory, Manufacturing, and Pricing modules.
*   **Extensibility**: Allow storing diverse, product-specific attributes via custom fields.
*   **Multi-Tenancy**: Product definitions must be scoped by Organization.

## 3. Functional Requirements

### 3.1 `Product` Model Definition
*   **Inheritance**: Must inherit `Timestamped`, `Auditable`, `OrganizationScoped`.
*   **Fields**:
    *   `name`: (CharField, max_length=255, db_index=True) Primary display name of the product/service.
    *   `sku`: (CharField, max_length=100, db_index=True) Stock Keeping Unit or unique product code. Should be unique within the organization (`unique_together = ('organization', 'sku')`).
    *   `description`: (TextField, blank=True) Detailed description of the product.
    *   `product_type`: (CharField with choices, db_index=True) High-level type (e.g., 'PHYSICAL_GOOD', 'SERVICE', 'DIGITAL', 'RAW_MATERIAL', 'COMPONENT', 'FINISHED_GOOD').
    *   `category`: (ForeignKey to `Category`, on_delete=models.PROTECT, null=True, blank=True, limit_choices_to={'category_type': 'PRODUCT'}, related_name='products') Primary category assignment. *(Consider ManyToManyField if products can belong to multiple categories)*.
    *   `status`: (CharField, max_length=50, choices=..., default='draft', db_index=True) Lifecycle status (e.g., 'Draft', 'Active', 'Discontinued', 'EndOfLife'). References slugs defined in the `Status` model/system.
    *   `base_uom`: (ForeignKey to `UnitOfMeasure`, on_delete=models.PROTECT, related_name='products_base') The primary unit of measure for stocking and basic pricing (e.g., 'EA', 'KG', 'M').
    *   `is_inventory_tracked`: (BooleanField, default=True) Does this product's stock level need tracking in the Inventory system? False for most services or non-stock items.
    *   `is_purchasable`: (BooleanField, default=True) Can this item typically be purchased?
    *   `is_sellable`: (BooleanField, default=True) Can this item typically be sold?
    *   `tags`: (ManyToManyField via `django-taggit` or similar, blank=True) For flexible classification.
    *   `attributes`: (JSONField, default=dict, blank=True) For storing semi-structured key-value attributes like dimensions, color, weight (if not using custom fields or variants).
    *   **`custom_fields`**: (JSONField, default=dict, blank=True) Stores values for dynamically defined custom fields specific to products.
*   **Meta**:
    *   `verbose_name = "Product"`
    *   `verbose_name_plural = "Products"`
    *   `unique_together = (('organization', 'sku'),)`
    *   `ordering = ['name']`
*   **String Representation**: Return `name` and/or `sku`.

### 3.2 Custom Field Schema Definition (External Mechanism)
*   Requirement for separate `CustomFieldDefinition` model/mechanism (possibly filtered by `Product.product_type` or `Category`) to define schema for product custom fields.

### 3.3 Data Management & Operations
*   **CRUD**: Standard operations via Admin/API, respecting Organization scope. Includes managing `custom_fields` and `attributes`.
*   **Validation**: Unique SKU within Org. FK constraints. Custom field validation against schema. Status logic enforced by Workflow/StateMachine system later.

### 3.4 Relationships
*   Links *to* `Organization` (via `OrganizationScoped`), `Category`, `UnitOfMeasure`.
*   Is linked *from* `PriceList` items, `InventoryItem` records, `OrderLine` items, `BillOfMaterial` components, etc. (defined in those modules).

### 3.5 Out of Scope for this Model/PRD
*   **Pricing Engine/Price Lists**: Handled by a separate Pricing module referencing `Product`.
*   **Inventory Level Tracking**: Handled by a separate Inventory module referencing `Product`.
*   **Complex Product Variants**: (e.g., Size/Color combinations with own SKUs/Inventory). Requires dedicated `ProductVariant` models/logic, potentially built upon this base `Product`. Treat as separate feature/PRD.
*   **Product Bundles/Kits**: Requires dedicated `BundleComponent` models/logic linking the bundle `Product` to its constituent `Product`s. Treat as separate feature/PRD.
*   **Detailed Lifecycle/Versioning**: Handled by `Status` field changes logged in `Audit Log`, or a dedicated Versioning system if needed.

## 4. Technical Requirements

### 4.1 Data Management
*   Storage: Standard fields + JSONFields.
*   Indexing: `sku`, `name`, `status`, `category`, `base_uom`, `organization` (from OrgScoped). **GIN index on `attributes` and `custom_fields`** if querying needed.
*   Search: API filtering/search on key fields, category, tags, potentially attributes/custom fields.

### 4.2 Security
*   **Access Control**: Permissions (`add_product`, `change_product`, `delete_product`, `view_product`). Enforced within Organization scope via `OrganizationScoped` mechanism. Field-level permissions may apply to sensitive fields (e.g., cost price if stored here) or custom fields.
*   **Audit Logging**: Log CRUD operations and changes to key fields/custom fields via Audit System.

### 4.3 Performance
*   Efficient querying/filtering/searching of products is critical. Requires good indexing.
*   Caching for frequently accessed product data.

### 4.4 Integration
*   **Core Integration**: Central model referenced by Inventory, Sales, Purchasing, Pricing, Manufacturing modules.
*   **API Endpoint**: Provide RESTful API (`/api/v1/products/`) for CRUD, respecting Org Scoping and permissions. Include filtering/search capabilities. Define `custom_fields`/`attributes` handling.
*   **Custom Field Schema Integration**: Integrates with `CustomFieldDefinition` mechanism.

## 5. Non-Functional Requirements

*   **Scalability**: Support potentially millions of product records.
*   **Availability**: Product catalog needs to be highly available.
*   **Data Consistency**: Maintain unique SKUs within Org, FK integrity.
*   **Backup/Recovery**: Standard procedures.

## 6. Success Metrics

*   Accurate product catalog data.
*   Ease of product management.
*   Successful integration with operational modules (Sales, Inventory, etc.).
*   Performant product searching/filtering.
*   Successful use of custom fields/attributes.

## 7. API Documentation Requirements

*   Document `Product` model fields (incl. `custom_fields`, `attributes`).
*   Document API endpoints for CRUD, filtering, searching. Detail filterable fields.
*   Document handling of `custom_fields`/`attributes` in API requests/responses.
*   Auth/Permission requirements (mentioning Org Scoping).
*   Document how to discover custom field schemas (if applicable).

## 8. Testing Requirements

*   **Unit Tests**: Test `Product` model, `unique_together` constraints, custom field logic if any.
*   **Integration Tests**:
    *   Test API CRUD operations, ensuring Org Scoping is enforced.
    *   Test filtering/searching via API.
    *   Test assigning Category, UoM.
    *   Test permissions.
    *   Test **saving/validating `custom_fields` and `attributes`**.
*   **Performance Tests**: Test API list/search performance with large product datasets.

## 9. Deployment Requirements

*   Migrations for `Product` table, indexes (incl. JSONFields).
*   Dependencies on `Category`, `UnitOfMeasure`, `Organization` models/migrations.
*   Deployment of `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements

*   Ongoing product data management via Admin/API.
*   Monitoring performance, adding indexes as needed. Backups.
*   Management of custom field schemas.

---
### Category

# Generic Category Model - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To define a standardized, hierarchical model for creating and managing various category structures used to classify different entities (e.g., Products, Documents, Assets) across the ERP system.
*   **Scope**: Definition of a generic `Category` data model supporting hierarchy, core attributes, type differentiation, custom fields, and basic management.
*   **Implementation**: Defined as a concrete Django Model using `django-mptt` for hierarchy. It should inherit `Timestamped`, `Auditable`. Uses a `JSONField` for custom fields.
*   **Target Users**: Product Managers, Content Managers, System Administrators, Developers (linking entities to categories).

## 2. Business Requirements

*   **Flexible Classification**: Allow grouping and classification of various ERP entities (Products, Documents, etc.) using consistent, hierarchical structures.
*   **Hierarchical Organization**: Support nested categories (trees) with parent-child relationships.
*   **Support Multiple Uses**: Accommodate different types of categorization needs via a `category_type` discriminator.
*   **Extensibility**: Allow adding specific dynamic attributes to categories via custom fields.
*   **Foundation for Filtering/Reporting**: Enable filtering, searching, and reporting based on assigned categories.

## 3. Functional Requirements

### 3.1 `Category` Model Definition
*   **Inheritance**: Must inherit `Timestamped`, `Auditable`, and `mptt.models.MPTTModel`.
*   **Fields**:
    *   `name`: (CharField, max_length=255) Human-readable name of the category.
    *   `slug`: (SlugField, max_length=255, unique=True, blank=True) A unique URL-friendly identifier. Auto-populated from name if blank. *(Alternatively, use a `code` field if non-slug identifiers are needed)*.
    *   `description`: (TextField, blank=True) Optional description.
    *   `parent`: (TreeForeignKey to `self`, on_delete=models.CASCADE, null=True, blank=True, related_name='children') Managed by `django-mptt`. Defines the parent in the hierarchy. `CASCADE` delete means deleting a parent deletes its children. *(Consider `PROTECT` if children should prevent parent deletion)*.
    *   `category_type`: (CharField, max_length=50, db_index=True) **Required**. Discriminator field indicating the type of hierarchy this category belongs to (e.g., 'PRODUCT', 'DOCUMENT_TYPE', 'ASSET_TYPE', 'ORG_COST_CENTER'). *(Consider using choices or a FK to a simple `CategoryType` model)*.
    *   `is_active`: (BooleanField, default=True, db_index=True) Allows deactivating categories without deletion.
    *   **`custom_fields`**: (JSONField, default=dict, blank=True) Stores values for dynamically defined custom fields relevant to the category definition itself.
*   **MPTT Meta**: `class MPTTMeta: order_insertion_by = ['name']`.
*   **Model Meta**:
    *   `verbose_name = "Category"`
    *   `verbose_name_plural = "Categories"`
    *   `unique_together = ('parent', 'name', 'category_type')` (Ensure name is unique within the same parent and type).
*   **String Representation**: `__str__` method should typically return the `name`. Consider indenting based on level for admin display.

### 3.2 Custom Field Schema Definition (External Mechanism)
*   **Requirement**: If custom fields are used, a separate mechanism (e.g., `CustomFieldDefinition` model, possibly filtered by `Category.category_type`) is needed to define their schema.
*   **Schema Attributes**: Defines key, label, type, validation, choices, etc.

### 3.3 Data Management & Operations
*   **CRUD Operations**: Ability to Create, Read, Update, Deactivate (`is_active=False`), and potentially Delete categories (via Admin UI and API). Note `on_delete` behavior for `parent`. Includes managing `custom_fields` data.
*   **Hierarchy Management**: Ability to change the `parent` of a category to restructure the tree (provided by `django-mptt` admin features or specific API actions).
*   **Validation**: Unique constraints (`slug`, `unique_together`). Basic field validation. Custom field validation against schema (in Serializer/Form). Prevent creating circular dependencies (handled by `django-mptt`).
*   **Initial Data**: Might require initial setup of root categories for different `category_type`s via migration.

### 3.4 Relationship with Other Models
*   This `Category` model will be linked *to* by other models that need classification.
*   Examples:
    *   `Product` might have `category = ForeignKey(Category, on_delete=models.PROTECT, limit_choices_to={'category_type': 'PRODUCT'}, related_name='products')` or `categories = ManyToManyField(Category, limit_choices_to={'category_type': 'PRODUCT'}, related_name='products')`.
    *   `Document` might have `document_type = ForeignKey(Category, on_delete=models.PROTECT, limit_choices_to={'category_type': 'DOCUMENT_TYPE'})`.
*   Use `limit_choices_to` on the ForeignKey/ManyToManyField in the referencing model to ensure only categories of the correct `category_type` can be assigned.

### 3.5 Custom Field Validation
*   **Requirement**: Data saved to `Category.custom_fields` must be validated against the corresponding schema.
*   **Implementation**: Logic in API Serializers or Forms.

### 3.6 Out of Scope for this Model/PRD
*   Complex cross-category relationships or categorization rules beyond simple assignment.
*   Detailed history of category usage by entities (tracked via Audit Log of entity changes).

## 4. Technical Requirements

### 4.1 Data Management
*   **Storage**: Standard fields + JSONField. MPTT fields (`lft`, `rght`, `tree_id`, `level`) managed automatically.
*   **Indexing**: Indexes on `slug`, `category_type`, `is_active`. MPTT fields are indexed by the library. **Requires DB support (e.g., GIN index) for efficient querying on `custom_fields`** if needed.
*   **Search**: API filtering/search on `name`, `category_type`, potentially parent/ancestors, and `custom_fields`.

### 4.2 Security
*   **Access Control**: Define permissions (`add_category`, `change_category`, `delete_category`, `view_category`). Access might be further restricted based on `category_type` or organizational scope if categories themselves become scoped (though often they are global reference data). Custom field access control.
*   **Audit Logging**: Log CRUD operations, hierarchy changes (parent change), and changes to `custom_fields` via Audit System.

### 4.3 Performance
*   Efficient hierarchy queries using `django-mptt` methods (`get_descendants`, `get_ancestors`).
*   Efficient filtering by `category_type`.
*   Efficient `custom_fields` querying (needs indexing).
*   Caching for category trees or frequently accessed categories.

### 4.4 Integration
*   **Primary Integration**: Serves as target for FK/M2M from classifiable models (`Product`, `Document`, etc.).
*   **API Endpoint**: Provide RESTful API (`/api/v1/categories/`) for managing categories, potentially including hierarchy-specific actions (get tree, descendants).
*   **Custom Field Schema Integration**: Integrates with `CustomFieldDefinition` mechanism.
*   **Library Dependency**: Requires installation and configuration of `django-mptt`. Requires `django-taggit` if `tags` field is added.

## 5. Non-Functional Requirements

*   **Scalability**: Support deep hierarchies and a large number of categories.
*   **Availability**: Category data is important reference data.
*   **Data Consistency**: Maintain hierarchy integrity (via MPTT). Enforce `unique_together`.
*   **Backup and Recovery**: Standard procedures.

## 6. Success Metrics

*   Successful classification of diverse entities using the category system.
*   Accurate representation of hierarchies.
*   Ease of managing categories and hierarchies.
*   Performant querying based on categories.
*   Successful use of custom fields where needed.

## 7. API Documentation Requirements

*   Document `Category` model fields (incl. `custom_fields`, `category_type`).
*   Document API endpoints for CRUD and hierarchy operations. Document filtering options (by type, name, parent, custom fields).
*   Document how `custom_fields` are handled.
*   Auth/Permission requirements.
*   Document how to discover custom field schemas (if applicable).

## 8. Testing Requirements

*   **Unit Tests**: Test `Category` model, MPTT setup, `unique_together` constraints, `custom_fields` logic if any.
*   **Integration Tests**:
    *   Test API CRUD operations.
    *   Test hierarchy operations (creating children, moving nodes) via API/Admin.
    *   Test filtering by `category_type`, name, parent, etc.
    *   Test assigning categories to other models (e.g., a Product) and respecting `limit_choices_to`.
    *   Test permissions.
    *   Test **saving/validating `custom_fields`**.
*   **Performance Tests**: Test performance of deep hierarchy traversals or filtering on large category sets.

## 9. Deployment Requirements

*   **Migrations**: Standard migrations for `Category` table, MPTT fields, custom fields, indexes. Requires `django-mptt` to be installed before migration.
*   **Initial Data**: Potentially populate root categories or core structures via data migration.
*   **Custom Field Schema Deployment**: Deploy `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements

*   Standard backups. Potential need for `manage.py rebuild_category_tree` (MPTT command) if tree becomes corrupted (rare).
*   Admin management of categories and custom field schemas.

---
### Tax

# Tax Definition Models - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To define standardized models for storing core tax information, including jurisdictions, categories, and rates, providing foundational data for tax calculations within the ERP system.
*   **Scope**: Definition of `TaxJurisdiction`, `TaxCategory`, and `TaxRate` data models, their attributes, relationships, basic management, and custom field capability. **Excludes the tax calculation engine/logic itself**.
*   **Implementation**: Defined as concrete Django Models, inheriting `Timestamped`, `Auditable`. May use `django-mptt` for `TaxJurisdiction`. Use `JSONField` for custom fields.
*   **Target Users**: Finance Teams, Accounting Teams, System Administrators (managing tax definitions), Developers (referencing tax data).

## 2. Business Requirements

*   **Represent Tax Structures**: Define geographic tax jurisdictions (countries, states, etc.) and product/service tax categories.
*   **Manage Tax Rates**: Store applicable tax rates, their types (VAT, GST, Sales Tax), and validity periods, linked to jurisdictions and potentially categories.
*   **Foundation for Calculation**: Provide the necessary, accurate reference data required by an internal or external tax calculation engine/service.
*   **Historical Rate Tracking**: Maintain a history of tax rates and their effective dates.
*   **Extensibility**: Allow adding specific dynamic attributes via custom fields.

## 3. Functional Requirements

### 3.1 `TaxJurisdiction` Model Definition
*   **Purpose**: Represents a geographic area where specific tax rules apply.
*   **Inheritance**: Inherit `Timestamped`, `Auditable`. Could optionally inherit `MPTTModel` for hierarchy (Country -> State -> County/City).
*   **Fields**:
    *   `code`: (CharField/SlugField, unique=True, db_index=True) Unique code for the jurisdiction (e.g., 'US', 'US-CA', 'GB', 'DE').
    *   `name`: (CharField, max_length=255) Name of the jurisdiction (e.g., "United States", "California", "United Kingdom").
    *   `jurisdiction_type`: (CharField with choices, e.g., 'Country', 'State', 'Province', 'County', 'City', 'Other', db_index=True).
    *   `parent`: (TreeForeignKey to `self`, null=True, blank=True) If using MPTT for hierarchy.
    *   `is_active`: (BooleanField, default=True, db_index=True).
    *   **`custom_fields`**: (JSONField, default=dict, blank=True).
*   **Meta**: `verbose_name`, `plural`, `ordering`. MPTT Meta if used.
*   **String Representation**: Return `name`.

### 3.2 `TaxCategory` Model Definition
*   **Purpose**: Classifies items (products, services) for differential tax treatment.
*   **Inheritance**: Inherit `Timestamped`, `Auditable`.
*   **Fields**:
    *   `code`: (CharField/SlugField, unique=True, db_index=True) Unique code (e.g., 'STANDARD', 'REDUCED', 'ZERO', 'EXEMPT', 'SERVICE').
    *   `name`: (CharField, max_length=100) Human-readable name (e.g., "Standard Rate Goods", "Reduced Rate Food", "Zero-Rated Books", "Exempt Services").
    *   `description`: (TextField, blank=True).
    *   `is_active`: (BooleanField, default=True, db_index=True).
    *   **`custom_fields`**: (JSONField, default=dict, blank=True).
*   **Meta**: `verbose_name`, `plural`, `ordering`.
*   **String Representation**: Return `name`.

### 3.3 `TaxRate` Model Definition
*   **Purpose**: Defines a specific tax rate applicable under certain conditions.
*   **Inheritance**: Inherit `Timestamped`, `Auditable`.
*   **Fields**:
    *   `jurisdiction`: (ForeignKey to `TaxJurisdiction`, on_delete=models.CASCADE) **Required**. The jurisdiction where this rate applies.
    *   `tax_category`: (ForeignKey to `TaxCategory`, on_delete=models.CASCADE, null=True, blank=True) Optional link if the rate applies only to specific item categories. Null means it applies generally within the jurisdiction (subject to other rules).
    *   `name`: (CharField, max_length=100) Descriptive name (e.g., "CA State Sales Tax", "UK Standard VAT", "Reduced VAT Food DE").
    *   `rate`: (DecimalField, max_digits=10, decimal_places=5) The tax rate percentage (e.g., 0.0825 for 8.25%).
    *   `tax_type`: (CharField with choices, e.g., 'VAT', 'GST', 'SALES', 'OTHER', db_index=True) The type of tax.
    *   `is_compound`: (BooleanField, default=False) Is this tax calculated on top of other taxes? (Requires careful handling in calculation logic).
    *   `priority`: (IntegerField, default=0) Order in which compound taxes are applied (lower first).
    *   `valid_from`: (DateField, null=True, blank=True, db_index=True) Date the rate becomes effective.
    *   `valid_to`: (DateField, null=True, blank=True, db_index=True) Date the rate expires. Null means currently active indefinitely.
    *   `is_active`: (BooleanField, default=True, db_index=True).
    *   **`custom_fields`**: (JSONField, default=dict, blank=True).
*   **Meta**: `verbose_name`, `plural`, `ordering` (e.g., by jurisdiction, priority). `index_together` on `jurisdiction`, `tax_category`, `valid_from`, `valid_to`.
*   **String Representation**: Return `name` or combination of jurisdiction/rate.

### 3.4 Custom Field Schema Definition (External Mechanism)
*   Requirement for separate `CustomFieldDefinition` model/mechanism if custom fields are used on Tax models.

### 3.5 Data Management & Operations
*   **CRUD**: Admin/API for managing `TaxJurisdiction`, `TaxCategory`, `TaxRate`. Includes managing `custom_fields`.
*   **Rate Validity**: System logic (or tax calculation engine) must use `valid_from`/`valid_to` dates when determining the applicable rate for a transaction date.
*   **Validation**: Unique constraints. Rate should be sensible (e.g., >= 0). Custom field validation.

### 3.6 Relationships & Usage
*   `Product` model likely has a ForeignKey to `TaxCategory`.
*   `Customer`/`Organization`/`Address` models provide jurisdictional information (e.g., shipping address -> `TaxJurisdiction`).
*   The Tax Calculation Engine (separate) uses Jurisdiction, Category (from Product), transaction date, etc., to query the `TaxRate` model and find the applicable rate(s).

### 3.7 Out of Scope for this PRD
*   **Tax Calculation Engine**: The logic to determine applicable taxes and calculate amounts.
*   **Complex Tax Rules/Exceptions**: Handled by the Calculation Engine.
*   **Integration with External Tax Services**: Defined in a separate PRD/specification.
*   **Tax Reporting/Filing**: Separate reporting features.
*   **History of Tax Calculations**: Belongs with transactions or Audit Log.

## 4. Technical Requirements

### 4.1 Data Management
*   Storage: Standard fields + JSONField. DecimalField for `rate`.
*   Indexing: On FKs, date ranges, codes, names, types. **GIN index for `custom_fields`** if querying needed.
*   Initial Population: May need to load common jurisdictions/categories/rates.

### 4.2 Security
*   Access Control: Restrict management of tax definitions to Admin/Finance roles.
*   Audit Logging: Log CRUD and custom field changes via Audit System.

### 4.3 Performance
*   Efficient querying of `TaxRate` based on jurisdiction, category, and date is **critical** for calculation performance. Requires good indexing.
*   Caching of tax rates can significantly improve performance.

### 4.4 Integration
*   Provide reference data for Tax Calculation Engine/Service.
*   API Endpoint (Optional): Read-only API (`/api/v1/tax-rates/` etc.) for listing definitions. Management API restricted.
*   Integrates with `CustomFieldDefinition` mechanism.

## 5. Non-Functional Requirements

*   Availability, Consistency (rates, validity dates), Accuracy, Backup/Recovery, Scalability (handle many jurisdictions/rates).

## 6. Success Metrics

*   Accurate storage of required tax definitions.
*   Successful use of definitions by the tax calculation mechanism.
*   Ease of administration for tax rates/jurisdictions/categories.

## 7. API Documentation Requirements (If API Endpoint is implemented)

*   Document Tax models/fields (incl. `custom_fields`).
*   Document read-only list API endpoints.
*   Document how `custom_fields` are represented.

## 8. Testing Requirements

*   Unit Tests (Models, unique constraints, custom fields).
*   Integration Tests (Admin/API CRUD, relationship constraints, **saving/validating `custom_fields`**).
*   Tests ensuring correct rates are retrieved based on jurisdiction/category/date (may overlap with calculation engine tests).

## 9. Deployment Requirements

*   Migrations for Tax models, indexes (incl. JSONField).
*   Initial data population for common taxes/jurisdictions.
*   Deployment of `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements

*   **Critical**: Process for updating tax rates based on regulatory changes. Accuracy is paramount.
*   Admin management of definitions and custom field schemas. Backups.

---
### Currency

# Currency Model - Product Requirements Document (PRD) - Simplified (with Custom Fields)

## 1. Overview

*   **Purpose**: To define the standard representation of world currencies, potentially extended with **dynamic custom fields**, within the ERP system, based on ISO 4217 standards.
*   **Scope**: Definition of the `Currency` data model, its core attributes, basic management, and custom field capability. Excludes exchange rates, conversion logic, and formatting rules.
*   **Implementation**: Defined as a concrete Django Model. Inherits `Timestamped`, `Auditable`. Uses a `JSONField` for custom fields.
*   **Target Users**: Admins, Finance Teams, Developers.

## 2. Business Requirements

*   Standardized currency representation (ISO 4217).
*   Support multiple required global currencies.
*   Allow adding specific, dynamic attributes to currencies (via Custom Fields), if needed by specific integrations or reporting.
*   Foundation for financial operations (referencing).
*   Data accuracy for core currency info.

## 3. Functional Requirements

### 3.1 `Currency` Model Definition
*   **Inheritance**: Inherit `Timestamped`, `Auditable`.
*   **Fields**:
    *   `code`: (CharField, max_length=3, primary_key=True) ISO 4217 alphabetic code.
    *   `name`: (CharField, max_length=100, unique=True, indexed) Official name.
    *   `symbol`: (CharField, max_length=5) Common symbol.
    *   `numeric_code`: (CharField, max_length=3, unique=True, null=True, blank=True, indexed) ISO 4217 numeric code.
    *   `decimal_places`: (PositiveSmallIntegerField, default=2).
    *   `is_active`: (BooleanField, default=True, db_index=True).
    *   **`custom_fields`**: (JSONField, default=dict, blank=True) Stores values for dynamically defined custom fields relevant to currencies.
*   **Meta**: `verbose_name`, `plural`, `ordering`.
*   **String Representation**: Returns `code`.

### 3.2 Custom Field Schema Definition (External Mechanism)
*   **Requirement**: If custom fields are used, a separate mechanism (e.g., `CustomFieldDefinition` model) is needed to define their schema.
*   **Schema Attributes**: Defines key, label, type, validation, choices, etc.

### 3.3 Data Management & Operations
*   **CRUD**: Primarily via Admin/initial load. Updating name/symbol/decimals/status. Deactivation (`is_active=False`). Deletion protected by FKs in other models.
*   **Custom Field Value Management**: API/Admin to view/update `custom_fields` JSON object.
*   **Initial Data**: Load comprehensive ISO 4217 list via migration/command.
*   **Validation**: Unique constraints (`code`, `name`, `numeric_code`). Custom field validation against schema (in Serializer/Form).

### 3.4 Relationship with Other Models
*   Target for `ForeignKey` from financial/setting models (Organization, ProductPrice, Invoice, etc.), using `on_delete=PROTECT`.

### 3.5 Custom Field Validation
*   **Requirement**: Data saved to `Currency.custom_fields` must be validated against the corresponding schema.
*   **Implementation**: Logic in API Serializers or Forms.

### 3.6 Out of Scope for this Model
*   Exchange Rates, Conversion Logic, Formatting Rules, Rate/Conversion History.

## 4. Technical Requirements

### 4.1 Data Management
*   Storage: Standard fields + JSONField.
*   Indexing: PK (`code`), `name`, `numeric_code`, `is_active`. **Requires DB support (e.g., GIN index) for efficient querying on `custom_fields`** if needed.
*   Initial Population: Data migration/command required.

### 4.2 Security
*   Access Control: Restrict management to Admin/Finance roles (`add_currency`, etc.). Custom field access control.
*   Audit Logging: Log changes (esp. `is_active`, `custom_fields`) via Audit System.

### 4.3 Performance
*   High performance for lookups by `code`. Efficient listing. Efficient `custom_fields` querying (needs indexing). Small/static table generally.

### 4.4 Integration
*   Target for ForeignKeys.
*   Optional read-only API for listing active currencies. Management API restricted.
*   Integrates with `CustomFieldDefinition` mechanism.
*   Potential use of `django-money` or `pycountry`.

## 5. Non-Functional Requirements

*   Availability, Consistency, Accuracy (ISO 4217), Backup/Recovery.

## 6. Success Metrics

*   Accurate currency representation. Successful referencing by other modules. Data integrity. Ease of admin. Successful use of custom fields if implemented.

## 7. API Documentation Requirements (If API Endpoint is implemented)

*   Document Currency model fields (incl. `custom_fields`).
*   Document API endpoints, `custom_fields` handling.
*   Auth/Permission requirements.
*   Document how to discover custom field schemas (if applicable).

## 8. Testing Requirements

*   Unit Tests (Model, defaults, `custom_fields` logic if any).
*   Data Tests (Initial population script).
*   Integration Tests (CRUD via Admin/API, activation/deactivation, FK protection, permissions, **saving/validating `custom_fields`**).

## 9. Deployment Requirements

*   Migrations (Currency table, indexes incl. JSONField if needed).
*   Initial data population script execution.
*   Deployment of `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements

*   Occasional updates to ISO data. Backups.
*   Management of custom field schemas.
### Unit of Measure

# Unit of Measure (UoM) Model - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To define a standardized model for representing distinct Units of Measure (UoM) used within the ERP system for products, inventory, transactions, etc.
*   **Scope**: Definition of the `UnitOfMeasure` data model, its core attributes (code, name, type/category), status, and custom field capability. Acknowledges the need for, but separates the detailed implementation of, unit conversion factors and logic.
*   **Implementation**: Defined as a concrete Django Model. It should inherit standard base models like `Timestamped`, `Auditable`. Uses a `JSONField` for custom fields.
*   **Target Users**: Inventory Managers, Product Managers, Purchasing/Sales Staff, Developers (referencing UoMs), System Administrators.

## 2. Business Requirements

*   **Standardized Units**: Provide a consistent and predefined list of units for measuring quantities (length, mass, volume, count, etc.).
*   **Consistency**: Ensure uniform use of UoMs in product specifications, inventory tracking, pricing, ordering, and manufacturing.
*   **Foundation for Conversion**: Provide the necessary unit definitions to support subsequent unit conversion calculations (handled by separate logic/library).
*   **Extensibility**: Allow administrators to define custom or industry-specific units and add dynamic attributes via custom fields.

## 3. Functional Requirements

### 3.1 `UnitOfMeasure` Model Definition
*   **Inheritance**: Should inherit `Timestamped`, `Auditable`.
*   **Fields**:
    *   `code`: (CharField, max_length=20, primary_key=True) A unique, often abbreviated, code for the unit (e.g., 'M', 'KG', 'L', 'EA', 'BOX', 'FT', 'LB'). **Primary Key**.
    *   `name`: (CharField, max_length=100, unique=True) The full, human-readable name of the unit (e.g., "Meter", "Kilogram", "Liter", "Each", "Box", "Foot", "Pound").
    *   `uom_type`: (CharField, max_length=50, db_index=True) The type or category of measurement this unit belongs to (e.g., 'Length', 'Mass', 'Volume', 'Count', 'Time', 'Area'). This is critical for determining valid conversions. *(Consider using choices or a ForeignKey to a `UomType` model if types need more attributes)*.
    *   `symbol`: (CharField, max_length=10, blank=True) Common symbol if applicable (e.g., 'm', 'kg', 'L', 'ft', 'lb').
    *   `is_active`: (BooleanField, default=True, db_index=True) Flag to enable/disable the UoM within the system.
    *   **`custom_fields`**: (JSONField, default=dict, blank=True) Stores values for dynamically defined custom fields relevant to the UoM definition itself.
*   **Meta**:
    *   `verbose_name = "Unit of Measure"`
    *   `verbose_name_plural = "Units of Measure"`
    *   `ordering = ['uom_type', 'name']`
*   **String Representation**: `__str__` method should return the `name` or `code`.

### 3.2 Custom Field Schema Definition (External Mechanism)
*   **Requirement**: If custom fields are used, a separate mechanism (e.g., `CustomFieldDefinition` model, potentially filtered by a 'UoM' context) is needed to define their schema (key, label, type, validation, etc.).

### 3.3 Data Management & Operations
*   **CRUD Operations**: Ability to Create, Read, Update, Deactivate (`is_active=False`) UoM records (primarily via Admin UI or initial data load). Includes managing `custom_fields` data.
*   **Deletion Constraint**: Deletion should be strictly prohibited if the UoM `code` is referenced by any other model (Products, Inventory Records, Order Lines, etc.). Use `on_delete=PROTECT` in referencing ForeignKeys. Deactivation (`is_active=False`) is the preferred method for retiring units.
*   **Validation**: Unique constraints (`code`, `name`). Custom field validation against schema.
*   **Initial Data**: A predefined set of common standard units (SI, Imperial where needed, 'Each') should be created via data migration.

### 3.4 Relationship with Other Models
*   Models requiring a unit of measure (e.g., `Product`, `InventoryItem`, `PurchaseOrderLine`, `SalesOrderLine`) will use a `ForeignKey` to this `UnitOfMeasure` model, referencing the `code` field, with `on_delete=models.PROTECT`.

### 3.5 Unit Conversion (Separate Concern)
*   **Requirement**: The system needs the ability to convert quantities between different UoMs *of the same `uom_type`* (e.g., KG to LB, M to FT).
*   **Implementation Approach**:
    *   **Option A (Recommended - Library):** Integrate a dedicated library like `pint`. This library handles definitions, dimensionality (`uom_type`), base units, conversion factors, and calculations robustly. The `UnitOfMeasure` model might store the `pint`-compatible string representation.
    *   **Option B (Manual Conversion Factors):** Create a separate `UomConversion` model storing `from_uom` (FK), `to_uom` (FK), `factor` (DecimalField), potentially relative to a base unit per `uom_type`. Requires building the conversion logic.
*   **This PRD**: Focuses only on defining the `UnitOfMeasure` records themselves. The conversion mechanism choice and implementation details belong in a separate PRD or technical design document.

### 3.6 Out of Scope for this Model/PRD
*   Detailed implementation of the unit conversion engine/factors.
*   Complex multi-step conversion logic.
*   Historical tracking of *instances* of conversions (belongs in Audit/Transaction logs).

## 4. Technical Requirements

### 4.1 Data Management
*   **Storage**: Standard storage for the `UnitOfMeasure` model + JSONField.
*   **Indexing**: PK (`code`), `name`, `uom_type`, `is_active`. **Requires DB support (e.g., GIN index) for efficient querying on `custom_fields`** if needed.
*   **Initial Population**: Data migration required for standard units.

### 4.2 Security
*   **Access Control**: Restrict management of `UnitOfMeasure` records (including `custom_fields`) to Admin roles.
*   **Audit Logging**: Log CRUD operations and changes to `custom_fields` via Audit System.

### 4.3 Performance
*   High performance for lookups by `code` (PK). Efficient listing. Small/medium table size expected.

### 4.4 Integration
*   **Primary Integration**: Serves as the target for ForeignKeys from Product, Inventory, Order models etc.
*   **Conversion Integration**: Provides definitions needed by the separate Unit Conversion logic/library.
*   **API Endpoint (Optional)**: Read-only API (`/api/v1/uoms/`) to list active UoMs might be useful. Management API restricted.
*   **Custom Field Schema Integration**: Integrates with `CustomFieldDefinition` mechanism.

## 5. Non-Functional Requirements

*   **Availability**: UoM definitions need to be reliably available reference data.
*   **Data Consistency**: `code`/`name` uniqueness. Referential integrity (`PROTECT` deletes). Correct `uom_type` classification.
*   **Accuracy**: Unit definitions should be accurate.

## 6. Success Metrics

*   Accurate representation and classification of required UoMs.
*   Successful referencing of `UnitOfMeasure` data by dependent modules.
*   No data integrity issues related to UoM references.
*   Successful use of UoM definitions by the unit conversion mechanism.

## 7. API Documentation Requirements (If API Endpoint is implemented)

*   Document `UnitOfMeasure` model fields (incl. `custom_fields`).
*   Document API endpoints (likely read-only list).
*   Auth/Permission requirements.
*   Document how to discover custom field schemas (if applicable).

## 8. Testing Requirements

*   **Unit Tests**: Test `UnitOfMeasure` model, unique constraints, `custom_fields` logic if any.
*   **Data Tests**: Verify initial population script loads expected standard units with correct types.
*   **Integration Tests**: Test CRUD via Admin/API. Test `PROTECT` deletion constraint by attempting to delete a UoM used by a Product (should fail). Test permissions. Test **saving/validating `custom_fields`**.

## 9. Deployment Requirements

*   **Migrations**: Standard migration for `UnitOfMeasure` table, indexes (incl. JSONField if needed).
*   **Initial Data Population**: Execute data migration for standard UoMs.
*   **Custom Field Schema Deployment**: Deploy `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements

*   Administrators may need to add/deactivate UoMs or manage custom field schemas. Backups.

---
### Warehouse

# Warehouse Model - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To define the core model representing physical or logical warehouses where inventory is stored or managed within the ERP system.
*   **Scope**: Definition of the `Warehouse` data model, its essential attributes (identification, type, location/address), status, and custom field capability. Excludes internal location structure (bins, racks) and warehouse operations (receiving, picking, etc.).
*   **Implementation**: Defined as a concrete Django Model. It **must** inherit `Timestamped`, `Auditable`, and `OrganizationScoped`. Uses a `JSONField` for custom fields.
*   **Target Users**: Inventory Managers, Warehouse Managers, Logistics Planners, System Administrators.

## 2. Business Requirements

*   **Identify Storage Locations**: Define distinct warehouse facilities or logical storage areas (e.g., distribution centers, retail backrooms, consignment locations, trucks).
*   **Support Different Types**: Differentiate warehouses based on their function or type (e.g., physical DC, virtual drop-ship, 3PL).
*   **Link to Physical Address**: Associate warehouses with their physical location.
*   **Foundation for Inventory/Logistics**: Provide the primary location reference needed by Inventory Management, Order Fulfillment, and Logistics modules.
*   **Extensibility**: Allow storing warehouse-specific attributes via custom fields.
*   **Multi-Tenancy**: Warehouse definitions must be scoped by Organization.

## 3. Functional Requirements

### 3.1 `Warehouse` Model Definition
*   **Inheritance**: Must inherit `Timestamped`, `Auditable`, `OrganizationScoped`.
*   **Fields**:
    *   `name`: (CharField, max_length=255, db_index=True) Human-readable name of the warehouse.
    *   `code`: (CharField, max_length=50, db_index=True) A unique identifier code for the warehouse within the organization.
    *   `warehouse_type`: (CharField with choices, db_index=True) Categorization (e.g., 'DISTRIBUTION_CENTER', 'RETAIL_STORE', 'MANUFACTURING', 'VIRTUAL_DROPSHIP', 'THIRD_PARTY_LOGISTICS', 'TRANSIT').
    *   `address`: (ForeignKey to `Address`, on_delete=models.PROTECT, null=True, blank=True) The primary physical address of the warehouse. Nullable for purely logical/virtual warehouses.
    *   `is_active`: (BooleanField, default=True, db_index=True) Flag to enable/disable the warehouse for use in transactions.
    *   `tags`: (ManyToManyField via `django-taggit` or similar, blank=True) For flexible classification.
    *   **`custom_fields`**: (JSONField, default=dict, blank=True) Stores values for dynamically defined custom fields specific to warehouses (e.g., capacity, manager_contact_id, temperature_controlled).
*   **Meta**:
    *   `verbose_name = "Warehouse"`
    *   `verbose_name_plural = "Warehouses"`
    *   `unique_together = (('organization', 'code'),)`
    *   `ordering = ['name']`
*   **String Representation**: Return `name` or `code`.

### 3.2 Custom Field Schema Definition (External Mechanism)
*   Requirement for separate `CustomFieldDefinition` model/mechanism (possibly filtered by a 'Warehouse' context or `warehouse_type`) to define schema for warehouse custom fields.

### 3.3 Data Management & Operations
*   **CRUD**: Standard operations via Admin/API, respecting Organization scope. Includes managing `custom_fields`.
*   **Validation**: Unique code within Org. FK constraints. Custom field validation against schema.
*   **Deactivation**: Use `is_active` flag. Deletion restricted if inventory or locations exist (handled by related models' `PROTECT` constraints).

### 3.4 Relationships
*   Links *to* `Organization` (via `OrganizationScoped`), `Address`.
*   Is linked *from* `StockLocation` (internal structure model - separate PRD), `InventoryItem`/`StockLevel` (inventory tracking model - separate PRD), potentially `PurchaseOrder`/`SalesOrder` (for fulfillment location).

### 3.5 Out of Scope for this Model/PRD
*   **Internal Location Structure (Bins, Racks, Aisles)**: Defined in a separate `StockLocation` model/PRD, linking to `Warehouse`.
*   **Inventory Tracking (Quantity on Hand)**: Handled by separate Inventory models linking Product and Warehouse/StockLocation.
*   **Warehouse Operations (Receiving, Put-away, Picking, Packing, Shipping)**: Handled by Inventory/WMS modules.
*   **Capacity Management/Validation**: Complex logic, likely part of WMS features.
*   **Detailed History**: Handled by Audit Log (for definition changes) and Inventory Ledger (for stock movements).

## 4. Technical Requirements

### 4.1 Data Management
*   Storage: Standard fields + JSONField.
*   Indexing: `code`, `name`, `warehouse_type`, `is_active`, `organization`. **GIN index on `custom_fields`** if querying needed.
*   Search: API filtering/search on key fields, type, status, tags, potentially custom fields.

### 4.2 Security
*   **Access Control**: Permissions (`add_warehouse`, `change_warehouse`, `delete_warehouse`, `view_warehouse`). Enforced within Organization scope. Field-level permissions may apply to custom fields.
*   **Audit Logging**: Log CRUD operations and changes to `custom_fields` via Audit System.

### 4.3 Performance
*   Efficient querying/filtering of warehouses.
*   Efficient retrieval when linked from Inventory/Order records.

### 4.4 Integration
*   **Core Integration**: Foundational model referenced by Inventory, Logistics, Order Management modules. Links to `Address`. Is referenced by `StockLocation`.
*   **API Endpoint**: Provide RESTful API (`/api/v1/warehouses/`) for CRUD, respecting Org Scoping and permissions. Include filtering/search. Define `custom_fields` handling.
*   **Custom Field Schema Integration**: Integrates with `CustomFieldDefinition` mechanism.

## 5. Non-Functional Requirements

*   **Scalability**: Support potentially hundreds/thousands of warehouse locations.
*   **Availability**: Warehouse definitions need to be highly available.
*   **Data Consistency**: Maintain unique codes within Org, FK integrity.
*   **Backup/Recovery**: Standard procedures.

## 6. Success Metrics

*   Accurate representation of physical/logical warehouse locations.
*   Successful referencing by Inventory and Order Management modules.
*   Ease of administration for warehouse definitions.
*   Successful use of custom fields.

## 7. API Documentation Requirements

*   Document `Warehouse` model fields (incl. `custom_fields`).
*   Document API endpoints for CRUD, filtering, searching. Detail filterable fields.
*   Document handling of `custom_fields` in API requests/responses.
*   Auth/Permission requirements (mentioning Org Scoping).
*   Document how to discover custom field schemas (if applicable).

## 8. Testing Requirements

*   **Unit Tests**: Test `Warehouse` model, `unique_together` constraints, custom field logic if any.
*   **Integration Tests**:
    *   Test API CRUD operations, ensuring Org Scoping is enforced.
    *   Test filtering/searching via API.
    *   Test linking to `Address`.
    *   Test permissions.
    *   Test **saving/validating `custom_fields`**.
    *   Test deletion protection (if linked from `StockLocation` or `StockLevel`).

## 9. Deployment Requirements

*   Migrations for `Warehouse` table, indexes (incl. JSONField).
*   Dependencies on `Address`, `Organization` models/migrations.
*   Deployment of `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements

*   Ongoing warehouse data management via Admin/API.
*   Monitoring performance, adding indexes as needed. Backups.
*   Management of custom field schemas.

---
### Stock Location



# StockLocation Model - Product Requirements Document (PRD)

## 1. Overview

*   **Purpose**: To define a standardized model for representing specific, hierarchical storage locations (e.g., Zone, Aisle, Rack, Shelf, Bin) within a defined `Warehouse`.
*   **Scope**: Definition of the `StockLocation` data model, its hierarchical relationship (parent/child locations), link to a parent `Warehouse`, core attributes, status, and custom field capability. This model provides the granularity needed for precise inventory tracking within a warehouse.
*   **Implementation**: Defined as a concrete Django Model using `django-mptt` for hierarchy. It **must** inherit `Timestamped`, `Auditable`, and `OrganizationScoped`. Uses a `JSONField` for custom fields. It has a mandatory link to the `Warehouse` model.
*   **Target Users**: Warehouse Managers, Warehouse Staff (Put-away, Picking), Inventory Managers, System Administrators.

## 2. Business Requirements

*   **Represent Warehouse Layout**: Model the physical or logical structure of storage locations within a warehouse (e.g., Receiving Area -> Aisle A -> Rack 01 -> Shelf 03 -> Bin 05).
*   **Hierarchical Structure**: Support nested locations to represent zones, aisles, racks, shelves, bins, etc.
*   **Link to Warehouse**: Clearly associate each specific location with its parent `Warehouse`.
*   **Precise Inventory Tracking**: Provide the specific location reference needed by Inventory Management systems to track *where* stock resides within a warehouse.
*   **Put-away/Picking Guidance**: Serve as destinations for put-away operations and source locations for picking operations.
*   **Extensibility**: Allow storing location-specific attributes (e.g., dimensions, weight capacity, environment type) via custom fields.
*   **Multi-Tenancy**: Stock locations must be scoped by Organization (inherited via Warehouse or directly).

## 3. Functional Requirements

### 3.1 `StockLocation` Model Definition
*   **Inheritance**: Must inherit `Timestamped`, `Auditable`, `OrganizationScoped`, and `mptt.models.MPTTModel`.
*   **Fields**:
    *   `name`: (CharField, max_length=255) Human-readable name or identifier for the location (e.g., "Aisle A", "Rack 01-03", "Bin A-01-03-05", "Receiving Dock").
    *   `barcode`: (CharField, max_length=100, blank=True, db_index=True) Optional barcode identifier for scanning. Should be unique within the organization.
    *   `warehouse`: (ForeignKey to `Warehouse`, on_delete=models.CASCADE, related_name='stock_locations') **Required**. The parent warehouse this location belongs to. Cascade delete means if the warehouse is deleted, all its internal locations are also deleted.
    *   `parent`: (TreeForeignKey to `self`, on_delete=models.CASCADE, null=True, blank=True, related_name='children') Managed by `django-mptt`. Defines the parent location within the warehouse hierarchy (e.g., a Bin's parent is a Shelf). Root locations within a warehouse have `parent=None`.
    *   `location_type`: (CharField with choices, blank=True, db_index=True) Optional field to categorize the location type (e.g., 'ZONE', 'AISLE', 'RACK', 'SHELF', 'BIN', 'DOCK', 'STAGING_AREA').
    *   `is_active`: (BooleanField, default=True, db_index=True) Can this location currently be used for storing inventory?
    *   **`custom_fields`**: (JSONField, default=dict, blank=True) Stores values for dynamically defined custom fields (e.g., `{'max_weight_kg': 50, 'width_cm': 30, 'height_cm': 20, 'depth_cm': 40, 'environment': 'AMBIENT'}`).
*   **MPTT Meta**: `class MPTTMeta: order_insertion_by = ['name']`. Specify `parent_attr = 'parent'`.
*   **Model Meta**:
    *   `verbose_name = "Stock Location"`
    *   `verbose_name_plural = "Stock Locations"`
    *   `unique_together = (('warehouse', 'barcode'), ('warehouse', 'parent', 'name'))` (Ensure barcode is unique per warehouse, and name is unique under the same parent within the same warehouse). Adjust constraints as needed.
*   **String Representation**: Return `name`, potentially prefixed with warehouse code or parent names for clarity.

### 3.2 Custom Field Schema Definition (External Mechanism)
*   Requirement for separate `CustomFieldDefinition` model/mechanism (possibly filtered by a 'StockLocation' context or `location_type`) to define schema for location custom fields.

### 3.3 Data Management & Operations
*   **CRUD**: Standard operations via Admin/API, respecting Organization scope. Includes managing `custom_fields`. Requires specifying the parent `warehouse`.
*   **Hierarchy Management**: Ability to change the `parent` location via Admin (`MPTTModelAdmin`) or API actions.
*   **Validation**: Unique constraints. Parent must belong to the same `warehouse` as the child. Custom field validation. Prevent circular dependencies (handled by MPTT).

### 3.4 Relationship with Other Models
*   Links *to* `Warehouse` (required parent), `Organization` (via `OrganizationScoped`), potentially `self` (parent location).
*   Is linked *from* Inventory tracking models (e.g., `StockLevel`, `InventoryTransaction`, `StockMove`) which specify the precise location of inventory items.

### 3.5 Out of Scope for this Model/PRD
*   **Inventory Quantities**: Stock levels are stored in separate Inventory models, not directly on the location.
*   **Warehouse Operations Logic**: Put-away strategies, picking path optimization, etc., are part of WMS/Inventory modules.
*   **Capacity Calculation/Enforcement**: Complex logic based on dimensions/weight stored potentially in `custom_fields` or related models.

## 4. Technical Requirements

### 4.1 Data Management
*   Storage: Standard fields + JSONField. MPTT fields managed automatically.
*   Indexing: On `barcode`, `warehouse`, `parent`, `location_type`, `is_active`, `organization`. MPTT fields indexed by library. **GIN index on `custom_fields`** if querying needed.
*   Search: API filtering/search on name, barcode, type, warehouse, potentially parent/ancestors and custom fields.

### 4.2 Security
*   **Access Control**: Permissions (`add_stocklocation`, etc.). Enforced within Organization scope. Access often tied to permissions on the parent `Warehouse`. Custom field access control.
*   **Audit Logging**: Log CRUD, hierarchy changes (parent change), and `custom_fields` changes via Audit System.

### 4.3 Performance
*   Efficient hierarchy queries using `django-mptt`.
*   Efficient filtering by `warehouse`.
*   Efficient querying on `custom_fields` (needs indexing).

### 4.4 Integration
*   **Core Integration**: Provides granular locations for the Inventory Management system. Tightly coupled with `Warehouse`. Uses `django-mptt`.
*   **API Endpoint**: Provide RESTful API (`/api/v1/stock-locations/` or potentially nested under warehouses `/api/v1/warehouses/{wh_id}/stock-locations/`) for CRUD, respecting Org Scoping and permissions. Include filtering/search and potentially hierarchy actions. Define `custom_fields` handling.
*   **Custom Field Schema Integration**: Integrates with `CustomFieldDefinition` mechanism.

## 5. Non-Functional Requirements

*   **Scalability**: Support potentially large numbers of locations within warehouses and deep hierarchies.
*   **Availability**: Location data needed for inventory operations.
*   **Data Consistency**: Maintain hierarchy integrity (via MPTT). Enforce `unique_together` constraints. FK integrity with `Warehouse`.

## 6. Success Metrics

*   Accurate modeling of warehouse internal layouts.
*   Successful use of locations by the Inventory Management system for tracking stock.
*   Ease of managing location structures.
*   Performant querying of locations and hierarchies.

## 7. API Documentation Requirements

*   Document `StockLocation` model fields (incl. `custom_fields`).
*   Document API endpoints for CRUD and hierarchy operations (if applicable). Detail filtering options.
*   Document handling of `custom_fields`.
*   Auth/Permission requirements (mentioning Org Scoping).
*   Document how to discover custom field schemas (if applicable).

## 8. Testing Requirements

*   **Unit Tests**: Test `StockLocation` model, MPTT setup, `unique_together` constraints, custom field logic.
*   **Integration Tests**:
    *   Test API CRUD operations, ensuring link to `Warehouse` and Org Scoping.
    *   Test hierarchy operations (creating children under specific parents, moving locations) via API/Admin.
    *   Test filtering by `warehouse`, type, parent, etc.
    *   Test permissions.
    *   Test **saving/validating `custom_fields`**.
*   **Performance Tests**: Test performance of deep hierarchy traversals or filtering with many locations.

## 9. Deployment Requirements

*   **Migrations**: Standard migrations for `StockLocation` table, MPTT fields, custom fields, indexes. Requires `django-mptt` installed.
*   **Dependencies**: Depends on `Warehouse` model/migration.
*   **Custom Field Schema Deployment**: Deploy `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements

*   Standard backups. Potential need for `manage.py rebuild_stocklocation_tree` (MPTT command) if tree issues arise (rare).
*   Admin management of locations and custom field schemas.

--- END OF FILE stock_location_prd.md ---
## Communication & Collaboration


### Chat

# Real-Time Chat System - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To define the requirements for a real-time chat system integrated within the ERP, enabling direct messaging, group chats, basic file sharing, and persistent message history.
*   **Scope**: Definition of core chat models (`ChatRoom`, `ChatMessage`), integration with real-time communication infrastructure (WebSockets via Django Channels), basic message/file operations, user presence indication, search integration, and permission handling. Excludes advanced features like complex threading, reactions, video calls within chat, or sophisticated moderation tools initially.
*   **Implementation Strategy**: Involves concrete Django Models (`ChatRoom`, `ChatMessage`, potentially `ChatParticipant`) inheriting base models. Relies heavily on **Django Channels** for WebSocket communication. Integrates with `FileStorage`, `Search`, `Notification`, `User`, `Organization`, `RBAC`, and `Audit` systems. Asynchronous tasks (Celery) may be used for notifications or background processing.
*   **Target Users**: All internal ERP users.

## 2. Business Requirements

*   **Instant Communication**: Facilitate real-time conversations between individuals and groups within the organizational context.
*   **Persistent History**: Store chat messages reliably for later reference and searching.
*   **Basic Collaboration**: Allow sharing relevant files directly within conversations.
*   **Contextual Chat**: Potentially link chat rooms to specific business objects (e.g., a chat about a specific Order). *(Consider as v2 feature)*.
*   **Secure Communication**: Ensure chats are scoped by organization and access is controlled by permissions.

## 3. Functional Requirements

### 3.1 Core Models
*   **`ChatRoom` Model**:
    *   **Purpose**: Represents a conversation space (DM or Group).
    *   **Inheritance**: `Timestamped`, `Auditable`, `OrganizationScoped`.
    *   **Fields**:
        *   `name`: (CharField, max_length=255, blank=True) Name of the group chat/channel. Blank for DMs.
        *   `room_type`: (CharField with choices: 'DIRECT', 'GROUP', 'CHANNEL', default='GROUP', db_index=True).
        *   `participants`: (ManyToManyField to `User`, related_name='chat_rooms') Members of the room. *(Consider a `through` model `ChatParticipant` if per-user state like `last_read_timestamp` is needed)*.
        *   `is_active`: (BooleanField, default=True).
        *   **`custom_fields`**: (JSONField, default=dict, blank=True).
    *   **Meta**: `verbose_name`, `plural`, `ordering`.
*   **`ChatMessage` Model**:
    *   **Purpose**: Represents a single message within a room.
    *   **Inheritance**: `Timestamped`, `Auditable`, `OrganizationScoped`.
    *   **Fields**:
        *   `room`: (ForeignKey to `ChatRoom`, on_delete=models.CASCADE, related_name='messages') **Required**.
        *   `sender`: (ForeignKey to `User`, on_delete=models.SET_NULL, null=True, related_name='sent_chat_messages') **Required** (except for system messages).
        *   `content`: (TextField) The message text. *(Consider JSONField for rich content later)*.
        *   `parent`: (ForeignKey to `'self'`, on_delete=models.SET_NULL, null=True, blank=True, related_name='replies') For basic threading/replies.
        *   `attachments`: (ManyToManyField to `FileStorage`, blank=True).
        *   `is_edited`: (BooleanField, default=False).
        *   `is_deleted`: (BooleanField, default=False) For soft deletes.
        *   **`custom_fields`**: (JSONField, default=dict, blank=True).
    *   **Meta**: `verbose_name`, `plural`, `ordering = ['created_at']`, index on `room`.

### 3.2 Real-Time Communication (Django Channels)
*   **WebSockets**: Implement Django Channels consumers to handle WebSocket connections (`connect`, `disconnect`, `receive`).
*   **Authentication**: Authenticate WebSocket connections using user session/token.
*   **Room Joining**: When a user connects, subscribe them to Channels groups corresponding to their active `ChatRoom`s.
*   **Message Broadcasting**: When a `ChatMessage` is saved:
    1.  Trigger a signal or task.
    2.  The handler sends the message data (or a notification) to the relevant Channels group for the message's `room`.
    3.  Consumers relay the message to connected clients in that room.
*   **Presence**: Implement basic online status tracking (users connected to the Channels chat consumer). Broadcast presence updates.
*   **Typing Indicators**: Client sends "start typing" / "stop typing" events via WebSocket; consumer broadcasts these temporary indicators to other room participants.

### 3.3 Core Chat Operations (API + WebSockets)
*   **Fetch Rooms**: API endpoint (`GET /api/v1/chat/rooms/`) to list rooms the user is a participant in.
*   **Fetch Messages**: API endpoint (`GET /api/v1/chat/rooms/{room_id}/messages/`) to retrieve historical messages for a room (paginated).
*   **Send Message**: Client sends message content (and optional attachment IDs, parent ID) via **WebSocket** `receive` handler OR a dedicated **API endpoint** (`POST /api/v1/chat/rooms/{room_id}/messages/`).
    *   Backend logic: Check permissions, create `ChatMessage`, save attachments M2M, save message, trigger broadcast (see 3.2).
*   **Edit/Delete Message**: API endpoints (`PUT/DELETE /api/v1/chat/messages/{message_id}/`). Check permissions (author only, potentially time-limited). Update `is_edited`/`is_deleted`. Broadcast update/delete event via WebSockets.
*   **Create Room**: API endpoint (`POST /api/v1/chat/rooms/`) to create new GROUP rooms, specifying initial participants. Check permissions. DMs might be created implicitly when sending the first message.
*   **Manage Participants**: API endpoints to add/remove participants from GROUP rooms (`POST/DELETE /api/v1/chat/rooms/{room_id}/participants/`). Check permissions (room admin/creator?).
*   **File Upload**: Use the existing `FileStorage` upload API. Client uploads file, gets ID, includes ID when sending message.

### 3.4 User Experience Features
*   **Real-time Updates**: New messages, edits, deletes, typing indicators, presence updates delivered via WebSockets.
*   **Read Receipts**: *(Defer to v2 - requires tracking last read message per user per room, potentially in `ChatParticipant` model)*.

### 3.5 Integration Requirements
*   **Organization Scoping**: `ChatRoom` and `ChatMessage` inherit `OrganizationScoped`. Queries and broadcasts must respect this.
*   **User Management**: Links heavily to `User` model for participants, sender.
*   **File Storage**: Uses `FileStorage` for attachments.
*   **Notification System**: Trigger for offline users/mentions (requires parsing content for `@user` - potentially async task).
*   **Search Integration**: `ChatMessage.content` should be indexed by the Search Engine. API needs to pass search queries to the engine.
*   **Audit Logging**: Log room creation, participant changes, potentially message deletion (if required beyond `is_deleted` flag).

### 3.6 Custom Field Schema Definition (External Mechanism)
*   Requirement for separate `CustomFieldDefinition` model/mechanism if custom fields are used on `ChatRoom` or `ChatMessage`.

### 3.7 Out of Scope (Initial Implementation)
*   Advanced threading (beyond direct replies), message reactions, read receipts, rich text formatting/previews, video/audio calls, sophisticated moderation tools, bots, channel-specific features (topics, pins).

## 4. Technical Requirements

### 4.1 Infrastructure & Libraries
*   **ASGI Server**: Required for Django Channels (e.g., Daphne, Uvicorn).
*   **Channel Layers**: Backend for communication between consumers/workers (e.g., `channels_redis`).
*   **Django Channels**: Core library for WebSocket handling.
*   **(Optional) Celery**: For asynchronous notification sending or message processing.
*   **Database**: Standard Django ORM + JSONField support.

### 4.2 Data Management
*   Storage for `ChatRoom`, `ChatMessage`. Efficient querying for message history (pagination crucial). Indexing on FKs, timestamps, potentially content (if DB search needed alongside search engine). GIN index for `custom_fields`.

### 4.3 Performance
*   **Real-time Latency**: Minimize delay between message send and receipt by connected clients. Requires efficient broadcasting via Channel Layers.
*   **Database Load**: Optimize message fetching queries. Writing messages should be fast.
*   **WebSocket Connections**: Server must handle potentially large numbers of persistent connections.
*   **Async Tasks**: Ensure Celery workers (if used) can handle notification/processing load.

### 4.4 Security
*   **Authentication**: Securely authenticate WebSocket connections.
*   **Authorization**: Check permissions rigorously for joining rooms, sending messages, managing participants, editing/deleting. Ensure users can only access rooms/messages within their organization scope.
*   **Encryption**: Consider TLS/WSS for WebSocket traffic. Encryption at rest for messages/files if required by compliance.
*   **Input Sanitization**: Sanitize message content to prevent XSS attacks if displaying HTML.

### 4.5 Integration Points
*   API endpoints for history, management. WebSocket endpoint for real-time.
*   Signals/tasks for broadcasting, notifications, search indexing.
*   Integration with User/Org/File/Search/Notification systems.

## 5. Non-Functional Requirements

*   **Scalability**: Handle many concurrent users, connections, rooms, and messages. Requires scalable ASGI server, Channel Layer (Redis cluster?), and database.
*   **Availability**: Chat service (WebSocket server, API) needs high availability.
*   **Reliability**: Minimize message loss during broadcast or saving.
*   **Consistency**: Ensure messages are eventually consistent across participants' views.

## 6. Success Metrics

*   High message delivery success rate (saved and broadcast).
*   Low real-time latency.
*   High user adoption/engagement.
*   System reliability and availability meet targets.

## 7. API Documentation Requirements

*   Document `ChatRoom`, `ChatMessage` models/fields (incl. `custom_fields`).
*   Document REST API endpoints (fetching rooms/messages, creating rooms, managing participants, editing/deleting messages).
*   **Crucially**: Document the WebSocket protocol/events (connecting, authentication, expected message format for sending, message format received from server, presence/typing events).
*   Auth/Permission requirements for API and WebSocket actions.
*   Document custom field handling.

## 8. Testing Requirements

*   **Unit Tests**: Test model logic, message creation/validation. Test Channels consumer logic in isolation (mocking channel layer sends).
*   **Integration Tests**:
    *   Requires setting up Django Channels testing infrastructure (`channels.testing.WebsocketCommunicator`).
    *   Test WebSocket lifecycle: connect, auth success/fail, receive message, send message, disconnect.
    *   Test message broadcasting: Send message via API/WebSocket, verify other connected clients receive it.
    *   Test API endpoints for fetching history, managing rooms/participants.
    *   Test permissions and Org Scoping for API and WebSocket actions.
    *   Test file attachment handling.
    *   Test search integration.
    *   Test notification integration (triggering async task).
    *   Test **saving/validating `custom_fields`**.
*   **Load Tests**: Simulate many concurrent WebSocket connections and high message volume.

## 9. Deployment Requirements

*   Deployment of ASGI server (Daphne/Uvicorn).
*   Deployment of Channel Layer backend (Redis).
*   Deployment of Django application code (models, views, consumers).
*   Configuration of Channels routing.
*   Migrations for chat models, indexes (incl. JSONField).
*   Setup of Celery workers if used.
*   Deployment of `CustomFieldDefinition` mechanism if needed.

## 10. Maintenance Requirements

*   Monitor ASGI server, Channel Layer, WebSocket connections, Celery queues.
*   Standard database/model maintenance. Backups.
*   Keep Channels and related libraries updated.
*   Management of custom field schemas if applicable.

---
### Comment


# Comment Model - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To define a standardized model for users to add comments, replies, and potentially attach files to various business objects (e.g., Products, Orders, Tasks) within the ERP system.
*   **Scope**: Definition of the `Comment` data model, its core attributes, generic relationship to parent objects, basic threading (replies), attachment support, and custom field capability. Excludes real-time features, mentions, reactions, and advanced moderation workflows.
*   **Implementation**: Defined as a concrete Django Model using Generic Relations (`ContentType` framework). It **must** inherit `Timestamped`, `Auditable`, and potentially `OrganizationScoped`. Uses a `JSONField` for custom fields. Links to `FileStorage`.
*   **Target Users**: All users collaborating on business objects, System Administrators (potential moderation).

## 2. Business Requirements

*   **Contextual Discussion**: Allow users to discuss and provide feedback directly related to specific business objects (Orders, Products, etc.).
*   **Collaboration**: Facilitate communication and information sharing among users working on the same items.
*   **Record Keeping**: Maintain a record of discussions and decisions related to specific objects.
*   **Attachments**: Allow users to attach relevant files to their comments.
*   **Basic Threading**: Support direct replies to comments to structure conversations.
*   **Extensibility**: Allow storing comment-specific attributes via custom fields.

## 3. Functional Requirements

### 3.1 `Comment` Model Definition
*   **Inheritance**: Must inherit `Timestamped`, `Auditable`. **Must inherit `OrganizationScoped`** (comments exist within the context of an organization's data).
*   **Fields**:
    *   `user`: (ForeignKey to `User`, on_delete=models.SET_NULL, null=True, related_name='comments') The author of the comment. Uses `Auditable.created_by`, but explicit FK is standard.
    *   `content`: (TextField) The main text content of the comment. Support for basic markup (e.g., Markdown) might be considered later.
    *   **Generic Relation to Parent Object**:
        *   `content_type`: (ForeignKey to `ContentType`, on_delete=models.CASCADE) The model of the object being commented on.
        *   `object_id`: (CharField or PositiveIntegerField, db_index=True) The primary key of the object being commented on. *(Use CharField if targeting UUID PKs)*.
        *   `content_object`: (GenericForeignKey 'content_type', 'object_id') Provides direct access to the parent object.
    *   `parent`: (ForeignKey to `'self'`, on_delete=models.CASCADE, null=True, blank=True, related_name='replies') Links a reply to its parent comment. Null for top-level comments.
    *   `is_edited`: (BooleanField, default=False) Flag indicating if the comment was edited after creation.
    *   `status`: (CharField with choices, e.g., 'VISIBLE', 'HIDDEN', 'PENDING_MODERATION', default='VISIBLE', db_index=True) Basic visibility/moderation status.
    *   `attachments`: (ManyToManyField to `FileStorage`, blank=True) Links to uploaded files attached to the comment.
    *   **`custom_fields`**: (JSONField, default=dict, blank=True) Stores values for dynamically defined custom fields relevant to the comment (e.g., 'feedback_type', 'severity').
*   **Meta**:
    *   `verbose_name = "Comment"`
    *   `verbose_name_plural = "Comments"`
    *   `ordering = ['created_at']` (Order comments chronologically by default).
    *   `indexes`: Index `content_type` and `object_id` together for efficient lookup of comments for a specific object.
*   **String Representation**: Return truncated content and author.

### 3.2 Custom Field Schema Definition (External Mechanism)
*   Requirement for separate `CustomFieldDefinition` model/mechanism (possibly filtered by a 'Comment' context or comment type derived from custom fields) to define schema for comment custom fields.

### 3.3 Comment Operations
*   **CRUD**: API endpoints for:
    *   Creating comments/replies associated with a specific parent object (using Generic Relation fields). Requires upload handling for attachments.
    *   Reading/Listing comments for a specific parent object (filtered by `content_type` and `object_id`). API should handle returning comments in a threaded structure (e.g., top-level comments with their direct replies nested).
    *   Updating own comments (limited time window? Sets `is_edited` flag). Requires specific permissions.
    *   Deleting own comments (soft delete via `status='HIDDEN'` or hard delete). Requires specific permissions.
    *   *(Moderation)* Endpoints for users with moderation permissions to change comment `status`.
*   Includes managing `custom_fields` data during create/update.

### 3.4 Validation
*   `content` cannot be empty.
*   Generic Relation fields (`content_type`, `object_id`) must point to a valid object.
*   Parent comment (if provided) must belong to the same parent object thread.
*   Attachment validation (size, type) handled by `FileStorage` upload process.
*   Custom field validation against schema.

### 3.5 Out of Scope for this Model/PRD
*   **Real-time Updates**: Displaying new comments instantly (requires WebSockets).
*   **Mentions (`@user`)**: Parsing content and triggering notifications.
*   **Reactions (`like`, etc.)**: Requires separate `Reaction` model.
*   **Advanced Moderation Workflows**: Queues, reporting, moderator assignment.
*   **Full-text Search on Content**: Requires integration with a search engine (like Elasticsearch).

## 4. Technical Requirements

### 4.1 Data Management
*   Storage: Standard fields, Generic Relation fields, JSONField. Links to User, ContentType, FileStorage. Self-referential FK for parent.
*   Indexing: On GFK fields (`content_type`, `object_id`), `user`, `parent`, `status`, `organization`. **GIN index on `custom_fields`** if querying needed.
*   Querying: Efficient retrieval of comment threads for a specific object.

### 4.2 Security
*   **Access Control**:
    *   Permission to *create* comments usually depends on permissions on the *parent object*.
    *   Permission to *view* comments depends on view permissions for the *parent object*.
    *   Permission to *update/delete* comments usually restricted to the comment author (potentially time-limited) or moderators.
    *   Permissions required for moderation actions (changing `status`).
    *   Enforced within Organization scope.
*   **Attachment Security**: Accessing attachments must respect permissions on the comment AND potentially the parent object. Use `FileStorage` system's secure access mechanisms.
*   **Audit Logging**: Log create/update/delete/status changes via Audit System, including `custom_fields` changes.

### 4.3 Performance
*   Efficient retrieval of comment threads (potentially involves recursive queries or specific techniques if using MPTT for deeper nesting later). Use `select_related('user')` and `prefetch_related('replies', 'attachments')`.
*   Efficient filtering/counting of comments per object.

### 4.4 Integration
*   **Core Integration**: Uses `ContentType` framework, `User`, `FileStorage`, `Organization` (scoping).
*   **Notification System**: Trigger notifications on new comments/replies based on user subscriptions or context (separate logic).
*   **API Endpoint**: Provide RESTful API (e.g., `/api/v1/comments/`, potentially nested under parent objects like `/api/v1/invoices/{id}/comments/`). Needs to handle GFK linking and attachment uploads.
*   **Custom Field Schema Integration**: Integrates with `CustomFieldDefinition` mechanism.

## 5. Non-Functional Requirements

*   **Scalability**: Handle a large volume of comments across many objects.
*   **Availability**: Comment viewing/creation should be available.
*   **Data Consistency**: Maintain integrity of GFK links and parent reply links.
*   **Backup/Recovery**: Standard procedures (DB + File Storage for attachments).

## 6. Success Metrics

*   User engagement with comment feature.
*   Successful association of comments with business objects.
*   Performant retrieval of comment threads.
*   Ease of use for adding/viewing comments and replies.

## 7. API Documentation Requirements

*   Document `Comment` model fields (incl. `custom_fields`, GFK fields).
*   Document API endpoints for CRUD operations, including how to target a parent object and handle replies/attachments.
*   Document response structure for threaded comments.
*   Document handling of `custom_fields`.
*   Auth/Permission requirements.
*   Document how to discover custom field schemas (if applicable).

## 8. Testing Requirements

*   **Unit Tests**: Test `Comment` model, self-referential parent link, GFK usage.
*   **Integration Tests**:
    *   Test API CRUD operations for comments and replies on different parent object types.
    *   Test attachment upload/association/retrieval via API.
    *   Test retrieval of threaded comments.
    *   Test permission checks (creating, editing own, deleting own, moderation).
    *   Test Org Scoping enforcement.
    *   Test **saving/validating `custom_fields`**.
*   **Security Tests**: Test access control scenarios (viewing/editing/deleting comments on objects user shouldn't access).

## 9. Deployment Requirements

*   Migrations for `Comment` table, indexes (incl. GFK, JSONField).
*   Dependencies on `User`, `FileStorage`, `ContentType`, `Organization`.
*   Deployment of `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements

*   Standard backups. Potential moderation activities.
*   Management of custom field schemas. Monitoring performance of GFK queries.

---
### Notification

# Notification System - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To define a standardized system for generating, delivering, and tracking notifications related to system events and user communications within the ERP.
*   **Scope**: Definition of the core `Notification` model (primarily for in-app display and tracking), mechanisms for triggering notifications, integration with delivery channels (in-app, email, potentially others via async tasks), and respecting user preferences.
*   **Implementation**: Involves a concrete `Notification` Django Model (inheriting base models), potentially a `NotificationTemplate` model, integration with background task queues (e.g., Celery) for external channel delivery, and a notification service/function.
*   **Target Users**: All users receiving notifications, System Administrators (managing templates/settings), Developers (triggering notifications).

## 2. Business Requirements

*   **Inform Users**: Notify users promptly about relevant events, tasks, mentions, or system updates.
*   **Drive Action**: Alert users to items requiring their attention (e.g., approvals, overdue tasks).
*   **Configurable Delivery**: Allow users some control over which notifications they receive and potentially how (initially focusing on enabling/disabling types).
*   **Multi-Channel Potential**: Support delivery via in-app notifications and email initially, with architecture allowing for future channels (SMS, push).
*   **Reliable Delivery**: Ensure notifications are generated reliably and delivered efficiently (especially via background tasks).

## 3. Functional Requirements

### 3.1 `Notification` Model Definition (Primary: In-App/Tracking)
*   **Purpose**: Represents a single notification instance intended for a user.
*   **Inheritance**: Must inherit `Timestamped`, `Auditable`, and `OrganizationScoped` (notifications belong to the user's context within an org).
*   **Fields**:
    *   `recipient`: (ForeignKey to `User`, on_delete=models.CASCADE, related_name='notifications') **Required**. The user receiving the notification.
    *   `level`: (CharField with choices, e.g., 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'ACTION', default='INFO', db_index=True) Severity or type category.
    *   `title`: (CharField, max_length=255, blank=True) Optional short title/summary.
    *   `message`: (TextField) The main content/body of the notification. Can contain simple markup if needed for in-app display.
    *   `status`: (CharField with choices, e.g., 'UNSENT', 'SENT', 'DELIVERED', 'READ', 'ACTIONED', 'ERROR', default='UNSENT', db_index=True) Tracks the notification lifecycle.
    *   `read_at`: (DateTimeField, null=True, blank=True) Timestamp when the user marked the notification as read (for in-app).
    *   `action_url`: (URLField, blank=True) Optional URL for a primary action related to the notification.
    *   `action_text`: (CharField, max_length=50, blank=True) Optional text for the action button/link.
    *   **Linking Fields (Generic Relation or Specific FKs)**: Optional fields to link the notification back to the originating object (e.g., the specific Invoice that was approved). Uses `ContentType`/`object_id` or specific nullable FKs.
    *   `notification_type`: (CharField, max_length=100, blank=True, db_index=True) Application-defined code for the specific type of notification event (e.g., 'invoice_approved', 'task_assigned') used for user preferences.
*   **Meta**: `verbose_name`, `plural`, `ordering = ['-created_at']`, relevant indexes.
*   **String Representation**: Return title or truncated message.

### 3.2 `NotificationTemplate` Model (Optional but Recommended)
*   **Purpose**: Store reusable templates for notification content (especially email subjects/bodies).
*   **Fields**:
    *   `template_key`: (CharField, unique=True) Identifier used to select the template (e.g., 'invoice_approved_email').
    *   `subject_template`: (TextField) Django template syntax for the subject.
    *   `body_template_txt`: (TextField) Django template syntax for the plain text body.
    *   `body_template_html`: (TextField, blank=True) Django template syntax for the HTML body.
    *   *Inherit Timestamped/Auditable.*
*   **Management**: Via Admin UI or specific management commands/API.

### 3.3 Notification Generation & Triggering
*   **Central Service/Function**: Implement a reusable function/service (e.g., `send_notification(recipient, level, message, title=None, action_url=None, ..., notification_type=None, context=None, channels=['in_app', 'email'])`).
*   **Trigger Points**: This service will be called from various parts of the application logic:
    *   Model `save` methods (use with caution).
    *   Signal receivers (e.g., on `post_save` of an Order, on `user_logged_in`).
    *   Workflow transition actions (e.g., after an invoice is approved).
    *   Explicit calls in API views or service layers.
*   **Logic inside `send_notification`**:
    1.  Check recipient's preferences for the given `notification_type`. Abort if user opted out.
    2.  If templating used, render templates using provided `context`.
    3.  If 'in_app' in `channels`: Create and save a `Notification` model instance.
    4.  If 'email' in `channels`: Trigger an **asynchronous task** (Celery) to send the email using rendered templates.
    5.  If other channels in `channels`: Trigger corresponding async tasks.

### 3.4 Delivery Channels & Asynchronous Processing
*   **In-App**: Handled by creating the `Notification` record. Requires API endpoint for users to fetch their unread/recent notifications.
*   **Email**: Requires configuring Django's email backend. Email sending **must** be delegated to a background task queue (Celery) via dedicated tasks. Tasks should handle rendering, sending, and potentially updating the `Notification` status on success/failure.
*   **Other Channels (SMS/Push - Future)**: Require specific integrations with third-party services, also handled via asynchronous tasks.

### 3.5 User Preferences Integration
*   The `UserProfile` model needs a field (likely JSONField `notification_preferences`) to store user choices (e.g., `{"invoice_approved": {"email": true, "in_app": true}, "marketing_promo": {"email": false}}`).
*   The `send_notification` service must query these preferences before proceeding with generation/delivery for specific channels.
*   Need API endpoints/UI for users to manage their preferences.

### 3.6 Notification Interaction (In-App)
*   **API Endpoint**: `/api/v1/notifications/` (GET) - List notifications for the requesting user (paginated, filterable by status=READ/UNREAD).
*   **API Endpoint**: `/api/v1/notifications/{id}/mark-read/` (POST) - Mark a specific notification as read (updates `status`, `read_at`).
*   **API Endpoint**: `/api/v1/notifications/mark-all-read/` (POST) - Mark all unread notifications as read.

### 3.7 Out of Scope
*   Building complex channel integrations (SMS/Push) in the initial phase (focus on In-App and Email via Celery).
*   Real-time delivery using WebSockets (can be added later).
*   Detailed delivery tracking from external providers (e.g., email open/click tracking).

## 4. Technical Requirements

### 4.1 Data Management
*   Storage for `Notification` and `NotificationTemplate` models.
*   Indexing on `Notification` fields used for querying/filtering (`recipient`, `status`, `notification_type`, `organization`).
*   Efficient storage/retrieval of user preferences.

### 4.2 Asynchronous Task Queue
*   **Requirement**: A task queue system (e.g., **Celery** with Redis/RabbitMQ broker) **must** be implemented for handling external deliveries (Email, etc.).

### 4.3 Security
*   Users should only be able to access/manage their own notifications via API.
*   Secure management of templates.
*   Audit logging of notification generation (optional) and template changes.

### 4.4 Performance
*   Notification generation service should be fast (delegating slow tasks).
*   Efficient querying of user notifications.
*   Task queue must handle notification volume reliably.

### 4.5 Integration
*   Integrates with `User`, `UserProfile`, potentially `Organization` (scoping), `Audit Log`.
*   Called by various business modules/workflows.
*   Integrates with Celery (or chosen task queue).
*   Integrates with email backend/service.
*   *(Future)* Integrates with SMS/Push services.

## 5. Non-Functional Requirements

*   **Scalability**: Handle large volumes of notifications and users. Task queue scalability is key.
*   **Reliability**: Minimize notification loss. Handle delivery errors/retries (in async tasks).
*   **Availability**: Notification fetching API must be available. Delivery depends on task queue and external services.
*   **Timeliness**: While external delivery isn't instant, async tasks should process reasonably quickly.

## 6. Success Metrics

*   High delivery success rate (for triggered notifications respecting preferences).
*   Low error rate in async delivery tasks.
*   Performant fetching of user notifications via API.
*   User satisfaction with notification relevance and preference controls.

## 7. API Documentation Requirements

*   Document `Notification` model fields/states.
*   Document API endpoints for fetching notifications and marking as read.
*   Document available `notification_type` codes and their meaning (for preference management).
*   Document API for managing user notification preferences (if applicable).
*   Document any API for triggering notifications directly (if one exists beyond internal service calls).

## 8. Testing Requirements

*   **Unit Tests**: Test `Notification` model. Test notification service logic (preference checking, template rendering selection). Test template rendering. Test Celery task logic in isolation (mocking external calls).
*   **Integration Tests**:
    *   Trigger events that should generate notifications (e.g., approve an invoice). Verify `Notification` record is created and Celery task is queued.
    *   Test fetching notifications via API for different users.
    *   Test marking notifications as read via API.
    *   Test user preference logic (e.g., ensure email task isn't queued if user opted out).
    *   Mock email backend/services to test task execution.

## 9. Deployment Requirements

*   Migrations for `Notification`, `NotificationTemplate` models.
*   Setup and deployment of Celery workers and broker (Redis/RabbitMQ).
*   Configuration of email backend (API keys, etc.).
*   Initial population of essential `NotificationTemplate`s.

## 10. Maintenance Requirements

*   Monitor Celery queue length and task success/failure rates.
*   Manage notification templates.
*   Regular backups.
*   Keep email/SMS/Push service integrations updated.

---
### Video Meeting

# Video Meeting Integration - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To define the requirements for integrating a **third-party video conferencing service** into the ERP system, enabling users to schedule, manage, join, and access recordings/metadata for video meetings associated with ERP entities.
*   **Scope**: Definition of ERP-side models (`Meeting`, `MeetingParticipant`) to store meeting metadata and participant info, integration points with a chosen external video conferencing provider's API (scheduling, participant management, webhooks), embedding/linking the meeting UI, and managing recordings. **Excludes building WebRTC/media server infrastructure.**
*   **Implementation Strategy**:
    1.  **Choose External Provider**: Select a provider (e.g., Zoom, Vonage Video API, Daily.co, Twilio Video, Whereby Embedded). *(Decision Required)*
    2.  Implement ERP models (`Meeting`, `MeetingParticipant`) inheriting base models.
    3.  Integrate with the provider's REST API and potentially client SDKs.
    4.  Implement webhook handlers to receive events from the provider.
    5.  Embed the provider's UI or link to meeting URLs.
*   **Target Users**: All ERP users participating in meetings, Meeting Schedulers/Hosts, System Administrators.

## 2. Business Requirements

*   **Integrated Meetings**: Schedule and join video meetings directly from within the ERP context (e.g., linked to an Order, Project, or Contact).
*   **Simplified Scheduling**: Streamline the process of creating video meetings relevant to ERP tasks.
*   **Participant Management**: Track ERP users invited to or participating in meetings.
*   **Recording Access**: Provide links to meeting recordings within the relevant ERP context.
*   **Secure Access**: Ensure only authorized ERP users can schedule or join relevant meetings.
*   **Organization Scoping**: Meetings must be scoped by Organization.

## 3. Functional Requirements

### 3.1 Core ERP Models
*   **`Meeting` Model**:
    *   **Purpose**: Stores metadata about a scheduled meeting instance within the ERP.
    *   **Inheritance**: `Timestamped`, `Auditable`, `OrganizationScoped`.
    *   **Fields**:
        *   `topic`: (CharField, max_length=255) Meeting title/subject.
        *   `description`: (TextField, blank=True).
        *   `scheduled_start_time`: (DateTimeField, db_index=True).
        *   `scheduled_end_time`: (DateTimeField, null=True, blank=True).
        *   `actual_start_time`: (DateTimeField, null=True, blank=True) Populated via webhook.
        *   `actual_end_time`: (DateTimeField, null=True, blank=True) Populated via webhook.
        *   `status`: (CharField with choices: 'SCHEDULED', 'IN_PROGRESS', 'ENDED', 'CANCELLED', default='SCHEDULED', db_index=True). Updated via API calls or webhooks.
        *   `host`: (ForeignKey to `User`, on_delete=models.SET_NULL, null=True, related_name='hosted_meetings') The ERP user who scheduled/hosts.
        *   `provider`: (CharField, max_length=50) Identifier for the external provider used (e.g., 'zoom', 'vonage').
        *   `provider_meeting_id`: (CharField, max_length=255, unique=True, db_index=True) The unique ID assigned by the external provider.
        *   `join_url`: (URLField, max_length=1024, blank=True) The primary URL to join the meeting.
        *   `related_object_type`: (ForeignKey to `ContentType`, null=True, blank=True) Optional: Link to the type of ERP object this meeting relates to.
        *   `related_object_id`: (CharField/PositiveIntegerField, null=True, blank=True) Optional: PK of the related ERP object.
        *   **`custom_fields`**: (JSONField, default=dict, blank=True).
    *   **Meta**: `verbose_name`, `plural`, `ordering`.
*   **`MeetingParticipant` Model**:
    *   **Purpose**: Links ERP Users to a `Meeting`, tracking their role and status.
    *   **Inheritance**: `Timestamped`, `Auditable`, `OrganizationScoped`.
    *   **Fields**:
        *   `meeting`: (ForeignKey to `Meeting`, on_delete=models.CASCADE, related_name='participants').
        *   `user`: (ForeignKey to `User`, on_delete=models.CASCADE, related_name='meeting_participations').
        *   `role`: (CharField with choices: 'HOST', 'PARTICIPANT', default='PARTICIPANT').
        *   `join_time`: (DateTimeField, null=True, blank=True) Populated via webhook.
        *   `leave_time`: (DateTimeField, null=True, blank=True) Populated via webhook.
    *   **Meta**: `unique_together = ('meeting', 'user')`, `verbose_name`, `plural`.

### 3.2 Meeting Operations (via API -> Provider API)
*   **Schedule Meeting**: API endpoint (`POST /api/v1/meetings/`) receives topic, time, initial participants.
    *   Backend logic calls the **external provider's API** to create the meeting.
    *   Stores provider ID, join URL, etc., in the local `Meeting` record.
    *   Creates initial `MeetingParticipant` records.
    *   Potentially sends invites via `Notification` system.
*   **Update Meeting**: API endpoint (`PUT /api/v1/meetings/{id}/`) updates topic, time. Calls provider API.
*   **Cancel Meeting**: API endpoint (`DELETE /api/v1/meetings/{id}/` or `POST /cancel/`). Calls provider API. Updates local `status`.
*   **Get Meeting Info**: API endpoint (`GET /api/v1/meetings/{id}/`) returns local `Meeting` data (including join URL).
*   **List Meetings**: API endpoint (`GET /api/v1/meetings/`) lists meetings user is associated with (hosted or participant), filterable by date/status.

### 3.3 Joining Meetings
*   Users retrieve the `join_url` via the ERP API/UI.
*   Clicking the URL either launches the provider's app or loads an embedded experience (depending on provider and implementation). Authentication within the meeting is handled by the provider (potentially using tokens generated via ERP backend).

### 3.4 Real-Time Features (Handled by Provider)
*   Video/Audio Streaming, Screen Sharing, In-Meeting Chat, Reactions, Participant List within the meeting UI are provided by the external service.

### 3.5 Recording Management
*   **Webhook Handler**: Implement an endpoint to receive webhook events from the provider (e.g., `recording.completed`).
*   **Logic**: When a recording is ready, the webhook handler:
    1.  Finds the corresponding `Meeting` record using the `provider_meeting_id`.
    2.  Gets the recording URL(s) or download link(s) from the webhook payload.
    3.  **(Option A)** Stores the URL(s) directly on the `Meeting` record (e.g., in a JSONField `recording_links`).
    4.  **(Option B)** Downloads the recording file asynchronously (Celery task), saves it via the `FileStorage` system, and links the `FileStorage` record to the `Meeting` record (e.g., `Meeting.recording_files = ManyToManyField(FileStorage)`). *Option B provides more control but uses more storage.*

### 3.6 Integration Requirements
*   **External Provider API**: Requires secure storage and use of API keys/credentials for the chosen provider.
*   **Webhook Handling**: Requires a publicly accessible endpoint for provider webhooks with security verification (e.g., signature validation).
*   **User Interface**: Requires embedding the provider's meeting UI (e.g., via iFrame or SDK) or linking out to meeting URLs.
*   **Notification System**: Send meeting invitations and reminders.
*   **Calendar Integration (Optional)**: API calls to create/update events in users' external calendars (Google Calendar, Outlook) when meetings are scheduled/updated. Requires OAuth integration.
*   **Audit Logging**: Log creation, cancellation, participant changes (via webhooks) for `Meeting` records.

### 3.7 Custom Field Schema Definition (External Mechanism)
*   Requirement for separate `CustomFieldDefinition` model/mechanism if custom fields are used on the `Meeting` model.

### 3.8 Out of Scope
*   Building custom WebRTC/media server infrastructure.
*   Implementing in-meeting features (chat, screen share, recording) - rely on provider.

## 4. Technical Requirements

### 4.1 External API Integration
*   Robust client for interacting with the chosen provider's API (error handling, retries).
*   Secure storage for provider API credentials (`django-environ`, Vault, etc.).

### 4.2 Webhook Handling
*   Reliable webhook endpoint capable of handling provider events. Security validation is essential. Asynchronous processing (Celery) recommended for webhook payloads.

### 4.3 Security
*   Secure API key management. Webhook signature validation.
*   Permissions (RBAC) control who can schedule meetings, view recordings, manage participants.
*   Organization scoping ensures users only interact with meetings within their org.
*   Rely on provider's security for in-meeting encryption and access.

### 4.4 Performance
*   API calls to the external provider should ideally be asynchronous (Celery) if they might be slow.
*   Efficient querying of local `Meeting` / `MeetingParticipant` data.

### 4.5 Integration Points
*   ERP Models (`Meeting`, `MeetingParticipant`).
*   Provider API client. Webhook handler.
*   UI embedding/linking logic.
*   Notification System, Audit Log, RBAC, Org Scoping, File Storage (for recordings).
*   Optional Calendar API integration.

## 5. Non-Functional Requirements

*   **Reliability**: Depends heavily on the chosen external provider's reliability. Webhook handling must be reliable.
*   **Availability**: Depends on provider's availability. ERP endpoints for scheduling/viewing must be available.
*   **Scalability**: Provider handles media scalability. ERP must handle metadata/scheduling load.

## 6. Success Metrics

*   Successful scheduling and joining of meetings via ERP interface.
*   Reliable retrieval of meeting metadata and recording links.
*   High user satisfaction with the integrated meeting experience.
*   Provider service uptime and quality meet expectations.

## 7. API Documentation Requirements

*   Document ERP API endpoints for managing `Meeting` metadata (CRUD, list, get join URL).
*   Document webhook endpoint requirements (if applicable for external configuration).
*   Explain the relationship with the external provider and how joining works.
*   Auth/Permission requirements for meeting APIs.
*   Document `custom_fields` handling.

## 8. Testing Requirements

*   **Unit Tests**: Test `Meeting`, `MeetingParticipant` models. Test logic within API views/webhook handlers (mocking external API calls).
*   **Integration Tests**:
    *   **Requires mocking the external provider's API**.
    *   Test scheduling API call -> verify mock provider API called correctly -> verify local `Meeting` created.
    *   Test webhook handler -> send mock webhook payload -> verify local `Meeting`/`Participant`/`FileStorage` records are updated correctly.
    *   Test fetching meeting lists/details and join URLs.
    *   Test permissions and org scoping.
    *   Test **saving/validating `custom_fields`**.
*   **Manual/E2E Tests**: Test the full flow with the actual external provider in a staging environment.

## 9. Deployment Requirements

*   Migrations for `Meeting`, `MeetingParticipant` models, indexes (incl. JSONField).
*   Secure configuration of external provider API keys/secrets for each environment.
*   Deployment of webhook handler endpoint.
*   Setup of Celery workers for async tasks (provider calls, recording downloads).
*   Deployment of `CustomFieldDefinition` mechanism if needed.

## 10. Maintenance Requirements

*   Keep provider API client/SDK updated.
*   Monitor provider API usage and webhook success/failure rates.
*   Manage provider API keys/secrets securely.
*   Standard backups.
*   Manage custom field schemas if applicable.

---
## Document Management


### Document System

# Document Model - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To define a standardized model for representing logical documents within the ERP system, managing their metadata, associating them with underlying stored files, and linking them to relevant business contexts.
*   **Scope**: Definition of the `Document` data model, its core attributes (title, type, status), relationship to the `FileStorage` model, basic versioning information, custom field capability, and relationship to other business entities. Excludes complex workflow, content processing (OCR, indexing), and advanced sharing features.
*   **Implementation**: Defined as a concrete Django Model. It **must** inherit `Timestamped`, `Auditable`, and `OrganizationScoped`. Uses a `JSONField` for custom fields. Relies on the `FileStorage` model.
*   **Target Users**: All users interacting with documents (viewing, uploading attachments), Document Managers, System Administrators.

## 2. Business Requirements

*   **Organize Business Files**: Provide a structured way to manage documents beyond raw file storage, adding business context and metadata.
*   **Link Documents to Processes**: Associate documents with specific business records (e.g., attach an invoice PDF to an Invoice record, a contract PDF to an Organization record).
*   **Basic Version Awareness**: Track simple version increments for documents that undergo revisions.
*   **Categorization**: Classify documents by type (e.g., Invoice, Contract, Report).
*   **Access Control**: Ensure documents are accessed according to user permissions and organizational scope.
*   **Extensibility**: Allow storing document-specific attributes via custom fields.

## 3. Functional Requirements

### 3.1 `Document` Model Definition
*   **Inheritance**: Must inherit `Timestamped`, `Auditable`, `OrganizationScoped`.
*   **Fields**:
    *   `title`: (CharField, max_length=255, db_index=True) The primary display name or title of the document.
    *   `document_type`: (ForeignKey to `Category`, limit_choices_to={'category_type': 'DOCUMENT_TYPE'}, on_delete=models.PROTECT, null=True, blank=True) Classification using the generic Category model.
    *   `status`: (CharField, max_length=50, choices=..., default='draft', db_index=True) Status of the document (e.g., 'Draft', 'Active', 'Archived', 'Pending Review'). References slugs from the `Status` model/system.
    *   `file`: (ForeignKey to `FileStorage`, on_delete=models.PROTECT) **Required**. Links to the metadata record of the actual underlying file content.
    *   `version`: (PositiveIntegerField, default=1) Simple integer representing the document version number.
    *   `description`: (TextField, blank=True) Optional description or summary.
    *   `tags`: (ManyToManyField via `django-taggit` or similar, blank=True) For flexible classification.
    *   **`custom_fields`**: (JSONField, default=dict, blank=True) Stores values for dynamically defined custom fields relevant to the document (e.g., 'review_date', 'related_project_id').
    *   **Linking Fields (Generic Relation or Specific FKs)**: Need a way to link the Document to the business entity it belongs to. Options:
        *   **GenericForeignKey:** Use `content_type` (FK to `ContentType`), `object_id` (PositiveIntegerField/CharField), `content_object` (GenericForeignKey). Flexible but harder to query.
        *   **Specific ForeignKeys:** Add nullable ForeignKeys for common links (e.g., `related_organization = FK(Organization, null=True)`, `related_product = FK(Product, null=True)`). Less flexible, more explicit. *(Decision needed)*.
*   **Meta**:
    *   `verbose_name = "Document"`
    *   `verbose_name_plural = "Documents"`
    *   `ordering = ['-created_at']`
    *   Consider indexes on linking fields and `document_type`.
*   **String Representation**: Return `title` and perhaps `version`.

### 3.2 Custom Field Schema Definition (External Mechanism)
*   Requirement for separate `CustomFieldDefinition` model/mechanism (possibly filtered by a 'Document' context or `document_type`) to define schema for document custom fields.

### 3.3 Version Management (Simplified)
*   **Creating New Version**: Typically involves:
    1. Uploading a new file (creates a new `FileStorage` record).
    2. Creating a *new* `Document` record.
    3. Linking the new `Document` to the new `FileStorage` record.
    4. Incrementing the `version` number.
    5. Potentially linking the new `Document` to the previous version (e.g., add a `previous_version = ForeignKey('self', null=True)` field to the `Document` model). *(Decision needed on explicit version linking)*.
*   **Out of Scope (Advanced):** Complex diffing, merging, explicit rollback workflows.

### 3.4 Document Operations
  CRUD via API:
   Primary method for creating, reading, updating (metadata), and deleting Document records must be via API endpoints, respecting Organization scope and permissions. Creating a Document typically involves handling a related file upload to the FileStorage system simultaneously or referencing an existing FileStorage record.
  Association:
   API logic required to associate Document records with relevant business entities (using GenericForeignKey or specific FKs, depending on the chosen implementation). This might be part of the Document CRUD or handled by the API for the parent business entity.
Version Management (Simplified):
 If implementing versioning, API actions might trigger the creation of a new Document version (as described in 3.3).
Admin Management:
 Django Admin provides a secondary interface for administrators to view, potentially manage metadata, or troubleshoot Document records.

### 3.5 Validation
*   Required fields (`title`, `file`). FK constraints. Custom field validation against schema. Status logic enforced by Workflow/StateMachine system later.

### 3.6 Out of Scope for this Model/PRD
*   **File Storage Backend Details**: Handled by `FileStorage` system.
*   **Advanced Version Control**: Diffing, merging, branching.
*   **Content Processing**: OCR, full-text indexing, format conversion (separate features/integrations).
*   **Document Sharing/Collaboration**: Advanced features beyond base permissions.
*   **Document Workflows**: Review/Approval processes (handled by Workflow system referencing `Document.status`).
*   **Detailed History**: Handled by Audit Log.

## 4. Technical Requirements

### 4.1 Data Management
*   Storage: Standard fields + JSONField. Links to `FileStorage`, `ContentType`, potentially self for versioning.
*   Indexing: On `title`, `status`, `document_type`, `organization`. On Generic Relation fields (`content_type`, `object_id`) if used. **GIN index on `custom_fields`** if querying needed.
*   Search: API filtering/search on key metadata fields, type, status, tags, potentially custom fields. *Full-text search requires separate indexing solution.*

### 4.2 Security
*   **Access Control**: Permissions (`add_document`, `change_document`, `delete_document`, `view_document`). Enforced within Organization scope. Access may also depend on permissions for the *linked business entity* (e.g., view Invoice Document requires view permission on the Invoice). Field-level permissions may apply.
*   **File Access Security**: Accessing the underlying file content via the `Document.file` link must re-verify permissions, potentially using secure URL generation provided by the `FileStorage` system.
*   **Audit Logging**: Log CRUD operations, status changes, and `custom_fields` changes via Audit System.

### 4.3 Performance
*   Efficient querying/filtering of document metadata.
*   Performance of underlying file access depends on `FileStorage` system.

### 4.4 Integration
*   **Core Dependency**: Relies heavily on `FileStorage` model.
*   **Linking**: Integrates with various business models via GenericForeignKey or specific ForeignKeys.
*   **Categorization**: Integrates with `Category` model (for `document_type`).
*   **Status**: Integrates with `Status` model/system.
*   **API Endpoint**: Provide RESTful API (`/api/v1/documents/`) for CRUD, respecting Org Scoping and permissions. Needs careful handling of file uploads during create and linking to business entities. Include filtering/search. Define `custom_fields` handling.
*   **Custom Field Schema Integration**: Integrates with `CustomFieldDefinition` mechanism.

## 5. Non-Functional Requirements

*   **Scalability**: Support a large number of document metadata records. Scalability of file storage itself depends on the `FileStorage` backend.
*   **Availability**: Document metadata and access to underlying files need to be available.
*   **Data Consistency**: Maintain integrity of links (to FileStorage, Categories, Business Entities).
*   **Backup/Recovery**: Must include both Document metadata DB and the underlying FileStorage backend.

## 6. Success Metrics

*   Successful association of files with business context via `Document` records.
*   Ease of finding and managing relevant documents.
*   Reliable access control enforcement for documents and files.
*   Successful basic version tracking.

## 7. API Documentation Requirements

*   Document `Document` model fields (incl. `custom_fields`, linking fields).
*   Document API endpoints for CRUD, filtering, searching. Detail file handling on upload.
*   Document how `custom_fields` are handled.
*   Auth/Permission requirements (mentioning Org Scoping and potential dependency on linked entity permissions).
*   Document how to discover custom field schemas (if applicable).

## 8. Testing Requirements

*   **Unit Tests**: Test `Document` model, relationships, version increment logic (if implemented in `save`).
*   **Integration Tests**:
    *   Test API CRUD, ensuring file upload creates `FileStorage` and `Document` correctly.
    *   Test linking documents to other business entities (via GFK or specific FKs).
    *   Test Org Scoping enforcement.
    *   Test permissions (direct Document permissions and inherited from linked entity).
    *   Test basic version creation via API.
    *   Test filtering/searching.
    *   Test **saving/validating `custom_fields`**.
*   **Security Tests**: Test access control scenarios rigorously.

## 9. Deployment Requirements

*   Migrations for `Document` table, indexes (incl. JSONField).
*   Dependencies on `FileStorage`, `Category`, `Status`, `Organization`, `User` models/migrations.
*   Deployment of `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements

*   Standard backups (DB + File Storage).
*   Monitoring performance.
*   Management of document types (via Category system) and custom field schemas.

---
### File Storage

# FileStorage Model - Product Requirements Document (PRD)

## 1. Overview

*   **Purpose**: To define a standardized model for storing metadata about files uploaded and managed within the ERP system, providing a reference linking to the actual file stored via a **configured backend (supporting both local filesystem and cloud options)**.
*   **Scope**: Definition of the `FileStorage` data model holding file metadata (name, type, size, owner, storage path), basic management, custom field capability, and integration points. Excludes specific backend implementation details and built-in file versioning.
*   **Implementation**: Defined as a concrete Django Model. It **must** inherit `Timestamped`, `Auditable`, and `OrganizationScoped`. Uses a `JSONField` for custom fields. Relies on Django's configurable storage backend system.
*   **Target Users**: Any user/system uploading or accessing files, Developers (linking models to files), System Administrators.

## 2. Business Requirements

*   **Centralized File Reference**: Provide a metadata record for every managed file.
*   **Support Diverse File Types**: Handle various document, media, etc.
*   **Track Basic Metadata**: Store filename, size, MIME type, uploader.
*   **Foundation for Attachments**: Allow other entities to link to stored files.
*   **Access Control Foundation**: Provide ownership/scoping for permission checks.
*   **Extensibility**: Allow storing file-specific metadata via custom fields.
*   **Storage Flexibility**: Allow deployment using either local filesystem or cloud storage via configuration.

## 3. Functional Requirements

### 3.1 `FileStorage` Model Definition
*   **Inheritance**: Must inherit `Timestamped`, `Auditable`, `OrganizationScoped`.
*   **Fields**:
    *   `file`: (FileField) Stores the **relative path** within the configured storage backend. `upload_to` generates unique path (e.g., `org_{org_id}/files/{uuid}.{ext}`).
    *   `original_filename`: (CharField, max_length=255, db_index=True).
    *   `file_size`: (PositiveBigIntegerField, null=True) In bytes. Populated on upload.
    *   `mime_type`: (CharField, max_length=100, blank=True, db_index=True). Populated on upload.
    *   `uploaded_by`: (ForeignKey to `User`, SET_NULL, null=True, related_name='uploaded_files').
    *   `tags`: (TaggableManager, blank=True).
    *   **`custom_fields`**: (JSONField, default=dict, blank=True).
*   **Meta**: `verbose_name`, `plural`, `ordering`, indexes.
*   **String Representation**: Return `original_filename`.
*   **Properties/Methods**:
    *   `@property def filename(self): return os.path.basename(self.file.name)`
    *   `@property def url(self):` - **Crucial:** This method should securely generate the appropriate access URL by calling `self.file.url`, which respects the configured storage backend (returning local `/media/...` or cloud pre-signed URL). Requires request context for permission checks before returning URL.

### 3.2 Custom Field Schema Definition (External Mechanism)
*   Requires separate `CustomFieldDefinition` mechanism if custom fields are used.

### 3.3 File Operations (Handled by API Views/Services)
*   **Upload**: API endpoint handles receiving file binary, validation (type, size), creating `FileStorage` instance (populating metadata), saving file via `instance.file.save()` (uses configured backend), saving instance, returning metadata.
*   **Download/Access**: API endpoint/logic checks permissions (Org scope, RBAC), then generates a secure access URL using the `instance.url` property (which calls `instance.file.url`).
*   **Deletion**: API endpoint checks permissions, deletes `FileStorage` record, and **must** call `instance.file.delete(save=False)` to remove the file from the storage backend.
*   **Update**: API for updating metadata (`tags`, `custom_fields`). Replacing file content typically involves deleting the old record and creating a new one.

### 3.4 Validation
*   Upload validation (type, size) performed in API view/serializer using configured settings.
*   Custom field validation against schema.

### 3.5 Relationships
*   Links *to* `User`, `Organization`.
*   Linked *to* by other models via FK/M2M.

### 3.6 Out of Scope
*   Specific storage backend implementation details (handled by strategy/config).
*   File Versioning (separate feature).
*   File Content Validation (virus scan etc.).
*   Detailed History (Audit Log).

## 4. Technical Requirements

*(Largely the same as previous version, but emphasizes abstraction)*

### 4.1 Data Management
*   Storage: `FileField` stores relative path. Metadata in DB. Binaries in configured backend (local FS or cloud). Indexing on metadata. GIN index for `custom_fields` if needed.

### 4.2 Security
*   **Access Control:** Application brokers access based on permissions/Org Scope *before* generating download URLs (`instance.url`).
*   **Storage Security:** Configure backend appropriately (private buckets/folders, filesystem permissions).
*   **Secure URLs:** Rely on `instance.file.url` to generate appropriate URLs (direct path for local, pre-signed for cloud).
*   **Credentials:** Managed securely via Configuration Strategy.
*   **Upload Validation:** Enforce type/size limits.
*   **Audit Logging:** Log upload, delete, potentially controlled access events.

### 4.3 Performance
*   Metadata queries should be efficient. File transfer performance depends on backend/network.

### 4.4 Integration
*   **Storage Backend:** Relies on configured `DEFAULT_FILE_STORAGE` and `django-storages` if using cloud. Code uses Django storage abstraction.
*   **Primary Integration:** Target for FK/M2M.
*   **API Endpoint:** For Upload, Metadata management, Secure URL generation/Access, Deletion.
*   **Custom Field Integration:** With `CustomFieldDefinition` mechanism.

## 5. Non-Functional Requirements

*   Scalability (depends on chosen backend), Availability (depends on backend), Durability (depends on backend), Consistency (metadata vs file), Backup/Recovery (DB metadata + file backend).

## 6. Success Metrics

*   Successful upload/storage/retrieval using either configured backend. Reliable access control. Performant metadata/access. Successful linking.

## 7. API Documentation Requirements

*   Document `FileStorage` model fields.
*   Document Upload/Access/Delete API endpoints and processes. Explain validation.
*   Document how download URLs are obtained and their nature (direct vs signed).
*   Auth/Permission requirements.
*   Custom fields handling.

## 8. Testing Requirements

*   **Unit Tests**: Test model, `url` property logic (mocking `file.url`).
*   **Integration Tests**:
    *   **Run primarily against `FileSystemStorage`** using `override_settings` and temporary directories.
    *   Test Upload API (success, validation failures).
    *   Test Access/URL generation API (permission success/failure).
    *   Test Delete API (metadata + file deletion from mock storage).
    *   Test `custom_fields` save/validation.
    *   **(Optional)** Separate tests using `moto` to verify S3-specific interactions if needed.
*   **Security Tests**: Focus on access control for download URLs and deletion.

## 9. Deployment Requirements

*   Migrations for `FileStorage`.
*   **Configure `DEFAULT_FILE_STORAGE` and backend-specific settings (MEDIA_ROOT or Cloud Credentials/Bucket) appropriately for each environment** via environment variables/secrets management.
*   Configure web server for serving `MEDIA_URL` if using `FileSystemStorage` in production (with access controls).
*   Configure validation settings (size, type).
*   Deploy `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements

*   Monitor storage usage (local disk or cloud). Backups (DB + File Backend). Library updates (`django-storages`). Manage custom field schemas.

--- END OF FILE file_storage_prd.md ---
### Export/Import


# Data Import/Export Framework - Product Requirements Document (PRD) - Final Refined (v2)

## 1. Overview

*   **Purpose**: To define the standard framework, tools, and patterns for providing robust, user-driven data import and export capabilities across various key models within the ERP system.
*   **Scope**: Selection of core libraries, definition of asynchronous processing (Celery), design of a job tracking model (`DataJob`), specification of standard API patterns for initiating jobs, definition of a **generic resource factory** providing baseline import/export, guidelines for using **custom `ModelResource` classes**, support for standard data formats (**CSV, XLSX, PDF** for export), and refined error/warning handling for imports.
*   **Implementation Strategy**:
    *   Utilize **`django-import-export`** library for core logic and CSV/XLSX format handling via `ModelResource` classes (custom or generic).
    *   Integrate dedicated **PDF generation libraries** for PDF export.
    *   Utilize **Celery** for asynchronous job execution.
    *   Implement a **`DataJob`** model for tracking.
    *   Implement **API endpoints** for job initiation/monitoring.
    *   Leverage the **Advanced Filtering System's** JSON definition format for specifying export datasets.
    *   Implement a **Generic Resource Factory** providing baseline capabilities.
*   **Target Users**: Users needing bulk data operations/reports, Admins, Data Migration Teams, Developers.

## 2. Business Requirements

*   **Flexible Export**: Export specific data subsets based on complex filter criteria into CSV, XLSX, or PDF.
*   **Basic & Advanced Import**: Import data from CSV/XLSX. Provide automated basic import (direct fields, FK IDs) for most models. Enable robust, validated import with relationship lookups for key models via specific configurations (custom resources).
*   **Formatted Reports Export**: Allow specific views or predefined reports to be exported as PDF documents.
*   **Data Exchange**: Facilitate data transfer.
*   **User Control & Visibility**: Allow authorized users to initiate jobs, apply export filters, monitor progress, and review results/errors.
*   **Reliability & Error Handling**: Ensure jobs run reliably in the background, with clear reporting of success, failure, and specific row-level errors/warnings during import.

## 3. Core Framework Components

### 3.1 Core Library (`django-import-export`)
*   **Adoption**: Foundation for defining data mappings and handling CSV/XLSX formats via `ModelResource`.
*   **`ModelResource` (Custom)**: Developers **must** create specific `ModelResource` subclasses for models requiring:
    *   **Complex Import Logic:** Handling relationship lookups by non-PK fields (e.g., name, code), specific row validation logic, M2M field import, complex data transformations.
    *   **Custom Export Formatting:** Using `dehydrate_<field>` methods.
*   **`ModelResource` (Generic - Fallback)**: See 3.5.

### 3.2 PDF Generation Libraries (Integration)
*   Requires separate integration of libraries like ReportLab or WeasyPrint for PDF export tasks. Logic is specific per PDF report/export type.

### 3.3 Asynchronous Execution (Celery)
*   **Requirement**: All non-trivial jobs initiated via API **must** run asynchronously via Celery.
*   **Tasks**: `run_export_job(job_id)`, `run_import_job(job_id)`.

### 3.4 `DataJob` Model Definition (for Job Tracking)
*   **Purpose**: Track asynchronous import/export tasks.
*   **Inheritance**: `Timestamped`, `Auditable`, `OrganizationScoped`.
*   **Fields**:
    *   `job_type`: (Choices: 'IMPORT', 'EXPORT')
    *   `status`: (Choices: 'PENDING', 'QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', default='PENDING')
    *   `user`: (FK to User - from Auditable `created_by`)
    *   `organization`: (FK to Organization - from `OrganizationScoped`)
    *   `target_model_content_type`: (FK to `ContentType`, nullable)
    *   `export_format`: (CharField: 'CSV', 'XLSX', 'PDF', blank=True)
    *   `input_params`: (JSONField, nullable) Stores filters for export, import settings.
    *   `input_file`: (FK to `FileStorage`, nullable) For import jobs.
    *   `output_file`: (FK to `FileStorage`, nullable) For export jobs.
    *   `result_log`: (JSONField, nullable, default=dict) Stores summary results (row counts, errors, warnings).
    *   `celery_task_id`: (CharField, nullable, db_index=True).
*   **Meta**: `verbose_name`, `plural`, `ordering`, indexes.

### 3.5 Generic Resource Factory (`core/import_export_utils.py`)
*   **Requirement**: Implement `get_resource_class_for_model(model_class)` function:
    1.  Attempts to find/import a custom `ModelResource` (e.g., `app.resources.ModelResource`).
    2.  If none found, dynamically generates a basic `ModelResource`.
*   **Generic Resource Capabilities:**
    *   **Export:** Includes non-relational, non-sensitive fields. Optionally includes simple FK fields (exporting PK). Basic dehydration.
    *   **Import:**
        *   Maps columns to direct model fields or `fk_field_id` based on header match.
        *   Imports direct ForeignKey fields using provided **PKs** (checks existence).
        *   **Ignores** M2M fields, GFKs, and columns requiring relationship lookups by non-PK fields (e.g., `category_name`).
        *   Generates **row errors** if values for **required** direct model fields (`blank=False`) are missing/empty in the file.
        *   Generates **row errors** if values for **required** ForeignKey fields (`fk_field_id` column) are missing, invalid, or the referenced object doesn't exist.
        *   Calls model's `full_clean()` after populating direct/FK-by-ID fields. Rows failing model validation generate errors.
*   **Purpose**: Provide baseline import/export, focusing on direct field mapping and FKs by ID, without needing custom code for every model.

## 4. Functional Requirements (Framework Level)

### 4.1 API Endpoint Patterns
*   **Initiate Export**: `POST /api/v1/{model_plural_name}/export/` (Body: `{ "format": "...", "filters": { ... Advanced Filter JSON ... } }`). Returns `202 Accepted` with `job_id`.
*   **Initiate Import**: `POST /api/v1/{model_plural_name}/import/` (Body: `multipart/form-data` file + optional params). Returns `202 Accepted` with `job_id`.
*   **Job Status/Results**: `GET /api/v1/data-jobs/{job_id}/`.
*   **List Jobs**: `GET /api/v1/data-jobs/`.

### 4.2 Job Execution & Handling
*   API creates `DataJob`, queues Celery task.
*   `run_export_job` task: Parses filters, gets queryset, gets resource (custom or generic), generates file (CSV/XLSX via resource, PDF via custom logic), saves to `FileStorage`, updates `DataJob`.
*   `run_import_job` task: Gets file, gets resource (custom or generic), uses resource `import_data()`, handles results/errors, updates `DataJob` status and `result_log`.

### 4.3 Supported Formats
*   **Import:** CSV, XLSX.
*   **Export:** CSV, XLSX, PDF.

### 4.4 Validation & Error Handling (Import)
*   Validation performed by the chosen `ModelResource` (custom or generic).
*   **Row Errors:** Specific validation failures (required field missing, invalid FK ID, model `full_clean` fail) are logged per row in `DataJob.result_log['row_errors']`.
*   **Unmapped Columns:** Any columns in the import file header not used by the `ModelResource` are ignored. A **warning** listing these ignored columns **must** be added to `DataJob.result_log['summary']` or a similar key.
*   Job proceeds or fails based on `skip_errors` setting and severity of errors. Final status and summary counts updated in `DataJob`.

## 5. Technical Requirements

### 5.1 Libraries & Infrastructure
*   Requires `django-import-export`, `tablib[xlsx]`, Celery, Broker, `FileStorage`, PDF library (later). Requires Advanced Filtering parser logic for export.

### 5.2 Resource Development
*   Implement generic resource factory. Developers create custom `ModelResource` classes for advanced needs. Developers create specific PDF generators.

### 5.3 Security
*   API endpoints check specific import/export permissions. Async tasks respect Org Scoping. Secure file handling. Generic resource avoids sensitive fields by default.

### 5.4 Performance
*   Async execution. Optimize export queries. Optimize import batching (`use_transactions`). Handle large files. Efficient resource finding.

### 5.5 Error Handling & Logging
*   Robust Celery task error handling. Clear, structured logging of import row errors and unmapped column warnings in `DataJob.result_log`.

## 6. Non-Functional Requirements

*   Scalability, Reliability, Availability, Consistency, Usability (Job feedback).

## 7. Success Metrics

*   High job success rate. Accurate data/reports. Performant execution. Clear error/warning reporting. User satisfaction. Baseline import/export works for simple models without custom code.

## 8. API Documentation Requirements

*   Document `DataJob` model/status/`result_log` structure (including `row_errors` and `summary` for warnings).
*   Document export/import API endpoints per model: supported `format`s, `filters` JSON structure for export.
*   Document job status API. Explain permissions.

## 9. Testing Requirements

*   Unit Tests (Generic resource factory, Celery tasks - mocked, `ModelResource` classes).
*   Integration Tests (Requires Celery, FileStorage):
    *   Test full API flow for export/import (CSV/XLSX/PDF). Verify `DataJob` lifecycle and results/files.
    *   **Test generic import:** Use a model *without* a custom resource. Import file with direct fields, valid FK IDs, invalid FK IDs (for required/optional fields), missing required direct fields, and extra unmapped columns. Verify correct data import, expected row errors, and unmapped column warnings in `result_log`.
    *   Test import/export with custom resources.
    *   Test error handling scenarios. Test permissions.
*   Performance Tests (Large files).

## 10. Deployment Requirements

*   Install libraries. Deploy Celery. Configure FileStorage.
*   Migrations for `DataJob`. Deploy generic resource factory. Deploy initial custom `ModelResource` classes/PDF logic as needed.

## 11. Maintenance Requirements

*   Monitor Celery jobs & `DataJob` records/logs. Maintain resources/PDF logic. Manage job history/logs. Backups.

--- END OF FILE export_import_framework_prd.md ---
## System Features


### Search

# Search System Integration - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To define the requirements for integrating a dedicated **Search Engine** (e.g., Elasticsearch/OpenSearch) to provide robust full-text search, filtering, and relevance ranking capabilities across key data entities within the ERP system.
*   **Scope**: Integration strategy, data indexing pipeline (from Django models to search engine), core search API endpoint definition, basic filtering within search results, and security considerations. Excludes building a search engine from scratch or advanced features like query suggestions or personalized ranking.
*   **Implementation Strategy**: Utilize an external Search Engine (Assumption: **Elasticsearch or OpenSearch**). Integrate using libraries like `django-elasticsearch-dsl` or direct API calls via `elasticsearch-py`/`opensearch-py`. Indexing will likely use Django signals and potentially asynchronous tasks (Celery).
*   **Target Users**: All users needing to find information across the system, Developers (implementing indexing and querying), System Administrators (managing search infrastructure).

## 2. Business Requirements

*   **Efficient Information Retrieval**: Allow users to quickly find relevant records (Products, Documents, Contacts, Organizations, etc.) using keyword searches across multiple fields.
*   **Full-Text Search**: Search within descriptions, notes, potentially document content.
*   **Relevance Ranking**: Return the most relevant results first based on query matching.
*   **Basic Filtering**: Allow narrowing search results based on key criteria (e.g., object type, status, date range).
*   **Scalable Search**: Handle searching across large volumes of data efficiently.

## 3. Functional Requirements

### 3.1 Search Engine Integration & Setup
*   **Requirement**: Deploy and configure an instance of the chosen Search Engine (Elasticsearch/OpenSearch).
*   **Library Integration**: Integrate appropriate Python libraries (`elasticsearch-dsl-py`, `django-elasticsearch-dsl`, etc.) into the Django project for interacting with the search engine.

### 3.2 Data Indexing Pipeline
*   **Index Definition**: Define search engine index mappings for each searchable Django model. Specify which fields should be indexed and how (e.g., `text` for full-text search with appropriate analyzers, `keyword` for exact matching/filtering, `date`, `integer`).
*   **Indexable Models/Fields (Initial Scope - Define Explicitly)**:
    *   `Product`: `name`, `sku`, `description`, `tags`
    *   `Organization`: `name`, `code`, `tags`
    *   `Contact`: `first_name`, `last_name`, `organization_name`, `tags`
    *   `Document`: `title`, `description`, `tags` (*Content indexing requires file processing - see below*)
    *   *(Add other key models as needed)*
*   **Synchronization**: Implement logic to automatically update the search engine index when corresponding Django model instances are created, updated, or deleted.
    *   **Primary Method**: Use Django signals (`post_save`, `post_delete`) connected to handlers that update the search index.
    *   **Asynchronous Update**: Use a task queue (Celery) for index updates triggered by signals to avoid blocking web requests, especially for complex indexing or high-frequency updates.
    *   **Bulk Indexing**: Provide management commands to initially populate the index from existing database records and potentially re-index data periodically or on-demand.
*   **Document Content Indexing (Optional - Advanced)**: If searching *within* file content (`Document.file`) is required:
    *   Requires an additional pipeline step using libraries/tools (like Apache Tika, potentially integrated via `elasticsearch-ingest-attachment` plugin or custom processing) to extract text content from files during the indexing process. This significantly increases complexity. *(Defer unless critical initially)*.

### 3.3 Core Search API Endpoint
*   **Endpoint**: Define a primary search endpoint (e.g., `GET /api/v1/search/`).
*   **Request Parameters**:
    *   `q`: (String) The user's search query terms.
    *   *(Optional Filters)*: Basic filters applied to the search query (sent to the search engine):
        *   `type`: Filter by model type (e.g., `product`, `organization`). Uses `_index` or a dedicated `model_type` field in the index.
        *   `organization_id`: Filter by organization scope (requires `organization_id` in the index).
        *   `status`: Filter by a common status field.
        *   `created_after`/`created_before`: Date range filters.
*   **Backend Logic**:
    1. Receive search query `q` and filters.
    2. Construct a query using the search engine's Query DSL (e.g., using `multi_match` query for `q` across indexed text fields, combined with `filter` clauses for parameter filters).
    3. Execute the query against the search engine.
    4. Process the search engine's response (hits, relevance scores).
    5. Format the results for the API response (e.g., list of objects containing title, snippet/highlight, relevance score, link/ID to the original ERP object). Include pagination info.
*   **Response Format**: Define the structure of the search result objects returned by the API.

### 3.4 Search Features (Initial Scope)
*   **Keyword Matching**: Match terms provided in `q`.
*   **Full-Text Search**: Search within defined text fields.
*   **Relevance Ranking**: Utilize the search engine's default relevance scoring (e.g., TF-IDF, BM25).
*   **Basic Filtering**: Support filtering results by parameters defined in 3.3.

### 3.5 Out of Scope (Initial Implementation)
*   Fuzzy search, phrase search, proximity search, wildcard/regex search (can be added later by adjusting search engine queries).
*   Saving search history.
*   Query suggestions / "Did you mean?".
*   Advanced ranking customization.
*   Personalized search results.
*   Searching across external systems.

## 4. Technical Requirements

### 4.1 Infrastructure
*   Deployment and management of the Search Engine cluster (Elasticsearch/OpenSearch).
*   Network connectivity between Django application and Search Engine.

### 4.2 Index Management
*   Define index mappings (field types, analyzers).
*   Implement robust indexing logic (signals, async tasks).
*   Tools/commands for index creation, deletion, re-indexing.

### 4.3 Querying
*   Use appropriate search engine client library (`elasticsearch-py`, `elasticsearch-dsl-py`, etc.).
*   Construct effective search engine queries (Query DSL).

### 4.4 Security
*   **Search Results Security**: Search API results **must** be filtered based on user permissions *after* retrieving results from the search engine, OR the search query itself must incorporate permission filters (more complex, requires user/role/org data in the index). The primary approach is usually post-filtering:
    1. Perform search in engine.
    2. Get list of potential result IDs (e.g., Product IDs, Org IDs).
    3. Perform a database query for those specific IDs, applying standard Django ORM permissions/scoping (`Product.objects.filter(id__in=search_result_ids, ...permission_filters...)`).
    4. Return only the objects the user is allowed to see.
*   Secure connection to the search engine.
*   Restrict access to indexing management commands/tools.

### 4.5 Performance
*   **Indexing Performance**: Signal handlers/tasks should not significantly impact write performance. Bulk indexing should be efficient.
*   **Query Performance**: Search engine query execution must be fast. Requires appropriate engine sizing and index design. Post-filtering database query must also be efficient (uses `id__in`).
*   **Scalability**: Search engine must scale horizontally to handle data/query volume.

### 4.6 Integration
*   Integrates Django models with the Search Engine via an indexing pipeline.
*   Provides Search API endpoint for frontend/clients.
*   Requires Celery (or similar) for asynchronous indexing.
*   Relies on Permissions/Org Scoping for filtering results.

## 5. Non-Functional Requirements

*   **Scalability**: Indexing and querying must scale with data growth.
*   **Availability**: Search functionality should be highly available. Search Engine cluster needs HA.
*   **Consistency**: Search index should stay reasonably synchronized with the database (near real-time or acceptable delay).
*   **Relevance**: Search results should generally be relevant to user queries.

## 6. Success Metrics

*   Users can successfully find relevant information via search.
*   Search API response times meet performance targets.
*   Index synchronization lag is within acceptable limits.
*   Search functionality is reliable and available.

## 7. API Documentation Requirements

*   Document the Search API endpoint (`GET /api/v1/search/`).
*   Detail the `q` query parameter and available filter parameters (`type`, `organization_id`, etc.).
*   Describe the structure of the search result objects returned.
*   Explain that results are permission-filtered.

## 8. Testing Requirements

*   **Unit Tests**: Test indexing logic (e.g., transforming a model instance into a search document). Test search query construction logic.
*   **Integration Tests**:
    *   Requires a running test instance of the Search Engine.
    *   Test indexing pipeline: Create/update/delete Django models and verify corresponding documents appear/update/disappear in the search index.
    *   Test Search API endpoint with various queries (`q`) and filters. Verify relevance and correctness of results retrieved *from the search engine*.
    *   **Crucially**, test the security post-filtering: Ensure the final API response only contains items the specific test user has permission to view, even if the search engine initially found more items.
    *   Test error handling for invalid search queries.
*   **Performance Tests**: Measure indexing throughput and search query latency against realistic data volumes.

## 9. Deployment Requirements

*   Deployment strategy for the Search Engine cluster itself.
*   Deployment of Django application code including indexing logic and search API.
*   Configuration of connection details (search engine host, credentials).
*   Initial data indexing process (run management command).
*   Setup of asynchronous task queue (Celery) and workers for indexing.

## 10. Maintenance Requirements

*   Monitoring Search Engine cluster health, performance, and storage.
*   Managing index mappings, potentially re-indexing data after mapping changes.
*   Monitoring indexing queue/tasks for errors or backlog.
*   Keeping search engine and client libraries updated.
*   Standard backups (DB + Search Engine snapshots).

---
### Filtering


# Advanced Filtering System - Product Requirements Document (PRD) - Revised

## 1. Overview

*   **Purpose**: To define a standardized and **powerful filtering system** enabling complex, potentially nested, data querying across API list endpoints using URL query parameters. The system must support various operators and logical combinations (`AND`/`OR`). It may also include capabilities for defining and storing reusable filter sets.
*   **Scope**: Definition of the filtering syntax, the backend logic for parsing and applying complex filters to Django QuerySets, integration with DRF ViewSets, and potentially models/APIs for storing predefined filter definitions.
*   **Target Users**: API Consumers (Clients, Frontend Applications requiring advanced data slicing), Developers (integrating filtering), potentially System Administrators (managing predefined filters).

## 2. Business Requirements

*   **Precise Data Retrieval**: Allow API consumers to construct complex queries to retrieve highly specific data subsets, combining multiple criteria with `AND`/`OR` logic.
*   **Support Diverse Operators**: Enable filtering based on various comparison types (equals, contains, range, etc.).
*   **Standardized Querying**: Provide a consistent (though potentially complex) query parameter syntax for advanced filtering.
*   **(Optional/Tiered)** **Reusable Filters**: Allow common or complex filter criteria to be saved and reused (e.g., "My Overdue Tasks", "High-Priority Customers in EMEA").
*   **Performance**: Ensure that complex filtering operations remain performant.

## 3. Functional Requirements

### 3.1 Filtering Logic & Operators
*   **Core Requirement**: The system must be able to parse and apply filters involving:
    *   **Logical Operators**: `AND`, `OR` combinations. Nesting of logical groups must be supported (e.g., `(A AND B) OR C`).
    *   **Field Operators**:
        *   Equality/Inequality: `eq`, `neq` (or `=`, `!=`)
        *   Comparison: `gt`, `gte`, `lt`, `lte`
        *   Text Matching: `contains`, `icontains`, `startswith`, `istartswith`, `endswith`, `iendswith`, `exact`, `iexact`, potentially `like`/`ilike` (use with caution for performance).
        *   Membership: `in`, `notin` (list of values).
        *   Null Checks: `isnull`.
    *   **Target Fields**: Ability to filter on direct model fields and related fields via Django's `__` notation (e.g., `organization__name__icontains`).

### 3.2 API Query Parameter Syntax
*   **Requirement**: Define a clear and consistent syntax for representing nested logic and operators in URL query parameters. *(This is a critical design decision)*. Examples:
    *   **Option A (Structured JSON in Query Param):** `?filter={"and": [{"field": "status", "op": "eq", "value": "active"}, {"or": [{"field": "priority", "op": "gte", "value": 5}, {"field": "assignee__username", "op": "eq", "value": "admin"}]}]}` (Powerful but complex URL encoding).
    *   **Option B (Custom DSL with Prefixes/Separators):** `?filter=AND(status:active,OR(priority__gte:5,assignee__username:admin))` (Requires custom parsing).
    *   **Option C (Leveraging Existing Libraries):** Explore libraries like `drf-complex-filter` or adapt syntax from standards like OData or GraphQL filtering arguments if suitable.
*   **Decision Required:** Choose and document the specific query parameter syntax.

### 3.3 Filter Parsing and Application
*   **Backend Logic**: Implement a robust parser that takes the query parameter string (based on the chosen syntax) and translates it into a corresponding Django `Q` object.
*   **Integration**: This logic needs to be integrated into a custom DRF `FilterBackend`. The backend will:
    1. Extract the filter parameters from the request.
    2. Parse the parameters using the defined logic.
    3. Generate the appropriate `Q` object(s).
    4. Apply the `Q` object to the ViewSet's queryset: `queryset.filter(q_object)`.
*   **Error Handling**: The parser must handle invalid syntax, unknown fields, or invalid operators gracefully, returning appropriate API error responses (e.g., 400 Bad Request).

### 3.4 Filter Definition & Management (Optional - Stored Filters)
*   **If Stored Filters are required:**
    *   **`StoredFilter` Model:**
        *   `name`: (CharField) User-defined name for the filter.
        *   `description`: (TextField, blank=True).
        *   `target_content_type`: (ForeignKey to `ContentType`) The model this filter applies to.
        *   `definition`: (JSONField) Stores the filter structure (fields, operators, values, nested logic) in a defined format (matching the parser's expectation).
        *   `owner`: (ForeignKey to `User`, nullable, blank=True) If filters are user-specific.
        *   `organization`: (ForeignKey to `Organization`, nullable, blank=True) If filters are organization-specific or shared within an org.
        *   `is_public` / `is_shared`: (BooleanField) Flags for sharing.
        *   *Inherit Timestamped/Auditable.*
    *   **Management API**: CRUD API endpoints (e.g., `/api/v1/stored-filters/`) for managing these `StoredFilter` records (restricted by permissions).
    *   **Application API**: Mechanism for API consumers to *apply* a stored filter, likely via a query parameter (e.g., `?apply_filter=my_saved_filter_id` or `?apply_filter_slug=my-saved-filter`). The backend would retrieve the definition from the `StoredFilter` model and apply it.
    *   **Combination**: Decide if stored filters can be combined with ad-hoc query parameter filters in the same request.

### 3.5 Configuration
*   Mechanism to configure *which models/endpoints* support this advanced filtering and *which fields* on those models are allowed to be filtered (to prevent arbitrary filtering on sensitive or unindexed fields). This could be part of the ViewSet definition or a separate configuration registry.

## 4. Technical Requirements

### 4.1 Implementation
*   Develop or integrate a robust parser for the chosen query syntax -> `Q` object translation.
*   Implement a custom DRF `FilterBackend`.
*   (If storing filters) Implement the `StoredFilter` model and its management API/logic.
*   Configure allowed filterable fields per model/endpoint.

### 4.2 Performance
*   **Query Optimization**: The generated `Q` objects must translate to reasonably efficient SQL queries.
*   **Indexing**: **Crucial**. Fields designated as filterable *must* have appropriate database indexes. Complex filters involving multiple fields or relations benefit greatly from composite indexes.
*   **Parser Performance**: The filter string parser itself should be efficient.
*   **Caching**: Consider caching the *parsed* `Q` object structure for frequently used *stored* filters. Caching query *results* is handled by a separate Caching system but is important here.

### 4.3 Security
*   **Input Validation**: Sanitize and validate all input from query parameters to prevent injection attacks or unintended database queries.
*   **Field Restriction**: Enforce the configuration of allowed filterable fields to prevent users from filtering on sensitive or internal data.
*   **Permissions**: Standard model/row-level permissions (view permissions, org scoping) must still be applied *before or after* filtering. Filtering narrows down results the user is *already allowed* to see.
*   **Stored Filter Access**: Secure the API for managing `StoredFilter` records. Control who can create, view, update, delete, or share stored filters.

### 4.4 Integration
*   Integrates with DRF ViewSets via `filter_backends`.
*   Relies on Django ORM and `Q` objects.
*   Integrates with `ContentType` framework.
*   (If storing filters) Integrates with `User`, `Organization` models.
*   Logs relevant actions (filter creation/update/delete) to the `Audit Logging System`.

## 5. Non-Functional Requirements

*   **Scalability**: Handle complex filter queries against large datasets. Scale the storage/retrieval of stored filters if implemented.
*   **Availability**: Filtering capability should be highly available.
*   **Maintainability**: Parser logic and filter configuration should be maintainable.

## 6. Success Metrics

*   API consumers can successfully construct and apply complex/nested filters.
*   Filtering performance meets API latency targets.
*   Accuracy of filtered results.
*   (If storing filters) User satisfaction with saving and reusing filters.

## 7. API Documentation Requirements

*   **Crucial**: **Thoroughly document the chosen query parameter syntax** for constructing nested (`AND`/`OR`) filters and using operators. Provide clear examples.
*   Document which endpoints support advanced filtering.
*   Document the list of filterable fields and allowed operators for each endpoint/model.
*   Document error responses for invalid filter syntax or restricted fields.
*   (If storing filters) Document the API for managing and applying stored filters.

## 8. Testing Requirements

*   **Unit Tests**: Test the filter parser logic extensively with various valid and invalid syntax examples, nested structures, and operators. Test `Q` object generation.
*   **Integration Tests / API Tests**:
    *   Test API list endpoints with a wide range of complex and nested filter query parameters. Verify correctness of results.
    *   Test different operators (`eq`, `contains`, `gte`, `in`, `isnull`, etc.).
    *   Test filtering on related fields.
    *   Test error handling for invalid syntax or filtering on disallowed fields.
    *   Test interaction with pagination and ordering.
    *   Test filtering respects model/row-level permissions and org scoping.
    *   (If storing filters) Test CRUD operations for `StoredFilter` via its API. Test applying stored filters via query parameters. Test permissions for managing/using stored filters.
*   **Performance Tests**: Test list endpoints with complex filters against large datasets to measure query time and identify indexing needs.

## 9. Deployment Requirements

*   Deployment of the custom filter backend code.
*   Migrations for `StoredFilter` model (if implemented).
*   Creation of necessary database indexes for filterable fields **before enabling filtering in production**.
*   Configuration of filterable models/fields.

## 10. Maintenance Requirements

*   Monitor performance of filtered queries; add/tune indexes as needed.
*   Update parser/backend if query syntax evolves or new operators are needed.
*   Maintain configuration of filterable fields.
*   Regular database backups (includes `StoredFilter` data if used).

---

This revised PRD acknowledges the need for complex nested filtering and incorporates the possibility of storing filter definitions, making it a plan for a more advanced filtering system as you requested. The key next step would be to decide on the specific query parameter syntax (Section 3.2) and whether to include the `StoredFilter` model (Section 3.4) in the initial implementation of this system.
### Tagging


# Tagging System Integration - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To provide a standardized system for applying flexible tags (keywords, labels) to various business objects across the ERP system for organization, filtering, and search enhancement.
*   **Scope**: Integration of a tagging library (like `django-taggit`), enabling the association of tags with target models, basic tag management, API exposure for tagging operations, and optional custom fields on tags.
*   **Implementation Strategy**: Utilize the **`django-taggit`** library. Add the `TaggableManager` field to models requiring tagging. Optionally extend the base `Tag` model if custom fields are needed.
*   **Target Users**: All users (applying/filtering by tags), System Administrators (potential tag cleanup), Developers (adding tagging to models).

## 2. Business Requirements

*   **Flexible Organization**: Allow users to apply multiple relevant keywords (tags) to business objects (Products, Documents, Contacts, etc.) for non-hierarchical grouping.
*   **Improved Discoverability**: Enable finding objects based on assigned tags through search and filtering.
*   **User-Driven Categorization**: Allow for emergent categorization through common tag usage.
*   **(Optional)** **Tag Metadata**: Allow storing additional structured information about tags themselves via custom fields if needed.

## 3. Functional Requirements

### 3.1 Tagging Integration (`django-taggit`)
*   **Library**: Integrate `django-taggit`.
*   **Model Integration**: Add `tags = TaggableManager(blank=True)` field to all models that need to be taggable (e.g., `Product`, `Contact`, `Document`, `Organization`).
*   **Core Models (Provided by `django-taggit`)**:
    *   `taggit.models.Tag`: Stores the tag name (unique) and slug.
    *   `taggit.models.TaggedItem`: Generic relation linking a `Tag` to a specific tagged object instance.

### 3.2 `Tag` Model Customization (Optional - for Custom Fields)
*   **If Custom Fields are Required**:
    *   **Requirement**: Need to store additional structured data on the `Tag` itself.
    *   **Implementation**: Create a custom Tag model that inherits from `taggit.models.TagBase` and `taggit.models.GenericTaggedItemBase`, and add the `custom_fields` JSONField to this custom Tag model. Configure `settings.TAGGIT_TAG_MODEL` to point to this custom model.
    *   **`CustomTag` Model Fields**:
        *   Inherits `name` and `slug` from `TagBase`.
        *   **`custom_fields`**: (JSONField, default=dict, blank=True).
        *   *Inherit Timestamped/Auditable if needed on the tag itself.*
*   **If Custom Fields NOT Required**: Use the default `taggit.models.Tag` model.

### 3.3 Custom Field Schema Definition (External Mechanism)
*   Requirement for separate `CustomFieldDefinition` model/mechanism (possibly filtered by a 'Tag' context) if custom fields are added to the `Tag` model.

### 3.4 Tagging Operations via API
*   **Adding/Setting Tags**: When creating or updating a taggable object (e.g., Product) via API, the request payload should accept a list of tag names (strings) for the `tags` field. The serializer/view logic (using `TaggableManager`) will handle creating new `Tag` records if they don't exist and updating the `TaggedItem` associations.
*   **Removing Tags**: Setting an empty list `[]` for the `tags` field typically removes all tags. Specific removal might require custom handling or using specific `TaggableManager` methods.
*   **Listing Tags on an Object**: API endpoints retrieving a taggable object should include its associated list of tag names in the response.
*   **Filtering by Tags**: API list endpoints for taggable models should support filtering by one or more tags (e.g., `?tags__name__in=urgent,customer-a`). `django-filter` integration with `django-taggit` is possible (e.g., using `taggit.managers.TaggableManager.name` in filter fields).

### 3.5 Tag Management (Admin/API)
*   **Viewing Tags**: List all unique tags used in the system (via Django Admin for `Tag` model or a dedicated API endpoint).
*   **Editing Tags**: Editing a `Tag`'s `name` updates it everywhere it's used. Requires admin permissions. Edit `custom_fields` via this interface too, if implemented.
*   **Deleting Tags**: Deleting a `Tag` record automatically removes its association from all tagged items. Restricted to admins, potentially only allowed if the tag is unused.
*   **Merging Tags (Optional)**: Advanced feature - provide an admin action or utility to merge two similar tags (e.g., "product" and "products") into one, reassigning all items.

### 3.6 Out of Scope
*   Tag hierarchy, explicit tag types (beyond free-form strings), tag approval workflows, complex tag relationships, detailed tag analytics dashboards.

## 4. Technical Requirements

### 4.1 Library Integration
*   Install `django-taggit`. Add `'taggit'` to `INSTALLED_APPS`.
*   If using custom `Tag` model, configure `settings.TAGGIT_TAG_MODEL`.
*   Apply `TaggableManager` to relevant models.

### 4.2 Data Management
*   Storage handled by `django-taggit` models (`Tag`, `TaggedItem`) plus custom `Tag` model and JSONField if used.
*   Indexing handled mostly by `django-taggit`. Add **GIN index on `custom_fields`** if querying on tag custom fields is needed.

### 4.3 Security
*   Permissions to *add/remove* tags from an object are typically tied to the `change` permission for that object.
*   Permissions to *manage* the global list of `Tag` records (`add_tag`, `change_tag`, `delete_tag`) should be restricted to administrators. Custom field access control if applicable.
*   Audit logging for tag assignments/removals (via Audit Log entry for the parent object change) and for direct `Tag` model management.

### 4.4 Performance
*   `django-taggit` generally performs well. Querying objects by tag requires joins.
*   Ensure efficient filtering by tags in API list views (library helpers often optimize this).
*   Efficient querying on `custom_fields` needs indexing.

### 4.5 Integration
*   Integrates with any model via `TaggableManager`.
*   Integrates with DRF serializers for input/output of tags.
*   Integrates with `django-filter` for API filtering.
*   Potential API endpoint for listing/managing global tags (`/api/v1/tags/`).
*   Integrates with `CustomFieldDefinition` mechanism if using custom fields on tags.

## 5. Non-Functional Requirements

*   **Scalability**: Handle large numbers of tags and tagged items efficiently.
*   **Availability**: Tagging functionality should be available.
*   **Consistency**: Ensure tag associations are correctly maintained.

## 6. Success Metrics

*   Effective use of tags for organizing and finding objects.
*   Performant tag-based filtering.
*   User satisfaction with the tagging feature.

## 7. API Documentation Requirements

*   Document how to provide/retrieve tags for taggable objects in API requests/responses (e.g., list of strings for the `tags` field).
*   Document API endpoints for filtering by tags (query parameters).
*   Document API endpoint for managing global tags (if implemented).
*   Document handling of tag `custom_fields` (if implemented).
*   Auth/Permission requirements.

## 8. Testing Requirements

*   **Unit Tests**: Test custom `Tag` model if created. Test custom field logic if added.
*   **Integration Tests**:
    *   Test adding, setting, and removing tags from objects via API.
    *   Test retrieving objects and verifying their tags are included.
    *   Test filtering list endpoints by single/multiple tags.
    *   Test permissions related to tagging objects and managing global tags.
    *   Test **saving/validating `custom_fields`** on tags if implemented.
    *   Test Admin interface for tag management.

## 9. Deployment Requirements

*   Install `django-taggit`.
*   Migrations for `taggit` models and any custom `Tag` model/custom fields/indexes.
*   Deployment of `CustomFieldDefinition` mechanism if using custom fields on tags.

## 10. Maintenance Requirements

*   Standard backups. Potential need for tag cleanup/merging by administrators.
*   Management of custom field schemas if applicable.

---
### Workflow

# Workflow/State Machine Integration - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To define the requirements for integrating a state machine or workflow capability into the ERP system, enabling controlled transitions between defined `Status` values for specific business models (e.g., Invoice, Order, Product).
*   **Scope**: Integration of a workflow library (e.g., `django-fsm`), defining state transitions and associated logic for key business models, exposing transition triggers via API, and integrating with status/audit systems. Excludes building a workflow engine from scratch or a visual workflow designer.
*   **Implementation Strategy**: Leverage a suitable Django state machine library (Assumption: **`django-fsm`**). Workflow logic (states, transitions, conditions, actions) will be defined primarily in Python code associated with the target models.
*   **Target Users**: Developers (implementing workflows on models), Business Analysts (defining workflow rules), End Users (interacting with models whose status changes via workflow).

## 2. Business Requirements

*   **Controlled Processes**: Ensure business entities (like Invoices, Orders) move through predefined lifecycle states in a controlled manner (e.g., cannot go directly from 'Draft' to 'Paid').
*   **Process Automation**: Trigger specific actions automatically when an entity transitions between states (e.g., send notification on 'Approved', update inventory on 'Shipped').
*   **Enforce Business Rules**: Allow transitions only when specific conditions are met or required permissions are held.
*   **Visibility**: Provide clear indication of the current status of an entity and potentially the allowed next steps.

## 3. Functional Requirements

### 3.1 State Field Integration
*   **Target Models**: Identify key business models requiring workflow management (e.g., `Invoice`, `PurchaseOrder`, `Product`, `UserRequest`).
*   **Status Field**: These target models must have a `status` field (likely `CharField`) to store the current state. This field will be managed by the workflow library. (Leverages the `Status` model/system for defined values).
*   **Library Integration**: Utilize `@fsm.transition` decorator (or equivalent) from the chosen library (`django-fsm`) on model methods to define allowed transitions.

### 3.2 Transition Definition (in Code)
*   For each target model, define methods decorated with `@fsm.transition`:
    *   **`field`**: Specifies the state field being managed (e.g., `field=status`).
    *   **`source`**: The state(s) the transition is allowed *from* (e.g., `source='draft'`). Can be a list or `*` (any state).
    *   **`target`**: The state the transition moves *to* (e.g., `target='pending_approval'`).
    *   **`conditions` (Optional)**: List of helper functions/methods that must return `True` for the transition to be allowed (e.g., `conditions=[is_total_amount_valid]`).
    *   **`permission` (Optional)**: Function or permission string (`app.codename`) required by the user to execute the transition (e.g., `permission='invoices.can_approve_invoice'`). Integrates with RBAC system.
    *   **Transition Method Body**: Contains the core logic to execute *during* the transition (before the status field is updated). Can perform checks or initial actions.
    *   **Side Effects (`on_error`, Library Signals)**: Implement logic that runs *after* a successful transition (e.g., sending notifications, updating related objects) or if a transition fails. Often done via library-provided signals or hooks.

### 3.3 Triggering Transitions via API
*   **Requirement**: Need API endpoints to trigger allowed state transitions for specific object instances.
*   **Implementation**:
    *   Use DRF's `@action` decorator on the ViewSet for the target model.
    *   Define an action for each logical transition (e.g., `POST /api/v1/invoices/{id}/submit/`, `POST /api/v1/invoices/{id}/approve/`).
    *   The action view will:
        1. Retrieve the object instance.
        2. Check **model-level** permissions for the *action* itself (using standard DRF permissions).
        3. Call the corresponding transition method on the model instance (e.g., `invoice.submit(user=request.user)`). The `@fsm.transition` decorator handles the permission/condition checks defined on the transition.
        4. Handle potential `TransitionNotAllowed` exceptions from the library, returning appropriate API errors (e.g., 400 Bad Request or 403 Forbidden).
        5. Return a success response, potentially with the updated object including the new status.

### 3.4 Status Information API
*   The standard GET endpoint for the target model (`/api/v1/invoices/{id}/`) should return the current `status`.
*   *(Optional)* Consider an API action (`/api/v1/invoices/{id}/available-transitions/`) that inspects the object's current state and uses library helpers (like `get_available_user_transitions`) to return a list of transitions the *current user* is permitted to trigger. Useful for driving UI buttons.

### 3.5 Audit Logging Integration
*   **Requirement**: Log successful state transitions.
*   **Implementation**: Implement a signal receiver (e.g., for `django-fsm`'s `post_transition` signal) that creates an `AuditLog` entry recording the user, object, `from_state`, `to_state`, and timestamp.

### 3.6 Out of Scope
*   Building a visual workflow designer/editor.
*   Database storage of workflow *definitions* (definitions primarily live in Python code with `django-fsm`). More complex libraries like `django-viewflow` might store definitions differently.
*   Complex BPMN features (gateways, timers, etc.) unless supported by the chosen library and explicitly required.

## 4. Technical Requirements

### 4.1 Library Integration
*   Install and configure the chosen workflow library (e.g., `pip install django-fsm`).
*   Follow library documentation for model integration (`FSMField` or decorators) and signal handling.

### 4.2 Performance
*   Transition logic (conditions, actions, side effects) should be reasonably efficient.
*   Permission checks within transitions should leverage the cached RBAC system.
*   Fetching available transitions should be performant.

### 4.3 Security
*   Transition methods must reliably check permissions using the integrated RBAC system.
*   Ensure API actions triggering transitions are properly protected.
*   Audit logging of transitions is essential.

### 4.4 Data Consistency
*   State transitions should ideally occur within database transactions if they involve multiple model updates as side effects. `django-fsm` typically updates the state field within the transition method's transaction.

## 5. Non-Functional Requirements

*   **Reliability**: State transitions should execute reliably and consistently.
*   **Maintainability**: Workflow definitions (transitions, conditions, actions in code) should be clear and maintainable.
*   **Testability**: Workflows must be easily testable.

## 6. Success Metrics

*   Successful enforcement of defined state transition rules.
*   Successful execution of automated actions triggered by transitions.
*   Correct logging of status changes in the Audit Log.
*   Developer/Admin satisfaction with defining and managing workflows for models.

## 7. API Documentation Requirements

*   Document the `status` field on relevant models and its possible values.
*   Document the specific API `@action` endpoints used to trigger transitions (e.g., `POST /submit/`, `POST /approve/`).
*   Specify required permissions for each transition endpoint.
*   Document the optional `/available-transitions/` endpoint if implemented.
*   Document error responses related to forbidden or invalid transitions.

## 8. Testing Requirements

*   **Unit Tests**:
    *   Test individual transition methods on models: mock conditions/permissions, verify state changes, check for `TransitionNotAllowed` exceptions when conditions/permissions fail.
    *   Test condition functions.
    *   Test side-effect/action logic.
*   **Integration Tests / API Tests**:
    *   Test calling the API transition actions (`POST /submit/`, etc.) with users having correct/incorrect permissions. Verify state changes and appropriate HTTP responses (2xx, 400, 403).
    *   Test sequences of transitions.
    *   Test that transitions fail if prerequisite conditions are not met.
    *   Verify Audit Log entries are created for successful transitions.
    *   Test the `/available-transitions/` endpoint if implemented.

## 9. Deployment Requirements

*   Ensure chosen workflow library is installed in all environments.
*   Migrations for any changes to models (e.g., adding the `status` field).
*   Ensure initial states for existing data are set correctly if applying workflows retrospectively.

## 10. Maintenance Requirements

*   Update workflow definitions (code) as business processes evolve.
*   Keep the workflow library updated.
*   Monitor Audit Logs related to transitions.

---
### Automation


# Automation Rule Engine - Product Requirements Document (PRD) - Revised

## 1. Overview

*   **Purpose**: To define a system for creating, managing, and executing **configurable automation rules** within the ERP. These rules allow for automated actions (including CRUD operations on data) based on **data change events** (Create/Update/Delete) or **time-based schedules**, subject to complex, potentially cross-model **conditions**.
*   **Scope**: Definition of models to store automation rules (`AutomationRule`, `RuleCondition`, `RuleAction`), integration with Django signals and a scheduler (Celery Beat) for triggering, a condition evaluation engine supporting cross-model checks and AND/OR logic, execution of predefined actions (including CRUD) via Celery, detailed execution logging, and API endpoints for rule management by authorized users.
*   **Implementation Strategy**: Involves concrete Django Models (`AutomationRule`, `RuleCondition`, `RuleAction`, `AutomationLog`). Relies on **Django Signals** for event triggers, **Celery Beat** integration for scheduled triggers, **Celery** for asynchronous condition evaluation and action execution. Requires a robust condition evaluation engine and predefined, registered action functions.
*   **Target Users**: System Administrators, Power Users (with appropriate permissions), Developers (defining available actions, ensuring system integrity).

## 2. Business Requirements

*   **Automate Business Processes**: Trigger sequences of actions automatically based on data events or schedules to streamline workflows and reduce manual effort.
*   **Enforce Complex Business Rules**: Implement conditional logic based on data across multiple related entities to ensure policies are followed or necessary steps are taken.
*   **Cross-Module Coordination**: Enable automation that spans different parts of the ERP (e.g., confirming a Sales Order triggers Project creation).
*   **Configurability via API**: Allow authorized administrators/users to define, manage, and monitor automation rules through API endpoints.
*   **Scheduled Operations**: Automate routine tasks or checks based on time schedules (daily, weekly, monthly, etc.).
*   **Reliability & Transparency**: Ensure automations execute reliably and provide detailed logs for tracking and troubleshooting.

## 3. Functional Requirements

### 3.1 Core Models
*   **`AutomationRule` Model**:
    *   **Purpose**: Defines a single automation rule.
    *   **Inheritance**: `Timestamped`, `Auditable`, `OrganizationScoped`.
    *   **Fields**:
        *   `name`: (CharField, max_length=255) Unique name for the rule within the organization.
        *   `description`: (TextField, blank=True).
        *   `trigger_type`: (CharField with choices: 'MODEL_EVENT', 'SCHEDULED').
        *   `trigger_source_content_type`: (ForeignKey to `ContentType`, null=True, blank=True) The model whose events trigger this rule (used if `trigger_type` is 'MODEL_EVENT').
        *   `trigger_event`: (CharField with choices: 'CREATED', 'UPDATED', 'DELETED', blank=True) The type of model event (used if `trigger_type` is 'MODEL_EVENT').
        *   `schedule`: (CharField, max_length=100, blank=True) Crontab-like schedule string (e.g., '0 2 * * *' for 2 AM daily) (used if `trigger_type` is 'SCHEDULED'). Requires validation.
        *   `condition_logic`: (CharField with choices: 'ALL_MET' (AND), 'ANY_MET' (OR), default='ALL_MET') How conditions are combined. *(Advanced: Could be JSON for nested logic)*.
        *   `is_active`: (BooleanField, default=True, db_index=True) Enable/disable the rule.
        *   `execution_delay_seconds`: (PositiveIntegerField, default=0) Optional delay before executing actions (handled via Celery `countdown`).
*   **`RuleCondition` Model**:
    *   **Purpose**: Defines a condition to be evaluated. Multiple conditions linked via `AutomationRule.condition_logic`.
    *   **Inheritance**: `Timestamped`, `Auditable`.
    *   **Fields**:
        *   `rule`: (ForeignKey to `AutomationRule`, on_delete=models.CASCADE, related_name='conditions')
        *   `field_name`: (CharField) Field to check on the triggering object or a related object (using `__` notation, e.g., `status`, `order__customer__category`, `triggering_object__related_invoice__total`). **Must support related lookups**.
        *   `operator`: (CharField with choices: 'EQ', 'NEQ', 'GT', 'GTE', 'LT', 'LTE', 'CONTAINS', 'ICONTAINS', 'IN', 'NOTIN', 'ISNULL', 'ISNOTNULL', 'CHANGED_TO', 'CHANGED_FROM') Comparison operator. *(`CHANGED_TO`/`FROM` require passing old/new state)*.
        *   `value`: (JSONField) The value to compare against (stores string, number, boolean, list).
*   **`RuleAction` Model**:
    *   **Purpose**: Defines an action to perform if conditions are met. Executes sequentially based on `order`.
    *   **Inheritance**: `Timestamped`, `Auditable`.
    *   **Fields**:
        *   `rule`: (ForeignKey to `AutomationRule`, on_delete=models.CASCADE, related_name='actions')
        *   `action_type`: (CharField, db_index=True) Code identifying the registered action function (e.g., 'update_field', 'send_notification', 'create_record', 'update_related_record', 'delete_record', 'call_webhook').
        *   `parameters`: (JSONField, default=dict, blank=True) Configuration/parameters for the action (e.g., `{"target_model": "app.Model", "data": {"field1": "value1", ...}}` for create/update, `{"notification_type": "...", ...}` for notify).
        *   `order`: (PositiveSmallIntegerField, default=0) Order of execution.
*   **`AutomationLog` Model**:
    *   **Purpose**: Tracks execution history and detailed state.
    *   **Inheritance**: `Timestamped`, `Auditable`, `OrganizationScoped`.
    *   **Fields**:
        *   `rule`: (ForeignKey to `AutomationRule`, on_delete=models.SET_NULL, null=True).
        *   `trigger_type`: (CharField: 'MODEL_EVENT', 'SCHEDULED').
        *   `trigger_content_type`, `trigger_object_id`: (FK to ContentType, Char/Int Field) Triggering object details (if applicable).
        *   `status`: (CharField: 'PENDING', 'EVALUATING', 'CONDITIONS_MET', 'CONDITIONS_NOT_MET', 'ACTIONS_QUEUED', 'ACTION_RUNNING', 'ACTION_FAILED', 'COMPLETED', 'FAILED', default='PENDING').
        *   `execution_start_time`, `execution_end_time`: (DateTimeField, nullable).
        *   `condition_results`: (JSONField, null=True) Stores outcome of condition checks.
        *   **`action_logs`**: (JSONField, default=list, blank=True) **Crucial for State Tracking (#5)**. List of dicts, each detailing an action step: `{"action_order": 0, "action_type": "update_field", "parameters": {...}, "status": "SUCCESS"|"FAILURE", "timestamp": "...", "message": "...", "state_before": {...}, "state_after": {...}}`. *(Storing before/after state can be complex/verbose)*.
        *   `error_message`: (TextField, blank=True) Overall error if job failed.
        *   `celery_task_id`: (CharField, nullable).

### 3.2 Trigger Mechanisms
*   **Model Events (Signals)**: Generic signal receivers (`post_save`, `post_delete`) query active `AutomationRule`s matching the sender model and event type, then queue `evaluate_automation_rule` Celery task. Receivers must efficiently pass necessary context (instance PK, content_type ID, potentially changed fields map, user ID).
*   **Scheduled Events (Celery Beat)**:
    1.  A periodic Celery Beat task runs (e.g., every minute).
    2.  It queries `AutomationRule`s where `trigger_type='SCHEDULED'`.
    3.  For each rule whose `schedule` matches the current time (using a crontab parsing library), it queues the `evaluate_automation_rule` Celery task (passing rule ID, maybe current time as context, no specific trigger object). Conditions for scheduled tasks often check date ranges or aggregated data.

### 3.3 Rule Evaluation & Action Execution (Celery Task)
*   Implement `evaluate_automation_rule(rule_id, trigger_context)` Celery task.
*   **Context**: Contains triggering object info (if any), triggering user (if any), potentially changed fields map.
*   **Logic**:
    1.  Log start in `AutomationLog` ('PENDING'/'EVALUATING').
    2.  Fetch `AutomationRule`, `instance` (if applicable).
    3.  **Evaluate Conditions**: Iterate through `RuleCondition`s. Implement robust evaluator handling `field_name` lookups (direct and `__` related), all specified `operator`s, and type-safe comparisons against `value`. Combine results using `rule.condition_logic` (AND/OR). Log condition results to `AutomationLog.condition_results`.
    4.  If conditions fail, update `AutomationLog` ('CONDITIONS_NOT_MET'), return.
    5.  If conditions pass, update `AutomationLog` ('CONDITIONS_MET'/'ACTIONS_QUEUED').
    6.  Iterate through `RuleAction`s by `order`. For each:
        *   Update `AutomationLog` ('ACTION_RUNNING' + action details).
        *   Lookup registered action function via `action_type`.
        *   *(Optional/Complex)* Capture relevant `state_before`.
        *   Execute action function, passing `instance` (if applicable), `parameters`, `user`.
        *   Capture `state_after` (if applicable), result/message, success/failure.
        *   Log action details, status, message, state changes into `AutomationLog.action_logs`.
        *   If an action fails, stop processing further actions for this rule instance, set overall `AutomationLog` status to 'FAILED', log error.
    7.  If all actions succeed, set `AutomationLog` status to 'COMPLETED'.

### 3.4 Available Actions (Predefined & Registered)
*   Requires a registry mapping `action_type` strings to Python functions.
*   **Must include CRUD:**
    *   `create_record(parameters, trigger_context)`: Creates a new record. `parameters` specify model type and field data (can use values from trigger context).
    *   `update_record(parameters, trigger_context)`: Updates fields on the triggering record OR a related record found via lookup defined in `parameters`.
    *   `delete_record(parameters, trigger_context)`: Deletes the triggering record OR a related record.
*   **Other essential actions:**
    *   `send_notification(parameters, trigger_context)`
    *   `call_webhook(parameters, trigger_context)`
*   *Developers add new reusable actions to the registry.*

### 3.5 Management & Monitoring API (#3 In Scope)
*   Provide RESTful API endpoints for **authorized users** to perform CRUD operations on `AutomationRule`, `RuleCondition`, `RuleAction`.
*   API for listing/retrieving `AutomationLog` records (filter by rule, status, date, triggering object). Include detailed `action_logs`.
*   Endpoints should enforce permissions (e.g., only admins or specific roles can manage rules).

## 4. Technical Requirements

### 4.1 Libraries & Infrastructure
*   Requires **Celery** and message broker.
*   Requires **Celery Beat** (or other scheduler) for scheduled triggers.
*   Relies on Django Signals, `ContentType`.
*   Needs a crontab parsing library (e.g., `python-crontab`, `croniter`).

### 4.2 Condition Engine
*   Implement a robust function to evaluate conditions, safely handling field lookups (`instance.related__field`) and various operators/types defined in `RuleCondition`. Handle potential `DoesNotExist` errors during related lookups gracefully. Support AND/OR combination based on `AutomationRule.condition_logic`.

### 4.3 Action Registry & Execution
*   Implement a pattern (e.g., Python dictionary, class registry) to map `RuleAction.action_type` strings to executable Python functions.
*   Action functions must accept standard arguments (like `parameters`, `trigger_context`) and handle their own logic, including database operations or external calls. They should return success/failure status and messages.

### 4.4 Security
*   Secure the Rule Management API endpoints with appropriate permissions.
*   Action execution context: Decide if actions run with system privileges or impersonate the triggering user. Impersonation is complex but often safer. System privileges require careful validation within actions to prevent unauthorized data access/modification.
*   Validate `field_name` lookups in conditions to prevent accessing unintended data.
*   Sanitize parameters passed to actions, especially for `call_webhook`.
*   Audit logging of rule definition changes and rule executions (`AutomationLog`).

### 4.5 Performance & Scalability
*   Efficient querying for active rules upon signal triggers.
*   Condition evaluation must be performant. Avoid very complex related lookups in conditions if possible.
*   Action execution via Celery allows scaling workers.
*   `AutomationLog` table can grow large; requires indexing and potentially partitioning/archiving strategy.

## 5. Non-Functional Requirements

*   Scalability (handle many rules, frequent triggers, many actions).
*   Reliability (ensure rules trigger, conditions evaluate correctly, actions run, errors handled).
*   Availability (Engine depends on Celery, Broker, DB).
*   Maintainability (Rule definitions, action functions, engine logic).

## 6. Success Metrics

*   High success rate for rule executions.
*   Measurable reduction in manual tasks corresponding to automated rules.
*   Performance of trigger handling, condition evaluation, and action execution within acceptable limits.
*   Administrators can successfully define and manage required automations via API.

## 7. API Documentation Requirements

*   Document models (`AutomationRule`, `RuleCondition`, `RuleAction`, `AutomationLog` including `action_logs` structure).
*   Document **API endpoints for managing rules/conditions/actions**. Detail payload structure for creation/update.
*   Document API endpoint for querying `AutomationLog` history.
*   Document available `trigger_event` types, condition `operator`s, registered `action_type`s and their required `parameters`.
*   Document schedule format (e.g., standard crontab).
*   Document permissions required for management APIs.

## 8. Testing Requirements

*   **Unit Tests**: Test condition evaluation logic extensively (all operators, related lookups, AND/OR). Test individual action functions (mocking DB/external calls). Test Celery task logic (mocking rule loading, evaluation, action calls). Test crontab parsing/matching.
*   **Integration Tests**:
    *   Requires Celery worker/beat (or eager mode).
    *   Test signal-triggered rules: Modify models, verify correct task queued, conditions evaluated correctly (met/not met), actions executed (verify side effects), `AutomationLog` updated accurately (including `action_logs` detail).
    *   Test schedule-triggered rules: Advance time (using libraries like `freezegun`), verify Celery Beat queues task, verify rule execution and logging.
    *   Test API endpoints for Rule CRUD: Create complex rules with conditions/actions via API, verify they are saved correctly.
    *   Test API endpoint for querying `AutomationLog`.
    *   Test permission enforcement on management APIs.
    *   Test various failure scenarios (condition fail, action fail) and check `AutomationLog`.
*   **Performance/Load Tests**: Simulate high frequency triggers to test system throughput.

## 9. Deployment Requirements

*   Migrations for automation models & indexes.
*   Deployment of Celery workers and Celery Beat service.
*   Deployment of registered action functions.
*   Secure configuration for action parameters (e.g., webhook URLs/secrets).
*   Initial setup of any default/required automation rules.

## 10. Maintenance Requirements

*   Monitor Celery queues, Beat schedule, worker health.
*   Monitor `AutomationLog` for failures and performance issues.
*   Maintain/update rule definitions via API/Admin as business processes change.
*   Develop and register new action functions as needed.
*   Manage `AutomationLog` size (archiving/pruning). Standard backups.

---