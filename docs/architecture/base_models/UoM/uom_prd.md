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