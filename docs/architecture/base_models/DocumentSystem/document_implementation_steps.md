
# Document System (Document Model) - Implementation Steps

## 1. Overview

**Model Name:**
`Document`

**Corresponding PRD:**
`document_system_prd.md` (Simplified version)

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationScoped`, `FileStorage`, `Category`, `Status` (model/choices), `ContentType` framework, `django-taggit`. Requires Custom Field Definition mechanism if used.

**Key Features:**
Represents logical documents, linking metadata (title, type, status, version, custom fields, tags) to a physical file (`FileStorage`). Uses GenericForeignKey to link to various parent business objects. Scoped by Organization.

**Primary Location(s):**
`api/v1/base_models/common/` (Assuming `common` app hosts `FileStorage` and potentially `Document`) or dedicated `documents` app (`api/v1/features/documents/`). Let's assume **`common`** for this example.

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `OrganizationScoped`, `FileStorage`, `Category`, `Status`, `Organization`, `User`, `ContentType`) are implemented and migrated.
[ ] Ensure `django-taggit` is installed and configured.
[ ] Ensure the `common` app structure exists.
[ ] Ensure `factory-boy` is set up. Factories for `User`, `Organization`, `FileStorage`, `Category` exist.
[ ] Define `DocumentStatus` choices (referencing `Status.slug` values).

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `common`) verifying:
      *   `Document` creation with required fields (`title`, `file`, `organization`).
      *   Default values (`version`, `status`, `custom_fields`).
      *   FKs (`document_type`, `file`) work. `limit_choices_to` for `document_type`.
      *   GenericForeignKey fields (`content_type`, `object_id`) can be set and `content_object` retrieves the parent.
      *   `tags` manager exists. `__str__` works. Inheritance works.
      Run; expect failure (`Document` doesn't exist).
  [ ] Define the `Document` class in `api/v1/base_models/common/models.py`.
  [ ] Add inheritance: `Timestamped`, `Auditable`, `OrganizationScoped`.
      ```python
      # api/v1/base_models/common/models.py
      from django.contrib.contenttypes.fields import GenericForeignKey
      from django.contrib.contenttypes.models import ContentType
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from taggit.managers import TaggableManager

      from core.models import Timestamped, Auditable, OrganizationScoped # Adjust path
      from .models import Category, Status, FileStorage # Ensure these are defined first

      # Define choices (or import) - should reference Status slugs
      class DocumentStatus:
          DRAFT = 'draft'
          ACTIVE = 'active'
          ARCHIVED = 'archived'
          PENDING_REVIEW = 'pending_review'
          CHOICES = [...] # Define choices tuple based on Status model slugs

      class Document(Timestamped, Auditable, OrganizationScoped):
          title = models.CharField(_("Title"), max_length=255, db_index=True)
          document_type = models.ForeignKey(
              Category,
              verbose_name=_("Document Type"),
              related_name='typed_documents',
              on_delete=models.PROTECT,
              limit_choices_to={'category_type': 'DOCUMENT_TYPE'}, # Filter categories
              null=True, blank=True
          )
          status = models.CharField(
              _("Status"), max_length=50, default=DocumentStatus.DRAFT, db_index=True
              # choices=DocumentStatus.CHOICES # Optional: for admin validation
          )
          # Link to the actual file stored
          file = models.ForeignKey(
              FileStorage,
              verbose_name=_("File"),
              on_delete=models.PROTECT, # Don't delete Document if File is deleted? Or CASCADE? PROTECT is safer.
              related_name='documents'
          )
          version = models.PositiveIntegerField(_("Version"), default=1)
          description = models.TextField(_("Description"), blank=True)
          tags = TaggableManager(blank=True, verbose_name=_("Tags"))
          custom_fields = models.JSONField(_("Custom Fields"), default=dict, blank=True)

          # Generic relation to parent object (e.g., Invoice, Project, Organization)
          content_type = models.ForeignKey(
              ContentType,
              on_delete=models.CASCADE, # If parent type deleted, link is invalid
              null=True, blank=True,
              verbose_name=_("Related Object Type")
          )
          object_id = models.CharField( # Use CharField to support UUIDs etc.
              _("Related Object ID"), max_length=255,
              null=True, blank=True, db_index=True
          )
          content_object = GenericForeignKey('content_type', 'object_id')

          class Meta:
              verbose_name = _("Document")
              verbose_name_plural = _("Documents")
              ordering = ['-created_at']
              indexes = [
                  models.Index(fields=['content_type', 'object_id']),
                  models.Index(fields=['organization', 'title']),
                  models.Index(fields=['document_type']),
                  models.Index(fields=['status']),
              ]

          def __str__(self):
              return f"{self.title} (v{self.version})"

          # Note: Logic for incrementing version or linking previous_version
          # would typically live in the API View/Service that handles
          # creating a new version, not in the model's save().
      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `DocumentFactory` in `api/v1/base_models/common/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from django.contrib.contenttypes.models import ContentType
      from ..models import Document, DocumentStatus, Category, FileStorage # Import Status choices if needed
      from .factories import OrganizationFactory, UserFactory, FileStorageFactory, CategoryFactory

      class DocumentFactory(DjangoModelFactory):
          class Meta:
              model = Document

          title = factory.Sequence(lambda n: f'Document Title {n}')
          organization = factory.SubFactory(OrganizationFactory)
          # Ensure category is of correct type
          document_type = factory.SubFactory(CategoryFactory, category_type='DOCUMENT_TYPE')
          status = DocumentStatus.ACTIVE # Or DRAFT
          file = factory.SubFactory(FileStorageFactory, organization=factory.SelfAttribute('..organization'))
          version = 1
          custom_fields = {}

          # Example for setting GenericForeignKey
          # Assumes a 'Project' model and factory exist
          # from api.v1.features.project.tests.factories import ProjectFactory
          # content_object = factory.SubFactory(ProjectFactory, organization=factory.SelfAttribute('..organization'))

          # Handle tags if needed via post-generation
          # @factory.post_generation
          # def tags(self, create, extracted, **kwargs): ...
      ```
  [ ] **(Test)** Write simple tests ensuring the factory creates valid instances, including setting `content_object`.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Create/Update `api/v1/base_models/common/admin.py`.
  [ ] Define `DocumentAdmin`:
      ```python
      from django.contrib import admin
      from django.contrib.contenttypes.admin import GenericTabularInline # For showing docs on parent admin
      from .models import Document

      @admin.register(Document)
      class DocumentAdmin(admin.ModelAdmin):
          list_display = (
              'title', 'version', 'document_type', 'status', 'organization',
              'content_object_link', 'file_link', 'updated_at'
          )
          list_filter = ('organization', 'document_type', 'status', 'created_at')
          search_fields = ('title', 'description', 'file__original_filename', 'object_id')
          list_select_related = ('organization', 'document_type', 'file', 'content_type')
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by', 'file') # File linked on create
          autocomplete_fields = ['document_type', 'file'] # If needed and admins registered
          fieldsets = (
               (None, {'fields': ('organization', 'title', 'status', 'version')}),
               ('Content & Type', {'fields': ('file', 'description', 'document_type', 'tags')}),
               ('Related Object', {'fields': ('content_type', 'object_id')}), # Readonly GFK usually easier
               ('Custom Data', {'classes': ('collapse',), 'fields': ('custom_fields',)}),
               ('Audit Info', {'classes': ('collapse',), 'fields': ('created_at', 'created_by', 'updated_at', 'updated_by')}),
          )

          @admin.display(description='Related Object')
          def content_object_link(self, obj):
              # Similar linking logic as AuditLogAdmin
              if obj.content_object:
                   # ... create admin link ...
                   return obj.content_object
              return "-"

          @admin.display(description='File')
          def file_link(self, obj):
              if obj.file:
                  # Link to file admin or direct URL if safe/desired
                  return obj.file.original_filename
              return "-"

      # Optional: Inline for showing documents on parent model admin pages
      # class DocumentInline(GenericTabularInline):
      #    model = Document
      #    fields = ('title', 'version', 'status', 'file') # etc.
      #    readonly_fields = ('file',) # Upload happens separately usually
      #    extra = 0
      ```
  [ ] **(Manual Test):** Verify Admin CRUD (though creation often happens via API), filtering, search. Check GFK display.

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations api.v1.base_models.common`.
  [ ] **Review generated migration file carefully.** Check FKs, GFK fields (`content_type_id`, `object_id`), indexes.
  [ ] Run `python manage.py migrate` locally.

  ### 3.5 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write Unit/Integration Tests for `DocumentSerializer`. Test validation (required fields, FKs, GFK linking on create/update?), representation (file URL, nested objects?), custom field handling, version handling.
  [ ] Define `DocumentSerializer` in `api/v1/base_models/common/serializers.py`. Handle GFK and file link.
      ```python
      from rest_framework import serializers
      from django.contrib.contenttypes.models import ContentType
      from ..models import Document, FileStorage, Category # etc
      from .serializers import FileStorageSerializer # Assume exists

      class DocumentSerializer(TaggitSerializer, serializers.ModelSerializer): # Add FieldPermissionMixin
          tags = TagListSerializerField(required=False)
          # Read-only nested representation of the file metadata
          file_details = FileStorageSerializer(source='file', read_only=True)
          # Allow linking file by ID on create/update
          file = serializers.PrimaryKeyRelatedField(queryset=FileStorage.objects.all()) # Scope queryset by org?

          # Handle GFK - representation is tricky, often expose type/id
          content_type_app_label = serializers.CharField(source='content_type.app_label', read_only=True, allow_null=True)
          content_type_model = serializers.CharField(source='content_type.model', read_only=True, allow_null=True)
          # For writing GFK, often handled in view based on URL or request data
          # content_type = serializers.PrimaryKeyRelatedField(queryset=ContentType.objects.all(), write_only=True, required=False)
          # object_id = serializers.CharField(write_only=True, required=False)

          document_type_slug = serializers.SlugRelatedField(
              slug_field='slug', source='document_type', read_only=True # Read slug
          )

          class Meta:
              model = Document
              fields = [
                  'id', 'title', 'document_type', 'document_type_slug', 'status',
                  'file', 'file_details', # Write ID, read nested
                  'version', 'description', 'tags', 'custom_fields',
                  'content_type', 'object_id', # IDs for linking, maybe write_only
                  'content_type_app_label', 'content_type_model', # Read-only context
                  'organization', 'created_at', 'updated_at',
              ]
              read_only_fields = ('id', 'organization', 'version', 'created_at', 'updated_at',
                                  'file_details', 'content_type_app_label', 'content_type_model',
                                  'document_type_slug')

          # Add validate_custom_fields
          # Add validation for GFK based on how it's intended to be set via API
          # Add validation for file ownership/organization match if needed
      ```
  [ ] Run tests; expect pass. Refactor (especially GFK handling in API).

  ### 3.6 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests checking `/api/v1/documents/` URL, authentication, Org Scoping, basic permissions.
  [ ] Define `DocumentViewSet` in `api/v1/base_models/common/views.py`. Inherit `OrganizationScopedViewSetMixin`.
      ```python
      from rest_framework import viewsets, permissions
      from django.contrib.contenttypes.models import ContentType
      from core.views import OrganizationScopedViewSetMixin # Adjust path
      from ..models import Document, FileStorage
      from ..serializers import DocumentSerializer
      # Import filters, permissions

      class DocumentViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
          serializer_class = DocumentSerializer
          permission_classes = [permissions.IsAuthenticated] # Add specific Document permissions
          # Base queryset filtered by org via mixin
          queryset = Document.objects.select_related(
              'organization', 'document_type', 'file', 'content_type'
          ).prefetch_related('tags').all()

          filter_backends = [...] # Advanced filtering, Search, Ordering
          # filterset_fields = ['document_type', 'status', 'tags__name', 'content_type', 'object_id']
          search_fields = ['title', 'description', 'file__original_filename']
          ordering_fields = ['title', 'version', 'created_at', 'updated_at']

          # Override perform_create to potentially link GFK based on request data
          # Override perform_create/update to handle version increment logic if desired
          # Add custom actions if needed (e.g., create_new_version)
      ```
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.7 URL Routing (`urls.py`)

  [ ] Import `DocumentViewSet` in `api/v1/base_models/common/urls.py`.
  [ ] Register with router: `router.register(r'documents', views.DocumentViewSet)`.
  [ ] **(Test):** Rerun basic API tests; expect 2xx/4xx codes.

  ### 3.8 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests covering:
      *   LIST (with filters for type, status, tags, parent object via GFK params?). **Verify Org Scoping.**
      *   CREATE (associating with `FileStorage`, setting parent GFK). Test permission checks.
      *   RETRIEVE. Check file details included.
      *   UPDATE (PUT/PATCH - primarily metadata like title, description, status, custom fields). Test permissions.
      *   DELETE (check permissions).
      *   Saving/Validating `custom_fields`.
      *   Tag assignment/filtering via API.
      *   Basic versioning (if `version` field manually incremented via API logic).
  [ ] Implement/Refine ViewSet methods (`perform_create`, `perform_update`) and Serializer logic (GFK handling, custom fields). Ensure Field-Level permissions checked if applicable.
  [ ] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/base_models/common`). Review document-related logic.
[ ] Manually test document creation (associating with files/objects), listing, retrieval via API client. Check Admin UI.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs (GFK setting via API, version increment logic).
[ ] Decide on and implement explicit version linking (`previous_version` FK) if needed.
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Plan implementation for document-related workflows or content processing if required later.

--- END OF FILE document_implementation_steps.md ---