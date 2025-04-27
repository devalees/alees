# FileStorage Model - Product Requirements Document (PRD)

## 1. Overview

*   **Purpose**: To define a standardized model for storing metadata about files uploaded and managed within the ERP system, providing a reference linking to the actual file stored via a **configured backend (supporting both local filesystem and cloud options)**.
*   **Scope**: Definition of the `FileStorage` data model holding file metadata (name, type, size, owner, storage path), basic management, custom field capability, and integration points. Excludes specific backend implementation details and built-in file versioning.
*   **Implementation**: Defined as a concrete Django Model. It **must** inherit `Timestamped`, `Auditable`, and `OrganizationScoped`. Uses a `JSONField` for custom fields. Relies on Django's configurable storage backend system.
*   **Target Users**: Any user/system uploading or accessing files, Developers (linking models to files), System Administrators.

## 2. Business Requirements

*   **Centralized File Reference**: Provide a metadata record for every managed file.
*   **Support Diverse File Types**: Handle various document, media, etc.
*   **Track Basic Metadata**: Store filename, size, MIME type, uploader.
*   **Foundation for Attachments**: Allow other entities to link to stored files.
*   **Access Control Foundation**: Provide ownership/scoping for permission checks.
*   **Extensibility**: Allow storing file-specific metadata via custom fields.
*   **Storage Flexibility**: Allow deployment using either local filesystem or cloud storage via configuration.

## 3. Functional Requirements

### 3.1 `FileStorage` Model Definition
*   **Inheritance**: Must inherit `Timestamped`, `Auditable`, `OrganizationScoped`.
*   **Fields**:
    *   `file`: (FileField) Stores the **relative path** within the configured storage backend. `upload_to` generates unique path (e.g., `org_{org_id}/files/{uuid}.{ext}`).
    *   `original_filename`: (CharField, max_length=255, db_index=True).
    *   `file_size`: (PositiveBigIntegerField, null=True) In bytes. Populated on upload.
    *   `mime_type`: (CharField, max_length=100, blank=True, db_index=True). Populated on upload.
    *   `uploaded_by`: (ForeignKey to `User`, SET_NULL, null=True, related_name='uploaded_files').
    *   `tags`: (TaggableManager, blank=True).
    *   **`custom_fields`**: (JSONField, default=dict, blank=True).
*   **Meta**: `verbose_name`, `plural`, `ordering`, indexes.
*   **String Representation**: Return `original_filename`.
*   **Properties/Methods**:
    *   `@property def filename(self): return os.path.basename(self.file.name)`
    *   `@property def url(self):` - **Crucial:** This method should securely generate the appropriate access URL by calling `self.file.url`, which respects the configured storage backend (returning local `/media/...` or cloud pre-signed URL). Requires request context for permission checks before returning URL.

### 3.2 Custom Field Schema Definition (External Mechanism)
*   Requires separate `CustomFieldDefinition` mechanism if custom fields are used.

### 3.3 File Operations (Handled by API Views/Services)
*   **Upload**: API endpoint handles receiving file binary, validation (type, size), creating `FileStorage` instance (populating metadata), saving file via `instance.file.save()` (uses configured backend), saving instance, returning metadata.
*   **Download/Access**: API endpoint/logic checks permissions (Org scope, RBAC), then generates a secure access URL using the `instance.url` property (which calls `instance.file.url`).
*   **Deletion**: API endpoint checks permissions, deletes `FileStorage` record, and **must** call `instance.file.delete(save=False)` to remove the file from the storage backend.
*   **Update**: API for updating metadata (`tags`, `custom_fields`). Replacing file content typically involves deleting the old record and creating a new one.

### 3.4 Validation
*   Upload validation (type, size) performed in API view/serializer using configured settings.
*   Custom field validation against schema.

### 3.5 Relationships
*   Links *to* `User`, `Organization`.
*   Linked *to* by other models via FK/M2M.

### 3.6 Out of Scope
*   Specific storage backend implementation details (handled by strategy/config).
*   File Versioning (separate feature).
*   File Content Validation (virus scan etc.).
*   Detailed History (Audit Log).

## 4. Technical Requirements

*(Largely the same as previous version, but emphasizes abstraction)*

### 4.1 Data Management
*   Storage: `FileField` stores relative path. Metadata in DB. Binaries in configured backend (local FS or cloud). Indexing on metadata. GIN index for `custom_fields` if needed.

### 4.2 Security
*   **Access Control:** Application brokers access based on permissions/Org Scope *before* generating download URLs (`instance.url`).
*   **Storage Security:** Configure backend appropriately (private buckets/folders, filesystem permissions).
*   **Secure URLs:** Rely on `instance.file.url` to generate appropriate URLs (direct path for local, pre-signed for cloud).
*   **Credentials:** Managed securely via Configuration Strategy.
*   **Upload Validation:** Enforce type/size limits.
*   **Audit Logging:** Log upload, delete, potentially controlled access events.

### 4.3 Performance
*   Metadata queries should be efficient. File transfer performance depends on backend/network.

### 4.4 Integration
*   **Storage Backend:** Relies on configured `DEFAULT_FILE_STORAGE` and `django-storages` if using cloud. Code uses Django storage abstraction.
*   **Primary Integration:** Target for FK/M2M.
*   **API Endpoint:** For Upload, Metadata management, Secure URL generation/Access, Deletion.
*   **Custom Field Integration:** With `CustomFieldDefinition` mechanism.

## 5. Non-Functional Requirements

*   Scalability (depends on chosen backend), Availability (depends on backend), Durability (depends on backend), Consistency (metadata vs file), Backup/Recovery (DB metadata + file backend).

## 6. Success Metrics

*   Successful upload/storage/retrieval using either configured backend. Reliable access control. Performant metadata/access. Successful linking.

## 7. API Documentation Requirements

*   Document `FileStorage` model fields.
*   Document Upload/Access/Delete API endpoints and processes. Explain validation.
*   Document how download URLs are obtained and their nature (direct vs signed).
*   Auth/Permission requirements.
*   Custom fields handling.

## 8. Testing Requirements

*   **Unit Tests**: Test model, `url` property logic (mocking `file.url`).
*   **Integration Tests**:
    *   **Run primarily against `FileSystemStorage`** using `override_settings` and temporary directories.
    *   Test Upload API (success, validation failures).
    *   Test Access/URL generation API (permission success/failure).
    *   Test Delete API (metadata + file deletion from mock storage).
    *   Test `custom_fields` save/validation.
    *   **(Optional)** Separate tests using `moto` to verify S3-specific interactions if needed.
*   **Security Tests**: Focus on access control for download URLs and deletion.

## 9. Deployment Requirements

*   Migrations for `FileStorage`.
*   **Configure `DEFAULT_FILE_STORAGE` and backend-specific settings (MEDIA_ROOT or Cloud Credentials/Bucket) appropriately for each environment** via environment variables/secrets management.
*   Configure web server for serving `MEDIA_URL` if using `FileSystemStorage` in production (with access controls).
*   Configure validation settings (size, type).
*   Deploy `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements

*   Monitor storage usage (local disk or cloud). Backups (DB + File Backend). Library updates (`django-storages`). Manage custom field schemas.

--- END OF FILE file_storage_prd.md ---