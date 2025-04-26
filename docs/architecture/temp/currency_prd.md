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