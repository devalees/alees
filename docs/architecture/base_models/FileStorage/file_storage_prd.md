
# FileStorage Model - Product Requirements Document (PRD)

## 1. Overview

*   **Purpose**: To define a standardized model for storing metadata about files uploaded and managed within the ERP system, providing a reference linking to the actual file stored via a **configured backend (supporting both local filesystem and cloud options)**.
*   **Scope**: Definition of the `FileStorage` data model holding file metadata (name, type, size, owner, storage path), basic management, custom field capability, and integration points. Excludes specific backend implementation details and built-in file versioning.
*   **Implementation**: Defined as a concrete Django Model. It **must** inherit `Timestamped`, `Auditable`, and `OrganizationScoped`. Uses a `JSONField` for custom fields. Relies on Django's configurable storage backend system.
*   **Target Users**: Any user/system uploading or accessing files, Developers (linking models to files), System Administrators.

## 2. Business Requirements

*   **Centralized File Reference**: Provide a metadata record for every managed file.
*   **Support Diverse File Types**: Handle various document, media, etc., types.
*   **Track Basic Metadata**: Store original filename, size, MIME type, uploader, upload timestamp.
*   **Foundation for Attachments**: Allow other entities (like `Document`, `Comment`, `UserProfile`) to link to stored files.
*   **Access Control Foundation**: Provide ownership (`uploaded_by`) and organizational scoping (`organization`) for permission checks. Ensure access is granted based on user roles and permissions within the correct organization.
*   **Extensibility**: Allow storing file-specific metadata via custom fields.
*   **Storage Flexibility**: Allow deployment using either local filesystem or cloud storage via configuration without changing application logic interacting with files.

## 3. Functional Requirements

### 3.1 `FileStorage` Model Definition
*   **Inheritance**: Must inherit `Timestamped`, `Auditable`, `OrganizationScoped`.
*   **Fields**:
    *   `file`: (FileField) Stores the **relative path** within the configured storage backend. `upload_to` generates unique path (e.g., `org_{org_id}/files/{uuid}_{filename}`).
    *   `original_filename`: (CharField, max_length=255, db_index=True). The filename as uploaded by the user.
    *   `file_size`: (PositiveBigIntegerField, null=True) Size in bytes. Populated automatically on upload.
    *   `mime_type`: (CharField, max_length=100, blank=True, db_index=True). Populated automatically on upload.
    *   `uploaded_by`: (ForeignKey to `User`, SET_NULL, null=True, related_name='uploaded_files'). Set automatically during upload.
    *   `tags`: (TaggableManager via `django-taggit`, blank=True).
    *   **`custom_fields`**: (JSONField, default=dict, blank=True).
