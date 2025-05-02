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
`api/v1/base_models/common/fileStorage/fileStorage` (Assuming `common` app hosts shared base models) - Corrected to `api/v1/base_models/common/fileStorage/`

## 2. Prerequisites

[x] Verify prerequisites models/mixins and `django-taggit` are implemented/configured. (Assumed based on tests passing)
[x] Ensure `file_storage` app exists and is in `INSTALLED_APPS`. Ensure `factory-boy` setup. (Done during troubleshooting)
[x] **Configure File Storage Backend Strategy:** (As detailed in PRD) Dev/Test use `FileSystemStorage`. Prod/Staging configurable via Env Var. Define settings (`MEDIA_ROOT/URL`, `MAX_UPLOAD_SIZE`, etc.). (Verified test uses temp dir)
[x] Set up local `MEDIA_ROOT` directory and Docker volume mount if needed. Add `media/` to `.gitignore`. (Assumed Docker setup handles this)
[x] Ensure Org-Aware RBAC function (e.g., `has_perm_in_org`) is implemented or mockable. (Mocked/Placeholders used)

## 3. Implementation Steps (TDD Workflow)

  *(Model -> Factory -> Admin -> Migrations -> Serializer -> API Views)*

  ### 3.1 Model Definition (`models.py`)

  [x] **(Test First)** Write Unit Tests verifying model structure, fields, inheritance, `__str__`, `@property filename`.
  [x] Define `FileStorage` model in `api/v1/base_models/common/fileStorage/models.py` (inheriting TS/A/OS, including `FileField`, metadata, tags, custom fields).
  [x] Implement `get_secure_url(self, requesting_user)` method placeholder (permission logic will be added in serializer/view tests).
  [x] Run tests; expect pass. Refactor.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [x] Define `FileStorageFactory` using `ContentFile` for the `file` field. Ensure `organization` is set.
  [x] **(Test)** Write simple tests ensuring factory creates instances.

  ### 3.3 Admin Registration (`admin.py`)

  [x] Define `FileStorageAdmin` (mostly read-only fields).
  [ ] **(Manual Test):** Verify registration in Admin. (Needs manual check)

  ### 3.4 Migrations

  [x] Run `python manage.py makemigrations file_storage`.
  [x] **Review generated migration file carefully.**
  [x] Run `python manage.py migrate` locally.

  ### 3.5 Serializer Definition (`serializers.py`)

  [x] **(Test First)** Write Unit/Integration Tests for `FileStorageSerializer`.
      *   [x] Test representation (incl. `download_url`, `file_size_display`). Test read-only fields.
      *   [x] **Test `get_download_url`:** Mock the request context. Use `mocker.patch` to mock the Org-Aware RBAC function (`has_perm_in_org`). Test cases where permission check returns `True` (assert URL returned) and `False` (assert `None` or error raised). Test with different users/objects.
      *   [x] Test custom field handling (if metadata updatable).
  [x] Define `FileStorageSerializer` in `api/v1/base_models/common/fileStorage/serializers.py` including `SerializerMethodField` for `download_url`.
  [x] **Implement `get_download_url`:**
      *   [x] Get `request` from `self.context`. Get `user = request.user`.
      *   [x] Check `has_perm_in_org(user, 'common.view_filestorage', obj.organization)` (adjust permission codename and import path).
      *   [x] If permitted, return `obj.file.url`. Otherwise, return `None`.
  [x] Implement `validate_custom_fields` if metadata updates are allowed.
  [x] Run tests; expect pass. Refactor `get_download_url` and permission logic.

  ### 3.6 API ViewSet/View Definition (`views.py`)

  [x] **(Test First - Upload)** Write API tests for `FileUploadView` (`POST /api/v1/files/upload/`).
      *   [x] Verify success (201, response metadata). Test validation (type, size). Test auth required.
      *   [x] **Test Permissions:** Mock the Org-Aware RBAC function. Verify `perform_create` checks `add_filestorage` permission in the target organization before saving. Test success/failure (403).
      *   [x] Verify `organization` and `uploaded_by` fields are set correctly.
  [x] Define `FileUploadView` (`generics.CreateAPIView`). **Ensure it sets the organization correctly** (e.g., from user's primary org, or a required request parameter). Override `perform_create` to explicitly check the `add_filestorage` permission using the Org-Aware RBAC function *before* calling `serializer.save()`.
  [x] Run upload tests; expect pass. Refactor view.
  [x] **(Test First - Metadata/Access)** Write API tests for `FileStorageViewSet` (`ReadOnlyModelViewSet` on `/api/v1/files/`).
      *   [x] Test LIST: Verify `OrganizationScopedViewSetMixin` filters results correctly. Test permissions (requires `view_filestorage`).
      *   [x] Test RETRIEVE: Verify standard DRF `permission_classes` (using Org-Aware checker) correctly check `view_filestorage` on the object's organization before returning metadata. Test success (200) and failure (403/404). Verify `download_url` field reflects permissions checked by the serializer.
  [x] Define `FileStorageViewSet` inheriting `OrganizationScopedViewSetMixin` and `ReadOnlyModelViewSet`. Add appropriate `permission_classes` that utilize the Org-Aware RBAC checker for `view_filestorage`.
  [x] Run metadata/access tests; expect pass. Refactor.
  [x] **(Test First - Delete)** Write API tests for `DELETE /api/v1/files/{id}/` (add destroy action to ViewSet).
      *   [x] Verify requires `delete_filestorage` permission (checked by standard DRF permissions using Org-Aware checker on the object's organization). Test success (204) and failure (403/404).
      *   [x] Verify metadata deletion. Verify storage backend `delete` is called (mock).
  [x] Add `DestroyModelMixin` to `FileStorageViewSet`. Override `perform_destroy` to call `instance.file.delete(save=False)` *after* standard permission checks pass but *before* `super().perform_destroy(instance)`.
  [x] Run delete tests; expect pass. Refactor.

  ### 3.7 URL Routing (`urls.py`)

  [x] Define URL patterns for upload view and the `FileStorageViewSet` router in `api/v1/base_models/common/fileStorage/urls.py`.
  [x] **(Test):** Rerun basic API tests. (Done implicitly)

  ### 3.8 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [x] Ensure comprehensive API tests cover upload (incl. `add` permission), metadata retrieval/list (incl. `view` permission & Org Scoping), download URL generation (incl. `view` permission), deletion (incl. `delete` permission), validation errors, and `custom_fields` handling (if metadata is updatable). Focus on verifying permissions using the **Org-Aware RBAC context**.

## 4. Final Checks

[x] Run the *entire* test suite (`pytest`), ensuring storage is mocked or uses test settings. Ensure RBAC function is mocked or real implementation used correctly.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/base_models/common/fileStorage`). Pay attention to permission logic in views/serializers.
[ ] Manually test upload/download flow with local `FileSystemStorage`. Test permissions with different user roles/org memberships via API client.
[ ] Review API documentation draft, ensuring permission requirements are clearly stated.

## 5. Follow-up Actions

[ ] Address TODOs (e.g., replace placeholder permissions/mixins).
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Implement file attachment linking (FK/M2M) on other models (`Document`, `Comment`, `UserProfile` etc.).

---