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