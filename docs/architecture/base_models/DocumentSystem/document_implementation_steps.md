
## Updated: `document_implementation_steps.md` (Fully Integrated with Centralized RBAC)

# Document System (Document Model) - Implementation Steps

## 1. Overview

**Model Name:**
`Document`

**Corresponding PRD:**
`document_system_prd.md` (Simplified version)

**Depends On:**
`Timestamped`, `Auditable`, **`OrganizationScoped`** (Done), `FileStorage` (Done), `Category` (Done), `Status` (Done), `Organization` (Done), `User` (Done), `ContentType` framework (Done), `django-taggit` (Done).
**Crucially depends on Centralized RBAC System:**
*   `core.rbac.permissions.has_perm_in_org`
*   `core.rbac.drf_permissions.HasModelPermissionInOrg`
*   `core.rbac.utils.get_user_request_context`
*   `core.serializers.mixins.OrganizationScopedSerializerMixin`
*   `core.viewsets.mixins.OrganizationScopedViewSetMixin`

**Key Features:**
Represents logical documents, linking metadata to a `FileStorage` record. Uses GenericForeignKey. Scoped by Organization. Tagging. CRUD via API secured by Org-Aware RBAC.

**Primary Location(s):**
`api/v1/base_models/common/` (or `api/v1/features/documents/` if moved to a feature app). Assume **`common`** as per original steps.

## 2. Prerequisites

