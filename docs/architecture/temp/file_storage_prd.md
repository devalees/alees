# FileStorage Model - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To define a standardized model for storing metadata about files uploaded and managed within the ERP system, providing a reference linking to the actual file stored via a configured backend.
*   **Scope**: Definition of the `FileStorage` data model holding file metadata (name, type, size, owner, storage path), basic management, custom field capability, and integration points. Excludes the specific file storage backend implementation (e.g., S3, local disk) and built-in file versioning.
*   **Implementation**: Defined as a concrete Django Model. It **must** inherit `Timestamped`, `Auditable`, and potentially `OrganizationScoped` (if file access/visibility needs org scoping). Uses a `JSONField` for custom fields.
*   **Target Users**: Any user/system uploading or accessing files, Developers (linking models to files), System Administrators.

## 2. Business Requirements

*   **Centralized File Reference**: Provide a single point of reference (metadata record) for every managed file within the system.
*   **Support Diverse File Types**: Handle various document, media, and other file types needed by different modules.
*   **Track Basic Metadata**: Store essential information like original filename, file size, MIME type, and uploader.
*   **Foundation for Attachments**: Allow various business entities (Products, Orders, Documents, etc.) to link to stored files.
*   **Access Control Foundation**: Provide necessary ownership/scoping information to enable permission checks for file access.
*   **Extensibility**: Allow storing application-specific metadata about files via custom fields.

## 3. Functional Requirements

### 3.1 `FileStorage` Model Definition
*   **Inheritance**: Must inherit `Timestamped`, `Auditable`. **Must inherit `OrganizationScoped`** if files are tied to specific organizations for access control/visibility. *(Decision Required: Are files org-scoped? Assuming YES for this revision)*.
*   **Fields**:
    *   `file`: (FileField) The core field managed by Django's storage backend. Stores the relative path to the actual file in the configured storage (e.g., S3 bucket path or local filesystem path). `upload_to` should generate a unique path (e.g., based on UUID or org/date structure).
    *   `original_filename`: (CharField, max_length=255, db_index=True) The name of the file as uploaded by the user.
    *   `file_size`: (PositiveIntegerField, null=True) Size of the file in bytes. Populated on upload.
    *   `mime_type`: (CharField, max_length=100, blank=True, db_index=True) The detected MIME type (e.g., 'application/pdf', 'image/jpeg'). Populated on upload.
    *   `uploaded_by`: (ForeignKey to `User`, on_delete=models.SET_NULL, null=True, related_name='uploaded_files') Link to the user who uploaded the file (uses `Auditable.created_by` but making it explicit can be useful).
    *   `tags`: (ManyToManyField via `django-taggit` or similar, blank=True) For flexible classification.
    *   **`custom_fields`**: (JSONField, default=dict, blank=True) Stores values for dynamically defined custom fields relevant to the file (e.g., 'document_type', 'image_resolution').
*   **Meta**:
    *   `verbose_name = "Stored File"`
    *   `verbose_name_plural = "Stored Files"`
    *   `ordering = ['-created_at']`
*   **String Representation**: Return `original_filename`.
*   **Properties/Methods**:
    *   Consider adding properties like `@property def download_url(self):` which generates a temporary signed URL if using cloud storage, or a direct URL if appropriate. Logic depends heavily on the storage backend and security requirements.

### 3.2 Custom Field Schema Definition (External Mechanism)
*   Requirement for separate `CustomFieldDefinition` model/mechanism (possibly filtered by a 'File' context or MIME type) to define schema for file custom fields.

### 3.3 File Operations (Handled by API Views/Services)
*   **Upload**: API endpoint(s) required to handle file uploads. This logic will:
    1.  Receive the file binary.
    2.  Perform validation (file type, size limits).
    3.  Create a `FileStorage` model instance.
    4.  Save the file using the configured Django storage backend (which populates the `file` field path).
    5.  Populate metadata fields (`original_filename`, `file_size`, `mime_type`, `uploaded_by`, `organization`).
    6.  Save the `FileStorage` instance.
    7.  Return metadata (including ID and potentially download URL) to the client.
*   **Download/Access**: API endpoint(s) or logic required to serve files or provide access URLs. This must:
    1.  Check permissions (based on user, role, organization scope of the `FileStorage` record, and potentially the context of the model linking *to* the file).
    2.  Generate a secure download URL (e.g., pre-signed URL for cloud storage) or stream the file content.
*   **Deletion**: API endpoint(s) to delete `FileStorage` records. Must also delete the actual file from the storage backend. Requires permissions. `on_delete` behavior of models linking *to* this file needs consideration (often `SET_NULL`).
*   **Update**: Updating metadata (tags, custom fields) via API. Replacing the underlying file usually involves deleting the old `FileStorage` record and uploading a new one, unless versioning is implemented.

### 3.4 Validation
*   **Upload Validation**: File type (check MIME type against allowed list), file size (check against configured limits) must be performed during the upload process (in the view/serializer).
*   **Custom Field Validation**: Validate `custom_fields` data against schema during upload/update.

