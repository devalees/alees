
# Organization Base Model - Product Requirements Document (PRD)

## 1. Overview
- **Purpose**: To define the core `Organization` entity, providing a flexible and scalable foundation for managing organizational units, their structures, attributes, and relationships within the ERP system.
- **Scope**: Definition, attributes, hierarchy, relationships, custom fields, and management of `Organization` entities. This model serves as the anchor point for the `OrganizationScoped` multi-tenancy mechanism.
- **Implementation**: Defined as a concrete Django Model. It **must** inherit the `Timestamped` and `Auditable` Abstract Base Models. It will also utilize `django-mptt` for hierarchy and `django-taggit` for tags.
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
    - `status`: (CharField with choices) e.g., 'Active', 'Inactive', 'Archived'. (Indexed). References `Status.slug`.
    - `parent`: (TreeForeignKey to `self`, managed by `django-mptt`) Defines the primary hierarchical parent. `on_delete=PROTECT`.
    - `effective_date`: (DateField/DateTimeField, null=True, blank=True) Date the organization unit becomes active/valid.
    - `end_date`: (DateField/DateTimeField, null=True, blank=True) Date the organization unit ceases to be active/valid.
- **Contact Information**: (ForeignKey to `Contact` model, `on_delete=models.SET_NULL`, `null=True`, `blank=True`, related_name='primary_for_organizations') Primary contact person.
- **Address Details**: (ForeignKey to `Address` model, `on_delete=models.SET_NULL`, `null=True`, `blank=True`, related_name='primary_for_organizations') Primary address.
- **Localization**:
    - `timezone`: (CharField, using standard timezone names) Default timezone.
    - `currency`: (ForeignKey to `Currency` model, `on_delete=models.PROTECT`, `null=True`, `blank=True`) Default operating currency.
    - `language`: (CharField with choices) Default language preference.
- **Metadata & Classification**:
    - `tags`: (TaggableManager via `django-taggit`, blank=True) For flexible categorization.
    *   `metadata`: (JSONField, default=dict, blank=True) For storing other structured or unstructured metadata specific to the organization.

### 3.2 Organization Types (Reference)
- Relies on the separate `OrganizationType` model via the `organization_type` ForeignKey.

### 3.3 Organization Structure & Relationships
- **Primary Hierarchy**: Managed via the `parent` TreeForeignKey and `django-mptt`.
- **Other Relationships**: Handled by separate linking models if required.

### 3.4 Custom Fields
- **Implementation**: Use a `custom_fields` **JSONField** on the `Organization` model (default=dict, blank=True).
- **Schema Definition**: Relies on the external `CustomFieldDefinition` mechanism to define schema.
- **Functionality**: Store/retrieve values. Validate against schema (logic in Serializers/Forms). Allow querying/filtering (requires DB index).

### 3.5 History Tracking & Auditing
- **Requirement**: Track significant changes to `Organization` records.
- **Implementation**: Captured via `Auditable` mixin and logged by the central **`Audit Logging System`**. Changes to key fields (name, status, parent, type, custom fields diffs) should trigger audit logs.

### 3.6 Operations
- **CRUD**: API endpoints/Admin UI for CRUD (soft delete via `status`).
- **Hierarchy Management**: API actions/Admin UI for moving organizations (changing `parent`).

## 4. Technical Requirements

### 4.1 Performance
- **Hierarchy Queries**: Leverage `django-mptt`.
- **Attribute Queries**: Index core fields.
- **Custom Field Queries**: Requires DB GIN index on `custom_fields`.
- **Scalability**: Support thousands of records. Caching for static data.

### 4.2 Security
- **Access Control**:
    - Utilize the **Organization-Aware RBAC System**.
    - Permissions (`view_organization`, `add_organization`, `change_organization`, `delete_organization`) are checked based on the user's role within the relevant organization context (typically derived from `OrganizationMembership`).
    - Specific actions like changing hierarchy may require distinct permissions (e.g., `change_organization_hierarchy`).
    - **No separate field-level permission checks.** Access to all model fields (including `custom_fields`) is granted if the user has the required model-level permission (e.g., `change_organization`) within the organizational context.
- **Audit Logging**: Ensure changes trigger logs in the central `Audit Logging System`.

### 4.3 Integration
- **API Endpoints**: Comprehensive RESTful APIs for `/organizations/` (CRUD), hierarchy actions. Handle custom fields.
- **Dependency APIs**: Relies on APIs for `/organization-types/`, `/currencies/`, `/addresses/`, `/contacts/`, `/custom-field-definitions/`.
- **Webhook Support**: Trigger webhooks on Organization lifecycle events.
- **Import/Export**: Mechanisms for bulk import/export.
- **Module Integration**: Target for ForeignKeys from `OrganizationScoped` models, `User` (via `OrganizationMembership`), `Contact` (optional link), etc.

## 5. Non-Functional Requirements
- Scalability, High Availability, Data Consistency, Backup and Recovery, Compliance.

## 6. Success Metrics
- API Performance, Data Integrity, User Satisfaction, Scalability, Adoption as scoping foundation.

## 7. API Documentation Requirements
- Document `Organization` model fields (incl. `custom_fields`, `metadata`, `tags`).
- Document API endpoints (CRUD, hierarchy actions).
- Document how to provide/update nested/related data (`tags`, `custom_fields`).
- **Explicitly state that permissions (`view`, `add`, `change`, `delete`) are required and checked within the organizational context.**
- Document error codes.
- Document how to discover custom field schemas (if applicable).

## 8. Testing Requirements
- **Unit Tests**: Model validation, defaults, `__str__`, MPTT setup.
- **Integration Tests / API Tests**:
    - Test API CRUD operations.
    - Test hierarchy actions.
    - Test filtering/searching.
    - Test saving/validating `custom_fields`, `metadata`, `tags`.
    - **Test Permission Enforcement:** Verify users can only perform actions (view, add, change, delete) based on their **model-level permissions granted via `OrganizationMembership`** for the relevant organization(s). Test users without appropriate membership/permissions are denied (403). Test superuser access.
    - Test nullability handling for optional FKs (contact, address, currency).

## 9. Deployment Requirements
- Migrations (table, MPTT fields, FKs, indexes). MPTT library installed. Dependencies migrated. Initial Org Types populated.
- Deployment of `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements
- Standard backups. MPTT tree maintenance (`rebuild` command if needed). Admin management.
- Management of custom field schemas.
