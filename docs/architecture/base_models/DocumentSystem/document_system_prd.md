# Document Model - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To define a standardized model for representing logical documents within the ERP system, managing their metadata, associating them with underlying stored files, and linking them to relevant business contexts.
*   **Scope**: Definition of the `Document` data model, its core attributes (title, type, status), relationship to the `FileStorage` model, basic versioning information, custom field capability, and relationship to other business entities. Excludes complex workflow, content processing (OCR, indexing), and advanced sharing features.
*   **Implementation**: Defined as a concrete Django Model. It **must** inherit `Timestamped`, `Auditable`, and `OrganizationScoped`. Uses a `JSONField` for custom fields. Relies on the `FileStorage` model.
*   **Target Users**: All users interacting with documents (viewing, uploading attachments), Document Managers, System Administrators.

## 2. Business Requirements

*   **Organize Business Files**: Provide a structured way to manage documents beyond raw file storage, adding business context and metadata.
*   **Link Documents to Processes**: Associate documents with specific business records (e.g., attach an invoice PDF to an Invoice record, a contract PDF to an Organization record).
*   **Basic Version Awareness**: Track simple version increments for documents that undergo revisions.
*   **Categorization**: Classify documents by type (e.g., Invoice, Contract, Report).
*   **Access Control**: Ensure documents are accessed according to user permissions and organizational scope.
*   **Extensibility**: Allow storing document-specific attributes via custom fields.

## 3. Functional Requirements

### 3.1 `Document` Model Definition
*   **Inheritance**: Must inherit `Timestamped`, `Auditable`, `OrganizationScoped`.
*   **Fields**:
    *   `title`: (CharField, max_length=255, db_index=True) The primary display name or title of the document.
    *   `document_type`: (ForeignKey to `Category`, limit_choices_to={'category_type': 'DOCUMENT_TYPE'}, on_delete=models.PROTECT, null=True, blank=True) Classification using the generic Category model.
    *   `status`: (CharField, max_length=50, choices=..., default='draft', db_index=True) Status of the document (e.g., 'Draft', 'Active', 'Archived', 'Pending Review'). References slugs from the `Status` model/system.
    *   `file`: (ForeignKey to `FileStorage`, on_delete=models.PROTECT) **Required**. Links to the metadata record of the actual underlying file content.
    *   `version`: (PositiveIntegerField, default=1) Simple integer representing the document version number.
    *   `description`: (TextField, blank=True) Optional description or summary.
    *   `tags`: (ManyToManyField via `django-taggit` or similar, blank=True) For flexible classification.
    *   **`custom_fields`**: (JSONField, default=dict, blank=True) Stores values for dynamically defined custom fields relevant to the document (e.g., 'review_date', 'related_project_id').
    *   **Linking Fields (Generic Relation or Specific FKs)**: Need a way to link the Document to the business entity it belongs to. Options:
        *   **GenericForeignKey:** Use `content_type` (FK to `ContentType`), `object_id` (PositiveIntegerField/CharField), `content_object` (GenericForeignKey). Flexible but harder to query.
        *   **Specific ForeignKeys:** Add nullable ForeignKeys for common links (e.g., `related_organization = FK(Organization, null=True)`, `related_product = FK(Product, null=True)`). Less flexible, more explicit. *(Decision needed)*.
*   **Meta**:
    *   `verbose_name = "Document"`
    *   `verbose_name_plural = "Documents"`
    *   `ordering = ['-created_at']`
    *   Consider indexes on linking fields and `document_type`.
*   **String Representation**: Return `title` and perhaps `version`.

### 3.2 Custom Field Schema Definition (External Mechanism)
*   Requirement for separate `CustomFieldDefinition` model/mechanism (possibly filtered by a 'Document' context or `document_type`) to define schema for document custom fields.

### 3.3 Version Management (Simplified)
*   **Creating New Version**: Typically involves:
    1. Uploading a new file (creates a new `FileStorage` record).
    2. Creating a *new* `Document` record.
    3. Linking the new `Document` to the new `FileStorage` record.
    4. Incrementing the `version` number.
    5. Potentially linking the new `Document` to the previous version (e.g., add a `previous_version = ForeignKey('self', null=True)` field to the `Document` model). *(Decision needed on explicit version linking)*.
*   **Out of Scope (Advanced):** Complex diffing, merging, explicit rollback workflows.

### 3.4 Document Operations
  CRUD via API:
   Primary method for creating, reading, updating (metadata), and deleting Document records must be via API endpoints, respecting Organization scope and permissions. Creating a Document typically involves handling a related file upload to the FileStorage system simultaneously or referencing an existing FileStorage record.
  Association:
   API logic required to associate Document records with relevant business entities (using GenericForeignKey or specific FKs, depending on the chosen implementation). This might be part of the Document CRUD or handled by the API for the parent business entity.