### 3.5 Relationships
*   Links *to* `User` (`uploaded_by`), `Organization` (via `OrganizationScoped`).
*   Is linked *to* by other models needing attachments via `ForeignKey` or `ManyToManyField` (e.g., `Product.images`, `Invoice.pdf_attachment`).

### 3.6 Out of Scope for this Model/PRD
*   **File Storage Backend Implementation**: Choice and configuration of S3, local disk, etc., is a deployment/configuration concern.
*   **File Versioning**: Requires a separate model (`FileVersion`) and logic. Treat as a separate feature/PRD.
*   **File Content Validation**: Virus scanning, content analysis are external processes.
*   **Detailed History**: Handled by Audit Log.

## 4. Technical Requirements

### 4.1 Data Management
*   Storage: `FileField` for path reference, standard fields for metadata, JSONField for custom fields. Actual file binaries stored via configured backend.
*   Indexing: `original_filename`, `mime_type`, `uploaded_by`, `organization`. **GIN index on `custom_fields`** if querying needed.
*   Database does *not* store file binary content directly.

### 4.2 Security
*   **Access Control**: Critical. Permissions to upload, download, delete files. Access checks must consider the `FileStorage` record's scope (`organization`) and potentially the context of the object *linking* to the file. Generating secure, time-limited download URLs (e.g., pre-signed URLs) is essential for cloud storage.
*   **Storage Security**: Secure configuration of the file storage backend (e.g., S3 bucket policies, private access).
*   **Audit Logging**: Log file uploads, downloads (if feasible/required), deletions, and metadata changes via Audit System.

### 4.3 Performance
*   Efficient metadata querying.
*   Upload/download performance depends heavily on the storage backend, network, and file sizes.
*   Efficient `custom_fields` querying (needs indexing).

### 4.4 Integration
*   **Storage Backend**: Requires integration with a Django storage backend (e.g., `django-storages` for S3, GCS, Azure).
*   **Primary Integration**: Serves as target for FK/M2M from other models requiring attachments.
*   **API Endpoint**: Provide RESTful API endpoints for upload, potentially download/access URL generation, metadata retrieval/update, and deletion. Structure carefully (e.g., `/api/v1/files/upload/`, `/api/v1/files/{id}/`, `/api/v1/files/{id}/access-url/`).
*   **Custom Field Schema Integration**: Integrates with `CustomFieldDefinition` mechanism.

## 5. Non-Functional Requirements

*   **Scalability**: Storage backend must scale to handle expected file volume and sizes. Metadata database must scale.
*   **Availability**: File access must be highly available.
*   **Durability**: File storage backend should provide high durability for stored files (e.g., S3 standard).
*   **Consistency**: Metadata in the DB should accurately reflect the stored file.
*   **Backup/Recovery**: Procedures must include both the database (metadata) and the file storage backend (binaries).

## 6. Success Metrics

*   Successful upload, storage, and retrieval of files.
*   Reliable access control enforcement.
*   Performant metadata querying and file access.
*   Successful linkage of files to relevant business entities.

## 7. API Documentation Requirements

*   Document `FileStorage` model fields (incl. `custom_fields`).
*   Document API endpoints for upload, download/access, metadata management, deletion. Detail expected request formats (e.g., multipart/form-data for upload) and responses.
*   Document validation rules (allowed types, max size).
*   Document authentication/permission requirements, especially for file access.
*   Document how `custom_fields` are handled.
*   Document how to discover custom field schemas (if applicable).

## 8. Testing Requirements

*   **Unit Tests**: Test `FileStorage` model, any custom properties/methods.
*   **Integration Tests**:
    *   Requires mocking the storage backend (`override_settings(DEFAULT_FILE_STORAGE=...)`).
    *   Test file upload API: successful upload, validation failures (type, size), metadata creation, org scoping.
    *   Test file access/download API: permission checks (allowed/denied), URL generation (if applicable).
    *   Test metadata update API.
    *   Test file deletion API (verify metadata deleted and file deleted from mock storage).
    *   Test **saving/validating `custom_fields`** during upload/update.
*   **Security Tests**: Test access control thoroughly, attempt unauthorized access/deletion, test security of download URL generation.

## 9. Deployment Requirements

*   **Migrations**: Standard migrations for `FileStorage` table, indexes (incl. JSONField).
*   **Storage Backend Configuration**: Configure `DEFAULT_FILE_STORAGE` and related settings (e.g., S3 bucket name, access keys, CDN) for each environment. Ensure appropriate permissions are set on the storage backend itself.
*   **Validation Configuration**: Configure allowed MIME types and maximum file sizes.
*   **Custom Field Schema Deployment**: Deploy `CustomFieldDefinition` mechanism.

## 10. Maintenance Requirements

*   Monitor storage usage and costs. Backups (DB and file storage).
*   Keep storage libraries (`django-storages`) updated.
*   Manage custom field schemas.

---