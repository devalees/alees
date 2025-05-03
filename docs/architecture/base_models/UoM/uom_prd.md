Understood. Using a separate `UomType` model provides better structure, allows adding descriptions or other metadata to the types themselves, and is generally more scalable than hardcoding choices.

Let's update the `UnitOfMeasure` PRD and Implementation Steps to reflect the decision to use a dedicated `UomType` model.

---

## Updated: `uom_prd.md` (Using `UomType` Model)

# Unit of Measure (UoM) System - Product Requirements Document (PRD)

## 1. Overview

*   **Purpose**: To define a standardized system for representing distinct Units of Measure (UoM) and their classifications (UoM Types) within the ERP system.
*   **Scope**: Definition of the `UomType` model (e.g., Length, Mass, Count) and the `UnitOfMeasure` model (e.g., KG, M, EA), their core attributes, relationship, status, and custom field capability. Acknowledges the need for, but separates the detailed implementation of, unit conversion factors and logic.
*   **Implementation**: Defined as concrete Django Models (`UomType`, `UnitOfMeasure`). Both should inherit standard base models like `Timestamped`, `Auditable`. Uses `JSONField` for custom fields.
*   **Target Users**: Inventory Managers, Product Managers, Purchasing/Sales Staff, Developers (referencing UoMs), System Administrators.

## 2. Business Requirements

*   **Standardized Units & Types**: Provide a consistent and predefined list of measurement types (Length, Mass, etc.) and the specific units within each type.
*   **Consistency**: Ensure uniform use of UoMs in product specifications, inventory tracking, pricing, ordering, and manufacturing.
*   **Foundation for Conversion**: Provide the necessary unit definitions and **type groupings** to support subsequent unit conversion calculations (which should only occur between units of the *same type*).
*   **Extensibility**: Allow administrators to define custom or industry-specific units/types and add dynamic attributes via custom fields.

## 3. Functional Requirements

### 3.1 `UomType` Model Definition (NEW)
*   **Purpose**: Classifies the type of measurement (dimensionality). Critical for conversion logic.
*   **Inheritance**: Should inherit `Timestamped`, `Auditable`.
*   **Fields**:
    *   `code`: (CharField/SlugField, max_length=50, primary_key=True) Unique code for the type (e.g., 'LENGTH', 'MASS', 'COUNT'). **Primary Key**.
    *   `name`: (CharField, max_length=100, unique=True) Human-readable name (e.g., "Length", "Mass", "Count/Each").
    *   `description`: (TextField, blank=True) Optional explanation.
    *   `is_active`: (BooleanField, default=True, db_index=True).
    *   **`custom_fields`**: (JSONField, default=dict, blank=True).
*   **Meta**: `verbose_name`, `plural`, `ordering`.
*   **String Representation**: Return `name`.
*   **Management**: CRUD via Admin/API (restricted). Initial types loaded via migration. Deletion protected if referenced by `UnitOfMeasure`.

### 3.2 `UnitOfMeasure` Model Definition (Revised)
*   **Inheritance**: Should inherit `Timestamped`, `Auditable`.
*   **Fields**:
    *   `code`: (CharField, max_length=20, primary_key=True) Unique code for the unit (e.g., 'M', 'KG', 'EA'). **Primary Key**.
    *   `name`: (CharField, max_length=100, unique=True) Full name (e.g., "Meter", "Kilogram", "Each").
    *   `uom_type`: (**ForeignKey to `UomType`**, `on_delete=models.PROTECT`, related_name='units') **Required**. Links the unit to its measurement type.
    *   `symbol`: (CharField, max_length=10, blank=True) Common symbol (e.g., 'm', 'kg').
    *   `is_active`: (BooleanField, default=True, db_index=True).
    *   **`custom_fields`**: (JSONField, default=dict, blank=True).
*   **Meta**: `verbose_name`, `plural`, `ordering` (e.g., `['uom_type__name', 'name']`).
*   **String Representation**: Return `name` or `code`.

### 3.3 Custom Field Schema Definition (External Mechanism)
*   Requirement for separate `CustomFieldDefinition` mechanism if custom fields are used on `UomType` or `UnitOfMeasure`.

### 3.4 Data Management & Operations
*   **CRUD**: Admin/API for `UomType` and `UnitOfMeasure`. Includes managing `custom_fields`.
*   **Deletion Constraints**: `UomType` protected by `UnitOfMeasure`. `UnitOfMeasure` protected by referencing models (Products, etc.). Deactivation (`is_active=False`) preferred.
*   **Validation**: Unique constraints. FK constraints. Custom field validation.
*   **Initial Data**: Populate common `UomType`s and `UnitOfMeasure`s via data migration.

### 3.5 Relationship with Other Models
*   `UnitOfMeasure.uom_type` links to `UomType`.
*   Other models (e.g., `Product`) use a `ForeignKey` to `UnitOfMeasure` (with `on_delete=PROTECT`).

### 3.6 Unit Conversion (Separate Concern)
*   Remains a separate concern, but the `uom_type` link is now the primary way to determine which units *can* be converted between each other.

### 3.7 Out of Scope for this PRD
*   Unit conversion engine/factors, complex conversions, conversion history.

## 4. Technical Requirements

### 4.1 Data Management
*   Storage/Indexing for both models. **GIN index for `custom_fields`** if needed. Initial population via migration.

### 4.2 Security
*   Restrict management of `UomType` and `UnitOfMeasure` (including `custom_fields`) to Admin roles. Audit CRUD via Audit System.

### 4.3 Performance
*   High performance for lookups by `code` (PK). Efficient listing.

### 4.4 Integration
*   `UnitOfMeasure` is target for FKs. Both models provide data for Conversion logic. Optional read-only APIs. Integrates with `CustomFieldDefinition`.

## 5. Non-Functional Requirements

*   Availability, Data Consistency, Accuracy, Backup/Recovery.

## 6. Success Metrics

*   Accurate representation/classification of UoMs/Types. Successful referencing by dependent modules. Successful use by conversion mechanism.

## 7. API Documentation Requirements (If API Endpoints implemented)

*   Document `UomType` and `UnitOfMeasure` models/fields (incl. `custom_fields`). Document relationship. Document read-only APIs.

## 8. Testing Requirements

*   Unit Tests (Both models, constraints, relationships, `custom_fields`). Data Tests (Initial population). Integration Tests (Admin/API CRUD, FK protection, permissions, `custom_fields`).

## 9. Deployment Requirements

*   Migrations for both tables, indexes. Initial data population migration. `CustomFieldDefinition` mechanism deployment.

## 10. Maintenance Requirements

*   Admin management. Backups. Custom field schema management.

