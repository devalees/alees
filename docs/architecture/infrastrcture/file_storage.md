# File Storage Strategy (Local Primary, Cloud Compatible)

## 1. Overview

*   **Purpose**: To define the strategy for storing and serving user-uploaded files (`FileField`, `ImageField`) associated with ERP models, using the **local filesystem as the primary method** while ensuring **compatibility with cloud storage backends** (like AWS S3) for future scalability or specific deployment needs.
*   **Scope**: Configuration of Django's storage backend system, Django integration, security considerations for both local and potential cloud storage, local development setup, testing, and deployment considerations.
*   **Chosen Technology**:
    *   **Default/Development/Testing:** Django's built-in **`FileSystemStorage`**.
    *   **Production/Staging (Optional/Future):** Cloud Storage (AWS S3, GCS, Azure Blob) via **`django-storages`** (e.g., `storages.backends.s3boto3.S3Boto3Storage`). The system must work seamlessly with either backend based on configuration.

## 2. Core Requirements

*   **Reliable Storage**: Store uploaded files persistently.
*   **Django Integration**: Work seamlessly with Django's `FileField`, `ImageField`, and ORM.
*   **Secure Access**: Control access to files based on application permissions, preventing direct unauthorized access.
*   **Configuration Flexibility**: Allow switching between local filesystem storage and cloud storage purely through Django settings and environment variables without requiring application code changes.
*   **Scalability Foundation**: While starting local, the approach shouldn't preclude scaling to cloud storage later.

## 3. Configuration Strategy (`config/settings/`)

*   **`DEFAULT_FILE_STORAGE` Setting**: This setting controls the active storage backend.
    *   In `settings/base.py` or `settings/dev.py`: **Default to `django.core.files.storage.FileSystemStorage'`.**
        ```python
        # settings/base.py (or dev.py)
        DEFAULT_FILE_STORAGE = env('DJANGO_DEFAULT_FILE_STORAGE', default='django.core.files.storage.FileSystemStorage')
        ```
    *   In `settings/prod.py` / `settings/staging.py`: Override this setting using an environment variable if cloud storage is deployed for that environment.
        ```python
        # settings/prod.py
        DEFAULT_FILE_STORAGE = env('DJANGO_DEFAULT_FILE_STORAGE') # Must be set in prod env if using S3
        # Example value in prod .env: DJANGO_DEFAULT_FILE_STORAGE=storages.backends.s3boto3.S3Boto3Storage
        ```
*   **Local Storage Settings (`settings/base.py` or `dev.py`):**
    *   `MEDIA_URL = '/media/'` (URL prefix for serving files via Django dev server or dedicated web server).
    *   `MEDIA_ROOT = BASE_DIR / 'media'` (Filesystem path where files are stored locally). Load from `env('MEDIA_ROOT', default=...)` if customization needed.
*   **Cloud Storage Settings (`settings/prod.py` - Loaded via Env Vars):**
    *   Only required if `DEFAULT_FILE_STORAGE` is set to a cloud backend.
    *   Include `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`, `AWS_S3_CUSTOM_DOMAIN`, `AWS_DEFAULT_ACL = 'private'`, `AWS_S3_FILE_OVERWRITE = False`, `AWS_QUERYSTRING_AUTH = True`, etc. **All loaded from environment variables.**
*   **File Validation Settings (`settings/base.py`):**
    *   Define `MAX_UPLOAD_SIZE` (e.g., `10 * 1024 * 1024` for 10MB).
    *   Define `ALLOWED_MIME_TYPES` (list of strings). Load from environment if they need to be configurable per deployment.

## 4. Local Development Setup (`docker-compose.yml`)

*   **Default:** Use `FileSystemStorage`.
*   **Volume Mount:** Mount a local host directory (e.g., `./media/`) to the container's `MEDIA_ROOT` path using Docker Compose volumes to persist uploads locally.
    ```yaml
    # docker-compose.yml
    services:
      api:
        # ... other settings ...
        volumes:
          - .:/app
          - ./media:/app/media # Mount local media dir to container's MEDIA_ROOT
        environment:
          # Explicitly set FileSystemStorage for local dev via .env is also an option
          # DJANGO_DEFAULT_FILE_STORAGE: 'django.core.files.storage.FileSystemStorage'
          MEDIA_ROOT: /app/media
          MEDIA_URL: /media/
          # ... other env vars ...
    ```
