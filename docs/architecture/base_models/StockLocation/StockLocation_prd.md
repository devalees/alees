

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