*   **Meta**: `verbose_name`, `plural`, `ordering` (e.g., `['-created_at']`), indexes (e.g., on `organization`, `uploaded_by`).
*   **String Representation**: Return `original_filename`.
*   **Properties/Methods**:
    *   `@property def filename(self): return os.path.basename(self.file.name)` (Returns the potentially renamed stored filename).
    *   `get_secure_url(requesting_user)`: (Method - preferred over property) A method that performs permission checks before returning the result of `self.file.url`. Requires access to the user making the request. *(The actual URL generation `self.file.url` is handled by Django's storage backend.)*

### 3.2 Custom Field Schema Definition (External Mechanism)
*   Requires separate `CustomFieldDefinition` mechanism if custom fields are used, potentially filtered by a 'FileStorage' context.

### 3.3 File Operations (Handled by API Views/Services)
*   **Upload**: API endpoint handles receiving file binary, validation (type, size limits from settings), creating `FileStorage` instance (populating metadata, setting `organization`, `uploaded_by`), saving file via `instance.file.save()` (uses configured backend), saving instance, returning metadata. Requires `add_filestorage` permission in the target organization.
*   **Download/Access**: API endpoint/logic checks user permissions (e.g., `view_filestorage` permission for the file's organization using Org-Aware RBAC, OR potentially view permission on a related object like `Document`), then calls a method like `instance.get_secure_url(request.user)` which in turn calls `instance.file.url` to generate the appropriate access URL (e.g., local path or pre-signed cloud URL).
*   **Deletion**: API endpoint checks user permissions (`delete_filestorage` permission for the file's organization using Org-Aware RBAC), deletes `FileStorage` record, and **must** call `instance.file.delete(save=False)` to remove the file from the storage backend.
*   **Update**: API for updating metadata (`tags`, `custom_fields`). Requires `change_filestorage` permission. Replacing file content typically involves deleting the old record and creating a new one.

### 3.4 Validation
*   Upload validation (MIME type, size) performed in API view/serializer using configured settings (`ALLOWED_MIME_TYPES`, `MAX_UPLOAD_SIZE`).
*   Custom field validation against schema.

### 3.5 Relationships
*   Links *to* `User` (`uploaded_by`), `Organization` (via `OrganizationScoped`).
*   Linked *to* by other models (e.g., `Document`, `Comment`, `UserProfile.profile_picture`) via `ForeignKey` or `ManyToManyField`.

### 3.6 Out of Scope
*   Specific storage backend implementation details (handled by strategy/config).
*   File Versioning (separate feature).
*   File Content Validation (virus scan etc.).
*   Detailed access/download history (potentially part of Audit Log).

## 4. Technical Requirements

### 4.1 Data Management
*   `FileField` stores relative path. Metadata in DB. Binaries in configured backend. Indexing on metadata fields. GIN index for `custom_fields` if needed.

### 4.2 Security
*   **Access Control:** Application API views/serializers **must** broker access.
    *   **Upload:** Requires `add_filestorage` permission (Org-Aware RBAC) in the target organization.
    *   **Read/Download:** Requires `view_filestorage` permission (Org-Aware RBAC) on the file's organization (or potentially inherited view permission from a linked object) *before* generating download URLs via `file.url`.
    *   **Update Metadata:** Requires `change_filestorage` permission (Org-Aware RBAC) on the file's organization.
    *   **Delete:** Requires `delete_filestorage` permission (Org-Aware RBAC) on the file's organization.
*   **Storage Security:** Configure backend appropriately (private buckets/folders, filesystem permissions).
*   **Secure URLs:** Rely on `instance.file.url` to generate appropriate URLs (direct path for local handled by secure webserver config, pre-signed URL for cloud).
*   **Credentials:** Managed securely via Configuration Strategy.
*   **Upload Validation:** Enforce configured type/size limits server-side.
*   **Audit Logging:** Log upload, delete, metadata changes, potentially controlled access events (if required).

### 4.3 Performance
*   Metadata queries should be efficient. File transfer performance depends on backend/network. URL generation (especially pre-signed URLs) should be reasonably fast.

### 4.4 Integration
*   **Storage Backend:** Relies on configured `DEFAULT_FILE_STORAGE` and `django-storages` (if using cloud). Code uses Django storage abstraction layer.
*   **Primary Integration:** Target for FK/M2M from other models.
*   **API Endpoint:** For Upload, Metadata management, Secure URL generation/Access, Deletion.
*   **Custom Field Integration:** With `CustomFieldDefinition` mechanism.
*   **RBAC Integration:** Permission checks use the Org-Aware RBAC system.

## 5. Non-Functional Requirements

*   Scalability (depends on chosen backend), Availability (depends on backend), Durability (depends on backend), Consistency (metadata vs file), Backup/Recovery (DB metadata + file backend).

## 6. Success Metrics

*   Successful upload/storage/retrieval using either configured backend. Reliable access control enforcement based on org-aware permissions. Performant metadata/access. Successful linking from other models.

## 7. API Documentation Requirements

*   Document `FileStorage` model fields (incl. `custom_fields`, `tags`).
*   Document Upload API endpoint and validation rules (size, type).
*   Document Metadata/Access API endpoint (how to retrieve metadata and secure download URLs).
*   Document Delete API endpoint.
*   Explain how download URLs are obtained and their nature (potentially time-limited if pre-signed).
*   **Explicitly document required model-level permissions** (`add_filestorage`, `view_filestorage`, `change_filestorage`, `delete_filestorage`) and that they are checked within the organizational context.
*   Document `custom_fields` handling.

## 8. Testing Requirements

*   **Unit Tests**: Test model, `filename` property. Test custom field validation logic (if any on model).
*   **Integration Tests (API & Storage Backend):**
    *   **Run primarily against `FileSystemStorage`** using `override_settings` and temporary directories.
    *   Test Upload API (success, validation failures - type/size). Verify `organization` and `uploaded_by` are set correctly. Verify files are saved to temp media root.
    *   Test Access/URL generation API:
        *   Verify metadata retrieval is subject to `view_filestorage` permission (Org-Aware check).
        *   Verify `download_url` generation logic correctly checks `view_filestorage` permission (Org-Aware check) before returning a URL. Test success/failure cases.
    *   Test Delete API:
        *   Verify requires `delete_filestorage` permission (Org-Aware check).
        *   Verify metadata record is deleted.
        *   Verify underlying file is deleted from storage (use `mock.patch` on `storage.delete`).
    *   Test `custom_fields` save/validation via API (if metadata updatable).
    *   Test tag assignment/filtering via API (if metadata updatable/listable).
    *   Test Org Scoping on List/Retrieve views (using `OrganizationScopedViewSetMixin`).
    *   **(Optional)** Separate tests using `moto` to verify S3-specific interactions (like pre-signed URL generation nuances) if needed.
*   **Security Tests**: Focus on access control for download URLs and deletion across different organizations and user roles.

## 9. Deployment Requirements

*   Migrations for `FileStorage`.
*   **Configure `DEFAULT_FILE_STORAGE` and backend-specific settings (MEDIA_ROOT or Cloud Credentials/Bucket) appropriately for each environment** via environment variables/secrets management.
*   Configure web server for serving `MEDIA_URL` if using `FileSystemStorage` in production (requires access control configuration - e.g., Nginx `internal` directive or signed URLs via Django).
*   Configure validation settings (`MAX_UPLOAD_SIZE`, `ALLOWED_MIME_TYPES`).
*   Deploy `CustomFieldDefinition` mechanism.
*   Ensure RBAC permissions (`add_filestorage`, etc.) are defined and assigned to relevant roles.

## 10. Maintenance Requirements

*   Monitor storage usage (local disk or cloud). Backups (DB + File Backend). Library updates (`django-storages`). Manage custom field schemas.
