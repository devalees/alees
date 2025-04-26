# Generic Category Model - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To define a standardized, hierarchical model for creating and managing various category structures used to classify different entities (e.g., Products, Documents, Assets) across the ERP system.
*   **Scope**: Definition of a generic `Category` data model supporting hierarchy, core attributes, type differentiation, custom fields, and basic management.
*   **Implementation**: Defined as a concrete Django Model using `django-mptt` for hierarchy. It should inherit `Timestamped`, `Auditable`. Uses a `JSONField` for custom fields.
*   **Target Users**: Product Managers, Content Managers, System Administrators, Developers (linking entities to categories).

## 2. Business Requirements

*   **Flexible Classification**: Allow grouping and classification of various ERP entities (Products, Documents, etc.) using consistent, hierarchical structures.
*   **Hierarchical Organization**: Support nested categories (trees) with parent-child relationships.
*   **Support Multiple Uses**: Accommodate different types of categorization needs via a `category_type` discriminator.
*   **Extensibility**: Allow adding specific dynamic attributes to categories via custom fields.
*   **Foundation for Filtering/Reporting**: Enable filtering, searching, and reporting based on assigned categories.

## 3. Functional Requirements

### 3.1 `Category` Model Definition
*   **Inheritance**: Must inherit `Timestamped`, `Auditable`, and `mptt.models.MPTTModel`.
*   **Fields**:
    *   `name`: (CharField, max_length=255) Human-readable name of the category.
    *   `slug`: (SlugField, max_length=255, unique=True, blank=True) A unique URL-friendly identifier. Auto-populated from name if blank. *(Alternatively, use a `code` field if non-slug identifiers are needed)*.
    *   `description`: (TextField, blank=True) Optional description.
    *   `parent`: (TreeForeignKey to `self`, on_delete=models.CASCADE, null=True, blank=True, related_name='children') Managed by `django-mptt`. Defines the parent in the hierarchy. `CASCADE` delete means deleting a parent deletes its children. *(Consider `PROTECT` if children should prevent parent deletion)*.
    *   `category_type`: (CharField, max_length=50, db_index=True) **Required**. Discriminator field indicating the type of hierarchy this category belongs to (e.g., 'PRODUCT', 'DOCUMENT_TYPE', 'ASSET_TYPE', 'ORG_COST_CENTER'). *(Consider using choices or a FK to a simple `CategoryType` model)*.
    *   `is_active`: (BooleanField, default=True, db_index=True) Allows deactivating categories without deletion.
    *   **`custom_fields`**: (JSONField, default=dict, blank=True) Stores values for dynamically defined custom fields relevant to the category definition itself.
*   **MPTT Meta**: `class MPTTMeta: order_insertion_by = ['name']`.
*   **Model Meta**:
    *   `verbose_name = "Category"`
    *   `verbose_name_plural = "Categories"`
    *   `unique_together = ('parent', 'name', 'category_type')` (Ensure name is unique within the same parent and type).
*   **String Representation**: `__str__` method should typically return the `name`. Consider indenting based on level for admin display.

### 3.2 Custom Field Schema Definition (External Mechanism)
*   **Requirement**: If custom fields are used, a separate mechanism (e.g., `CustomFieldDefinition` model, possibly filtered by `Category.category_type`) is needed to define their schema.
*   **Schema Attributes**: Defines key, label, type, validation, choices, etc.

### 3.3 Data Management & Operations
*   **CRUD Operations**: Ability to Create, Read, Update, Deactivate (`is_active=False`), and potentially Delete categories (via Admin UI and API). Note `on_delete` behavior for `parent`. Includes managing `custom_fields` data.
*   **Hierarchy Management**: Ability to change the `parent` of a category to restructure the tree (provided by `django-mptt` admin features or specific API actions).
*   **Validation**: Unique constraints (`slug`, `unique_together`). Basic field validation. Custom field validation against schema (in Serializer/Form). Prevent creating circular dependencies (handled by `django-mptt`).
*   **Initial Data**: Might require initial setup of root categories for different `category_type`s via migration.

### 3.4 Relationship with Other Models
*   This `Category` model will be linked *to* by other models that need classification.
*   Examples:
    *   `Product` might have `category = ForeignKey(Category, on_delete=models.PROTECT, limit_choices_to={'category_type': 'PRODUCT'}, related_name='products')` or `categories = ManyToManyField(Category, limit_choices_to={'category_type': 'PRODUCT'}, related_name='products')`.
    *   `Document` might have `document_type = ForeignKey(Category, on_delete=models.PROTECT, limit_choices_to={'category_type': 'DOCUMENT_TYPE'})`.
