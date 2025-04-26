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