*   **`.gitignore`:** Add `media/` to `.gitignore`.
*   **(Optional) S3 Compatibility:** Include a MinIO service in `docker-compose.yml` for developers who want to test S3 compatibility locally by changing their `.env` file to point `DEFAULT_FILE_STORAGE` to S3 and configuring S3 settings for MinIO.

## 5. Application Code Interaction

*   **Abstraction:** Code **must** interact with files via Django's storage abstraction layer:
    *   Model fields: `models.FileField`, `models.ImageField`.
    *   Accessing URL: Always use `instance.file.url`. This method correctly returns the local `/media/...` URL when using `FileSystemStorage` and a (potentially pre-signed) cloud URL when using `S3Boto3Storage` (if configured for query string auth).
    *   Direct Operations: Use `instance.file.save()`, `instance.file.delete()`, `instance.file.open()` or `default_storage` methods.
*   **Avoid Backend Specific Code:** Do not write code that directly imports or calls `boto3` or checks `isinstance(default_storage, S3Boto3Storage)` unless absolutely necessary for a specific, unavoidable feature (like generating upload forms with direct-to-S3 capability, which is advanced).

## 6. Security Considerations

*   **Local `FileSystemStorage`:**
    *   The Django development server (`runserver`) serves `/media/` files only if `DEBUG=True`.
    *   **Production (with Local Storage):** This is **NOT RECOMMENDED** for scalability or security if serving directly from Django. A dedicated web server (Nginx, Apache) **must** be configured to serve the `MEDIA_ROOT` directory. Access control must be carefully implemented at the web server level or by having Django views broker access (e.g., using `X-Accel-Redirect` with Nginx) which check permissions before serving the file. Direct filesystem access via `/media/` URLs is insecure without proper controls.
*   **Cloud Storage:**
    *   Configure buckets for **private** access.
    *   Rely on **pre-signed URLs** (`AWS_QUERYSTRING_AUTH = True`) generated via `instance.file.url` for secure, time-limited download access brokered by the application's permission checks.
*   **General:** Apply RBAC and Org Scoping checks within API views/serializers *before* granting access to file metadata or generating download URLs. Validate uploads (size, type). Consider virus scanning. Secure cloud credentials.

## 7. Monitoring Considerations

*   **Local Storage:** Monitor disk space usage on the server hosting `MEDIA_ROOT`. Monitor application logs for file operation errors.
*   **Cloud Storage:** Use cloud provider monitoring tools.

## 8. Backup & Recovery Strategy

*   **Local Storage:** The directory defined by `MEDIA_ROOT` **must** be included in the regular server backup strategy alongside the database.
*   **Cloud Storage:** Rely on provider durability. Enable versioning. Back up the **metadata database** (`FileStorage` model table) regularly.

## 9. Testing Considerations

*   Use `FileSystemStorage` configured with a **temporary directory** in `settings/test.py`. `pytest-django` or fixtures can manage creating/deleting this temp directory.
    ```python
    # settings/test.py
    import tempfile
    MEDIA_ROOT = tempfile.mkdtemp() # Creates a unique temp dir for test run
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    ```
*   Mock cloud storage using libraries like `moto` only for tests *specifically* verifying cloud integration aspects (e.g., signed URL generation nuances). Most tests should work against the `FileSystemStorage` mock.

## 10. Deployment Considerations

*   **Local Storage Deployment:**
    *   Ensure the `MEDIA_ROOT` directory exists and has correct write permissions for the application user.
    *   Configure Nginx/Apache (or other web server) to serve files from `MEDIA_ROOT` at the `/media/` URL path, **ideally with access control checks** (e.g., `internal` directive with `X-Accel-Redirect` handled by Django).
    *   Ensure backups include `MEDIA_ROOT`. Consider shared storage (NFS, EFS) if deploying multiple application instances that need access to the same `MEDIA_ROOT`.
*   **Cloud Storage Deployment:**
    *   Configure `DEFAULT_FILE_STORAGE` setting via environment variable.
    *   Configure all necessary cloud credentials and bucket settings via secure environment variables/secrets management.
    *   Configure bucket policies/ACLs and potentially CDN/CORS as needed.

--- END OF FILE file_storage_strategy.md ---