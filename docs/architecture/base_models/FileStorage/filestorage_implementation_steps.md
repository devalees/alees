Okay, let's generate the implementation steps for the `FileStorage` model. This focuses on storing file *metadata* and integrating with Django's storage backend system.

**Decision Reminder:** The PRD assumes `OrganizationScoped` is needed. These steps include that inheritance. If files are global, remove `OrganizationScoped` inheritance and related Org Scoping logic/tests.

--- START OF FILE filestorage_implementation_steps.md ---

# FileStorage - Implementation Steps

## 1. Overview

**Model Name:**
`FileStorage`

**Corresponding PRD:**
`file_storage_prd.md` (Simplified version)

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationScoped` (Abstract Base Models), `User`, `Organization`, `django-taggit` (if using tags). Requires configuration of Django File Storage backend.

**Key Features:**
Stores metadata about uploaded files (original name, size, type, uploader, org scope). Uses Django's `FileField` to link to the actual file binary managed by a configured storage backend (e.g., S3, local). Supports tagging and custom fields. Provides foundation for file attachments.

**Primary Location(s):**
`api/v1/base_models/common/` (Assuming `common` app)

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `Organization`) are implemented and migrated.
[ ] Ensure `django-taggit` is installed and configured if using tags.
[ ] Ensure the `common` app structure exists.
[ ] Ensure `factory-boy` is set up. Factories for `User`, `Organization` exist.
[ ] **Configure File Storage Backend:**
    *   Define `DEFAULT_FILE_STORAGE` in `settings/dev.py` (e.g., `FileSystemStorage`) and `settings/prod.py`/`staging.py` (e.g., `S3Boto3Storage`).
    *   Configure necessary backend settings (e.g., `MEDIA_ROOT` for local, `AWS_STORAGE_BUCKET_NAME` etc. for S3) via environment variables (as per `file_storage_setup.md` strategy).
[ ] Define application settings for `MAX_UPLOAD_SIZE` and `ALLOWED_MIME_TYPES` (e.g., in `settings/base.py`).

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `common`) verifying:
      *   `FileStorage` instance creation.
      *   `file` field is a `FileField`.
      *   Metadata fields (`original_filename`, `file_size`, `mime_type`) exist and allow appropriate values (null/blank).
      *   FKs (`uploaded_by`, `organization`) link correctly.
      *   `tags` manager exists. `custom_fields` defaults to `{}`.
      *   `__str__` works. Inheritance works.
      Run; expect failure.
  [ ] Define the `FileStorage` class in `api/v1/base_models/common/models.py`.
  [ ] Add inheritance: `Timestamped`, `Auditable`, `OrganizationScoped`.
      ```python
      # api/v1/base_models/common/models.py
      import os
      import uuid
      from django.conf import settings
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from taggit.managers import TaggableManager
      from core.models import Timestamped, Auditable, OrganizationScoped # Adjust path

      def get_upload_path(instance, filename):
          """Generates unique upload path like: org_<id>/files/<uuid>.<ext>"""
          ext = filename.split('.')[-1]
          uid = uuid.uuid4()
          org_id = instance.organization_id or 'unknown_org'
          # Consider adding year/month for better partitioning if volume is huge
          return os.path.join(f'org_{org_id}', 'files', f'{uid}.{ext}')

      class FileStorage(Timestamped, Auditable, OrganizationScoped):
          # Organization field inherited from OrganizationScoped
          # Created_by/updated_by from Auditable (uploaded_by is redundant but explicit)
          # Created_at/updated_at from Timestamped

          file = models.FileField(
              _("File"),
              upload_to=get_upload_path, # Use function for dynamic unique paths
              max_length=500 # Allow for longer S3 paths etc.
          )
          original_filename = models.CharField(
              _("Original Filename"), max_length=255, db_index=True
          )
          file_size = models.PositiveBigIntegerField( # Use BigIntegerField for large files
              _("File Size (bytes)"), null=True # Populated after upload
          )
          mime_type = models.CharField(
              _("MIME Type"), max_length=100, blank=True, db_index=True
          )
          # Explicit link to uploader, Auditable.created_by serves similar purpose
          uploaded_by = models.ForeignKey(
              settings.AUTH_USER_MODEL,
              verbose_name=_("Uploaded By"),
              related_name='uploaded_files',
              on_delete=models.SET_NULL,
              null=True, blank=True # System uploads might not have a user
          )
          tags = TaggableManager(blank=True, verbose_name=_("Tags"))
          custom_fields = models.JSONField(
              _("Custom Fields"), default=dict, blank=True
          )

          class Meta:
              verbose_name = _("Stored File")
              verbose_name_plural = _("Stored Files")
              ordering = ['-created_at']
              indexes = [
                  models.Index(fields=['organization', 'original_filename']),
                  models.Index(fields=['mime_type']),
                  models.Index(fields=['uploaded_by']),
              ]

          def __str__(self):
              return self.original_filename

          @property
          def filename(self):
              return os.path.basename(self.file.name)

          # Add download_url property later - depends heavily on storage backend
          # @property
          # def download_url(self): ...
      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `FileStorageFactory` in `api/v1/base_models/common/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from django.core.files.base import ContentFile
      from ..models import FileStorage
      from api.v1.base_models.organization.tests.factories import OrganizationFactory
      from api.v1.base_models.user.tests.factories import UserFactory

      class FileStorageFactory(DjangoModelFactory):
          class Meta:
              model = FileStorage

          # Create a dummy file content for the FileField
          file = factory.LazyFunction(
              lambda: ContentFile(factory.Faker('binary', length=100).generate(), name='test_file.bin')
          )
          original_filename = factory.LazyAttribute(lambda o: o.file.name)
          # Populate size/mime after file is assigned (or mock) - tricky in factory
          # file_size = factory.LazyAttribute(lambda o: o.file.size) # Requires file to be saved first
          # mime_type = 'application/octet-stream'
          organization = factory.SubFactory(OrganizationFactory)
          uploaded_by = factory.SubFactory(UserFactory)
          custom_fields = {}

          # Note: file_size and mime_type might need to be set manually
          # in tests after instance creation and file save, or use post-generation hooks
          # with careful handling of the storage backend interaction.
      ```
  [ ] **(Test)** Write simple tests ensuring the factory creates instances. Testing `file_size`/`mime_type` population might require integration tests involving saving.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Create/Update `api/v1/base_models/common/admin.py`.
  [ ] Define `FileStorageAdmin`:
      ```python
      from django.contrib import admin
      from .models import FileStorage

      @admin.register(FileStorage)
      class FileStorageAdmin(admin.ModelAdmin):
          list_display = (
              'id', 'original_filename', 'mime_type', 'file_size_display',
              'organization', 'uploaded_by', 'created_at'
          )
          list_filter = ('organization', 'mime_type', 'created_at')
          search_fields = ('original_filename', 'id', 'file', 'uploaded_by__username')
          list_select_related = ('organization', 'uploaded_by')
          readonly_fields = (
              'created_at', 'created_by', 'updated_at', 'updated_by',
              'file_size', 'mime_type', 'original_filename', 'file', 'uploaded_by'
              # Make most fields read-only; files managed via API uploads
          )
          # Do not allow adding/changing files directly via Admin usually
          # Add custom_fields / tags if needed

          @admin.display(description='Size')
          def file_size_display(self, obj):
              # Format size nicely (KB, MB etc.)
              if obj.file_size is None: return None
              if obj.file_size < 1024: return f"{obj.file_size} B"
              if obj.file_size < 1024*1024: return f"{obj.file_size/1024:.1f} KB"
              return f"{obj.file_size/(1024*1024):.1f} MB"
      ```
  [ ] **(Manual Test):** Verify registration in Admin. Note that direct upload/modification via Admin is usually discouraged; manage files via application logic/API.

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations api.v1.base_models.common`.
  [ ] **Review generated migration file carefully.** Check `FileField`, FKs, indexes.
  [ ] Run `python manage.py migrate` locally.

  ### 3.5 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write Unit/Integration Tests for `FileStorageSerializer`. Test representation, read-only fields, custom field handling.
  [ ] Define `FileStorageSerializer` in `api/v1/base_models/common/serializers.py`. This is typically read-only as file uploads are handled separately.
      ```python
      from rest_framework import serializers
      from taggit.serializers import TagListSerializerField, TaggitSerializer # If using tags
      from ..models import FileStorage
      # from core.serializers import FieldPermissionSerializerMixin # If needed

      class FileStorageSerializer(TaggitSerializer, serializers.ModelSerializer): # Add FieldPermissionMixin if needed
          tags = TagListSerializerField(required=False, read_only=True)
          # Expose download URL via property on model or SerializerMethodField
          download_url = serializers.SerializerMethodField()
          uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True, allow_null=True)
          organization_name = serializers.CharField(source='organization.name', read_only=True, allow_null=True)
          # Display size nicely
          file_size_display = serializers.SerializerMethodField()

          class Meta:
              model = FileStorage
              fields = [
                  'id',
                  'file', # Often excluded in favor of download_url
                  'original_filename',
                  'file_size',
                  'file_size_display',
                  'mime_type',
                  'uploaded_by', # ID
                  'uploaded_by_username',
                  'organization', # ID
                  'organization_name',
                  'tags',
                  'custom_fields',
                  'created_at',
                  'updated_at',
                  'download_url',
              ]
              read_only_fields = fields # Usually make all read-only

          def get_download_url(self, obj):
              # Logic to generate download URL (requires request context for permissions/signed URLs)
              request = self.context.get('request')
              # 1. Check permissions based on request.user and obj/context
              # 2. If allowed, generate URL (e.g., obj.file.url for simple storage,
              #    or storage.url(obj.file.name) for signed URLs with django-storages)
              # Placeholder: assumes simple direct URL (adjust based on storage/security)
              if request and request.user.is_authenticated: # Basic auth check example
                  try:
                      return request.build_absolute_uri(obj.file.url)
                  except ValueError: # Handle file not found etc.
                      return None
              return None # No URL if no permission or error

          def get_file_size_display(self, obj):
              # Use the same helper as in Admin
              if obj.file_size is None: return None
              if obj.file_size < 1024: return f"{obj.file_size} B"
              # ... etc ... KB, MB
              return f"{obj.file_size/(1024*1024):.1f} MB"

          # Add validate_custom_fields if metadata update API allows it
      ```
  [ ] Run tests; expect pass. Refactor (especially `get_download_url` implementation).

  ### 3.6 API ViewSet/View Definition (`views.py`)

  [ ] **(Test First - Upload)** Write API tests (`tests/api/test_endpoints.py`) for a dedicated file upload endpoint (e.g., `POST /api/v1/files/upload/`).
      *   Test successful upload (authenticated user), assert 201, check response contains `FileStorage` metadata. Check file exists in test storage.
      *   Test upload validation failures (no auth, wrong file type, exceeds size limit), assert 4xx errors.
      *   Test Org Scoping on creation.
  [ ] Define an `FileUploadView` (e.g., inheriting `generics.CreateAPIView`):
      ```python
      # api/v1/base_models/common/views.py
      from rest_framework import generics, permissions, parsers
      from rest_framework.response import Response
      from django.conf import settings
      from core.views import OrganizationScopedViewSetMixin # Or similar base for org logic
      from ..models import FileStorage
      from ..serializers import FileStorageSerializer

      class FileUploadView(generics.CreateAPIView):
           parser_classes = [parsers.MultiPartParser] # Handle file uploads
           serializer_class = FileStorageSerializer # Use for response, maybe different for request
           permission_classes = [permissions.IsAuthenticated] # Must be logged in to upload
           # Potentially add specific upload permission check

           def perform_create(self, serializer):
                # Simplified - assumes file is in request.FILES['file']
                # Add validation for file type and size from settings
                uploaded_file = self.request.FILES.get('file')
                if not uploaded_file:
                     raise serializers.ValidationError("No file provided.")

                # Validate Size
                max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 10*1024*1024) # Default 10MB
                if uploaded_file.size > max_size:
                    raise serializers.ValidationError(f"File size exceeds limit ({max_size} bytes).")

                # Validate Type
                allowed_types = getattr(settings, 'ALLOWED_MIME_TYPES', ['image/jpeg', 'application/pdf'])
                if uploaded_file.content_type not in allowed_types:
                    raise serializers.ValidationError(f"File type '{uploaded_file.content_type}' not allowed.")

                # Determine Organization (Example using request user's primary org)
                user = self.request.user
                user_orgs = user.get_organizations() if hasattr(user, 'get_organizations') else []
                primary_org = user_orgs[0] if user_orgs else None
                if not primary_org: # Ensure user has an org context to upload into
                    raise serializers.ValidationError("Cannot determine user organization context.")

                # Create FileStorage instance
                # Note: file is saved to storage backend when model instance is saved
                instance = serializer.save(
                    file=uploaded_file,
                    original_filename=uploaded_file.name,
                    file_size=uploaded_file.size,
                    mime_type=uploaded_file.content_type,
                    uploaded_by=user,
                    organization=primary_org
                    # Pass custom_fields from request data if applicable
                )

      # Potentially add ReadOnlyModelViewSet for listing/retrieving FileStorage metadata
      # class FileStorageViewSet(OrganizationScopedViewSetMixin, viewsets.ReadOnlyModelViewSet): ...
      ```
  [ ] Run upload tests; expect pass. Refactor view logic (validation, org context).

  ### 3.7 URL Routing (`urls.py`)

  [ ] Define URL pattern for `FileUploadView` in `api/v1/base_models/common/urls.py`.
      ```python
      # Example
      path('files/upload/', views.FileUploadView.as_view(), name='file-upload'),
      # Register FileStorageViewSet if created
      # router.register(r'files', views.FileStorageViewSet)
      ```
  [ ] **(Test):** Rerun basic API tests for upload endpoint; expect correct status codes.

  ### 3.8 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - Download/Access)** Write API tests for accessing files.
      *   Test getting metadata (`GET /api/v1/files/{id}/` if ViewSet exists).
      *   Test getting a download URL (e.g., via `download_url` field in metadata response or a dedicated `/files/{id}/access-url/` endpoint).
      *   Test permissions (user in same org, different org, superuser).
      *   Requires mocking `get_download_url` or the storage backend's URL generation.
  [ ] Implement download/access URL generation logic (e.g., in serializer `get_download_url` or dedicated view), ensuring permission checks.
  [ ] **(Test First - Delete)** Write API tests for `DELETE /api/v1/files/{id}/`. Verify 204 response, metadata deletion, and mock storage backend deletion. Test permissions.
  [ ] Implement deletion logic in appropriate view (e.g., in `FileStorageViewSet` if using it, or a dedicated view). Ensure file is deleted from storage backend on successful metadata deletion.
  [ ] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`), mocking storage backend.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/base_models/common`).
[ ] Manually test file upload/download flow via API client. Check files appear in configured storage (local media or S3 bucket). Check Django Admin.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs (Refine download URL generation, robust custom field validation on upload).
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Ensure models needing attachments add FK/M2M to `FileStorage`.

--- END OF FILE filestorage_implementation_steps.md ---