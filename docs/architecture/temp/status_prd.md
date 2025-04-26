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
