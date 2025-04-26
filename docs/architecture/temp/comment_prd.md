
# Comment Model - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To define a standardized model for users to add comments, replies, and potentially attach files to various business objects (e.g., Products, Orders, Tasks) within the ERP system.
*   **Scope**: Definition of the `Comment` data model, its core attributes, generic relationship to parent objects, basic threading (replies), attachment support, and custom field capability. Excludes real-time features, mentions, reactions, and advanced moderation workflows.
*   **Implementation**: Defined as a concrete Django Model using Generic Relations (`ContentType` framework). It **must** inherit `Timestamped`, `Auditable`, and potentially `OrganizationScoped`. Uses a `JSONField` for custom fields. Links to `FileStorage`.
*   **Target Users**: All users collaborating on business objects, System Administrators (potential moderation).

## 2. Business Requirements

*   **Contextual Discussion**: Allow users to discuss and provide feedback directly related to specific business objects (Orders, Products, etc.).
*   **Collaboration**: Facilitate communication and information sharing among users working on the same items.
*   **Record Keeping**: Maintain a record of discussions and decisions related to specific objects.
*   **Attachments**: Allow users to attach relevant files to their comments.
*   **Basic Threading**: Support direct replies to comments to structure conversations.
*   **Extensibility**: Allow storing comment-specific attributes via custom fields.

## 3. Functional Requirements