Version Management (Simplified):
 If implementing versioning, API actions might trigger the creation of a new Document version (as described in 3.3).
Admin Management:
 Django Admin provides a secondary interface for administrators to view, potentially manage metadata, or troubleshoot Document records.

### 3.5 Validation
*   Required fields (`title`, `file`). FK constraints. Custom field validation against schema. Status logic enforced by Workflow/StateMachine system later.

### 3.6 Out of Scope for this Model/PRD
*   **File Storage Backend Details**: Handled by `FileStorage` system.
*   **Advanced Version Control**: Diffing, merging, branching.
*   **Content Processing**: OCR, full-text indexing, format conversion (separate features/integrations).
*   **Document Sharing/Collaboration**: Advanced features beyond base permissions.
*   **Document Workflows**: Review/Approval processes (handled by Workflow system referencing `Document.status`).
*   **Detailed History**: Handled by Audit Log.

## 4. Technical Requirements

### 4.1 Data Management
*   Storage: Standard fields + JSONField. Links to `FileStorage`, `ContentType`, potentially self for versioning.
*   Indexing: On `title`, `status`, `document_type`, `organization`. On Generic Relation fields (`content_type`, `object_id`) if used. **GIN index on `custom_fields`** if querying needed.
*   Search: API filtering/search on key metadata fields, type, status, tags, potentially custom fields. *Full-text search requires separate indexing solution.*

### 4.2 Security
*   **Access Control**: Permissions (`add_document`, `change_document`, `delete_document`, `view_document`). Enforced within Organization scope. Access may also depend on permissions for the *linked business entity* (e.g., view Invoice Document requires view permission on the Invoice). Field-level permissions may apply.
*   **File Access Security**: Accessing the underlying file content via the `Document.file` link must re-verify permissions, potentially using secure URL generation provided by the `FileStorage` system.
*   **Audit Logging**: Log CRUD operations, status changes, and `custom_fields` changes via Audit System.

### 4.3 Performance
*   Efficient querying/filtering of document metadata.
*   Performance of underlying file access depends on `FileStorage` system.

### 4.4 Integration
*   **Core Dependency**: Relies heavily on `FileStorage` model.
*   **Linking**: Integrates with various business models via GenericForeignKey or specific ForeignKeys.
*   **Categorization**: Integrates with `Category` model (for `document_type`).
*   **Status**: Integrates with `Status` model/system.
*   **API Endpoint**: Provide RESTful API (`/api/v1/documents/`) for CRUD, respecting Org Scoping and permissions. Needs careful handling of file uploads during create and linking to business entities. Include filtering/search. Define `custom_fields` handling.
*   **Custom Field Schema Integration**: Integrates with `CustomFieldDefinition` mechanism.

## 5. Non-Functional Requirements

*   **Scalability**: Support a large number of document metadata records. Scalability of file storage itself depends on the `FileStorage` backend.
*   **Availability**: Document metadata and access to underlying files need to be available.
*   **Data Consistency**: Maintain integrity of links (to FileStorage, Categories, Business Entities).
*   **Backup/Recovery**: Must include both Document metadata DB and the underlying FileStorage backend.

## 6. Success Metrics

*   Successful association of files with business context via `Document` records.
*   Ease of finding and managing relevant documents.
*   Reliable access control enforcement for documents and files.
*   Successful basic version tracking.

## 7. API Documentation Requirements

*   Document `Document` model fields (incl. `custom_fields`, linking fields).
*   Document API endpoints for CRUD, filtering, searching. Detail file handling on upload.
*   Document how `custom_fields` are handled.
*   Auth/Permission requirements (mentioning Org Scoping and potential dependency on linked entity permissions).
*   Document how to discover custom field schemas (if applicable).

## 8. Testing Requirements

*   **Unit Tests**: Test `Document` model, relationships, version increment logic (if implemented in `save`).
*   **Integration Tests**:
    *   Test API CRUD, ensuring file upload creates `FileStorage` and `Document` correctly.
    *   Test linking documents to other business entities (via GFK or specific FKs).
    *   Test Org Scoping enforcement.
    *   Test permissions (direct Document permissions and inherited from linked entity).
    *   Test basic version creation via API.
    *   Test filtering/searching.
    *   Test **saving/validating `custom_fields`**.
*   **Security Tests**: Test access control scenarios rigorously.

## 9. Deployment Requirements

*   Migrations for `Document` table, indexes (incl. JSONField).
*   Dependencies on `FileStorage`, `Category`, `Status`, `Organization`, `User` models/migrations.
*   Deployment of `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements

*   Standard backups (DB + File Storage).
*   Monitoring performance.
*   Management of document types (via Category system) and custom field schemas.

---