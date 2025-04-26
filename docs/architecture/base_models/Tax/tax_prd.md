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