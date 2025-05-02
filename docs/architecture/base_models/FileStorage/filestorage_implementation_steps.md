

# FileStorage - Implementation Steps

## 1. Overview

**Model Name:**
`FileStorage`

**Corresponding PRD:**
`file_storage_prd.md` (Revised - Final)

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationScoped` (Done), `User` (Done), `Organization` (Done), `django-taggit` (Done). Requires configured Django File Storage backend. Requires Org-Aware RBAC function.

**Key Features:**
Stores file metadata, links to binary via `FileField` respecting configured storage backend. Org-scoped. Supports tags, custom fields. Includes upload/access API patterns with Org-Aware permission checks.

**Primary Location(s):**
`api/v1/base_models/common/fileStorage/fileStorage` (Assuming `common` app hosts shared base models)

## 2. Prerequisites

[ ] Verify prerequisites models/mixins and `django-taggit` are implemented/configured.
[ ] Ensure `common` app exists and is in `INSTALLED_APPS`. Ensure `factory-boy` setup.
[ ] **Configure File Storage Backend Strategy:** (As detailed in PRD) Dev/Test use `FileSystemStorage`. Prod/Staging configurable via Env Var. Define settings (`MEDIA_ROOT/URL`, `MAX_UPLOAD_SIZE`, etc.).
[ ] Set up local `MEDIA_ROOT` directory and Docker volume mount if needed. Add `media/` to `.gitignore`.
[ ] Ensure Org-Aware RBAC function (e.g., `has_perm_in_org`) is implemented or mockable.

## 3. Implementation Steps (TDD Workflow)

  *(Model -> Factory -> Admin -> Migrations -> Serializer -> API Views)*

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)** Write Unit Tests verifying model structure, fields, inheritance, `__str__`, `@property filename`.
  [ ] Define `FileStorage` model in `api/v1/base_models/common/fileStorage/fileStoragemodels.py` (inheriting TS/A/OS, including `FileField`, metadata, tags, custom fields).
  [ ] Implement `get_secure_url(self, requesting_user)` method placeholder (permission logic will be added in serializer/view tests).
  [ ] Run tests; expect pass. Refactor.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `FileStorageFactory` using `ContentFile` for the `file` field. Ensure `organization` is set.
  [ ] **(Test)** Write simple tests ensuring factory creates instances.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Define `FileStorageAdmin` (mostly read-only fields).
  [ ] **(Manual Test):** Verify registration in Admin.

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations api.v1.base_models.common`.
  [ ] **Review generated migration file carefully.**
  [ ] Run `python manage.py migrate` locally.

  ### 3.5 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write Unit/Integration Tests for `FileStorageSerializer`.
      *   Test representation (incl. `download_url`, `file_size_display`). Test read-only fields.
      *   **Test `get_download_url`:** Mock the request context. Use `mocker.patch` to mock the Org-Aware RBAC function (`has_perm_in_org`). Test cases where permission check returns `True` (assert URL returned) and `False` (assert `None` or error raised). Test with different users/objects.
      *   Test custom field handling (if metadata updatable).
  [ ] Define `FileStorageSerializer` in `api/v1/base_models/common/fileStorage/fileStorageserializers.py` including `SerializerMethodField` for `download_url`.
  [ ] **Implement `get_download_url`:**
      *   Get `request` from `self.context`. Get `user = request.user`.
      *   Check `has_perm_in_org(user, 'common.view_filestorage', obj.organization)` (adjust permission codename and import path).
      *   If permitted, return `obj.file.url`. Otherwise, return `None`.
  [ ] Implement `validate_custom_fields` if metadata updates are allowed.
  [ ] Run tests; expect pass. Refactor `get_download_url` and permission logic.

  ### 3.6 API ViewSet/View Definition (`views.py`)

  [ ] **(Test First - Upload)** Write API tests for `FileUploadView` (`POST /api/v1/files/upload/`).
      *   Verify success (201, response metadata). Test validation (type, size). Test auth required.
      *   **Test Permissions:** Mock the Org-Aware RBAC function. Verify `perform_create` checks `add_filestorage` permission in the target organization before saving. Test success/failure (403).
      *   Verify `organization` and `uploaded_by` fields are set correctly.
  [ ] Define `FileUploadView` (`generics.CreateAPIView`). **Ensure it sets the organization correctly** (e.g., from user's primary org, or a required request parameter). Override `perform_create` to explicitly check the `add_filestorage` permission using the Org-Aware RBAC function *before* calling `serializer.save()`.
  [ ] Run upload tests; expect pass. Refactor view.
  [ ] **(Test First - Metadata/Access)** Write API tests for `FileStorageViewSet` (`ReadOnlyModelViewSet` on `/api/v1/files/`).
      *   Test LIST: Verify `OrganizationScopedViewSetMixin` filters results correctly. Test permissions (requires `view_filestorage`).
      *   Test RETRIEVE: Verify standard DRF `permission_classes` (using Org-Aware checker) correctly check `view_filestorage` on the object's organization before returning metadata. Test success (200) and failure (403/404). Verify `download_url` field reflects permissions checked by the serializer.
  [ ] Define `FileStorageViewSet` inheriting `OrganizationScopedViewSetMixin` and `ReadOnlyModelViewSet`. Add appropriate `permission_classes` that utilize the Org-Aware RBAC checker for `view_filestorage`.
  [ ] Run metadata/access tests; expect pass. Refactor.
  [ ] **(Test First - Delete)** Write API tests for `DELETE /api/v1/files/{id}/` (add destroy action to ViewSet).
      *   Verify requires `delete_filestorage` permission (checked by standard DRF permissions using Org-Aware checker on the object's organization). Test success (204) and failure (403/404).
      *   Verify metadata deletion. Verify storage backend `delete` is called (mock).
  [ ] Add `DestroyModelMixin` to `FileStorageViewSet`. Override `perform_destroy` to call `instance.file.delete(save=False)` *after* standard permission checks pass but *before* `super().perform_destroy(instance)`.
  [ ] Run delete tests; expect pass. Refactor.

  ### 3.7 URL Routing (`urls.py`)

  [ ] Define URL patterns for upload view and the `FileStorageViewSet` router in `api/v1/base_models/common/fileStorage/fileStorageurls.py`.
  [ ] **(Test):** Rerun basic API tests.

  ### 3.8 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] Ensure comprehensive API tests cover upload (incl. `add` permission), metadata retrieval/list (incl. `view` permission & Org Scoping), download URL generation (incl. `view` permission), deletion (incl. `delete` permission), validation errors, and `custom_fields` handling (if metadata is updatable). Focus on verifying permissions using the **Org-Aware RBAC context**.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`), ensuring storage is mocked or uses test settings. Ensure RBAC function is mocked or real implementation used correctly.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/base_models/common`). Pay attention to permission logic in views/serializers.
[ ] Manually test upload/download flow with local `FileSystemStorage`. Test permissions with different user roles/org memberships via API client.
[ ] Review API documentation draft, ensuring permission requirements are clearly stated.

## 5. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Implement file attachment linking (FK/M2M) on other models (`Document`, `Comment`, `UserProfile` etc.).

---