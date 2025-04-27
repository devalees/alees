# FileStorage - Implementation Steps

## 1. Overview

**Model Name:**
`FileStorage`

**Corresponding PRD:**
`file_storage_prd.md` (Revised - Local Primary, Cloud Compatible)

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `Organization`, `django-taggit`. Requires configured Django File Storage backend (supporting local FS and cloud).

**Key Features:**
Stores file metadata, links to binary via `FileField` respecting configured storage backend. Org-scoped. Supports tags, custom fields. Includes upload/access API patterns.

**Primary Location(s):**
`api/v1/base_models/common/fileStorage/`

## 2. Prerequisites

[ ] Verify prerequisites models/mixins and `django-taggit` are implemented/configured.
[ ] Ensure `common` app exists. Ensure `factory-boy` setup.
[ ] **Configure File Storage Backend Strategy:**
    *   Set `DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'` in `settings/dev.py` and `settings/test.py`.
    *   Set `MEDIA_ROOT` and `MEDIA_URL` in `settings/dev.py`.
    *   Set `DEFAULT_FILE_STORAGE` via environment variable in `settings/prod.py` / `staging.py` (allowing override to cloud backend).
    *   Define `MAX_UPLOAD_SIZE`, `ALLOWED_MIME_TYPES` in settings.
[ ] Set up local `MEDIA_ROOT` directory and configure Docker volume mount if using Docker. Add `media/` to `.gitignore`.

## 3. Implementation Steps (TDD Workflow)

  *(Model -> Factory -> Admin -> Migrations -> Serializer -> API Views)*

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)** Write Unit Tests verifying model creation, fields (`FileField`, metadata, FKs, M2M `tags`, `custom_fields`), inheritance (`Timestamped`, `Auditable`, `OrganizationScoped`), `__str__`, `@property filename`.
  [ ] Define `FileStorage` model in `api/v1/base_models/common/fileStorage/models.py` (as per previous correct version, including `Timestamped`, `Auditable`, `OrganizationScoped`, `TaggableManager`, `custom_fields`, and `FileField` using `get_upload_path`).
  [ ] Implement `@property def url(self)` - This property should primarily call `self.file.url` but **must** be wrapped in permission check logic (likely requiring access to the request user, making it tricky as a simple model property - better handled in Serializer or View). For now, implement basic `return self.file.url` and note security check happens elsewhere.
  [ ] Run tests; expect pass. Refactor.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `FileStorageFactory` in `api/v1/base_models/common/fileStorage/tests/factories.py` (as per previous correct version, using `ContentFile`).
  [ ] **(Test)** Write simple tests ensuring factory creates instances.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Define `FileStorageAdmin` in `api/v1/base_models/common/fileStorage/admin.py` (as per previous correct version - mostly read-only fields).
  [ ] **(Manual Test):** Verify registration in Admin. Confirm files aren't managed directly here.

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations api.v1.base_models.common`.
  [ ] **Review generated migration file carefully.**
  [ ] Run `python manage.py migrate` locally.

  ### 3.5 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write Unit/Integration Tests for `FileStorageSerializer`. Test representation (including `download_url`, `file_size_display`), read-only fields, custom field handling. Test `get_download_url` logic (requires mocking request/user/permissions).
  [ ] Define `FileStorageSerializer` in `api/v1/base_models/common/fileStorage/serializers.py` (as per previous correct version, including `SerializerMethodField` for `download_url` and `file_size_display`).
  [ ] **Implement `get_download_url`:** This method *must* get the `request` from `self.context`. Check user permissions based on `request.user` and the `obj` (`FileStorage` instance) and potentially its linked parent object (if context available). If permitted, return `obj.file.url` (which generates correct local or signed cloud URL). If not permitted, return `None` or raise PermissionDenied (depending on desired behavior).
  [ ] Implement `validate_custom_fields` if metadata updates are allowed via API.
  [ ] Run tests; expect pass. Refactor `get_download_url`.

  ### 3.6 API ViewSet/View Definition (`views.py`)

  [ ] **(Test First - Upload)** Write API tests for `FileUploadView` (`POST /api/v1/files/upload/`). Verify success (201, response metadata), validation (type, size), auth, Org Scoping. Ensure tests run against the test `FileSystemStorage`.
  [ ] Define `FileUploadView` (`generics.CreateAPIView`) in `api/v1/base_models/common/fileStorage/views.py` (as per previous correct version). Ensure it performs size/type validation using settings, sets `organization`, `uploaded_by`, and saves the file via the serializer/model instance save.
  [ ] Run upload tests; expect pass. Refactor view.
  [ ] **(Test First - Metadata/Access)** Write API tests for potential read-only ViewSet (`FileStorageViewSet` on `/api/v1/files/`) or a dedicated URL lookup view (`/api/v1/files/{id}/access-url/`).
      *   Test retrieving metadata.
      *   Test getting a valid `download_url` (mocking storage `.url` if needed).
      *   Test permissions and Org Scoping (user should only see/access files in their org or linked to objects they can access).
  [ ] Define `FileStorageViewSet` (e.g., `ReadOnlyModelViewSet` inheriting `OrganizationScopedViewSetMixin`) OR a dedicated `FileAccessView(APIView)`. Implement permission checks before returning metadata or calling `get_download_url` logic.
  [ ] Run metadata/access tests; expect pass. Refactor.
  [ ] **(Test First - Delete)** Write API tests for `DELETE /api/v1/files/{id}/`. Verify 204, metadata deletion, *mocked* storage backend file deletion (`mock.patch('django.core.files.storage.default_storage.delete')`). Test permissions.
  [ ] Implement deletion logic in `FileStorageViewSet` or dedicated view. Ensure `instance.file.delete(save=False)` is called *after* permission checks but *before* or *during* `instance.delete()`.
  [ ] Run delete tests; expect pass. Refactor.

  ### 3.7 URL Routing (`urls.py`)

  [ ] Define URL patterns for upload view, and potentially metadata ViewSet/access view in `api/v1/base_models/common/fileStorage/urls.py`.
  [ ] **(Test):** Rerun basic API tests.

  ### 3.8 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] Ensure comprehensive API tests cover upload, metadata retrieval, download URL generation (and permissions), deletion (and permissions), Org Scoping, validation errors, and `custom_fields` handling (if metadata is updatable).

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`), ensuring storage is mocked or uses test settings correctly.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/base_models/common`).
[ ] Manually test upload/download flow with local `FileSystemStorage`. Verify files land in `MEDIA_ROOT`. Test permissions via API client.
[ ] *(Optional)* Manually configure local dev environment for S3/MinIO and test basic upload/download to verify cloud compatibility.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs (Refine permission checks for download URLs).
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Implement file attachment linking (FK/M2M) on other models.

--- END OF FILE filestorage_implementation_steps.md ---