[x] All prerequisite models/mixins and `django-taggit` are implemented/configured.
[x] The `common` app (or `documents` app) structure exists and is in `INSTALLED_APPS`.
[x] Factories for `User`, `Organization`, `FileStorage`, `Category`, `Group`, `OrganizationMembership` exist.
[x] `DocumentStatus` choices are defined.
[x] **Centralized RBAC components** are implemented and tested.
[x] Standard Django model permissions (`add_document`, `change_document`, `view_document`, `delete_document`) will be generated for the `Document` model and need to be assigned to appropriate `Group`s (Roles) by an Administrator.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)** Write Unit Tests verifying model structure, GFK, FKs, defaults, inheritance of `OrganizationScoped`, `tags`, `__str__`.
  [ ] Define the `Document` class in `api/v1/base_models/common/models.py` (or `documents/models.py`).
  [ ] **Ensure it inherits `OrganizationScoped`** (in addition to `Timestamped`, `Auditable`).
      ```python
      # api/v1/base_models/common/models.py (or documents/models.py)
      # ... imports ...
      from core.models import Timestamped, Auditable, OrganizationScoped # Ensure OrganizationScoped
      # ...

      class Document(OrganizationScoped, Timestamped, Auditable): # Add OrganizationScoped
          # ... (fields as defined in the original document_implementation_steps.md) ...

          class Meta:
              # ... (as before) ...
              permissions = [ # Add any custom model-level permissions here if needed
                  # ('can_version_document', 'Can create new versions of a document'),
              ]
      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `DocumentFactory` as before, ensuring the `organization` field is set (e.g., `organization = factory.SubFactory(OrganizationFactory)`). Handle GFK setup in the factory (e.g., by accepting a `content_object` parameter).
  [ ] **(Test)** Write simple tests for `DocumentFactory`.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Define `DocumentAdmin` as before. (Admin permission enforcement is secondary to API).
  [ ] **(Manual Test):** Verify Admin CRUD.

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations api.v1.base_models.common` (or `documents`).
  [ ] **Review migration:** Ensure `organization_id` FK is added.
  [ ] Run `python manage.py migrate` locally.

  ### 3.5 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write Unit/Integration Tests for `DocumentSerializer`.
      *   Test validation (FKs, GFK linking on create, versioning).
      *   Test representation (file URL, nested objects, tags, GFK representation).
      *   Test custom field handling.
      *   **Test context passing for `OrganizationScopedSerializerMixin`**.
  [ ] Define `DocumentSerializer` in `api/v1/base_models/common/serializers.py` (or `documents/serializers.py`).
  [ ] **Inherit from `OrganizationScopedSerializerMixin` and `TaggitSerializer`.**
      ```python
      # api/v1/base_models/common/serializers.py (or documents/serializers.py)
      from rest_framework import serializers
      from taggit.serializers import TagListSerializerField, TaggitSerializer
      from django.contrib.contenttypes.models import ContentType
      # Import the RBAC mixin
      from core.serializers.mixins import OrganizationScopedSerializerMixin
      from ..models import Document, FileStorage, Category # etc.
      from .serializers import FileStorageSerializer # Assuming FileStorageSerializer is defined

      class DocumentSerializer(OrganizationScopedSerializerMixin, TaggitSerializer, serializers.ModelSerializer):
          tags = TagListSerializerField(required=False)
          file_details = FileStorageSerializer(source='file', read_only=True)
          file = serializers.PrimaryKeyRelatedField(
              queryset=FileStorage.objects.all() # Note: May need further scoping based on request context
          )

          # GFK Representation (Read-only for simplicity, write handled by view)
          content_type_app_label = serializers.CharField(source='content_type.app_label', read_only=True, allow_null=True)
          content_type_model = serializers.CharField(source='content_type.model', read_only=True, allow_null=True)
          # content_object_id for retrieve (it's 'object_id' on model)
          content_object_id_display = serializers.CharField(source='object_id', read_only=True, allow_null=True)


          # GFK Write fields (handled by view's perform_create)
          # These are declared to be in the request body for creation, not directly mapped to model fields by DRF
          parent_content_type_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
          parent_object_id = serializers.CharField(write_only=True, required=False, allow_null=True)

          document_type_slug = serializers.SlugRelatedField(
              slug_field='slug', source='document_type', read_only=True, allow_null=True
          )
          document_type = serializers.PrimaryKeyRelatedField(
              queryset=Category.objects.filter(category_type='DOCUMENT_TYPE'),
              allow_null=True, required=False
          )


          class Meta:
              model = Document
              fields = [
                  'id', 'title', 'document_type', 'document_type_slug', 'status',
                  'file', 'file_details',
                  'version', 'description', 'tags', 'custom_fields',
                  'content_type', 'object_id', # Read-only representation of GFK link
                  'content_type_app_label', 'content_type_model', 'content_object_id_display',
                  'parent_content_type_id', 'parent_object_id', # Write-only for linking
                  'organization', # Handled by OrganizationScopedSerializerMixin
                  'created_at', 'updated_at',
              ]
              read_only_fields = (
                  'id', 'version', 'created_at', 'updated_at',
                  'file_details', 'content_type', 'object_id', # Read-only for GFK after creation
                  'content_type_app_label', 'content_type_model', 'content_object_id_display',
                  'document_type_slug',
                  # 'organization' will be made read-only or handled by OrganizationScopedSerializerMixin
              )

          # validate_custom_fields
          # validate GFK inputs if passed (e.g., ensure parent_content_type_id + parent_object_id point to valid object)
          # The OrganizationScopedSerializerMixin handles the 'organization' field during create/update.
      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.6 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests checking `/api/v1/documents/` URL, authentication.
  [ ] Define `DocumentViewSet` in `api/v1/base_models/common/views.py` (or `documents/views.py`).
  [ ] **Inherit `OrganizationScopedViewSetMixin`.**
  [ ] **Set `permission_classes` to use `HasModelPermissionInOrg`.**
      ```python
      # api/v1/base_models/common/views.py (or documents/views.py)
      from rest_framework import viewsets, permissions
      from django.contrib.contenttypes.models import ContentType
      from django.shortcuts import get_object_or_404
      # Import RBAC components
      from core.viewsets.mixins import OrganizationScopedViewSetMixin
      from core.rbac.drf_permissions import HasModelPermissionInOrg
      from ..models import Document, FileStorage
      from ..serializers import DocumentSerializer
      # Import filters

      class DocumentViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
          serializer_class = DocumentSerializer
          # queryset automatically filtered by OrganizationScopedViewSetMixin.get_queryset()
          queryset = Document.objects.select_related(
              'organization', 'document_type', 'file', 'content_type' # Added 'content_type'
          ).prefetch_related('tags').all()

          # Permissions handled by HasModelPermissionInOrg
          permission_classes = [permissions.IsAuthenticated, HasModelPermissionInOrg]

          # filter_backends, search_fields, ordering_fields as before
          # filterset_fields for GFK might need custom filter setup
          # e.g. content_type_id=X&object_id=Y
          # ...

          def perform_create(self, serializer):
              # Organization is set by OrganizationScopedViewSetMixin's perform_create
              # Here we handle linking the GFK parent if provided
              parent_ctype_id = serializer.validated_data.pop('parent_content_type_id', None)
              parent_object_id = serializer.validated_data.pop('parent_object_id', None)

              # Call super() to let OrganizationScopedViewSetMixin handle org and permission check
              super().perform_create(serializer) # This saves the instance

              # Now link the GFK if data was provided
              instance = serializer.instance
              if parent_ctype_id and parent_object_id:
                  try:
                      parent_content_type = get_object_or_404(ContentType, pk=parent_ctype_id)
                      # TODO: Validate parent_content_type is a valid target for documents?
                      # TODO: Validate parent_object_id exists for that content_type?
                      #       (serializer validation might be better place for this)
                      instance.content_type = parent_content_type
                      instance.object_id = parent_object_id
                      instance.save(update_fields=['content_type', 'object_id'])
                  except Http404:
                      # Or raise ValidationError from serializer
                      pass # Handle error appropriately

          # Override perform_update for GFK linking if allowed, and version increment
      ```
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.7 URL Routing (`urls.py`)

  [ ] Create appropriate URL file. Register `DocumentViewSet` with router. Include in main API URLs.
  [ ] **(Test):** Rerun basic API tests.

  ### 3.8 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests covering:
      *   **LIST:**
          *   Verify user only sees documents from organizations they are a member of.
          *   Verify user needs `common.view_document` permission *in their selected organization context*.
          *   Test filtering by type, status, tags, and GFK parent (e.g., `?content_type_id=X&object_id=Y`).
      *   **CREATE:**
          *   Verify user needs `common.add_document` permission *in their selected organization context* (or target org if explicitly set).
          *   Test associating with `FileStorage` (by `file` ID).
          *   Test setting parent GFK via `parent_content_type_id` and `parent_object_id`.
          *   Verify document is created in the correct organization.
      *   **RETRIEVE:**
          *   Verify user can only retrieve a document if it's in an organization they are a member of.
          *   Verify user needs `common.view_document` permission *in the document's organization*.
          *   Check `file_details` included.
      *   **UPDATE (PUT/PATCH):**
          *   Verify user needs `common.change_document` permission *in the document's organization*.
          *   Test updating metadata (title, description, status, custom fields, tags).
      *   **DELETE:**
          *   Verify user needs `common.delete_document` permission *in the document's organization*.
      *   Test GFK validation (e.g., attempting to link to non-existent parent).
  [ ] Implement/Refine ViewSet (`perform_create`, `perform_update`), Serializer (GFK validation), and any supporting logic.
  [ ] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/base_models/common` or `documents`). Focus on ViewSet/Serializer RBAC integration.
[ ] Manually test API endpoints with different users/roles/orgs, focusing on GFK linking and permissions.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs (GFK validation in serializer, version increment logic).
[ ] Create Pull Request.
[ ] Update API documentation, clearly stating Org-Aware permissions and GFK linking.
[ ] Plan document-related workflows or content processing if needed.

---