*   Use `limit_choices_to` on the ForeignKey/ManyToManyField in the referencing model to ensure only categories of the correct `category_type` can be assigned.

### 3.5 Custom Field Validation
*   **Requirement**: Data saved to `Category.custom_fields` must be validated against the corresponding schema.
*   **Implementation**: Logic in API Serializers or Forms.

### 3.6 Out of Scope for this Model/PRD
*   Complex cross-category relationships or categorization rules beyond simple assignment.
*   Detailed history of category usage by entities (tracked via Audit Log of entity changes).

## 4. Technical Requirements

### 4.1 Data Management
*   **Storage**: Standard fields + JSONField. MPTT fields (`lft`, `rght`, `tree_id`, `level`) managed automatically.
*   **Indexing**: Indexes on `slug`, `category_type`, `is_active`. MPTT fields are indexed by the library. **Requires DB support (e.g., GIN index) for efficient querying on `custom_fields`** if needed.
*   **Search**: API filtering/search on `name`, `category_type`, potentially parent/ancestors, and `custom_fields`.

### 4.2 Security
*   **Access Control**: Define permissions (`add_category`, `change_category`, `delete_category`, `view_category`). Access might be further restricted based on `category_type` or organizational scope if categories themselves become scoped (though often they are global reference data). Custom field access control.
*   **Audit Logging**: Log CRUD operations, hierarchy changes (parent change), and changes to `custom_fields` via Audit System.

### 4.3 Performance
*   Efficient hierarchy queries using `django-mptt` methods (`get_descendants`, `get_ancestors`).
*   Efficient filtering by `category_type`.
*   Efficient `custom_fields` querying (needs indexing).
*   Caching for category trees or frequently accessed categories.

### 4.4 Integration
*   **Primary Integration**: Serves as target for FK/M2M from classifiable models (`Product`, `Document`, etc.).
*   **API Endpoint**: Provide RESTful API (`/api/v1/categories/`) for managing categories, potentially including hierarchy-specific actions (get tree, descendants).
*   **Custom Field Schema Integration**: Integrates with `CustomFieldDefinition` mechanism.
*   **Library Dependency**: Requires installation and configuration of `django-mptt`. Requires `django-taggit` if `tags` field is added.

## 5. Non-Functional Requirements

*   **Scalability**: Support deep hierarchies and a large number of categories.
*   **Availability**: Category data is important reference data.
*   **Data Consistency**: Maintain hierarchy integrity (via MPTT). Enforce `unique_together`.
*   **Backup and Recovery**: Standard procedures.

## 6. Success Metrics

*   Successful classification of diverse entities using the category system.
*   Accurate representation of hierarchies.
*   Ease of managing categories and hierarchies.
*   Performant querying based on categories.
*   Successful use of custom fields where needed.

## 7. API Documentation Requirements

*   Document `Category` model fields (incl. `custom_fields`, `category_type`).
*   Document API endpoints for CRUD and hierarchy operations. Document filtering options (by type, name, parent, custom fields).
*   Document how `custom_fields` are handled.
*   Auth/Permission requirements.
*   Document how to discover custom field schemas (if applicable).

## 8. Testing Requirements

*   **Unit Tests**: Test `Category` model, MPTT setup, `unique_together` constraints, `custom_fields` logic if any.
*   **Integration Tests**:
    *   Test API CRUD operations.
    *   Test hierarchy operations (creating children, moving nodes) via API/Admin.
    *   Test filtering by `category_type`, name, parent, etc.
    *   Test assigning categories to other models (e.g., a Product) and respecting `limit_choices_to`.
    *   Test permissions.
    *   Test **saving/validating `custom_fields`**.
*   **Performance Tests**: Test performance of deep hierarchy traversals or filtering on large category sets.

## 9. Deployment Requirements

*   **Migrations**: Standard migrations for `Category` table, MPTT fields, custom fields, indexes. Requires `django-mptt` to be installed before migration.
*   **Initial Data**: Potentially populate root categories or core structures via data migration.
*   **Custom Field Schema Deployment**: Deploy `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements

*   Standard backups. Potential need for `manage.py rebuild_category_tree` (MPTT command) if tree becomes corrupted (rare).
*   Admin management of categories and custom field schemas.

---