### 3.1 `Comment` Model Definition
*   **Inheritance**: Must inherit `Timestamped`, `Auditable`. **Must inherit `OrganizationScoped`** (comments exist within the context of an organization's data).
*   **Fields**:
    *   `user`: (ForeignKey to `User`, on_delete=models.SET_NULL, null=True, related_name='comments') The author of the comment. Uses `Auditable.created_by`, but explicit FK is standard.
    *   `content`: (TextField) The main text content of the comment. Support for basic markup (e.g., Markdown) might be considered later.
    *   **Generic Relation to Parent Object**:
        *   `content_type`: (ForeignKey to `ContentType`, on_delete=models.CASCADE) The model of the object being commented on.
        *   `object_id`: (CharField or PositiveIntegerField, db_index=True) The primary key of the object being commented on. *(Use CharField if targeting UUID PKs)*.
        *   `content_object`: (GenericForeignKey 'content_type', 'object_id') Provides direct access to the parent object.
    *   `parent`: (ForeignKey to `'self'`, on_delete=models.CASCADE, null=True, blank=True, related_name='replies') Links a reply to its parent comment. Null for top-level comments.
    *   `is_edited`: (BooleanField, default=False) Flag indicating if the comment was edited after creation.
    *   `status`: (CharField with choices, e.g., 'VISIBLE', 'HIDDEN', 'PENDING_MODERATION', default='VISIBLE', db_index=True) Basic visibility/moderation status.
    *   `attachments`: (ManyToManyField to `FileStorage`, blank=True) Links to uploaded files attached to the comment.
    *   **`custom_fields`**: (JSONField, default=dict, blank=True) Stores values for dynamically defined custom fields relevant to the comment (e.g., 'feedback_type', 'severity').
*   **Meta**:
    *   `verbose_name = "Comment"`
    *   `verbose_name_plural = "Comments"`
    *   `ordering = ['created_at']` (Order comments chronologically by default).
    *   `indexes`: Index `content_type` and `object_id` together for efficient lookup of comments for a specific object.
*   **String Representation**: Return truncated content and author.

### 3.2 Custom Field Schema Definition (External Mechanism)
*   Requirement for separate `CustomFieldDefinition` model/mechanism (possibly filtered by a 'Comment' context or comment type derived from custom fields) to define schema for comment custom fields.

### 3.3 Comment Operations
*   **CRUD**: API endpoints for:
    *   Creating comments/replies associated with a specific parent object (using Generic Relation fields). Requires upload handling for attachments.
    *   Reading/Listing comments for a specific parent object (filtered by `content_type` and `object_id`). API should handle returning comments in a threaded structure (e.g., top-level comments with their direct replies nested).
    *   Updating own comments (limited time window? Sets `is_edited` flag). Requires specific permissions.
    *   Deleting own comments (soft delete via `status='HIDDEN'` or hard delete). Requires specific permissions.
    *   *(Moderation)* Endpoints for users with moderation permissions to change comment `status`.
*   Includes managing `custom_fields` data during create/update.

### 3.4 Validation
*   `content` cannot be empty.
*   Generic Relation fields (`content_type`, `object_id`) must point to a valid object.
*   Parent comment (if provided) must belong to the same parent object thread.
*   Attachment validation (size, type) handled by `FileStorage` upload process.
*   Custom field validation against schema.

### 3.5 Out of Scope for this Model/PRD
*   **Real-time Updates**: Displaying new comments instantly (requires WebSockets).
*   **Mentions (`@user`)**: Parsing content and triggering notifications.
*   **Reactions (`like`, etc.)**: Requires separate `Reaction` model.
*   **Advanced Moderation Workflows**: Queues, reporting, moderator assignment.
*   **Full-text Search on Content**: Requires integration with a search engine (like Elasticsearch).

## 4. Technical Requirements

### 4.1 Data Management
*   Storage: Standard fields, Generic Relation fields, JSONField. Links to User, ContentType, FileStorage. Self-referential FK for parent.
*   Indexing: On GFK fields (`content_type`, `object_id`), `user`, `parent`, `status`, `organization`. **GIN index on `custom_fields`** if querying needed.
*   Querying: Efficient retrieval of comment threads for a specific object.

### 4.2 Security
*   **Access Control**:
    *   Permission to *create* comments usually depends on permissions on the *parent object*.
    *   Permission to *view* comments depends on view permissions for the *parent object*.
    *   Permission to *update/delete* comments usually restricted to the comment author (potentially time-limited) or moderators.
    *   Permissions required for moderation actions (changing `status`).
    *   Enforced within Organization scope.
*   **Attachment Security**: Accessing attachments must respect permissions on the comment AND potentially the parent object. Use `FileStorage` system's secure access mechanisms.
*   **Audit Logging**: Log create/update/delete/status changes via Audit System, including `custom_fields` changes.

### 4.3 Performance
*   Efficient retrieval of comment threads (potentially involves recursive queries or specific techniques if using MPTT for deeper nesting later). Use `select_related('user')` and `prefetch_related('replies', 'attachments')`.
*   Efficient filtering/counting of comments per object.

### 4.4 Integration
*   **Core Integration**: Uses `ContentType` framework, `User`, `FileStorage`, `Organization` (scoping).
*   **Notification System**: Trigger notifications on new comments/replies based on user subscriptions or context (separate logic).
*   **API Endpoint**: Provide RESTful API (e.g., `/api/v1/comments/`, potentially nested under parent objects like `/api/v1/invoices/{id}/comments/`). Needs to handle GFK linking and attachment uploads.
*   **Custom Field Schema Integration**: Integrates with `CustomFieldDefinition` mechanism.

## 5. Non-Functional Requirements

*   **Scalability**: Handle a large volume of comments across many objects.
*   **Availability**: Comment viewing/creation should be available.
*   **Data Consistency**: Maintain integrity of GFK links and parent reply links.
*   **Backup/Recovery**: Standard procedures (DB + File Storage for attachments).

## 6. Success Metrics

*   User engagement with comment feature.
*   Successful association of comments with business objects.
*   Performant retrieval of comment threads.
*   Ease of use for adding/viewing comments and replies.

## 7. API Documentation Requirements

*   Document `Comment` model fields (incl. `custom_fields`, GFK fields).
*   Document API endpoints for CRUD operations, including how to target a parent object and handle replies/attachments.
*   Document response structure for threaded comments.
*   Document handling of `custom_fields`.
*   Auth/Permission requirements.
*   Document how to discover custom field schemas (if applicable).

## 8. Testing Requirements

*   **Unit Tests**: Test `Comment` model, self-referential parent link, GFK usage.
*   **Integration Tests**:
    *   Test API CRUD operations for comments and replies on different parent object types.
    *   Test attachment upload/association/retrieval via API.
    *   Test retrieval of threaded comments.
    *   Test permission checks (creating, editing own, deleting own, moderation).
    *   Test Org Scoping enforcement.
    *   Test **saving/validating `custom_fields`**.
*   **Security Tests**: Test access control scenarios (viewing/editing/deleting comments on objects user shouldn't access).

## 9. Deployment Requirements

*   Migrations for `Comment` table, indexes (incl. GFK, JSONField).
*   Dependencies on `User`, `FileStorage`, `ContentType`, `Organization`.
*   Deployment of `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements

*   Standard backups. Potential moderation activities.
*   Management of custom field schemas. Monitoring performance of GFK queries.

---