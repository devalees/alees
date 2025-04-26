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