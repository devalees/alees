
# Tagging System Integration - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To provide a standardized system for applying flexible tags (keywords, labels) to various business objects across the ERP system for organization, filtering, and search enhancement.
*   **Scope**: Integration of a tagging library (like `django-taggit`), enabling the association of tags with target models, basic tag management, API exposure for tagging operations, and optional custom fields on tags.
*   **Implementation Strategy**: Utilize the **`django-taggit`** library. Add the `TaggableManager` field to models requiring tagging. Optionally extend the base `Tag` model if custom fields are needed.
*   **Target Users**: All users (applying/filtering by tags), System Administrators (potential tag cleanup), Developers (adding tagging to models).

## 2. Business Requirements

*   **Flexible Organization**: Allow users to apply multiple relevant keywords (tags) to business objects (Products, Documents, Contacts, etc.) for non-hierarchical grouping.
*   **Improved Discoverability**: Enable finding objects based on assigned tags through search and filtering.
*   **User-Driven Categorization**: Allow for emergent categorization through common tag usage.
*   **(Optional)** **Tag Metadata**: Allow storing additional structured information about tags themselves via custom fields if needed.

## 3. Functional Requirements

### 3.1 Tagging Integration (`django-taggit`)
*   **Library**: Integrate `django-taggit`.
*   **Model Integration**: Add `tags = TaggableManager(blank=True)` field to all models that need to be taggable (e.g., `Product`, `Contact`, `Document`, `Organization`).
*   **Core Models (Provided by `django-taggit`)**:
    *   `taggit.models.Tag`: Stores the tag name (unique) and slug.
    *   `taggit.models.TaggedItem`: Generic relation linking a `Tag` to a specific tagged object instance.

### 3.2 `Tag` Model Customization (Optional - for Custom Fields)
*   **If Custom Fields are Required**:
    *   **Requirement**: Need to store additional structured data on the `Tag` itself.
    *   **Implementation**: Create a custom Tag model that inherits from `taggit.models.TagBase` and `taggit.models.GenericTaggedItemBase`, and add the `custom_fields` JSONField to this custom Tag model. Configure `settings.TAGGIT_TAG_MODEL` to point to this custom model.
    *   **`CustomTag` Model Fields**:
        *   Inherits `name` and `slug` from `TagBase`.
        *   **`custom_fields`**: (JSONField, default=dict, blank=True).
        *   *Inherit Timestamped/Auditable if needed on the tag itself.*
*   **If Custom Fields NOT Required**: Use the default `taggit.models.Tag` model.

### 3.3 Custom Field Schema Definition (External Mechanism)
*   Requirement for separate `CustomFieldDefinition` model/mechanism (possibly filtered by a 'Tag' context) if custom fields are added to the `Tag` model.

### 3.4 Tagging Operations via API
*   **Adding/Setting Tags**: When creating or updating a taggable object (e.g., Product) via API, the request payload should accept a list of tag names (strings) for the `tags` field. The serializer/view logic (using `TaggableManager`) will handle creating new `Tag` records if they don't exist and updating the `TaggedItem` associations.
*   **Removing Tags**: Setting an empty list `[]` for the `tags` field typically removes all tags. Specific removal might require custom handling or using specific `TaggableManager` methods.
*   **Listing Tags on an Object**: API endpoints retrieving a taggable object should include its associated list of tag names in the response.
*   **Filtering by Tags**: API list endpoints for taggable models should support filtering by one or more tags (e.g., `?tags__name__in=urgent,customer-a`). `django-filter` integration with `django-taggit` is possible (e.g., using `taggit.managers.TaggableManager.name` in filter fields).

### 3.5 Tag Management (Admin/API)
*   **Viewing Tags**: List all unique tags used in the system (via Django Admin for `Tag` model or a dedicated API endpoint).
*   **Editing Tags**: Editing a `Tag`'s `name` updates it everywhere it's used. Requires admin permissions. Edit `custom_fields` via this interface too, if implemented.
*   **Deleting Tags**: Deleting a `Tag` record automatically removes its association from all tagged items. Restricted to admins, potentially only allowed if the tag is unused.
*   **Merging Tags (Optional)**: Advanced feature - provide an admin action or utility to merge two similar tags (e.g., "product" and "products") into one, reassigning all items.

### 3.6 Out of Scope
*   Tag hierarchy, explicit tag types (beyond free-form strings), tag approval workflows, complex tag relationships, detailed tag analytics dashboards.

## 4. Technical Requirements

### 4.1 Library Integration
*   Install `django-taggit`. Add `'taggit'` to `INSTALLED_APPS`.
*   If using custom `Tag` model, configure `settings.TAGGIT_TAG_MODEL`.
*   Apply `TaggableManager` to relevant models.

### 4.2 Data Management
*   Storage handled by `django-taggit` models (`Tag`, `TaggedItem`) plus custom `Tag` model and JSONField if used.
*   Indexing handled mostly by `django-taggit`. Add **GIN index on `custom_fields`** if querying on tag custom fields is needed.

### 4.3 Security
*   Permissions to *add/remove* tags from an object are typically tied to the `change` permission for that object.
*   Permissions to *manage* the global list of `Tag` records (`add_tag`, `change_tag`, `delete_tag`) should be restricted to administrators. Custom field access control if applicable.
*   Audit logging for tag assignments/removals (via Audit Log entry for the parent object change) and for direct `Tag` model management.

### 4.4 Performance
*   `django-taggit` generally performs well. Querying objects by tag requires joins.
*   Ensure efficient filtering by tags in API list views (library helpers often optimize this).
*   Efficient querying on `custom_fields` needs indexing.

### 4.5 Integration
*   Integrates with any model via `TaggableManager`.
*   Integrates with DRF serializers for input/output of tags.
*   Integrates with `django-filter` for API filtering.
*   Potential API endpoint for listing/managing global tags (`/api/v1/tags/`).
*   Integrates with `CustomFieldDefinition` mechanism if using custom fields on tags.

## 5. Non-Functional Requirements

*   **Scalability**: Handle large numbers of tags and tagged items efficiently.
*   **Availability**: Tagging functionality should be available.
*   **Consistency**: Ensure tag associations are correctly maintained.

## 6. Success Metrics

*   Effective use of tags for organizing and finding objects.
*   Performant tag-based filtering.
*   User satisfaction with the tagging feature.

## 7. API Documentation Requirements

*   Document how to provide/retrieve tags for taggable objects in API requests/responses (e.g., list of strings for the `tags` field).
*   Document API endpoints for filtering by tags (query parameters).
*   Document API endpoint for managing global tags (if implemented).
*   Document handling of tag `custom_fields` (if implemented).
*   Auth/Permission requirements.

## 8. Testing Requirements

*   **Unit Tests**: Test custom `Tag` model if created. Test custom field logic if added.
*   **Integration Tests**:
    *   Test adding, setting, and removing tags from objects via API.
    *   Test retrieving objects and verifying their tags are included.
    *   Test filtering list endpoints by single/multiple tags.
    *   Test permissions related to tagging objects and managing global tags.
    *   Test **saving/validating `custom_fields`** on tags if implemented.
    *   Test Admin interface for tag management.

## 9. Deployment Requirements

*   Install `django-taggit`.
*   Migrations for `taggit` models and any custom `Tag` model/custom fields/indexes.
*   Deployment of `CustomFieldDefinition` mechanism if using custom fields on tags.

## 10. Maintenance Requirements

*   Standard backups. Potential need for tag cleanup/merging by administrators.
*   Management of custom field schemas if applicable.

---