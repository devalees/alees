# Base Models Implementation Steps

## Table of Contents

1. [Core Models](#core-models)
   - [Organization](#organization)
   - [Organization Type](#organization-type)
   - [User Profile](#user-profile)
   - [Contact](#contact)
   - [Address](#address)

2. [System Models](#system-models)
   - [Audit Logging](#audit-logging)
   - [Auditable](#auditable)
   - [Timestamped](#timestamped)
   - [Status](#status)

3. [Authentication & Authorization](#authentication--authorization)
   - [Auth API](#auth-api)
   - [Organization Membership](#organization-membership)
   - [Organization Scoped](#organization-scoped)

4. [Business Models](#business-models)
   - [Product](#product)
   - [Category](#category)
   - [Tax](#tax)
   - [Currency](#currency)
   - [Unit of Measure](#unit-of-measure)
   - [Warehouse](#warehouse)
   - [Stock Location](#stock-location)

5. [Communication & Collaboration](#communication--collaboration)
   - [Chat](#chat)
   - [Comment](#comment)
   - [Notification](#notification)
   - [Video Meeting](#video-meeting)

6. [Document Management](#document-management)
   - [Document System](#document-system)
   - [File Storage](#file-storage)
   - [Export/Import](#exportimport)

7. [System Features](#system-features)
   - [Search](#search)
   - [Filtering](#filtering)
   - [Tagging](#tagging)
   - [Workflow](#workflow)
   - [Automation](#automation)

---

## Core Models


### Organization


# Organization - Implementation Steps

## 1. Overview

**Model Name:**
`Organization`

**Corresponding PRD:**
`organization_prd.md`

**Depends On:**
`Timestamped`, `Auditable` (Done), `OrganizationType` (in `organization` app - Done), `Currency` (in `common` app - Done), `Contact` (in `contact` app - Done), `Address` (in `common` app - Done). Requires libraries `django-mptt` and `django-taggit`.

**Key Features:**
Core ERP entity representing internal/external org units. Supports hierarchy (MPTT), tagging (Taggit), custom fields (JSONField), status, localization settings, links to Type, Contact, Address, Currency. Foundation for `OrganizationScoped`.

**Primary Location(s):**
`api/v1/base_models/organization/`

## 2. Prerequisites

[x] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `OrganizationType`, `Currency`, `Contact`, `Address`) are implemented and migrated.
[x] Ensure the `organization` app structure exists (`api/v1/base_models/organization/`). Add `'api.v1.base_models.organization'` to `INSTALLED_APPS`.
[x] Install required libraries: `pip install django-mptt django-taggit`.
[x] Add `'mptt'` and `'taggit'` to `INSTALLED_APPS` in `config/settings/base.py`. Run `python manage.py migrate taggit` if this is the first time adding `taggit`.
[x] Ensure `factory-boy` is set up. Factories for `OrganizationType` (in `organization` app), `Currency` (in `common` app), `Contact` (in `contact` app), `Address` (in `common` app), and `User` exist.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`api/v1/base_models/organization/tests/unit/test_models.py`) verifying:
      *   An `Organization` can be created with required fields (`name`, `code`, `organization_type`).
      *   Unique constraints (`code` is globally unique, `unique_together` for `parent`/`name`).
      *   Default values (`status`, `metadata`, `custom_fields`, `timezone`, `language`).
      *   FK relationships (`organization_type`, `parent`, `primary_contact`, `primary_address`, `currency`) work and are initially nullable where specified.
      *   Inherited fields (`created_at`, `updated_at`, `created_by`, `updated_by`) exist.
      *   MPTT fields (`lft`, `rght`, `tree_id`, `level`) are present after save.
      *   `tags` manager from `django-taggit` exists.
      *   `__str__` method works.
      Run; expect failure (`Organization` doesn't exist).
  [ ] Define the `Organization` class in `api/v1/base_models/organization/models.py`.
  [ ] Add required inheritance: `Timestamped`, `Auditable`, `MPTTModel`.
      ```python
      # api/v1/base_models/organization/models.py
      from django.conf import settings
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from mptt.models import MPTTModel, TreeForeignKey
      from taggit.managers import TaggableManager

      from core.models import Timestamped, Auditable # Adjust import path if needed
      # Import related models from other apps using app_label.ModelName strings
      from .models import OrganizationType # Import OrgType from same app

      # Use strings for cross-app FKs
      CONTACT_MODEL = 'contact.Contact'
      ADDRESS_MODEL = 'common.Address'
      CURRENCY_MODEL = 'common.Currency'

      class Organization(Timestamped, Auditable, MPTTModel):
          STATUS_ACTIVE = 'active'
          STATUS_INACTIVE = 'inactive'
          STATUS_ARCHIVED = 'archived'
          STATUS_CHOICES = [
              (STATUS_ACTIVE, _('Active')),
              (STATUS_INACTIVE, _('Inactive')),
              (STATUS_ARCHIVED, _('Archived')),
          ]

          # Core Fields
          name = models.CharField(_("Name"), max_length=255, db_index=True)
          code = models.CharField(_("Code"), max_length=50, unique=True, db_index=True)
          organization_type = models.ForeignKey(
              OrganizationType, # Defined in this app
              verbose_name=_("Organization Type"),
              on_delete=models.PROTECT,
              related_name='organizations'
          )
          status = models.CharField(
              _("Status"), max_length=20, choices=STATUS_CHOICES,
              default=STATUS_ACTIVE, db_index=True
          )
          parent = TreeForeignKey(
              'self',
              verbose_name=_("Parent Organization"),
              on_delete=models.PROTECT, # Protect parent if children exist
              null=True, blank=True, related_name='children', db_index=True
          )
          effective_date = models.DateField(_("Effective Date"), null=True, blank=True)
          end_date = models.DateField(_("End Date"), null=True, blank=True)

          # Contact Information (FK to contact.Contact)
          primary_contact = models.ForeignKey(
              CONTACT_MODEL,
              verbose_name=_("Primary Contact"),
              related_name='primary_for_organizations',
              on_delete=models.SET_NULL, null=True, blank=True
          )
          # Address Details (FK to common.Address)
          primary_address = models.ForeignKey(
              ADDRESS_MODEL,
              verbose_name=_("Primary Address"),
              related_name='primary_for_organizations',
              on_delete=models.SET_NULL, null=True, blank=True
          )
          # Example: Separate Billing Address
          # billing_address = models.ForeignKey(ADDRESS_MODEL, related_name='billing_for_organizations', ...)

          # Localization (FK to common.Currency)
          timezone = models.CharField(_("Timezone"), max_length=60, default=settings.TIME_ZONE)
          currency = models.ForeignKey(
              CURRENCY_MODEL,
              verbose_name=_("Default Currency"),
              related_name='organizations',
              on_delete=models.PROTECT, null=True, blank=True
          )
          language = models.CharField(_("Language"), max_length=10, default=settings.LANGUAGE_CODE)

          # Metadata & Classification
          tags = TaggableManager(blank=True, verbose_name=_("Tags"))
          metadata = models.JSONField(_("Metadata"), default=dict, blank=True)
          custom_fields = models.JSONField(_("Custom Fields"), default=dict, blank=True)

          class MPTTMeta:
              order_insertion_by = ['name']
              parent_attr = 'parent'

          class Meta:
              verbose_name = _("Organization")
              verbose_name_plural = _("Organizations")
              unique_together = (('parent', 'name'),) # Name unique under same parent
              # 'code' is globally unique via unique=True on the field
              ordering = ['tree_id', 'lft'] # MPTT default ordering

          def __str__(self):
              return self.name
      ```
  [ ] Run tests; expect pass. Refactor model code if needed.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `OrganizationFactory` in `api/v1/base_models/organization/tests/factories.py`. Use full import paths for factories from other apps.
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from ..models import Organization, OrganizationType
      # Import factories for related models from other apps
      from .factories import OrganizationTypeFactory # Assumes in same file now
      # Adjust paths as per your project structure
      from api.v1.base_models.common.tests.factories import CurrencyFactory, AddressFactory
      from api.v1.base_models.contact.tests.factories import ContactFactory

      class OrganizationFactory(DjangoModelFactory):
          class Meta:
              model = Organization
              django_get_or_create = ('code',) # Use code for uniqueness

          name = factory.Sequence(lambda n: f'Test Organization {n}')
          code = factory.Sequence(lambda n: f'ORG-{n:04}')
          organization_type = factory.SubFactory(OrganizationTypeFactory)
          status = Organization.STATUS_ACTIVE
          parent = None # Set explicitly in tests if needed for hierarchy
          # Create related objects by default if needed for most tests
          primary_contact = factory.SubFactory(ContactFactory)
          primary_address = factory.SubFactory(AddressFactory)
          currency = factory.SubFactory(CurrencyFactory)
          timezone = 'UTC'
          language = 'en'
          metadata = {}
          custom_fields = {}

          # Example for tags:
          @factory.post_generation
          def tags(self, create, extracted, **kwargs):
              if not create: return
              if extracted: # Allows passing tags=['tag1', ...] to factory
                  for tag in extracted: self.tags.add(tag)
      ```
  [ ] **(Test)** Write tests ensuring `OrganizationFactory` creates valid instances and links related factories correctly. Test hierarchy creation.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Create/Update `api/v1/base_models/organization/admin.py`.
  [ ] Define `OrganizationAdmin` using `DraggableMPTTAdmin`. Use `raw_id_fields` for FKs.
      ```python
      from django.contrib import admin
      from mptt.admin import DraggableMPTTAdmin
      from .models import Organization, OrganizationType # Ensure both imported

      # Assume OrganizationTypeAdmin registered elsewhere or here

      @admin.register(Organization)
      class OrganizationAdmin(DraggableMPTTAdmin):
          list_display = ('tree_actions', 'indented_title', 'code', 'organization_type', 'status', 'currency')
          list_display_links = ('indented_title',)
          list_filter = ('organization_type', 'status', 'currency')
          search_fields = ('name', 'code')
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
          raw_id_fields = ('parent', 'primary_contact', 'primary_address', 'currency', 'organization_type')
          fieldsets = (
              (None, {'fields': ('name', 'code', 'organization_type', 'status', 'parent')}),
              ('Dates', {'fields': ('effective_date', 'end_date')}),
              ('Primary Links', {'fields': ('primary_contact', 'primary_address')}),
              ('Localization', {'fields': ('timezone', 'currency', 'language')}),
              ('Other Data', {'fields': ('tags', 'metadata', 'custom_fields')}),
              ('Audit Info', {'classes': ('collapse',), 'fields': readonly_fields}),
          )
          # Add filter_horizontal for tags if TaggableManager widget not ideal
      ```
  [ ] **(Manual Test):** Verify Admin operations, hierarchy management, related field selection.

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations api.v1.base_models.organization`.
  [ ] **Review generated migration file carefully.** Check MPTT setup, FKs (ensure they point to correct apps), unique constraints, indexes.
  [ ] Run `python manage.py migrate` locally.
  [ ] Run `python manage.py rebuild_organization` (MPTT command) if needed.

  ### 3.5 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write Tests for `OrganizationSerializer`. Test validation (unique code, FK existence), representation (fields, tags, maybe nested reads), custom/metadata field handling.
  [ ] Create `api/v1/base_models/organization/serializers.py`.
  [ ] Define `OrganizationSerializer`. Use `TaggitSerializer`. Handle FKs with `PrimaryKeyRelatedField` for writing, optionally nested serializers for reading.
      ```python
      # api/v1/base_models/organization/serializers.py
      from rest_framework import serializers
      # from rest_framework_mptt.serializers import MPTTModelSerializer # Optional
      from taggit.serializers import TagListSerializerField, TaggitSerializer
      from ..models import Organization, OrganizationType
      # Import models for querysets/FKs
      from api.v1.base_models.common.models import Currency, Contact, Address # Adjust

      class OrganizationSerializer(TaggitSerializer, serializers.ModelSerializer): # Or MPTTModelSerializer
          tags = TagListSerializerField(required=False)
          # Use PKs for writing FKs
          organization_type = serializers.PrimaryKeyRelatedField(queryset=OrganizationType.objects.all())
          parent = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all(), source='parent', allow_null=True, required=False) # Use parent_id? Field name match is best
          primary_contact = serializers.PrimaryKeyRelatedField(queryset=Contact.objects.all(), allow_null=True, required=False)
          primary_address = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all(), allow_null=True, required=False)
          currency = serializers.PrimaryKeyRelatedField(queryset=Currency.objects.all(), allow_null=True, required=False)

          # Read-only fields for context
          organization_type_name = serializers.CharField(source='organization_type.name', read_only=True)
          # Optionally add nested serializers for read-only representation

          class Meta:
              model = Organization
              fields = [
                  'id', 'name', 'code', 'organization_type', 'organization_type_name',
                  'status', 'parent', # 'parent_id' is implicit if source='parent'
                  'effective_date', 'end_date',
                  'primary_contact', 'primary_address', 'currency',
                  'timezone', 'language',
                  'tags', 'metadata', 'custom_fields',
                  'created_at', 'updated_at',
                  # Add MPTT fields like 'level' if needed for display
              ]
              read_only_fields = ('id', 'created_at', 'updated_at', 'organization_type_name')
              # Add MPTT fields to read_only if using MPTTSerializer and not needed for input

          def validate_code(self, value):
               # Example: Ensure code uniqueness if DB constraint isn't enough (e.g., case-insensitive)
               # Adjust query based on instance existence for updates
               queryset = Organization.objects.filter(code__iexact=value)
               if self.instance:
                   queryset = queryset.exclude(pk=self.instance.pk)
               if queryset.exists():
                   raise serializers.ValidationError(_("Organization with this code already exists."))
               return value

          # Add validate_custom_fields if needed
          # Add validate method for cross-field validation (e.g., end_date > effective_date)
      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.6 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests checking `/api/v1/organizations/` URL, authentication, basic permissions.
  [ ] Create `api/v1/base_models/organization/views.py`. Define `OrganizationViewSet`. Select/Prefetch related fields. Add filtering/search/ordering. Add MPTT actions.
      ```python
      # api/v1/base_models/organization/views.py
      from rest_framework import viewsets, permissions
      from rest_framework.decorators import action
      from rest_framework.response import Response
      from ..models import Organization
      from ..serializers import OrganizationSerializer
      # Import filters, permissions etc.

      class OrganizationViewSet(viewsets.ModelViewSet):
          serializer_class = OrganizationSerializer
          permission_classes = [permissions.IsAuthenticated] # Add specific RBAC permissions
          # authentication_classes = [...] # From API Strategy
          queryset = Organization.objects.select_related(
              'organization_type', 'currency', 'primary_contact', 'primary_address', 'parent'
          ).prefetch_related('tags').all() # Base queryset, actual filtering done by OrgScopedMixin if applied later
          filter_backends = [...] # Advanced filtering, Search, Ordering
          # filterset_fields = ['organization_type', 'status', 'parent', 'tags__name', 'currency']
          search_fields = ['name', 'code']
          ordering_fields = ['name', 'code', 'created_at']

          # MPTT actions (example)
          @action(detail=True, methods=['get'])
          def descendants(self, request, pk=None): ... # Implementation as before
          @action(detail=True, methods=['get'])
          def ancestors(self, request, pk=None): ... # Get ancestors

          # Add other actions like children, move, etc. as needed
      ```
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.7 URL Routing (`urls.py`)

  [ ] Create `api/v1/base_models/organization/urls.py`. Import `OrganizationViewSet`. Register with router.
  [ ] Include `organization.urls` in `api/v1/base_models/urls.py`.
  [ ] **(Test):** Rerun basic API tests; expect 2xx/4xx codes.

  ### 3.8 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests for `/api/v1/organizations/` CRUD & Features.
      *   LIST (with filters for type, status, parent, tags).
      *   CREATE (valid/invalid, check FK links). Test permissions.
      *   RETRIEVE (check permissions).
      *   UPDATE/PATCH (check permissions).
      *   DELETE (check permissions, check PROTECT constraints).
      *   Hierarchy actions (`/descendants/` etc.).
      *   Saving/Validating `metadata`, `custom_fields`.
      *   Tag assignment/filtering.
  [ ] Implement/Refine ViewSet methods and Serializer logic. Ensure Field-Level permissions checked.
  [ ] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/base_models/organization`).
[ ] Manually test via API client and Django Admin (hierarchy, FK links, tags).
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Ensure `OrganizationScoped` implementation uses this model.
[ ] Ensure `OrganizationMembership` uses this model.
[ ] Ensure `Contact.linked_organization` refinement steps are completed now.
[ ] Ensure `UserProfile` refinement steps for `primary_organization` (if kept) are completed.

--- END OF FILE organization_implementation_steps.md ---
### Organization Type


# OrganizationType - Implementation Steps

## 1. Overview

**Model Name:**
`OrganizationType`

**Corresponding PRD:**
`organization_type_prd.md`

**Depends On:**
`Timestamped`, `Auditable` (Abstract Base Models)

**Key Features:**
Defines the types or classifications for `Organization` entities (e.g., Company, Department, Customer). Provides a controlled vocabulary. Includes name and description.

**Primary Location(s):**
`api/v1/base_models/organization/` (Assuming it lives alongside the `Organization` model)

## 2. Prerequisites

[x] Verify prerequisite models/mixins (`Timestamped`, `Auditable`) are implemented.
[x] Ensure the `organization` app structure exists (`api/v1/base_models/organization/`).
[x] Ensure `factory-boy` is set up. Basic User factory exists.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [x] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `organization`) verifying:
      *   An `OrganizationType` instance can be created with a unique `name`.
      *   Saving duplicate names raises `IntegrityError`.
      *   The `description` field is optional.
      *   `__str__` method returns the `name`.
      *   Inherited `Timestamped`/`Auditable` fields exist.
      Run; expect failure (`OrganizationType` doesn't exist).
  [x] Define the `OrganizationType` class in `api/v1/base_models/organization/models.py`.
  [x] Add required inheritance: `Timestamped`, `Auditable`.
      ```python
      # api/v1/base_models/organization/models.py
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from core.models import Timestamped, Auditable # Adjust import path

      class OrganizationType(Timestamped, Auditable):
          # Consider using AutoField or UUIDField if name changes are possible
          # and name shouldn't be the logical key other models reference.
          # But using name as PK is simpler if names are stable identifiers.
          # Let's assume name is stable for now. Revisit if needed.
          # If not PK, add a slug or code field as PK.
          name = models.CharField(
              _("Name"),
              max_length=100,
              unique=True,
              db_index=True,
              primary_key=True, # Making name the PK simplifies lookups if stable
              help_text=_("Unique name for the organization type (e.g., Company, Department).")
          )
          description = models.TextField(
              _("Description"),
              blank=True,
              help_text=_("Optional description of this organization type.")
          )
          # is_internal = models.BooleanField(default=True) # Example future flag

          class Meta:
              verbose_name = _("Organization Type")
              verbose_name_plural = _("Organization Types")
              ordering = ['name']

          def __str__(self):
              return self.name

      # ... Organization model will be defined later in this file ...
      ```
      *(Note: Made `name` the primary key for simplicity, assuming names like 'Customer', 'Department' are stable identifiers. If frequent name changes are expected, use a separate AutoField/UUIDField PK and keep `name` as unique CharField).*
  [x] Run tests; expect pass. Refactor model code if needed.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [x] Define `OrganizationTypeFactory` in `api/v1/base_models/organization/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from ..models import OrganizationType

      class OrganizationTypeFactory(DjangoModelFactory):
          class Meta:
              model = OrganizationType
              # Use name as the lookup field since it's PK (or unique)
              django_get_or_create = ('name',)

          name = factory.Iterator(['Company', 'Department', 'Customer', 'Supplier', 'Branch'])
          description = factory.Faker('sentence')
      ```
  [x] **(Test)** Write a simple test ensuring `OrganizationTypeFactory` creates valid instances. Test `django_get_or_create` works.

  ### 3.3 Admin Registration (`admin.py`)

  [x] Create/Update `api/v1/base_models/organization/admin.py`.
  [x] Define `OrganizationTypeAdmin`:
      ```python
      from django.contrib import admin
      from .models import OrganizationType # Assuming OrganizationType in same models.py

      @admin.register(OrganizationType)
      class OrganizationTypeAdmin(admin.ModelAdmin):
          list_display = ('name', 'description', 'updated_at', 'updated_by')
          search_fields = ('name', 'description')
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
      ```
  [x] **(Manual Test):** Verify registration and basic CRUD in Django Admin locally.

  ### 3.4 Initial Data Population (Migration)

  [x] Create a new **Data Migration** file: `python manage.py makemigrations --empty --name populate_org_types api.v1.base_models.organization`.
  [x] Edit the generated migration file (`..._populate_org_types.py`). Add `RunPython` operations to load essential types.
      ```python
      from django.db import migrations

      INITIAL_ORG_TYPES = {
          # Name: Description
          'Company': 'Primary legal entity or top-level organization.',
          'Division': 'A major operational division within a company.',
          'Department': 'A functional department within a division or company.',
          'Team': 'A specific team within a department.',
          'Location/Branch': 'A physical office or branch location.',
          'Customer': 'An external organization that purchases goods/services.',
          'Supplier': 'An external organization that supplies goods/services.',
          'Partner': 'An external organization collaborated with.',
          'Vendor': 'Synonym for Supplier, or specific type.',
          # Add others as needed
      }

      def populate_organization_types(apps, schema_editor):
          OrganizationType = apps.get_model('organization', 'OrganizationType') # Use app_label from apps.py
          db_alias = schema_editor.connection.alias

          types_to_add = []
          for name, description in INITIAL_ORG_TYPES.items():
              types_to_add.append(
                  OrganizationType(name=name, description=description)
              )

          OrganizationType.objects.using(db_alias).bulk_create(types_to_add, ignore_conflicts=True)
          print(f"\nPopulated/updated {len(types_to_add)} organization types.")

      def remove_organization_types(apps, schema_editor):
          # Could delete specific types, but safer to often just pass in reverse
          pass

      class Migration(migrations.Migration):

          dependencies = [
              # Ensure this runs after the migration creating OrganizationType model
              ('organization', '000X_auto_...'),
          ]

          operations = [
              migrations.RunPython(populate_organization_types, reverse_code=remove_organization_types),
          ]
      ```

  ### 3.5 Migrations (Apply Initial Model & Data)

  [x] Run `python manage.py makemigrations api.v1.base_models.organization`.
  [x] **Review generated migration file(s) carefully.** (Should create `OrganizationType` table, then the data migration).
  [x] Run `python manage.py migrate` locally. Verify data loaded (e.g., via Admin).

  ### 3.6 Serializer Definition (`serializers.py`)

  [x] **(Test First - Representation)** Write Integration Tests (`tests/integration/test_serializers.py`) verifying `OrganizationTypeSerializer` output format.
  [x] Define `OrganizationTypeSerializer` in `api/v1/base_models/organization/serializers.py`:
      ```python
      from rest_framework import serializers
      from ..models import OrganizationType

      class OrganizationTypeSerializer(serializers.ModelSerializer):
          class Meta:
              model = OrganizationType
              fields = [
                  'name', # Or PK if not name
                  'description',
                  # Include Timestamped/Auditable fields if needed
              ]
              # Typically read-only for most API consumers
              read_only_fields = ['name', 'description']
      ```
  [x] Run tests; expect pass. Refactor.

  ### 3.7 API ViewSet Definition (`views.py`)

  [x] **(Test First - Permissions/Basic Structure)** Write basic API Tests (`tests/api/test_endpoints.py`) for `/api/v1/organization-types/`. Test unauthenticated/authenticated access (likely read-only allowed).
  [x] Define `OrganizationTypeViewSet` in `api/v1/base_models/organization/views.py`:
      ```python
      from rest_framework import viewsets, permissions, filters
      from django_filters.rest_framework import DjangoFilterBackend
      from .models import OrganizationType
      from .serializers import OrganizationTypeSerializer

      class OrganizationTypeViewSet(viewsets.ReadOnlyModelViewSet):
          """
          API endpoint that allows organization types to be viewed.
          Management is typically done via Admin interface.
          """
          queryset = OrganizationType.objects.all()
          serializer_class = OrganizationTypeSerializer
          permission_classes = [permissions.IsAuthenticatedOrReadOnly]
          search_fields = ['name', 'description']
          ordering_fields = ['name']
          ordering = ['name']  # Default ordering
          filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
          filterset_fields = ['name']  # Enable filtering by name
          lookup_field = 'name'  # Use name as the lookup field
      ```
  [x] Run basic structure/permission tests; expect pass. Refactor.

  ### 3.8 URL Routing (`urls.py`)

  [x] Import `OrganizationTypeViewSet` in `api/v1/base_models/organization/urls.py`.
  [x] Register the ViewSet with the router: `router.register(r'organization-types', views.OrganizationTypeViewSet)`.
  [x] Ensure `organization.urls` is included in `api/v1/base_models/urls.py`.
  [x] **(Test):** Rerun basic API tests; expect 200 OK for listing/retrieving.

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [x] **(Test First - List/Retrieve)** Write tests for `GET /api/v1/organization-types/` and `GET /api/v1/organization-types/{name}/`. Assert 200, check structure, verify initial types are present.
  [x] Ensure `queryset` and permissions are correct.
  [x] Run list/retrieve tests; expect pass. Refactor.
  [x] Implemented features:
      - Pagination with `results` in response
      - Ordering (both ascending and descending)
      - Filtering by name using DjangoFilterBackend
      - Detail view lookup by name
      - Read-only permissions
      - Search functionality
  [x] All tests passing with 100% coverage for the ViewSet.

## 4. Final Checks

[x] Run the *entire* test suite (`pytest`).
[x] Run linters (`flake8`) and formatters (`black`).
[x] Check code coverage:
   - Run pytest --cov=[app_path] (e.g., pytest --cov=api/v1/base_models/organization).
   - Review the coverage report (e.g., term-missing output).
   - Ensure coverage meets the project's agreed-upon threshold (e.g., >= 80-90%).
   - Analyze any uncovered lines, especially in critical logic sections, and add necessary tests.
[x] Manually test via API client and verify data/management in Django Admin.
[x] Review API documentation draft.

## 5. Follow-up Actions

[x] Address TODOs.
[x] Create Pull Request.
[x] Update API documentation.
[ ] Ensure `Organization` model uses `ForeignKey` to `OrganizationType`.

--- END OF FILE organizationtype_implementation_steps.md ---
### User Profile


# UserProfile - Implementation Steps (CLEANED - V5)

## 1. Overview

**Model Name:**
`UserProfile`

**Corresponding PRD:**
`UserProfile.md` (Refined version with Username Login + Custom Fields, excluding direct primary organization link)

**Depends On:**
Django `User` model (`settings.AUTH_USER_MODEL`), `Timestamped`, `Auditable`.
**Future Dependencies:** `FileStorage` (#7 in ranking).

**Key Features:**
Extends Django User with ERP-specific fields (job title, phone, manager), preferences (language, timezone), custom fields, and signals for auto-creation. User-Organization linkage is managed exclusively via `OrganizationMembership`.

**Primary Location(s):**
`api/v1/base_models/user/` (Following chosen project structure)

## 2. Prerequisites

[x] Verify prerequisite models/mixins (`Timestamped`, `Auditable`) are implemented and migrated.
[x] Verify Django `auth` app is configured and `AUTH_USER_MODEL` is correctly set (default `auth.User`).
[x] Ensure the `user` app structure exists (`api/v1/base_models/user/`). Add `'api.v1.base_models.user'` to `INSTALLED_APPS`.
[x] Ensure `factory-boy` is set up. Create `UserFactory` if not already done.
[x] Ensure `FileStorage` model is planned for later implementation (#7). `profile_picture` will be initially nullable.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [x] **(Test First - Basic)**
      Write **Unit Test(s)** (`api/v1/base_models/user/tests/unit/test_models.py`) verifying:
      *   A `UserProfile` instance can be created and linked to a `User` instance.
      *   The `__str__` method returns `user.username`.
      *   Inherited `Timestamped`/`Auditable` fields exist.
      *   `profile_picture` field exists and is nullable.
      *   Confirm necessary fields like `job_title`, `phone_number`, `manager`, preferences, `custom_fields` exist.
  [x] Define the `UserProfile` class in `api/v1/base_models/user/models.py`.
  [x] Add required inheritance: `Timestamped`, `Auditable`.
  [x] Define the core `OneToOneField` link to `User`.
  [x] Define basic attribute fields, Preferences Fields, Profile Picture Field (initially nullable), and `custom_fields`.
  [x] Run basic tests; expect pass. Refactor.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [x] Define `UserFactory` if not already done.
  [x] Define `UserProfileFactory` in `api/v1/base_models/user/tests/factories.py`. Ensure `profile_picture` is `None` by default.
  [x] **(Test)** Write tests ensuring `UserProfileFactory` creates valid instances.

  ### 3.3 Signal for Auto-Creation (`signals.py` or `models.py`)

  [x] **(Test First)** Write **Integration Test(s)** verifying automatic profile creation on `User` save.
  [x] Define `post_save` receiver for `User` model.
  [x] Connect the signal receiver in `apps.py`.
  [x] Run signal tests; expect pass. Refactor.

  ### 3.4 Admin Registration (`admin.py`)

  [x] Define `UserProfileInline(admin.StackedInline)`. Include `profile_picture` (using `raw_id_fields`).
  [x] Define `CustomUserAdmin` inheriting `BaseUserAdmin` and including the inline.
  [x] **(Test)** Write tests for admin registration and inline configuration.
  [x] Run admin tests; expect pass. Refactor.

  ### 3.5 Migrations

  [x] Run `python manage.py makemigrations api.v1.base_models.user`.
  [x] **Review generated migration file carefully.** `profile_picture_id` is created as nullable.
  [x] Run `python manage.py migrate` locally.

  ### 3.6 Serializer Definition (`serializers.py`)

  [x] **(Test First)** Write tests for `UserProfileSerializer`. Handle nullable `profile_picture`.
  [x] Define `UserProfileSerializer`. Ensure `profile_picture` field is `required=False, allow_null=True`.
  [x] Implement `validate_custom_fields`.
  [x] Run serializer tests; expect pass. Refactor.

  ### 3.7 API ViewSet Definition (`views.py`)

  [x] **(Test First)** Write basic API Tests for profile endpoints (e.g., `/profiles/me/`).
  [x] Define `MyProfileView` (`RetrieveUpdateAPIView`) with proper authentication.
  [x] Run basic tests; expect pass. Refactor.

  ### 3.8 URL Routing (`urls.py`)

  [x] Define URL patterns in `api/v1/base_models/user/urls.py` for the chosen views (e.g., `path('profiles/me/', views.MyProfileView.as_view(), name='my-profile')`).
  [x] Include these URLs in `api/v1/base_models/urls.py`.
  [x] **(Test):** Rerun basic API tests.

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [x] **(Test First - MyProfile)** Write tests for `GET` and `PUT`/`PATCH` on `/profiles/me/`. Test updating fields, including setting/unsetting `profile_picture`.
  [x] Implement view logic as needed.
  [x] Run MyProfile tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api.v1.base_models.user`).
[ ] Manually test profile viewing/editing via API client and Django Admin.

## 5. Dependency Refinement / Post-Requisite Steps

*   **After `FileStorage` (#7) is implemented:**
    1.  **Refine `UserProfile.profile_picture` ForeignKey:**
        *   **(Decision):** Field is **Optional (nullable)** - confirmed.
        *   **Model Change:** No change needed.
        *   **Serializer Update:** Update `queryset` in `PrimaryKeyRelatedField` for `profile_picture` in `UserProfileSerializer` to `FileStorage.objects.all()` (or scoped queryset if needed). Adjust `read_only` status based on how the picture is intended to be set/updated (e.g., make it `required=False` if allowing update via profile endpoint, or keep `read_only=True` if using a separate upload URL).
        *   **Rerun Tests:** Ensure tests covering profile picture linking via API pass according to the chosen update mechanism.

## 6. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request for the `UserProfile` implementation.
[ ] Update relevant documentation.
[ ] Note that user-organization linkage is handled solely by `OrganizationMembership`.

--- END OF FILE userprofile_implementation_steps.md (CLEANED - V5) ---


### Contact


# Contact & Communication Channels - Implementation Steps (Consolidated, FINAL REVISED)

## 1. Overview

**Model Name(s):**
`Contact`, `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress`

**Corresponding PRD:**
`contact_prd.md` (Simplified version with Custom Fields and related Channel models)

**Depends On:**
`Timestamped`, `Auditable` (Done), `Address` (Done, in `common` app), `Organization` (#4 - Future), `django-taggit`, `django-phonenumber-field`. Requires `User` model.

**Key Features:**
Central model for individual contacts (`Contact`) with core details, status, tags, custom fields. `linked_organization` is **optional**. Separate related models handle multiple email addresses, phone numbers, and physical addresses (linking to `Address` model), each with type and primary flags.

**Primary Location(s):**
`api/v1/base_models/contact/` (Dedicated `contact` app)

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `Address` [in `common` app]) are implemented and migrated.
[ ] Ensure the `contact` app structure exists (`api/v1/base_models/contact/`). Add `'api.v1.base_models.contact'` to `INSTALLED_APPS`.
[ ] Install required libraries: `pip install django-taggit django-phonenumber-field`. Add `'taggit'` and `'phonenumber_field'` to `INSTALLED_APPS`.
[ ] Ensure `factory-boy` is set up. Factories for `Address` (in `common` app), `User` exist.
[ ] Define TYPE choices for Contact Status, Contact Type, and Channel Types (e.g., in `contact/choices.py`).

## 3. Implementation Steps (TDD Workflow)

  *(Models -> Single Primary Logic -> Factories -> Admin -> Migrations -> Serializer -> API)*

  ### 3.1 Model Definitions (`models.py`)

  [ ] **(Test First - Contact & Channels)**
      Write **Unit Test(s)** (`api/v1/base_models/contact/tests/unit/test_models.py`) verifying all four models (`Contact`, `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress`).
      *   Verify `Contact` creation, fields, inheritance. Ensure `linked_organization` FK exists and is **nullable**.
      *   Verify Channel models creation, fields, FKs (to `Contact`, `common.Address`), `unique_together`, `__str__`, inheritance.
      Run; expect failure.
  [ ] Define the `Contact` model *first* in `api/v1/base_models/contact/models.py`. Include `TaggableManager`. Ensure `linked_organization` uses `null=True, blank=True`.
  [ ] Define the communication channel models (`ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress`) *after* `Contact` in the same file. Ensure `ContactAddress` links correctly to `common.Address`.
      ```python
      # api/v1/base_models/contact/models.py
      # ... (imports as defined previously) ...

      class Contact(Timestamped, Auditable):
          # ... fields as defined previously ...
          linked_organization = models.ForeignKey(
              ORGANIZATION_MODEL, # Defined as 'organization.Organization'
              verbose_name=_("Linked Organization"),
              on_delete=models.SET_NULL,
              null=True, # Optional field - confirmed
              blank=True,
              related_name='contacts',
              # TODO: [POST-ORGANIZATION] Update related logic/querysets when Org exists.
          )
          # ... rest of Contact model ...

      # --- Communication Channel Models ---
      class ContactEmailAddress(Timestamped, Auditable): ... # As defined previously
      class ContactPhoneNumber(Timestamped, Auditable): ... # As defined previously
      class ContactAddress(Timestamped, Auditable): ... # As defined previously, links to 'common.Address'
      ```
  [ ] Run tests for all models; expect pass. Refactor.

  ### 3.2 Single Primary Logic (Model `save` override)

  [ ] **(Test First)** Write Integration Tests verifying single primary logic for Email, Phone, and Address models.
  [ ] Implement the `save()` override method on `ContactEmailAddress`, `ContactPhoneNumber`, and `ContactAddress` (as shown previously).
  [ ] Run single primary logic tests; expect pass. Refactor.

  ### 3.3 Factory Definitions (`tests/factories.py`)

  [ ] Define `ContactFactory` in `api/v1/base_models/contact/tests/factories.py`. Ensure `linked_organization` is `None` by default.
  [ ] Define factories for `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress` in the same file. Ensure `ContactAddressFactory` uses `AddressFactory` from the `common` app.
      ```python
      # api/v1/base_models/contact/tests/factories.py
      # ... (imports as previously defined) ...

      class ContactFactory(DjangoModelFactory):
          class Meta: model = Contact
          # ... fields ...
          linked_organization = None # Optional field default
          # ...

      class ContactEmailAddressFactory(DjangoModelFactory): ... # As before
      class ContactPhoneNumberFactory(DjangoModelFactory): ... # As before
      class ContactAddressFactory(DjangoModelFactory): ... # As before
      ```
  [ ] **(Test)** Write simple tests ensuring factories create valid instances.

  ### 3.4 Admin Registration (`admin.py`)

  [ ] Create `api/v1/base_models/contact/admin.py`.
  [ ] Define `InlineModelAdmin` classes for channels.
  [ ] Define `ContactAdmin` including the inlines. Use `raw_id_fields` for `linked_organization`.
      ```python
      # api/v1/base_models/contact/admin.py
      # ... (definitions as previously shown) ...

      @admin.register(Contact)
      class ContactAdmin(admin.ModelAdmin):
          # ... (display, search, filter as before) ...
          raw_id_fields = ('linked_organization',) # Make optional FK easier
          inlines = [
              ContactEmailAddressInline,
              ContactPhoneNumberInline,
              ContactAddressInline,
          ]
          # ... rest of admin ...
      ```
  [ ] **(Manual Test):** Verify Admin interface works, including inline channels.

  ### 3.5 Migrations

  [ ] Run `python manage.py makemigrations contact`.
  [ ] **Review generated migration file(s) carefully.** Ensure `linked_organization_id` is nullable.
  [ ] Run `python manage.py migrate` locally.

  ### 3.6 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write tests for channel serializers and `ContactSerializer`. Handle nullable `linked_organization`. Test nested writes.
  [ ] Create `api/v1/base_models/contact/serializers.py`.
  [ ] Define channel serializers.
  [ ] Define `ContactSerializer`. Handle `linked_organization` as `required=False, allow_null=True`. Include `TaggitSerializer`. Implement/test nested write logic.
      ```python
      # api/v1/base_models/contact/serializers.py
      # ... (imports as defined previously) ...
      from api.v1.base_models.organization.models import Organization # For queryset

      # ... Channel Serializers ...

      class ContactSerializer(TaggitSerializer, serializers.ModelSerializer):
          # ... nested channel serializers ...
          linked_organization = serializers.PrimaryKeyRelatedField(
              queryset=Organization.objects.all(), # TODO: [POST-ORGANIZATION] Verify queryset.
              allow_null=True, # Optional field
              required=False
          )
          linked_organization_name = serializers.CharField(source='linked_organization.name', read_only=True, allow_null=True)
          # ... rest of Meta and fields ...

          # **CRITICAL:** Implement/test create/update to handle nested writes for channels
          # Add validate_custom_fields
      ```
  [ ] Run serializer tests; expect pass. Refactor (especially nested writes).

  ### 3.7 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests for `/api/v1/contacts/`.
  [ ] Create `api/v1/base_models/contact/views.py`. Define `ContactViewSet`. Prefetch related channels and `linked_organization`.
      ```python
      # api/v1/base_models/contact/views.py
      from rest_framework import viewsets, permissions
      from ..models import Contact
      from ..serializers import ContactSerializer
      # Import filters, permissions etc

      class ContactViewSet(viewsets.ModelViewSet): # Add OrgScoped mixin later IF contacts are scoped
          serializer_class = ContactSerializer
          permission_classes = [permissions.IsAuthenticated] # Add RBAC later
          queryset = Contact.objects.prefetch_related(
              'email_addresses', 'phone_numbers', 'addresses__address', 'tags' # Prefetch address via link model
          ).select_related('linked_organization').all()
          filter_backends = [...]
          # filterset_fields = [...]
          search_fields = [...]
          ordering_fields = [...]
      ```
  [ ] Run basic API tests; expect pass. Refactor.

  ### 3.8 URL Routing (`urls.py`)

  [ ] Create `api/v1/base_models/contact/urls.py`. Import `ContactViewSet`. Register with router: `router.register(r'contacts', views.ContactViewSet)`.
  [ ] Include `contact.urls` in `api/v1/base_models/urls.py`.
  [ ] **(Test):** Rerun basic API tests.

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests for `Contact` CRUD via `/api/v1/contacts/`.
      *   Test creating/updating contacts **with nested channel data**.
      *   Test primary flag logic via API updates.
      *   Test LIST with filtering.
      *   Test setting/unsetting optional `linked_organization`.
      *   Test validation errors. Test permissions. Test custom fields/tags.
  [ ] Implement/Refine ViewSet and Serializer logic, especially nested create/update.
  [ ] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api.v1.base_models.contact`).
[ ] Manually test Contact CRUD via API client and Admin UI, including nested channels.

## 5. Dependency Refinement / Post-Requisite Steps

*   **After `Organization` (#4) is implemented:**
    1.  **Refine `Contact.linked_organization` ForeignKey:**
        *   **(Decision):** Field is **Optional (nullable)** - confirmed.
        *   **Model Change:** No change needed.
        *   **Serializer Update:** Ensure `queryset=Organization.objects.all()` is correct in `ContactSerializer`.
        *   **Factory Update:** Update `ContactFactory` default for `linked_organization` to use `factory.SubFactory(OrganizationFactory)` if desired for typical test cases.
        *   **Rerun Tests:** Ensure tests pass, especially those involving creating/updating contacts with the organization link.

## 6. Follow-up Actions

[ ] Address TODOs (Nested write logic refinement, primary flag enforcement during nested create/update).
[ ] Create Pull Request for the `contact` app models and API.
[ ] Update API documentation.
[ ] Ensure other models needing contact links (e.g., `Organization`) add their FKs.

--- END OF FILE contact_implementation_steps.md (Consolidated, FINAL REVISED) ---
### Address


# Address - Implementation Steps

## 1. Overview

**Model Name:**
`Address`

**Corresponding PRD:**
`address_prd.md` (Simplified version with Custom Fields)

**Depends On:**
`Timestamped`, `Auditable` (Abstract Base Models). Potentially `django-countries` library.

**Key Features:**
Stores structured physical postal addresses (street, city, state, postal code, country), supports latitude/longitude, includes status and custom fields. Referenced by other models like UserProfile, Organization, Contact, Warehouse.

**Architectural Decision:**
Addresses are managed as nested objects within their parent entities rather than through standalone endpoints. This approach maintains data integrity, simplifies API design, and better represents real-world relationships. See the model and serializer documentation for details.

**Primary Location(s):**
`api/v1/base_models/common/address` (Assuming `common` app for shared entities)

## 2. Prerequisites

[x] Verify prerequisite models/mixins (`Timestamped`, `Auditable`) are implemented.
[x] Ensure the `common` app structure exists (`api/v1/base_models/common/address`).
[x] Ensure `factory-boy` is set up. Basic User factory exists.
[x] **Decision:** How to handle the `country` field?
    *   Option A: Simple `CharField(max_length=2)`. Requires manual validation or choices list later.
    *   Option B: Use `django_countries.fields.CountryField`. Requires installing `django-countries`. Provides built-in choices and validation. **(Chosen)** Steps below assume **Option B**. Install: `pip install django-countries`. Add `'django_countries'` to `INSTALLED_APPS`.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [x] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `common`) verifying:
      *   An `Address` instance can be created with required fields (`country`).
      *   Optional fields can be set (`street_address_1`, `city`, etc.).
      *   `custom_fields` defaults to an empty dict.
      *   `latitude`/`longitude` accept Decimal values.
      *   `country` field stores/validates 2-char code (or validates based on `django-countries`).
      *   `__str__` method returns a reasonable string.
      *   Inherited `Timestamped`/`Auditable` fields exist.
      Run; expect failure (`Address` doesn't exist).
  [x] Define the `Address` class in `api/v1/base_models/common/models.py`.
  [x] Add required inheritance: `Timestamped`, `Auditable`.
  [x] Run tests; expect pass. Refactor model code if needed.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [x] Define `AddressFactory` in `api/v1/base_models/common/tests/factories.py`.
  [x] **(Test)** Write a simple test ensuring `AddressFactory` creates valid `Address` instances.

  ### 3.3 Admin Registration (`admin.py`)

  [x] Create/Update `api/v1/base_models/common/addressadmin.py`.
  [x] Define `AddressAdmin`.
  [x] **(Manual Test):** Verify registration and basic CRUD in Django Admin locally. Check country field works as expected.

  ### 3.4 Migrations

  [x] Run `python manage.py makemigrations api_v1_common`.
  [x] **Review generated migration file carefully.** Check field definitions, indexes.
  [x] Run `python manage.py migrate` locally.

 ### 3.5 Serializer Definition (`serializers.py`)

  [x] **(Test First - Validation/Representation)** Write Unit/Integration Tests (`tests/unit/test_serializers.py`, `tests/integration/test_serializers.py`) for `Serializer`. Test validation (country code format/choice, field lengths), representation, custom field handling.
  [x] Define `Serializer` in `api/v1/ base_models/common/address/serializers.py`.
  [x] Implement `validate_custom_fields` method if applicable, validating against external schema.
  [x] Run tests; expect pass. Refactor.

  ### 3.6 API ViewSet Definition (`views.py`)

  [x] **(Decision):** Will there be standalone `/api/v1/addresses/` endpoints, or will addresses *only* be managed nested under their owning objects (e.g., creating/updating an Organization updates its address)? **Addresses are managed as nested objects within their parent entities rather than through standalone endpoints.** Address instances are created/updated *when needed* by other models. If standalone endpoints are needed later, they can be added.
  [x] *(No ViewSet needed initially if addresses are managed via related objects)*.

  ### 3.7 URL Routing (`urls.py`)

  [x] *(No URLs needed initially if no standalone ViewSet)*.

  ### 3.8 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [x] *(No direct API endpoint tests needed initially)*.
  [x] **Indirect Testing:** Tests for *other* models' API endpoints (e.g., creating an Organization with an address payload) will implicitly test the `AddressSerializer` validation and creation/update of Address instances linked via ForeignKey. Ensure these tests cover address creation/validation scenarios.

## 4. Final Checks

[x] Run the *entire* test suite (`pytest`).
[x] Run linters (`flake8`) and formatters (`black`).
[x] Check code coverage (`pytest --cov`).
[x] Manually test address creation/editing via Django Admin and indirectly via API calls that manage related objects (e.g., UserProfile, Organization).
[x] Review related documentation (Model fields, API Strategy on nested writes if applicable).

## 5. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request.
[x] Update documentation:
    - [x] Added architectural decisions document
    - [x] Updated README with implementation details
    - [x] Added comprehensive docstrings to code
[ ] Ensure other models (`UserProfile`, `Organization`, `Contact`, `Warehouse`, etc.) correctly add `ForeignKey` fields to `Address` as specified in their PRDs.

## 6. Documentation

[x] Create architectural decisions document explaining key design choices
[x] Update README with implementation details and usage examples
[x] Add comprehensive docstrings to code
[x] Document testing strategy and coverage
[x] Document future considerations and potential enhancements

## 7. Next Steps

1. Implement ForeignKey relationships in parent models
2. Add address validation in parent model serializers
3. Consider adding address reuse functionality if needed
4. Monitor performance and add additional indexes if required
5. Consider implementing geocoding integration

--- END OF FILE address_implementation_steps.md ---
## System Models


### Audit Logging


# Audit Logging System - Implementation Steps

## 1. Overview

**Model Name(s):**
`AuditLog`

**Corresponding PRD:**
`audit_logging_system_prd.md`

**Depends On:**
`Timestamped` (for inheritance), `User` (`settings.AUTH_USER_MODEL`), `Organization`, `ContentType` framework, potentially Celery (for async logging), middleware like `django-crum` (for user context).

**Key Features:**
Creates a historical trail of significant data changes (CRUD) and events (Login, Permissions) in a dedicated `AuditLog` model. Uses signals for automatic event capturing. Provides Admin/API for viewing logs.

**Primary Location(s):**
`audit/` (New dedicated app) or `core/`

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `User`, `Organization`, `ContentType`) are implemented and migrated.
[ ] **Create new Django app:** `python manage.py startapp audit`.
[ ] Add `'audit'` (or `core` if placed there) and `'django.contrib.contenttypes'` to `INSTALLED_APPS`.
[ ] Ensure middleware for getting current user (e.g., `django-crum`) is configured.
[ ] Ensure Celery is set up if asynchronous logging is desired (Decision: Sync or Async? Assuming **Sync initially**).
[ ] Ensure `factory-boy` is set up. Factories for `User`, `Organization`, and representative auditable models (e.g., `Product`) exist.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 `AuditLog` Model Definition (`audit/models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`audit/tests/unit/test_models.py`) verifying:
      *   An `AuditLog` instance can be created with required/nullable fields (`user`, `organization`, `action_type`, `content_type`, `object_id`, etc.).
      *   Default timestamping (via `Timestamped.created_at`) works.
      *   `changes` and `context` store JSON correctly.
      *   `__str__` method provides a useful representation.
      Run; expect failure (`AuditLog` doesn't exist).
  [ ] Define the `AuditLog` class in `audit/models.py`.
  [ ] Add required inheritance: `Timestamped`.
      ```python
      # audit/models.py
      from django.conf import settings
      from django.contrib.contenttypes.fields import GenericForeignKey
      from django.contrib.contenttypes.models import ContentType
      from django.db import models
      from django.utils import timezone # If using separate timestamp
      from django.utils.translation import gettext_lazy as _

      from core.models import Timestamped # Adjust import path
      # Import Organization based on final location
      from api.v1.base_models.organization.models import Organization # Adjust path

      # Define Action Type Choices (Store centrally, e.g., audit/choices.py)
      class AuditActionType:
          CREATE = 'CREATE'
          UPDATE = 'UPDATE'
          DELETE = 'DELETE'
          LOGIN_SUCCESS = 'LOGIN_SUCCESS'
          LOGIN_FAILED = 'LOGIN_FAILED'
          LOGOUT = 'LOGOUT'
          PERMISSION_ASSIGN = 'PERMISSION_ASSIGN'
          PERMISSION_REVOKE = 'PERMISSION_REVOKE'
          # ... add more specific types as needed

          CHOICES = [
              (CREATE, _('Create')),
              (UPDATE, _('Update')),
              (DELETE, _('Delete')),
              (LOGIN_SUCCESS, _('Login Success')),
              (LOGIN_FAILED, _('Login Failed')),
              (LOGOUT, _('Logout')),
              (PERMISSION_ASSIGN, _('Permission Assigned')),
              (PERMISSION_REVOKE, _('Permission Revoked')),
              # ...
          ]

      class AuditLog(Timestamped): # Inherits created_at, updated_at
          user = models.ForeignKey(
              settings.AUTH_USER_MODEL,
              verbose_name=_("User"),
              on_delete=models.SET_NULL,
              null=True, blank=True, db_index=True
          )
          organization = models.ForeignKey(
              Organization,
              verbose_name=_("Organization Context"),
              on_delete=models.SET_NULL,
              null=True, blank=True, db_index=True
          )
          action_type = models.CharField(
              _("Action Type"), max_length=50, choices=AuditActionType.CHOICES, db_index=True
          )
          # Generic relation to the object acted upon
          content_type = models.ForeignKey(
              ContentType,
              verbose_name=_("Content Type"),
              on_delete=models.SET_NULL, # Keep log even if model type is deleted
              null=True, blank=True, db_index=True
          )
          object_id = models.CharField(
              _("Object ID"), max_length=255, null=True, blank=True, db_index=True,
              help_text=_("Primary key of the object as string.")
          )
          content_object = GenericForeignKey('content_type', 'object_id')

          object_repr = models.CharField(
              _("Object Representation"), max_length=255, blank=True,
              help_text=_("A human-readable representation of the object.")
          )
          changes = models.JSONField(
              _("Changes"), null=True, blank=True, default=None, # Use None default for nullable JSON
              help_text=_("JSON detailing field changes for UPDATE actions (e.g., {'field': {'old': 'val1', 'new': 'val2'}}).")
          )
          context = models.JSONField(
              _("Context"), null=True, blank=True, default=None,
              help_text=_("Additional context (e.g., IP address, session key).")
          )

          class Meta:
              verbose_name = _("Audit Log Entry")
              verbose_name_plural = _("Audit Log Entries")
              ordering = ['-created_at'] # Show newest first
              indexes = [
                  models.Index(fields=['content_type', 'object_id']),
                  models.Index(fields=['organization', 'user']),
                  models.Index(fields=['action_type']),
              ]

          def __str__(self):
              return f"{self.get_action_type_display()} on {self.object_repr or self.object_id or 'System'} by {self.user or 'System'}"

      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.2 Factory Definition (`audit/tests/factories.py`)

  [ ] Define `AuditLogFactory` in `audit/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from django.contrib.contenttypes.models import ContentType
      from ..models import AuditLog, AuditActionType
      # Import factories for User, Organization, potentially a sample model like Product
      from api.v1.base_models.user.tests.factories import UserFactory
      from api.v1.base_models.organization.tests.factories import OrganizationFactory
      # from api.v1.base_models.common.tests.factories import ProductFactory

      class AuditLogFactory(DjangoModelFactory):
          class Meta:
              model = AuditLog

          user = factory.SubFactory(UserFactory)
          organization = factory.SubFactory(OrganizationFactory)
          action_type = factory.Iterator([choice[0] for choice in AuditActionType.CHOICES])
          # Example: Link to a product instance
          # content_object = factory.SubFactory(ProductFactory)
          # object_repr = factory.LazyAttribute(lambda o: str(o.content_object) if o.content_object else '')
          changes = None
          context = None

          # Correctly set GFK fields if content_object is set
          @factory.lazy_attribute
          def content_type(self):
              if self.content_object:
                  return ContentType.objects.get_for_model(self.content_object)
              return None

          @factory.lazy_attribute
          def object_id(self):
              if self.content_object:
                  return str(self.content_object.pk) # Use string representation
              return None
      ```
  [ ] **(Test)** Write simple tests ensuring the factory creates valid instances, including setting the GFK correctly.

  ### 3.3 Helper Function (`audit/utils.py` or `audit/services.py`)

  [ ] **(Test First)** Write Unit Tests for the `log_audit_event` helper function. Mock the `AuditLog.objects.create` call and verify it's called with the correct arguments based on inputs. Test masking logic if implemented here. Test context merging.
  [ ] Create `audit/utils.py`. Define `log_audit_event` helper:
      ```python
      # audit/utils.py
      from django.contrib.contenttypes.models import ContentType
      from django.utils.encoding import smart_str
      from crum import get_current_request # To get IP/context if needed
      from .models import AuditLog

      def get_object_repr(instance):
          """Get a limited string representation."""
          if instance is None:
              return None
          try:
              return smart_str(instance)[:255] # Limit length
          except Exception:
              return f"<{instance._meta.verbose_name} object ({instance.pk})>"

      def calculate_changes(instance, update_fields=None):
          """
          Calculates the changes dictionary for an UPDATE event.
          Placeholder: Implement actual diffing logic here.
          This is complex - requires comparing current state to previous state.
          Libraries like django-simple-history or careful signal handling needed.
          Returns None if no changes detected or not applicable.
          """
          # TODO: Implement robust change detection logic
          # Basic example (only works if update_fields is reliable AND old values known)
          # if update_fields:
          #    # Need mechanism to get old values (e.g., fetch from DB before save)
          #    pass
          return None # Placeholder

      def get_request_context():
          """Extract basic context from the current request."""
          request = get_current_request()
          if request:
              ip_address = request.META.get('REMOTE_ADDR')
              # Add other context like session key if needed
              return {'ip_address': ip_address}
          return None

      def log_audit_event(
          user, action_type, content_object=None, organization=None,
          changes=None, context=None, object_repr_override=None
      ):
          """Creates an AuditLog entry."""
          ctype = None
          object_id_str = None
          obj_repr = object_repr_override

          if content_object:
              ctype = ContentType.objects.get_for_model(content_object)
              object_id_str = str(content_object.pk)
              if obj_repr is None: # Only get default repr if not overridden
                  obj_repr = get_object_repr(content_object)

          # TODO: Implement sensitive field masking for 'changes' dict here

          final_context = get_request_context() or {}
          if context: # Merge provided context
              final_context.update(context)

          try:
              AuditLog.objects.create(
                  user=user,
                  organization=organization,
                  action_type=action_type,
                  content_type=ctype,
                  object_id=object_id_str,
                  object_repr=obj_repr,
                  changes=changes,
                  context=final_context or None # Store None if empty
              )
          except Exception as e:
              # Log error to standard logging, but don't crash primary operation
              import logging
              logger = logging.getLogger(__name__)
              logger.error(f"Failed to create AuditLog entry: {e}", exc_info=True)

      ```
  [ ] Run tests for helper; expect pass. Refactor.

  ### 3.4 Signal Receivers (`audit/signals.py`)

  [ ] **(Test First)** Write Integration Tests (`audit/tests/integration/test_signals.py`) using `@pytest.mark.django_db`.
      *   Test `post_save` on a sample audited model (e.g., `Product`):
          *   Create instance -> verify AuditLog created with `action_type='CREATE'`, correct user, object details.
          *   Update instance -> verify AuditLog created with `action_type='UPDATE'`, correct user, object details, and placeholder `changes=None` (or basic diff if implemented).
      *   Test `post_delete` -> verify `AuditLog` created with `action_type='DELETE'`.
      *   Test auth signals (`user_logged_in`, etc.) -> verify correct AuditLog created with user and context (mock request for IP).
      Run; expect failure (receivers not connected).
  [ ] Create `audit/signals.py`. Define signal receivers using the helper function.
      ```python
      # audit/signals.py
      from django.conf import settings
      from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
      from django.db.models.signals import post_save, post_delete
      from django.dispatch import receiver
      from crum import get_current_user

      from .models import AuditLog, AuditActionType
      from .utils import log_audit_event, calculate_changes # Import helper

      # List of models to automatically audit on CRUD
      # Get this from settings or explicitly list them
      AUDITED_MODELS = [
          'organization.Organization', 'user.UserProfile', 'common.Product', # etc.
          # Use 'app_label.ModelName' format
      ]

      def get_model_from_string(model_string):
          from django.apps import apps
          try:
              app_label, model_name = model_string.split('.')
              return apps.get_model(app_label, model_name)
          except (ValueError, LookupError):
              return None

      def get_org_from_instance(instance):
          # Helper to find organization context
          if hasattr(instance, 'organization'):
              return instance.organization
          if hasattr(instance, 'user') and hasattr(instance.user, 'profile') \
             and hasattr(instance.user.profile, 'primary_organization'):
              return instance.user.profile.primary_organization
          # Add other common ways to find org context
          return None

      @receiver(post_save)
      def audit_post_save(sender, instance, created, raw, using, update_fields, **kwargs):
          """Audit model CREATE and UPDATE events."""
          model_label = f"{sender._meta.app_label}.{sender._meta.model_name}"
          if raw or model_label not in AUDITED_MODELS: # Ignore fixture loading and non-audited models
              return

          user = get_current_user()
          organization = get_org_from_instance(instance)
          action = AuditActionType.CREATE if created else AuditActionType.UPDATE
          changes = None
          if not created:
              changes = calculate_changes(instance, update_fields) # Basic diff logic here

          log_audit_event(
              user=user,
              organization=organization,
              action_type=action,
              content_object=instance,
              changes=changes,
          )

      @receiver(post_delete)
      def audit_post_delete(sender, instance, using, **kwargs):
          """Audit model DELETE events."""
          model_label = f"{sender._meta.app_label}.{sender._meta.model_name}"
          if model_label not in AUDITED_MODELS:
              return

          user = get_current_user()
          organization = get_org_from_instance(instance)

          log_audit_event(
              user=user,
              organization=organization,
              action_type=AuditActionType.DELETE,
              content_object=instance, # Pass instance for object_repr even though it's deleted
              object_repr_override=str(instance) # Ensure representation captured
          )

      # --- Auth Signals ---
      @receiver(user_logged_in)
      def audit_user_logged_in(sender, request, user, **kwargs):
          # Note: organization context might be harder to get here reliably
          log_audit_event(user=user, action_type=AuditActionType.LOGIN_SUCCESS)

      @receiver(user_login_failed)
      def audit_user_login_failed(sender, credentials, request, **kwargs):
          # User object isn't available here
          log_audit_event(user=None, action_type=AuditActionType.LOGIN_FAILED, context={'username_attempt': credentials.get('username')})

      @receiver(user_logged_out)
      def audit_user_logged_out(sender, request, user, **kwargs):
           if user: # User might be None if session expired before logout
               log_audit_event(user=user, action_type=AuditActionType.LOGOUT)

      # --- Connect signals dynamically based on AUDITED_MODELS list ---
      # Or connect explicitly if list is small
      # Example explicit connection:
      # post_save.connect(audit_post_save, sender=Product)
      # post_delete.connect(audit_post_delete, sender=Product)

      # TODO: Implement dynamic connection based on AUDITED_MODELS setting
      # TODO: Add receivers for permission/role changes (m2m_changed)

      ```
  [ ] Connect signals in `audit/apps.py`:
      ```python
      # audit/apps.py
      from django.apps import AppConfig

      class AuditConfig(AppConfig):
          default_auto_field = 'django.db.models.BigAutoField'
          name = 'audit'

          def ready(self):
              try:
                  import audit.signals # Connect signals
              except ImportError:
                  pass
      ```
  [ ] Run signal integration tests; expect pass. Refactor receiver logic, especially change calculation and org context retrieval.

  ### 3.5 Admin Registration (`audit/admin.py`)

  [ ] Create `audit/admin.py`. Define `AuditLogAdmin`.
      ```python
      # audit/admin.py
      from django.contrib import admin
      from django.utils.html import format_html
      # Consider django-json-widget for better JSON display
      # from jsoneditor.forms import JSONEditor
      # from django.db import models

      from .models import AuditLog

      @admin.register(AuditLog)
      class AuditLogAdmin(admin.ModelAdmin):
          list_display = ('created_at', 'user_display', 'organization', 'action_type', 'object_link', 'object_repr')
          list_filter = ('action_type', 'content_type', ('created_at', admin.DateFieldListFilter), 'organization', 'user')
          search_fields = ('user__username', 'object_repr', 'object_id', 'changes', 'context') # Searching JSON might be slow
          list_select_related = ('user', 'organization', 'content_type')
          readonly_fields = [f.name for f in AuditLog._meta.fields] # Make all fields read-only
          # formfield_overrides = { # Example using django-json-widget
          #     models.JSONField: {'widget': JSONEditor},
          # }

          def has_add_permission(self, request): return False
          def has_change_permission(self, request, obj=None): return False
          def has_delete_permission(self, request, obj=None): return False

          @admin.display(description='User')
          def user_display(self, obj):
              return obj.user or 'System'

          @admin.display(description='Object')
          def object_link(self, obj):
              # Create link to the related object's admin page if possible
              if obj.content_object and obj.content_type:
                  try:
                      admin_url = admin.site.get_admin_url(obj.content_object)
                      return format_html('<a href="{}">{}</a>', admin_url, obj.object_repr or obj.object_id)
                  except Exception:
                       return obj.object_repr or obj.object_id
              return obj.object_repr or obj.object_id

      ```
  [ ] **(Manual Test):** Perform actions (create/update/delete audited models, login/logout). Verify logs appear in Admin. Check filters/search. Verify read-only nature.

  ### 3.6 API Endpoint Definition (Optional - Read-Only)

  [ ] **(Test First)** Write API tests for `/api/v1/audit-logs/`. Test permissions (admin/auditor only). Test filtering by user, org, type, date, object. Test pagination.
  [ ] Define `AuditLogSerializer` (read-only).
  [ ] Define `AuditLogViewSet` (inheriting `ReadOnlyModelViewSet`). Add necessary filters (`django-filter` recommended here). Secure with appropriate permission class.
  [ ] Define URL routing.
  [ ] Run API tests; expect pass.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=audit`). Review uncovered signal/helper logic.
[ ] Manually test Audit Log generation and viewing via Admin for key scenarios.
[ ] Review related documentation.

## 5. Follow-up Actions

[ ] Address TODOs (robust change calculation, dynamic signal connection, M2M auditing).
[ ] Implement Archiving/Purging strategy (requires separate command/task).
[ ] Implement Data Masking for sensitive fields in `changes`.
[ ] Create Pull Request.
[ ] Update documentation (list of audited models, action types, etc.).

--- END OF FILE auditlogging_implementation_steps.md ---
### Auditable


# Auditable - Implementation Steps

## 1. Overview

**Model Name:**
`Auditable` (Abstract Base Model)

**Corresponding PRD:**
`auditable_prd.md`

**Depends On:**
Django `User` model (`settings.AUTH_USER_MODEL`), `Timestamped` (often used together, but not a strict dependency for Auditable itself), Middleware pattern for accessing current user (e.g., `django-crum`).

**Key Features:**
Provides automatic `created_by` and `updated_by` foreign key fields (linking to User) via an Abstract Base Model, populated automatically on save.

**Primary Location(s):**
`core/models.py` (Alongside `Timestamped`)
`core/middleware.py` (Or separate app if `django-crum` is not used)
`config/settings/base.py` (For middleware registration)

## 2. Prerequisites

[x] Verify the `User` model (`settings.AUTH_USER_MODEL`) is correctly configured.
[x] Verify the `core` app exists.
[x] **Decide on User Fetching Mechanism:** Confirm use of `django-crum` OR plan for implementing custom thread-local middleware. Steps below assume **`django-crum`**.
[x] Install `django-crum`: `pip install django-crum` and add `'crum'` to `INSTALLED_APPS` in `config/settings/base.py`.

## 3. Implementation Steps (TDD Workflow)

  *(Testing abstract models involves testing their effect on a concrete test model)*

  ### 3.1 Middleware Setup (`django-crum`)

  [x] Add `crum.CurrentRequestUserMiddleware` to the `MIDDLEWARE` list in `config/settings/base.py`. Place it **after** `AuthenticationMiddleware`.
      ```python
      # config/settings/base.py
      MIDDLEWARE = [
          # ... other middleware
          'django.contrib.sessions.middleware.SessionMiddleware',
          'django.middleware.common.CommonMiddleware',
          'django.middleware.csrf.CsrfViewMiddleware',
          'django.contrib.auth.middleware.AuthenticationMiddleware',
          'crum.CurrentRequestUserMiddleware', # Add crum middleware
          'django.contrib.messages.middleware.MessageMiddleware',
          'django.middleware.clickjacking.XFrameOptionsMiddleware',
          # ... other middleware
      ]
      ```
  [x] *(No specific test needed for adding middleware itself, test its effect later)*.

  ### 3.2 Model Definition (`core/models.py`)

  [x] **(Test First)**
      Create/Update `core/tests/test_auditable_model.py`.
      Define a simple concrete test model *within the test file* inheriting `Auditable`:
      ```python
      # core/tests/test_auditable_model.py
      import pytest
      from django.db import models
      from django.contrib.auth import get_user_model
      from django.test import TestCase, RequestFactory
      from crum import set_current_user # For setting user in tests
      from core.models import Auditable # Will fail initially
      from api.v1.base_models.user.tests.factories import UserFactory # Adjust import

      User = get_user_model()

      class ConcreteAuditableModel(Auditable):
          name = models.CharField(max_length=100)
          # Add Timestamped if testing together
          # created_at = models.DateTimeField(auto_now_add=True)
          # updated_at = models.DateTimeField(auto_now=True)

          class Meta:
              app_label = 'core'
      ```
      Write **Integration Test(s)** using `@pytest.mark.django_db` (database needed to trigger `save`) and `mocker` (from `pytest-mock`) if needed to simulate requests/middleware interaction *if not relying solely on crum context manager*. Test cases:
      *   Create instance with `user1` set as current user -> verify `created_by` and `updated_by` are `user1`.
      *   Update instance with `user2` set as current user -> verify `created_by` is still `user1`, `updated_by` is `user2`.
      *   Create/Update instance with *no* current user set -> verify `created_by`/`updated_by` are `None`.
      ```python
      # core/tests/test_auditable_model.py (continued)
      @pytest.mark.django_db
      class AuditableModelTests:

          @pytest.fixture
          def user1(self):
              return UserFactory()

          @pytest.fixture
          def user2(self):
              return UserFactory()

          def test_user_set_on_create(self, user1):
              """Verify created_by and updated_by are set on creation."""
              set_current_user(user1) # Set user context using crum
              instance = ConcreteAuditableModel.objects.create(name="Test Create")
              set_current_user(None) # Clear context after operation

              assert instance.created_by == user1
              assert instance.updated_by == user1

          def test_updated_by_changes_on_update(self, user1, user2):
              """Verify updated_by changes on save() but created_by doesn't."""
              set_current_user(user1)
              instance = ConcreteAuditableModel.objects.create(name="Test Update")
              set_current_user(None) # Clear user1 context

              created_by_user = instance.created_by

              # Simulate update by a different user
              instance.name = "Updated Name"
              set_current_user(user2)
              instance.save()
              set_current_user(None) # Clear user2 context

              instance.refresh_from_db()

              assert instance.created_by == created_by_user # Should still be user1
              assert instance.updated_by == user2 # Should now be user2

          def test_users_are_null_if_no_user_in_context(self):
              """Verify fields are null if no user is set."""
              set_current_user(None) # Explicitly no user
              instance = ConcreteAuditableModel.objects.create(name="Test No User")

              assert instance.created_by is None
              assert instance.updated_by is None

              instance.name = "Update No User"
              instance.save()
              instance.refresh_from_db()

              assert instance.created_by is None # Still None
              assert instance.updated_by is None # Still None

      ```
      Run `pytest core/tests/test_auditable_model.py`; expect `ImportError` or test failures. **(Red)**

  [x] Define the `Auditable` abstract base model class in `core/models.py`:
      ```python
      # core/models.py
      from django.conf import settings
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from crum import get_current_user # Import crum function

      class Auditable(models.Model):
          """
          Abstract base model providing `created_by` and `updated_by` fields
          linked to the User model, automatically populated on save.
          Relies on middleware like django-crum to set the current user.
          """
          created_by = models.ForeignKey(
              settings.AUTH_USER_MODEL,
              verbose_name=_("Created By"),
              related_name="+", # No reverse relation needed
              on_delete=models.SET_NULL,
              null=True,
              blank=True,
              editable=False,
              help_text=_("User who created the record.")
          )
          updated_by = models.ForeignKey(
              settings.AUTH_USER_MODEL,
              verbose_name=_("Updated By"),
              related_name="+", # No reverse relation needed
              on_delete=models.SET_NULL,
              null=True,
              blank=True,
              editable=False,
              help_text=_("User who last updated the record.")
          )

          class Meta:
              abstract = True
              # Consider ordering if needed, maybe '-updated_at' if used with Timestamped

          def save(self, *args, **kwargs):
              """Override save to set created_by and updated_by."""
              user = get_current_user()
              if user and not user.pk:
                  # User object might exist but not be saved yet (e.g., during tests)
                  # Or user might be AnonymousUser which doesn't have pk
                  user = None

              # Set created_by only on first save (when pk is None)
              if self.pk is None and user:
                  self.created_by = user

              # Set updated_by on every save if user is available
              if user:
                  self.updated_by = user

              super().save(*args, **kwargs)
      ```
  [x] Run the tests again (`pytest core/tests/test_auditable_model.py`). They should now pass. **(Green)**
  [x] Refactor the model code (e.g., error handling in `save`) or test code for clarity. Ensure tests still pass. **(Refactor)**

  ### 3.2 Factory Definition (`tests/factories.py`)

  [x] Not applicable directly for the abstract model. Factories for concrete models inheriting `Auditable` might optionally set `created_by`/`updated_by` if specific test scenarios require it, but usually rely on the automatic population via `save()`.

  ### 3.3 Admin Registration (`admin.py`)

  [x] Not applicable directly. Admin classes for concrete models inheriting `Auditable` should add `created_by` and `updated_by` to `readonly_fields` and potentially `list_display`.

  ### 3.4 Migrations

  [x] Not applicable directly. Migrations are generated for concrete models inheriting `Auditable`, adding the `created_by_id` and `updated_by_id` columns and foreign key constraints.

  ### 3.5 Serializer Definition (`serializers.py`)

  [x] Not applicable directly. Serializers for concrete models inheriting `Auditable` may include `created_by` and `updated_by` as `read_only=True` fields, potentially using nested serializers or `PrimaryKeyRelatedField`.

  ### 3.6 API ViewSet Definition (`views.py`)

  [x] Not applicable directly.

  ### 3.7 URL Routing (`urls.py`)

  [x] Not applicable directly.

  ### 3.8 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [x] Not applicable directly. API tests for concrete models inheriting `Auditable` should verify (by inspecting the created/updated database object) that `created_by`/`updated_by` fields are correctly populated with the authenticated user making the API request.

## 4. Final Checks

[x] Run the *entire* test suite (`pytest`) to check for regressions.
[x] Run linters (`flake8`) and formatters (`black`) on `core/models.py` and `core/tests/test_auditable_model.py`.
[x] Review the code, especially the `save()` method override and the middleware dependency.

## 5. Follow-up Actions

[x] Commit the changes (`core/models.py`, `core/tests/test_auditable_model.py`, `settings.py` middleware addition, `requirements/test.txt` addition).
[ ] Create Pull Request for review.
[x] Concrete models implemented subsequently can now inherit from `core.models.Auditable` (usually alongside `Timestamped`).

## 6. Implementation Status

**Current Status:** Implementation completed successfully. All tests are passing with 100% coverage for the test file and 97% coverage for the model implementation.

**Key Achievements:**
- Successfully implemented the `Auditable` abstract base model
- Created and passed all test cases
- Set up middleware for user tracking
- Achieved high test coverage
- All prerequisites and implementation steps completed

**Next Steps:**
- Create Pull Request for review
- Document usage examples for concrete models
- Consider adding integration with `Timestamped` model for combined usage

--- END OF FILE auditable_implementation_steps.md ---
### Timestamped


# Timestamped - Implementation Steps

## 1. Overview

**Model Name:**
`Timestamped`

**Corresponding PRD:**
`timestamped_prd.md` (Simplified & Specified version)

**Depends On:**
None (Only base Django `models.Model`)

**Key Features:**
Provides automatic `created_at` and `updated_at` timezone-aware timestamp fields via an Abstract Base Model.

**Primary Location(s):**
`core/models.py` (Assuming a `core` app for shared base utilities/models as discussed in project structure options)

## 2. Prerequisites

[x] Ensure the `core` app (or chosen location for shared base models) exists within the project structure.
[x] Verify `USE_TZ = True` is set in `config/settings/base.py`.

## 3. Implementation Steps (TDD Workflow)

  *(Note: TDD for abstract models is slightly different; we test its effect on a concrete *test* model that inherits it).*

  ### 3.1 Model Definition (`core/models.py`)

  [x] **(Test First)**
      Created test file `core/tests/test_timestamped_model.py`.
      Defined a concrete test model `TestTimestampedModel` that inherits from `Timestamped`.
      Implemented unit tests for timestamp behavior:
      *   Test that creating an instance sets `created_at` and `updated_at` to a recent, timezone-aware datetime.
      *   Test that updating the instance changes `updated_at` but not `created_at`.
      *   Added proper timestamp comparison with microsecond delta tolerance.

  [x] Defined the `Timestamped` abstract base model class in `core/models.py`:
      ```python
      # core/models.py
      from django.db import models
      from django.utils.translation import gettext_lazy as _

      class Timestamped(models.Model):
          """
          Abstract base model providing self-updating `created_at` and `updated_at` fields.
          """
          created_at = models.DateTimeField(
              _("Created At"),
              auto_now_add=True,
              editable=False,
              help_text=_("Timestamp when the record was created.")
          )
          updated_at = models.DateTimeField(
              _("Updated At"),
              auto_now=True,
              editable=False,
              help_text=_("Timestamp when the record was last updated.")
          )

          class Meta:
              abstract = True
              ordering = ['-created_at'] # Default ordering for inheriting models
      ```

  [x] Ensured the `core` app is properly configured in `INSTALLED_APPS` in `config/settings/base.py` using `'core.apps.CoreConfig'`.
  [x] Ran and passed all tests with proper timestamp comparison handling.
  [x] Refactored test code for better timestamp comparison handling.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [x] Not applicable. No factory needed for an abstract base model itself. Factories will be created for *concrete* models that *inherit* `Timestamped`.

  ### 3.3 Admin Registration (`admin.py`)

  [x] Not applicable. Abstract base models cannot be registered with the Django Admin. Admin configuration will happen on concrete inheriting models.

  ### 3.4 Migrations

  [x] Not applicable directly. Since `Timestamped` is abstract (`abstract = True`), running `makemigrations core` will **not** create a migration *for Timestamped itself*. Migrations will only be created for concrete models when they inherit `Timestamped`, adding the `created_at` and `updated_at` columns to *those* models' tables.

  ### 3.5 Serializer Definition (`serializers.py`)

  [x] Not applicable. Serializers are defined for concrete models. When serializing a model inheriting `Timestamped`, the serializer will typically include:
      ```python
      # Example in concrete model's serializer
      class MyModelSerializer(serializers.ModelSerializer):
          created_at = serializers.DateTimeField(read_only=True)
          updated_at = serializers.DateTimeField(read_only=True)

          class Meta:
              model = MyModel
              fields = [..., 'created_at', 'updated_at'] # Include if needed
              read_only_fields = [..., 'created_at', 'updated_at'] # Alternative way
      ```

  ### 3.6 API ViewSet Definition (`views.py`)

  [x] Not applicable. ViewSets are defined for concrete models.

  ### 3.7 URL Routing (`urls.py`)

  [x] Not applicable.

  ### 3.8 API Endpoint Testing (CRUD & Features) (`tests/api/test_endpoints.py`)

  [x] Not applicable directly. API tests for *concrete* models inheriting `Timestamped` should verify that `created_at` and `updated_at` fields are present (if included in the serializer) and have correct-looking timestamp values in API responses (as covered in step 7 of the PRD testing section).

## 4. Final Checks

[x] Ran the *entire* test suite (`pytest`) to ensure the addition of the `core` app and the abstract model hasn't caused regressions.
[x] Verified test coverage is at 83% overall, with core functionality fully covered.
[x] Reviewed the code for clarity and adherence to standards.

## 5. Follow-up Actions

[x] Committed the changes (`core/models.py`, `core/tests/test_timestamped_model.py`, updates to `settings.py`).
[ ] Create Pull Request for review.
[x] Concrete models can now inherit from `core.models.Timestamped`.

## 6. Additional Improvements Made

- Added comprehensive security settings in `base.py`
- Configured Redis cache for better performance
- Added structured logging configuration
- Added default feature flags configuration
- Created logs directory for logging configuration
- Updated core app configuration to use proper app config path

--- END OF FILE timestamped_implementation_steps.md ---
### Status


# Status - Implementation Steps

## 1. Overview

**Model Name:**
`Status`

**Corresponding PRD:**
`status_prd.md` (Simplified version with Custom Fields)

**Depends On:**
`Timestamped`, `Auditable` (Abstract Base Models)

**Key Features:**
Defines standardized status values (e.g., 'Active', 'Pending', 'Draft') used across different ERP models. Includes slug (PK), name, description, category, color hint, and custom fields. Serves as a reference/vocabulary.

**Primary Location(s):**
`api/v1/base_models/common/` (Assuming `common` app for shared entities)

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`) are implemented.
[ ] Ensure the `common` app structure exists (`api/v1/base_models/common/`).
[ ] Ensure `factory-boy` is set up. Basic User factory exists.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `common`) verifying:
      *   A `Status` instance can be created with required fields (`slug`, `name`).
      *   `slug` is the primary key.
      *   Unique constraints (`slug`, `name`) are present.
      *   Optional fields (`description`, `category`, `color`) can be set.
      *   `custom_fields` defaults to an empty dict.
      *   `__str__` method returns the `name`.
      *   Inherited `Timestamped`/`Auditable` fields exist.
      Run; expect failure (`Status` doesn't exist).
  [ ] Define the `Status` class in `api/v1/base_models/common/models.py`.
  [ ] Add required inheritance: `Timestamped`, `Auditable`.
      ```python
      # api/v1/base_models/common/models.py
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from core.models import Timestamped, Auditable # Adjust import path

      class Status(Timestamped, Auditable):
          slug = models.SlugField(
              _("Slug"),
              max_length=50,
              primary_key=True, # Use slug as the stable identifier
              help_text=_("Unique machine-readable identifier (e.g., 'pending_approval').")
          )
          name = models.CharField(
              _("Name"),
              max_length=100,
              unique=True, # Human-readable name should also be unique
              db_index=True,
              help_text=_("Human-readable status name (e.g., 'Pending Approval').")
          )
          description = models.TextField(
              _("Description"),
              blank=True,
              help_text=_("Optional description of what this status represents.")
          )
          category = models.CharField(
              _("Category"),
              max_length=50,
              blank=True,
              db_index=True,
              help_text=_("Optional category for grouping statuses (e.g., 'General', 'Order Lifecycle').")
          )
          color = models.CharField(
              _("Color"),
              max_length=7, # e.g., #RRGGBB
              blank=True,
              help_text=_("Optional HEX color code for UI representation.")
          )
          # Consider adding is_active boolean if statuses can be retired
          # is_active = models.BooleanField(default=True, db_index=True)
          custom_fields = models.JSONField(
              _("Custom Fields"),
              default=dict,
              blank=True,
              help_text=_("Custom data associated with this status definition.")
          )

          class Meta:
              verbose_name = _("Status")
              verbose_name_plural = _("Statuses")
              ordering = ['category', 'name']

          def __str__(self):
              return self.name
      ```
  [ ] Run tests; expect pass. Refactor model code if needed.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `StatusFactory` in `api/v1/base_models/common/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from ..models import Status

      class StatusFactory(DjangoModelFactory):
          class Meta:
              model = Status
              django_get_or_create = ('slug',) # Use slug for get_or_create

          slug = factory.Sequence(lambda n: f'status_{n}')
          name = factory.Sequence(lambda n: f'Status Name {n}')
          description = factory.Faker('sentence')
          category = factory.Iterator(['General', 'Order', 'User', None])
          color = factory.Faker('hex_color')
          custom_fields = {}
      ```
  [ ] **(Test)** Write a simple test ensuring `StatusFactory` creates valid instances.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Create/Update `api/v1/base_models/common/admin.py`.
  [ ] Define `StatusAdmin`:
      ```python
      from django.contrib import admin
      from .models import Status

      @admin.register(Status)
      class StatusAdmin(admin.ModelAdmin):
          list_display = ('slug', 'name', 'category', 'color', 'updated_at')
          search_fields = ('slug', 'name', 'description', 'category')
          list_filter = ('category',)
          prepopulated_fields = {'slug': ('name',)} # Auto-populate slug from name
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
          fieldsets = (
              (None, {'fields': ('slug', 'name', 'description')}),
              ('Categorization', {'fields': ('category', 'color')}),
              ('Custom Data', {'fields': ('custom_fields',)}),
              ('Audit Info', {'classes': ('collapse',), 'fields': readonly_fields}),
          )
      ```
  [ ] **(Manual Test):** Verify registration, CRUD operations, and slug prepopulation in Django Admin locally.

  ### 3.4 Initial Data Population (Migration)

  [ ] Create a new **Data Migration** file: `python manage.py makemigrations --empty --name populate_initial_statuses api.v1.base_models.common`.
  [ ] Edit the generated migration file (`..._populate_initial_statuses.py`). Add `RunPython` operations to load essential common statuses.
      ```python
      from django.db import migrations

      INITIAL_STATUSES = [
          # Slug, Name, Category (Optional), Description (Optional), Color (Optional)
          ('draft', 'Draft', 'General', 'Record is being drafted, not yet active.', '#AAAAAA'),
          ('active', 'Active', 'General', 'Record is active and in use.', '#4CAF50'),
          ('inactive', 'Inactive', 'General', 'Record is not currently active but may be reactivated.', '#FF9800'),
          ('archived', 'Archived', 'General', 'Record is archived and typically read-only.', '#9E9E9E'),
          ('pending', 'Pending', 'Process', 'Waiting for action or approval.', '#2196F3'),
          ('pending_approval', 'Pending Approval', 'Approval', 'Waiting for approval step.', '#2196F3'),
          ('approved', 'Approved', 'Approval', 'Record has been approved.', '#4CAF50'),
          ('rejected', 'Rejected', 'Approval', 'Record has been rejected.', '#F44336'),
          ('completed', 'Completed', 'Process', 'Process or task is finished.', '#00BCD4'),
          ('cancelled', 'Cancelled', 'Process', 'Process or task was cancelled.', '#795548'),
          # Add other common statuses as needed
      ]

      def populate_statuses(apps, schema_editor):
          Status = apps.get_model('common', 'Status') # Use app_label from apps.py
          db_alias = schema_editor.connection.alias

          statuses_to_add = []
          for slug, name, category, desc, color in INITIAL_STATUSES:
              statuses_to_add.append(
                  Status(slug=slug, name=name, category=category or '', description=desc or '', color=color or '')
              )
          Status.objects.using(db_alias).bulk_create(statuses_to_add, ignore_conflicts=True)
          print(f"\nPopulated/updated {len(statuses_to_add)} statuses.")

      def remove_statuses(apps, schema_editor):
          pass # Usually safe to leave statuses in place on reversal

      class Migration(migrations.Migration):
          dependencies = [
              ('common', '000X_auto_...'), # Depends on Status model creation migration
          ]
          operations = [
              migrations.RunPython(populate_statuses, reverse_code=remove_statuses),
          ]
      ```

  ### 3.5 Migrations (Apply Initial Model & Data)

  [ ] Run `python manage.py makemigrations api.v1.base_models.common`.
  [ ] **Review generated migration file(s) carefully.**
  [ ] Run `python manage.py migrate` locally. Verify data loaded via Admin.

  ### 3.6 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write Unit/Integration Tests (`tests/unit/test_serializers.py`, etc.) for `StatusSerializer`. Test representation, custom field handling. Validation tests likely minimal as it's mostly read-only via API.
  [ ] Define `StatusSerializer` in `api/v1/base_models/common/serializers.py`:
      ```python
      from rest_framework import serializers
      from ..models import Status

      class StatusSerializer(serializers.ModelSerializer):
          class Meta:
              model = Status
              fields = [
                  'slug',
                  'name',
                  'description',
                  'category',
                  'color',
                  'custom_fields',
                  # Include Timestamped/Auditable fields if needed by API consumers
              ]
              # Generally read-only from an API perspective
              read_only_fields = fields
      ```
  [ ] Implement `validate_custom_fields` if needed (unlikely for read-only).
  [ ] Run tests; expect pass. Refactor.

  ### 3.7 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests (`tests/api/test_endpoints.py`) for `/api/v1/statuses/`. Test unauthenticated access (likely allowed for read).
  [ ] Define `StatusViewSet` in `api/v1/base_models/common/views.py`:
      ```python
      from rest_framework import viewsets, permissions
      from rest_framework import filters # Use standard filters
      from ..models import Status
      from ..serializers import StatusSerializer

      class StatusViewSet(viewsets.ReadOnlyModelViewSet):
          """
          API endpoint allowing statuses to be viewed.
          Statuses are typically managed via the Admin interface or migrations.
          """
          queryset = Status.objects.all() # Maybe filter is_active=True if added
          serializer_class = StatusSerializer
          permission_classes = [permissions.AllowAny] # Or IsAuthenticatedOrReadOnly
          lookup_field = 'slug' # Use slug for retrieval
          filter_backends = [filters.SearchFilter, filters.OrderingFilter]
          search_fields = ['slug', 'name', 'description', 'category']
          ordering_fields = ['category', 'name', 'slug']
          pagination_class = None # List is usually short
      ```
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.8 URL Routing (`urls.py`)

  [ ] Import `StatusViewSet` in `api/v1/base_models/common/urls.py`.
  [ ] Register with router: `router.register(r'statuses', views.StatusViewSet)`.
  [ ] **(Test):** Rerun basic API tests; expect 200 OK for listing/retrieving.

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - List/Retrieve)** Write tests for `GET /api/v1/statuses/` and `GET /api/v1/statuses/{slug}/`. Assert 200, check structure, verify initial statuses present. Test search filters.
  [ ] Ensure ViewSet query/filtering works.
  [ ] Run list/retrieve tests; expect pass. Refactor.
  [ ] *(CRUD tests not applicable for ReadOnlyModelViewSet)*.
  [ ] *(Test custom field saving/validation via API if management endpoints were added)*.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/base_models/common`).
[ ] Manually test via API client and Django Admin. Verify initial statuses exist.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Ensure other models use `CharField` with choices referencing these `Status.slug` values (or `ForeignKey` if that approach was chosen).

--- END OF FILE status_implementation_steps.md ---
## Authentication & Authorization


### Auth API


# Authentication API - Implementation Steps (Revised for API Keys)

## 1. Overview

**Feature Name:**
Authentication API (JWT + API Key + 2FA Enablement)

**Depends On:**
Django `auth` app (`User` model), `UserProfile` model, `djangorestframework-simplejwt`, `django-otp`, `djangorestframework-api-key`. Secure settings management.

**Key Features:**
Provides API endpoints for user login (username/password) via JWT, token refresh, and enables users to set up TOTP 2FA. Also integrates API Key authentication using `djangorestframework-api-key` via the `X-API-Key` header for server-to-server communication. Excludes 2FA verification during login and full password reset flow initially.

**Primary Location(s):**
*   Library Configuration: `settings.py`.
*   API Views/Serializers/URLs: Dedicated `auth` app (`api/v1/base_models/comon/auth/`) or within `user` app (`api/v1/base_models/user/`). Assume **new `auth` app**.
*   2FA Device Models: Provided by `django-otp`.
*   API Key Models: Provided by `rest_framework_api_key`.

## 2. Prerequisites

[x] Verify `User` and `UserProfile` models are implemented and migrated.
[x] **Install Libraries:** `pip install djangorestframework-simplejwt django-otp qrcode[pil] djangorestframework-api-key`.
[x] Add `'rest_framework_simplejwt'`, `'django_otp'`, `'django_otp.plugins.otp_totp'`, and `'rest_framework_api_key'` to `INSTALLED_APPS`.
[x] Add `'django_otp.middleware.OTPMiddleware'` to `MIDDLEWARE` (after `AuthenticationMiddleware`).
[x] **Configure `simplejwt`:** Set up `SIMPLE_JWT` settings (token lifetimes, etc.) as previously defined.
[x] **Configure `django-otp`:** Set `OTP_TOTP_ISSUER` as previously defined.
[x] **Configure `djangorestframework-api-key`:** Specify the custom header name in `settings.py`.
    ```python
    # config/settings/base.py
    REST_FRAMEWORK_API_KEY = {
        'HEADER_NAME': 'HTTP_X_API_KEY', # DRF converts X-Api-Key header to this META key
        'CLIENT_ID_HEADER_NAME': None, # Not using Client ID header
    }
    ```
[x] **Configure DRF Authentication Classes:** Update default authentication classes to include both JWT and API Key.
    ```python
    # config/settings/base.py
    REST_FRAMEWORK = {
        # ... other settings ...
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'rest_framework_simplejwt.authentication.JWTAuthentication',
            'rest_framework_api_key.authentication.APIKeyAuthentication', # Add API Key Auth
        ],
        # ... other settings like DEFAULT_PERMISSION_CLASSES ...
    }
    ```
[x] Create new Django app: `python manage.py startapp auth`. Add `'api.v1.base_models.comon.auth'` to `INSTALLED_APPS`.
[x] Ensure `factory-boy` and `UserFactory` exist.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Library Migrations

  [x] Run `python manage.py makemigrations django_otp otp_totp rest_framework_api_key`.
  [x] **Review migrations** created by the libraries.
  [x] Run `python manage.py migrate`.

  ### 3.2 JWT Token Endpoints (Login/Refresh)

  [x] **(Test First)** Write **API Test(s)** (`auth/tests/api/test_token_endpoints.py`) for JWT obtain/refresh endpoints.
  [x] Create `api/v1/base_models/comon/auth/urls.py`. Include `simplejwt` views (`TokenObtainPairView`, `TokenRefreshView`).
  [x] Include `auth.urls` in main `api/v1/urls.py` under the `auth/` prefix.
  [x] Run tests; expect pass. Refactor simplejwt settings if needed.

  ### 3.3 API Key Admin Management

  [x] **(Manual Test)** Access Django Admin. Verify the "API Key Permissions" section exists (provided by `djangorestframework-api-key`).
  [x] Create a test API Key via the Admin:
      *   Give it a Name (e.g., "Test Service Key").
      *   **Important:** Note down the **unhashed** key generated (it's only shown once).
      *   Optionally assign permissions directly to this key object if `HasAPIKey` permission class will be used later.
      *   Set an expiry date.
      *   Save the key.

  ### 3.4 API Key Authentication Testing

  [x] **(Test First)** Write **API Test(s)** (`auth/tests/api/test_api_key.py`) for accessing a sample authenticated endpoint (e.g., `/api/v1/profiles/me/` if implemented, or create a simple test view):
      *   Test making a request **without** the `X-API-Key` header -> Assert 401/403 (depending on if JWT allows anonymous or not).
      *   Test making a request with an **invalid/incorrect** `X-API-Key` header -> Assert 401/403.
      *   Test making a request with the **correct, unhashed** `X-API-Key` header (obtained from Admin) -> Assert 200 OK (or appropriate success code for the endpoint).
      *   Test with an **expired** API Key -> Assert 401/403.
      *   Test with a **revoked** API Key -> Assert 401/403.
      Run; expect tests requiring a valid key to pass, others to fail appropriately.
  [x] *(No code changes needed here, this tests the configuration)*.

  ### 3.5 2FA (TOTP) Device Setup Models & Admin

  [x] *(No code changes, covered by migrations in 3.1)*.
  [x] **(Manual Test - Optional)** Verify `TOTPDevice` admin integration if configured.

  ### 3.6 2FA (TOTP) Enablement API Endpoints

  [x] **(Test First)** Write API Tests (`auth/tests/api/test_2fa_setup.py`) for TOTP Setup (`POST /setup/`) and Verification (`POST /verify/`) as outlined previously.
  [x] Create `auth/views.py` and `auth/serializers.py`. Define `TOTPSetupView` and `TOTPVerifyView` as outlined previously.
  [x] Add URLs for these views in `auth/urls.py`.
  [x] Run setup/verification API tests; expect pass. Refactor views.

  ### 3.7 2FA Disable Endpoint (Basic)

  [x] **(Test First)** Write API Test for `POST /api/v1/auth/2fa/totp/disable/`.
  [x] Add `TOTPDisableView(APIView)` requiring password confirmation. Add URL.
  [x] Run disable tests; expect pass.

  ### 3.8 Password Management API (Basic Change)

  [x] **(Test First)** Write API Test for `POST /api/v1/auth/password/change/`.
  [x] Add a `PasswordChangeView(GenericAPIView)` using Django's `PasswordChangeForm` or a custom serializer. Add URL.
  [x] Run password change tests; expect pass.

## 4. Final Checks

[x] Run the *entire* test suite (`pytest`). Verify JWT and API Key auth paths work. Verify 2FA setup flow tests.
[x] Run linters (`flake8`) and formatters (`black`).
[x] Check code coverage (`pytest --cov=auth`).
[ ] Manually test JWT login/refresh via API client.
[ ] Manually test API access using a generated API Key with the `X-API-Key` header.
[ ] Manually test the TOTP setup flow: Call setup -> scan QR -> call verify. Test disable. Test password change.
[ ] Review API documentation draft for auth endpoints (JWT, API Key usage, 2FA setup).

## 5. Follow-up Actions / Future Considerations

[ ] **CRITICAL:** Implement 2FA verification **during the login flow** (modifying JWT obtain view).
[ ] Implement full Password Reset flow.
[ ] Implement API endpoint for Admins to manage API Keys if needed beyond Django Admin.
[ ] Implement management of other OTP devices (Static/Backup codes).
[ ] Implement token blocklisting for JWT logout.
[ ] Define and apply specific API Key permissions using `rest_framework_api_key.permissions.HasAPIKey` where needed.
[ ] Create Pull Request.
[ ] Update API documentation.

## 6. Current Status (Updated: [Current Date])

- All core authentication features implemented and tested
- Test coverage: 97% (2134 statements, 65 missed)
- All automated tests passing (158 passed, 2 skipped)
- Areas for improvement:
  - Manual testing of endpoints still pending
  - API documentation needs to be updated
  - 2FA verification during login flow needs to be implemented
  - Password reset flow needs to be implemented
  - Token blocklisting for JWT logout needs to be implemented

--- END OF FILE auth_api_implementation_steps.md (Revised for API Keys) ---
### Organization Membership



# OrganizationMembership - Implementation Steps

## 1. Overview

**Model Name:**
`OrganizationMembership`

**Corresponding PRD:**
`OrganizationMembership_prd.md`

**Depends On:**
`Timestamped`, `Auditable` (Abstract Base Models), `User` (`settings.AUTH_USER_MODEL`), `Organization`, Django `Group` (`django.contrib.auth.models.Group`).

**Key Features:**
Links Users to Organizations and assigns a specific Role (Django Group) for that membership. Enables multi-organization access and organization-specific roles. Core component for Org-Aware RBAC.

**Primary Location(s):**
`api/v1/base_models/organizations/` (Placing it within the organization app seems logical) or potentially a dedicated `memberships` app. Assume **`organizations` app** for this example.

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `User`, `Organization`) are implemented and migrated.
[ ] Verify Django `auth` app (providing `Group`) and `contenttypes` app are configured.
[ ] Ensure the `organization` app structure exists (`api/v1/base_models/organization/`).
[ ] Ensure `factory-boy` is set up. Factories for `User`, `Organization`, `Group` exist.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `organization`) verifying:
      *   `OrganizationMembership` creation with required fields (`user`, `organization`, `role`).
      *   `unique_together` constraint (`user`, `organization`) is enforced.
      *   Default values (`is_active`). FKs work correctly.
      *   `__str__` method returns expected string.
      *   Inherited `Timestamped`/`Auditable` fields exist.
      Run; expect failure (`OrganizationMembership` doesn't exist).
  [ ] Define the `OrganizationMembership` class in `api/v1/base_models/organization/models.py`.
  [ ] Add required inheritance: `Timestamped`, `Auditable`.
      ```python
      # api/v1/base_models/organization/models.py
      # ... (other imports like Organization, OrganizationType) ...
      from django.conf import settings
      from django.contrib.auth.models import Group
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from core.models import Timestamped, Auditable # Adjust import path

      class OrganizationMembership(Timestamped, Auditable):
          user = models.ForeignKey(
              settings.AUTH_USER_MODEL,
              on_delete=models.CASCADE,
              related_name='organization_memberships'
          )
          organization = models.ForeignKey(
              'Organization', # Self-app reference ok if in same models.py
              on_delete=models.CASCADE,
              related_name='memberships'
          )
          role = models.ForeignKey(
              Group, # Link to Django Group representing the Role
              verbose_name=_("Role (Group)"),
              on_delete=models.PROTECT, # Don't delete Group if used in membership
              related_name='organization_memberships'
              # null=True, blank=True, # Make role optional? PRD implies required
          )
          is_active = models.BooleanField(
              _("Is Active Member"), default=True, db_index=True
          )
          # Add is_default or join_date here if needed per PRD optional fields

          class Meta:
              verbose_name = _("Organization Membership")
              verbose_name_plural = _("Organization Memberships")
              unique_together = ('user', 'organization') # User has one definition per org
              ordering = ['organization__name', 'user__username']
              indexes = [
                  models.Index(fields=['user', 'organization']),
                  models.Index(fields=['role']),
                  models.Index(fields=['is_active']),
              ]

          def __str__(self):
              role_name = self.role.name if self.role else 'N/A'
              user_name = self.user.username if self.user else 'N/A'
              org_name = self.organization.name if self.organization else 'N/A'
              return f"{user_name} in {org_name} as {role_name}"

      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `OrganizationMembershipFactory` in `api/v1/base_models/organization/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from django.contrib.auth.models import Group
      from ..models import OrganizationMembership, Organization
      # Import UserFactory, OrganizationFactory
      from api.v1.base_models.user.tests.factories import UserFactory
      from .factories import OrganizationFactory # Assuming in same file

      class GroupFactory(DjangoModelFactory): # Define basic Group factory if not done elsewhere
          class Meta:
              model = Group
              django_get_or_create = ('name',)
          name = factory.Sequence(lambda n: f'Role {n}')

      class OrganizationMembershipFactory(DjangoModelFactory):
          class Meta:
              model = OrganizationMembership
              # Ensure unique combination for tests using get_or_create
              django_get_or_create = ('user', 'organization')

          user = factory.SubFactory(UserFactory)
          organization = factory.SubFactory(OrganizationFactory)
          role = factory.SubFactory(GroupFactory)
          is_active = True
      ```
  [ ] **(Test)** Write simple tests ensuring the factory creates valid instances and respects `unique_together`.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Create/Update `api/v1/base_models/organization/admin.py`.
  [ ] Define `OrganizationMembershipAdmin`. Use `raw_id_fields` for easier selection.
      ```python
      from django.contrib import admin
      from .models import OrganizationMembership

      @admin.register(OrganizationMembership)
      class OrganizationMembershipAdmin(admin.ModelAdmin):
          list_display = ('user', 'organization', 'role', 'is_active', 'updated_at')
          list_filter = ('organization', 'role', 'is_active')
          search_fields = ('user__username', 'organization__name', 'role__name')
          list_select_related = ('user', 'organization', 'role')
          raw_id_fields = ('user', 'organization', 'role') # Better for large numbers
          list_editable = ('is_active', 'role')
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
      ```
  [ ] **(Manual Test):** Verify Admin CRUD operations for memberships.

  ### 3.4 Implement `User.get_organizations()` Helper

  [ ] **(Test First)** Write Unit Tests (`tests/unit/test_models.py` in `user` app) for the `User.get_organizations()` method:
      *   Test user with no memberships -> returns empty queryset.
      *   Test user with one active membership -> returns queryset containing that one organization.
      *   Test user with multiple active memberships -> returns queryset containing all linked organizations.
      *   Test user with only inactive memberships -> returns empty queryset (assuming `is_active` should be checked).
      Run; expect failure (method doesn't exist or is wrong).
  [ ] Add/Modify the `get_organizations` method on the `User` model (or a Manager/Mixin):
      ```python
      # api/v1/base_models/user/models.py (or wherever User model is defined/extended)
      # Assuming Organization model imported correctly
      from api.v1.base_models.organization.models import Organization

      # If extending AbstractUser:
      class User(AbstractUser):
          # ... other fields ...
          def get_organizations(self):
              """Returns a QuerySet of active Organizations the user is a member of."""
              return Organization.objects.filter(
                  memberships__user=self,
                  memberships__is_active=True # Only consider active memberships
              ).distinct()

      # If using signals/profile with default User:
      # Add this method dynamically or on a custom Manager/Proxy model if needed.
      # For simplicity, often added directly if extending AbstractUser.
      ```
  [ ] Run `get_organizations` tests; expect pass. Refactor.

  ### 3.5 Migrations

  [ ] Run `python manage.py makemigrations api.v1.base_models.organization`.
  [ ] **Review generated migration file carefully.** Check FKs, `unique_together`, indexes.
  [ ] Run `python manage.py migrate` locally.

  ### 3.6 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write tests for `OrganizationMembershipSerializer`. Test representation (including nested User/Org/Role names/IDs), validation (`unique_together` if creating via API), read-only fields.
  [ ] Define `OrganizationMembershipSerializer` in `api/v1/base_models/organization/serializers.py`.
      ```python
      from rest_framework import serializers
      from django.contrib.auth.models import Group
      from ..models import OrganizationMembership, Organization
      # Import simplified serializers for related objects if needed
      # from api.v1.base_models.user.serializers import UserSummarySerializer

      class GroupSerializer(serializers.ModelSerializer): # Simple serializer for Role/Group
          class Meta: model = Group; fields = ['id', 'name']

      class OrganizationMembershipSerializer(serializers.ModelSerializer):
          # Represent related objects by ID for writing, potentially nested/summary for reading
          user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all()) # Or UserSummarySerializer(read_only=True)
          organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all()) # Or OrgSummarySerializer(read_only=True)
          role = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all()) # Or GroupSerializer(read_only=True)

          # Read-only expanded versions for easier consumption
          username = serializers.CharField(source='user.username', read_only=True)
          organization_name = serializers.CharField(source='organization.name', read_only=True)
          role_name = serializers.CharField(source='role.name', read_only=True)

          class Meta:
              model = OrganizationMembership
              fields = [
                  'id', 'user', 'username', 'organization', 'organization_name',
                  'role', 'role_name', 'is_active',
                  # Add optional fields like join_date, is_default if implemented
                  'created_at', 'updated_at',
              ]
              read_only_fields = ('id', 'username', 'organization_name', 'role_name', 'created_at', 'updated_at')
              # Add unique_together validation if allowing creation via API
              validators = [
                  serializers.UniqueTogetherValidator(
                      queryset=OrganizationMembership.objects.all(),
                      fields=('user', 'organization'),
                      message=_("User already has a membership in this organization.")
                  )
              ]
      ```
  [ ] Run serializer tests; expect pass. Refactor.

  ### 3.7 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write API Tests for `/api/v1/organization-memberships/`. Test CRUD operations (likely admin-restricted). Test LIST filtering by user or organization. Test permissions.
  [ ] Define `OrganizationMembershipViewSet` in `api/v1/base_models/organization/views.py`.
      ```python
      from rest_framework import viewsets, permissions
      from ..models import OrganizationMembership
      from ..serializers import OrganizationMembershipSerializer
      # Import filters, admin permissions etc

      class OrganizationMembershipViewSet(viewsets.ModelViewSet):
          """
          API endpoint for managing Organization Memberships (Admin/Restricted).
          """
          serializer_class = OrganizationMembershipSerializer
          permission_classes = [permissions.IsAdminUser] # Example: Restrict to Admins
          queryset = OrganizationMembership.objects.select_related(
              'user', 'organization', 'role'
          ).all()
          filter_backends = [...] # Add filtering backend
          filterset_fields = ['user', 'organization', 'role', 'is_active']
          search_fields = ['user__username', 'organization__name', 'role__name']
      ```
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.8 URL Routing (`urls.py`)

  [ ] Import `OrganizationMembershipViewSet` in `api/v1/base_models/organization/urls.py`.
  [ ] Register with router: `router.register(r'organization-memberships', views.OrganizationMembershipViewSet)`.
  [ ] **(Test):** Rerun basic API tests; expect 2xx/4xx codes.

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests for Membership CRUD via API.
      *   LIST (test filtering by user/org).
      *   CREATE (assign user to org with role). Test `unique_together`.
      *   RETRIEVE.
      *   UPDATE (change role or `is_active`).
      *   DELETE.
      *   Test permissions rigorously (only admins can manage).
  [ ] Implement/Refine ViewSet and Serializer logic.
  [ ] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/base_models/organization`).
[ ] Manually test assigning/changing/removing user memberships via Django Admin. Test filtering/searching.
[ ] Review API documentation draft (if management API exposed).

## 5. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request.
[ ] Update documentation.
[ ] Ensure Org-Aware RBAC strategy and implementation uses this model correctly.
[ ] Ensure `OrganizationScoped` ViewSet Mixin correctly uses `user.get_organizations()` based on this model.

--- END OF FILE organizationmembership_implementation_steps.md ---
### Organization Scoped


# OrganizationScoped Mechanism - Implementation Steps (Revised for Simple Org-Aware RBAC)

## 1. Overview

**Component Name:**
`OrganizationScoped` (Abstract Base Model) & `OrganizationScopedViewSetMixin`

**Corresponding PRD:**
`organizationscoped_prd.md` (Revised for Simple Org-Aware RBAC)

**Depends On:**
`Organization` model, `User` model, `OrganizationMembership` model, Org-Aware RBAC check function (`has_perm_in_org`), DRF (`viewsets`, `mixins`), Base API View structure.

**Key Features:**
Provides multi-tenancy via an `organization` ForeignKey (Abstract Base Model) and automatic queryset filtering in ViewSets based on user's `OrganizationMembership`. Ensures creation happens within authorized organizations using Org-Aware RBAC.

**Primary Location(s):**
*   Abstract Model: `core/models.py`
*   ViewSet Mixin: `core/views.py` or `api/v1/base_views.py`

## 2. Prerequisites

[ ] Verify `Organization`, `User`, `UserProfile`, `OrganizationMembership` models implemented/migrated.
[ ] Verify helper method `user.get_organizations()` (querying `OrganizationMembership`) is implemented and tested.
[ ] Verify the Org-Aware RBAC permission checking mechanism (`has_perm_in_org` or similar function/backend method) is implemented.
[ ] Ensure `core` app (or shared location) exists.
[ ] Ensure basic DRF ViewSet structure established.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Abstract Base Model Definition (`core/models.py`)

  [ ] **(Test First - Model Structure)** Write Unit Tests (`core/tests/test_orgscoped_model.py`) using a concrete test model inheriting `OrganizationScoped`. Verify `organization` FK exists, links to `Organization`, `on_delete=PROTECT`, non-nullable, `db_index=True`. Test `IntegrityError` on create without org. *(This step likely already done based on previous iteration)*.
  [ ] Define/Verify the `OrganizationScoped` abstract base model in `core/models.py`:
      ```python
      # core/models.py
      # ... other imports ...
      from api.v1.base_models.organization.models import Organization # Adjust path

      class OrganizationScoped(models.Model):
          organization = models.ForeignKey(
              Organization,
              verbose_name=_("Organization"),
              on_delete=models.PROTECT,
              related_name='%(app_label)s_%(class)s_set',
              db_index=True, # Ensure index is added via abstract model if possible
              help_text=_("The Organization this record belongs to.")
          )
          class Meta: abstract = True
      ```
  [ ] Run tests; expect pass.

  ### 3.2 Base ViewSet Mixin Definition (`core/views.py` or `api/base_views.py`)

  [ ] **(Test First - ViewSet Logic)**
      Write **Integration Test(s)** (`core/tests/test_orgscoped_views.py`) using `@pytest.mark.django_db`.
      *   Setup Orgs (A, B), Users (UserA in OrgA via Membership+Role, UserB in OrgB, Superuser). Give UserA `view_concretescopedmodel` permission *only* via their role in OrgA membership.
      *   Create test data using `ConcreteScopedModel` in OrgA and OrgB.
      *   Create test ViewSet (`ConcreteScopedViewSet`) inheriting `OrganizationScopedViewSetMixin` + `ReadOnlyModelViewSet`. Register with router.
      *   Test `GET` list as UserA -> Assert **only OrgA data** returned.
      *   Test `GET` list as UserB -> Assert **only OrgB data** returned (if they have view perm in OrgB).
      *   Test `GET` list as Superuser -> Assert **OrgA and OrgB data** returned.
      *   Test `GET` list as User belonging to *no* orgs -> Assert empty list.
      *   Test `GET` list as User belonging to *both* OrgA and OrgB -> Assert data from *both* orgs returned.
      *   **Add Test for Create:**
          *   Use a test ViewSet inheriting the Mixin + `CreateModelMixin`.
          *   `POST` as UserA with payload specifying `organization=OrgA.pk`. Mock the Org-Aware `has_perm` check to return `True`. Assert 201 Created, verify `instance.organization` is OrgA.
          *   `POST` as UserA with payload specifying `organization=OrgB.pk`. Mock Org-Aware `has_perm` check to return `False`. Assert 403 Forbidden or appropriate validation error from `perform_create`.
          *   `POST` as UserA *without* specifying `organization` in payload. Assert appropriate error (e.g., 400 Bad Request) because target org cannot be determined.
      Run; expect failure. **(Red)**
  [ ] Define/Refine the `OrganizationScopedViewSetMixin`:
      ```python
      # core/views.py (Example location)
      from rest_framework.exceptions import PermissionDenied, ValidationError
      from django.shortcuts import get_object_or_404
      # Import Organization based on final location
      from api.v1.base_models.organization.models import Organization
      # Import your Org-Aware permission checker
      from rbac.permissions import has_perm_in_org # Example import path

      class OrganizationScopedViewSetMixin:
          """
          DRF ViewSet Mixin for Organization Scoped data.
          - Filters querysets in get_queryset() based on user's memberships.
          - Validates/sets organization in perform_create() based on request data and permissions.
          """
          def get_queryset(self):
              queryset = super().get_queryset()
              user = self.request.user

              if not user or not user.is_authenticated: return queryset.none()
              if user.is_superuser: return queryset

              user_organizations = user.get_organizations() # Queries OrganizationMembership
              if not user_organizations.exists(): return queryset.none()

              # Filter by the organizations the user is an active member of
              return queryset.filter(organization__in=user_organizations)

          def perform_create(self, serializer):
              user = self.request.user
              # --- Determine Target Organization ---
              # Option 1: Explicitly require 'organization' in request data
              org_pk = serializer.validated_data.get('organization', None) # Assuming it's validated if present
              if not org_pk:
                  # Try getting from URL kwarg if nested route like /orgs/{org_pk}/items/
                  org_pk = self.kwargs.get('organization_pk') # Adjust kwarg name as needed

              if not org_pk:
                   raise ValidationError({'organization': ['This field is required for scoped creation.']})

              # Fetch the target organization instance
              target_organization = get_object_or_404(Organization, pk=org_pk)

              # --- Permission Check ---
              # Get the required model 'add' permission codename
              model_meta = self.queryset.model._meta
              add_perm = f'{model_meta.app_label}.add_{model_meta.model_name}'

              # Check permission using the Org-Aware RBAC function
              if not has_perm_in_org(user, add_perm, target_organization):
                   raise PermissionDenied(f"You do not have permission to add '{model_meta.model_name}' records in organization '{target_organization.name}'.")

              # Save with validated organization
              serializer.save(organization=target_organization) # Pass org to serializer save

          def get_serializer_context(self):
               """ Add org context for serializers if needed"""
               context = super().get_serializer_context()
               # If needed, determine target org for validation based on request/instance
               # target_organization = ... logic to determine context ...
               # context['target_organization'] = target_organization
               return context
      ```
      *   **Note on `perform_create`:** This example assumes the `organization` PK is passed in the request body. Adjust logic if using nested URLs or other context methods. The key is to **identify the target org** and **check permission *for that org***.
      *   **Note on Serializer:** The serializer for the inheriting model might need `serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all(), write_only=True, required=True)` for the `organization` field to accept input during POST/PUT, or it could be excluded and set only by `perform_create`.
  [ ] Run ViewSet logic tests; expect pass. **(Green)**
  [ ] Refactor the mixin. **(Refactor)**

  ### 3.3 Applying to Concrete Models/Views

  [ ] **(Test First - Real ViewSet)** Write comprehensive API tests for actual scoped models (`Product`, `Warehouse`, `Document`, etc.). Ensure LIST, RETRIEVE, CREATE, UPDATE, DELETE respect Org Scoping and Org-Aware permissions. Test creating objects by providing the target `organization` PK in the payload.
  [ ] Ensure concrete models inherit `OrganizationScoped`.
  [ ] Ensure concrete ViewSets inherit `OrganizationScopedViewSetMixin`.
  [ ] Ensure concrete Serializers handle the `organization` field appropriately (e.g., read-only for output, potentially writeable input field for create, validated in view `perform_create`).
  [ ] Run tests; expect pass.

  ### 3.4 Migrations

  [ ] Ensure `makemigrations` is run for apps containing models inheriting `OrganizationScoped`.
  [ ] **Review:** Verify `organization_id` column and index are added.
  [ ] Run `migrate`.

  ### 3.5 Documentation Updates

  [ ] Update documentation (API Strategy, Developer Guides) about Org Scoped models/views. Emphasize how target org is determined on create and how permissions are checked.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`). Verify all Org Scoping and permission tests pass for various users and organizations.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov`). Ensure mixin logic is covered.
[ ] Manually test API endpoints for scoped models with different users (Superuser, User in Org A, User in Org B, User in no Org). Verify data isolation and create permissions.

## 5. Follow-up Actions

[ ] Address TODOs (Refine `perform_create` org determination if needed).
[ ] Create Pull Request.
[ ] Update relevant documentation.
[ ] Apply mixins to all necessary future models.

--- END OF FILE organizationscoped_implementation_steps.md (Revised for Simple Org-Aware RBAC) ---
## Business Models


### Product



# Product - Implementation Steps

## 1. Overview

**Model Name:**
`Product`

**Corresponding PRD:**
`product_prd.md` (Simplified version)

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationScoped` (Abstract Base Models), `Organization`, `Category`, `UnitOfMeasure`, `Status` (model/choices), `django-taggit` library. Requires Custom Field Definition mechanism if used.

**Key Features:**
Central catalog item (good, service, etc.). Includes SKU, type, category, UoM, status, inventory tracking flag, basic attributes (JSON), custom fields (JSON). Scoped by Organization. Supports tagging.

**Primary Location(s):**
`api/v1/features/products/` (Assuming a dedicated `products` feature app/group within `features`, based on project structure examples)

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `OrganizationScoped`, `Organization`, `Category`, `UnitOfMeasure`, `Status`) are implemented and migrated.
[ ] Ensure `django-taggit` is installed and configured (`taggit` in `INSTALLED_APPS`, migrated).
[ ] Create the `products` app structure: `api/v1/features/products/`.
[ ] Add `'api.v1.features.products'` (adjust path) to `INSTALLED_APPS`.
[ ] Ensure `factory-boy` is set up. Factories for `Organization`, `Category`, `UnitOfMeasure`, `User` exist.
[ ] Define `ProductType` and `ProductStatus` choices (e.g., in `products/choices.py`, referencing `Status.slug` values for status).

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `products`) verifying:
      *   `Product` creation with required fields (`name`, `sku`, `organization`, `product_type`, `base_uom`).
      *   `unique_together` constraint (`organization`, `sku`) is enforced.
      *   Default values (`status`, `is_inventory_tracked`, `is_purchasable`, `is_sellable`, `attributes`, `custom_fields`) are set.
      *   FKs (`category`, `base_uom`, `organization`) work and respect `limit_choices_to` for category.
      *   `tags` manager exists and works.
      *   `__str__` method works.
      *   Inherited fields (`Timestamped`, `Auditable`, `OrganizationScoped`) exist.
      Run; expect failure (`Product` doesn't exist).
  [ ] Define the `Product` class in `api/v1/features/products/models.py`.
  [ ] Add required inheritance: `Timestamped`, `Auditable`, `OrganizationScoped`.
      ```python
      # api/v1/features/products/models.py
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from taggit.managers import TaggableManager

      # Assuming Abstract Base Models are in core
      from core.models import Timestamped, Auditable, OrganizationScoped
      # Assuming related models are in common base_models app
      from api.v1.base_models.common.models import Category, UnitOfMeasure # Adjust path
      # Import Status slugs if referencing them directly
      # from api.v1.base_models.common.models import Status

      # Define choices (or import from choices.py)
      class ProductType:
          PHYSICAL = 'PHYSICAL_GOOD'
          SERVICE = 'SERVICE'
          DIGITAL = 'DIGITAL'
          # ... add others ...
          CHOICES = [...]

      class ProductStatus: # Referencing Status slugs
          DRAFT = 'draft'
          ACTIVE = 'active'
          DISCONTINUED = 'discontinued'
          # ... add others matching Status model slugs ...
          CHOICES = [...] # Define choices tuple if needed for validation

      class Product(Timestamped, Auditable, OrganizationScoped):
          name = models.CharField(_("Name"), max_length=255, db_index=True)
          sku = models.CharField(_("SKU/Code"), max_length=100, db_index=True)
          description = models.TextField(_("Description"), blank=True)
          product_type = models.CharField(
              _("Product Type"), max_length=50, choices=ProductType.CHOICES, db_index=True
          )
          # Link to generic category, filtered by type
          category = models.ForeignKey(
              Category,
              verbose_name=_("Category"),
              related_name='products',
              on_delete=models.PROTECT,
              null=True, blank=True,
              limit_choices_to={'category_type': 'PRODUCT'} # Ensure correct category type
          )
          status = models.CharField(
              _("Status"), max_length=50, default=ProductStatus.DRAFT, db_index=True
              # choices=ProductStatus.CHOICES # Add choices for admin/serializer validation
          )
          base_uom = models.ForeignKey(
              UnitOfMeasure,
              verbose_name=_("Base Unit of Measure"),
              related_name='products_base',
              on_delete=models.PROTECT
          )
          is_inventory_tracked = models.BooleanField(_("Inventory Tracked?"), default=True)
          is_purchasable = models.BooleanField(_("Purchasable?"), default=True)
          is_sellable = models.BooleanField(_("Sellable?"), default=True)

          tags = TaggableManager(blank=True, verbose_name=_("Tags"))
          attributes = models.JSONField(
              _("Attributes"), default=dict, blank=True,
              help_text=_("Semi-structured attributes like color, size, dimensions if not using variants.")
          )
          custom_fields = models.JSONField(
              _("Custom Fields"), default=dict, blank=True
          )

          class Meta:
              verbose_name = _("Product")
              verbose_name_plural = _("Products")
              unique_together = (('organization', 'sku'),)
              ordering = ['name']
              indexes = [
                  models.Index(fields=['organization', 'sku']),
                  models.Index(fields=['organization', 'name']),
                  models.Index(fields=['status']),
                  models.Index(fields=['category']),
              ]

          def __str__(self):
              return f"{self.name} ({self.sku})"

      ```
  [ ] Run tests; expect pass. Refactor model code if needed.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `ProductFactory` in `api/v1/features/products/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from ..models import Product, ProductType, ProductStatus
      # Import related factories
      from api.v1.base_models.organization.tests.factories import OrganizationFactory
      from api.v1.base_models.common.tests.factories import CategoryFactory, UnitOfMeasureFactory

      class ProductFactory(DjangoModelFactory):
          class Meta:
              model = Product
              # Avoid duplicate SKUs within the same org during test runs
              # django_get_or_create = ('organization', 'sku') # Careful if org changes

          name = factory.Sequence(lambda n: f'Product {n}')
          sku = factory.Sequence(lambda n: f'SKU-{n:05}')
          organization = factory.SubFactory(OrganizationFactory)
          product_type = factory.Iterator([choice[0] for choice in ProductType.CHOICES])
          # Ensure category has correct type
          category = factory.SubFactory(
              CategoryFactory,
              category_type='PRODUCT',
              # Ensure category belongs to same org if categories are scoped
              # organization=factory.SelfAttribute('..organization')
          )
          status = ProductStatus.ACTIVE
          base_uom = factory.SubFactory(UnitOfMeasureFactory, code='EA', name='Each', uom_type='Count')
          is_inventory_tracked = True
          is_purchasable = True
          is_sellable = True
          attributes = {}
          custom_fields = {}

          # Example for adding tags
          # @factory.post_generation
          # def tags(self, create, extracted, **kwargs):
          #     if not create: return
          #     if extracted: # Pass tags=['tag1', 'tag2'] to factory
          #         for tag in extracted: self.tags.add(tag)
          #     else: # Add some default tags maybe
          #         self.tags.add('test-product')
      ```
  [ ] **(Test)** Write simple tests ensuring the factory creates valid instances and sets relationships correctly.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Create `api/v1/features/products/admin.py`.
  [ ] Define `ProductAdmin`:
      ```python
      from django.contrib import admin
      from .models import Product

      @admin.register(Product)
      class ProductAdmin(admin.ModelAdmin):
          list_display = (
              'sku', 'name', 'organization', 'category', 'product_type',
              'status', 'base_uom', 'is_inventory_tracked', 'updated_at'
          )
          list_filter = ('organization', 'product_type', 'status', 'category', 'is_inventory_tracked')
          search_fields = ('sku', 'name', 'description', 'category__name')
          list_select_related = ('organization', 'category', 'base_uom')
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
          autocomplete_fields = ['category', 'base_uom'] # Assumes admin registered for Category/UoM
          fieldsets = (
              (None, {'fields': ('organization', ('sku', 'name'), 'status')}),
              ('Classification', {'fields': ('product_type', 'category', 'tags')}),
              ('Details', {'fields': ('description', 'base_uom')}),
              ('Flags', {'fields': ('is_inventory_tracked', 'is_purchasable', 'is_sellable')}),
              ('Extended Data', {'classes': ('collapse',), 'fields': ('attributes', 'custom_fields')}),
              ('Audit Info', {'classes': ('collapse',), 'fields': readonly_fields}),
          )
          # Taggit admin widget usually works automatically
          # JSONFields might need django-json-widget
      ```
  [ ] **(Manual Test):** Verify registration, CRUD, filtering, search, related field lookups in Django Admin locally. Ensure Org Scoping seems respected (though primarily enforced via API).

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations api.v1.features.products`.
  [ ] **Review generated migration file carefully.** Check FKs, `unique_together`, indexes.
  [ ] Run `python manage.py migrate` locally.

  ### 3.5 Serializer Definition (`serializers.py`)

  [ ] **(Test First - Validation/Representation)** Write Unit/Integration Tests (`tests/unit/test_serializers.py`, etc.) for `ProductSerializer`. Test validation (`unique_together`, FK existence, `limit_choices_to` for category), representation (including tags, potentially nested Category/UoM), custom field/attribute handling.
  [ ] Define `ProductSerializer` in `api/v1/features/products/serializers.py`. Integrate `TaggitSerializer`. Handle nested reads/PK writes for FKs. Include `FieldPermissionSerializerMixin`.
      ```python
      from rest_framework import serializers
      from taggit.serializers import TagListSerializerField, TaggitSerializer
      from ..models import Product
      # Import related serializers if nesting read-only representation
      # from api.v1.base_models.common.serializers import CategorySerializer, UnitOfMeasureSerializer
      # Import FieldPermission mixin
      # from core.serializers import FieldPermissionSerializerMixin

      class ProductSerializer(TaggitSerializer, serializers.ModelSerializer): # Add FieldPermissionSerializerMixin
          tags = TagListSerializerField(required=False)
          # Example: Read-only nested, write via PK
          # category_details = CategorySerializer(source='category', read_only=True)
          # base_uom_details = UnitOfMeasureSerializer(source='base_uom', read_only=True)
          category = serializers.PrimaryKeyRelatedField(
              queryset=Category.objects.filter(category_type='PRODUCT'), # Enforce type
              allow_null=True, required=False
          )
          base_uom = serializers.PrimaryKeyRelatedField(
              queryset=UnitOfMeasure.objects.all() # Or filter active
          )
          # Organization is usually set via OrgScoped mixin, make read-only here
          organization = serializers.PrimaryKeyRelatedField(read_only=True)
          organization_name = serializers.CharField(source='organization.name', read_only=True)

          class Meta:
              model = Product
              fields = [
                  'id', 'name', 'sku', 'description', 'product_type',
                  'category', #'category_details',
                  'status',
                  'base_uom', #'base_uom_details',
                  'is_inventory_tracked', 'is_purchasable', 'is_sellable',
                  'tags', 'attributes', 'custom_fields',
                  'organization', 'organization_name',
                  'created_at', 'updated_at',
              ]
              read_only_fields = ('id', 'organization', 'organization_name', 'created_at', 'updated_at')
      ```
  [ ] Implement `validate_sku` (check uniqueness within organization if DB constraint insufficient), `validate_custom_fields`.
  [ ] Run tests; expect pass. Refactor.

  ### 3.6 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests checking `/api/v1/products/` URL existence, authentication, basic permissions.
  [ ] Define `ProductViewSet` in `api/v1/features/products/views.py`. Inherit `OrganizationScopedViewSetMixin`.
      ```python
      from rest_framework import viewsets, permissions
      from core.views import OrganizationScopedViewSetMixin # Adjust import path
      from ..models import Product
      from ..serializers import ProductSerializer
      # Import filters, permissions

      class ProductViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
          serializer_class = ProductSerializer
          permission_classes = [permissions.IsAuthenticated] # Add specific Product permissions
          # queryset is automatically filtered by OrganizationScopedViewSetMixin
          queryset = Product.objects.select_related(
              'organization', 'category', 'base_uom'
          ).prefetch_related('tags').all()

          filter_backends = [...] # Advanced filtering, Search, Ordering
          # Define filterset_class pointing to a ProductFilter defined in filters.py
          # filterset_fields = ['category', 'status', 'product_type', 'tags__name']
          search_fields = ['sku', 'name', 'description', 'category__name']
          ordering_fields = ['name', 'sku', 'created_at', 'updated_at']
      ```
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.7 URL Routing (`urls.py`)

  [ ] Create `api/v1/features/products/urls.py`. Import `ProductViewSet`. Register with router: `router.register(r'products', views.ProductViewSet)`.
  [ ] Include `products.urls` in `api/v1/features/urls.py`.
  [ ] **(Test):** Rerun basic API tests; expect 2xx/4xx codes.

  ### 3.8 API Endpoint Testing (CRUD & Features) (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests covering:
      *   LIST (with filters for category, status, type, tags). **Verify Org Scoping works.**
      *   CREATE (valid/invalid data, check org auto-set). Test permission checks (model & field).
      *   RETRIEVE (check permissions, org scoping).
      *   UPDATE (PUT/PATCH, check permissions, field permissions).
      *   DELETE (check permissions).
      *   Saving/Validating `attributes` and `custom_fields`.
      *   Tag assignment and filtering via API.
  [ ] Implement/Refine ViewSet methods (`get_queryset`, potentially `perform_create` if more than org setting needed) and Serializer logic.
  [ ] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/features/products`). Review uncovered lines.
[ ] Manually test via API client and Django Admin. Pay attention to Org Scoping.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Plan implementation for related features (Pricing, Inventory, Variants, Bundles).

--- END OF FILE product_implementation_steps.md ---
### Category



# Category - Implementation Steps

## 1. Overview

**Model Name:**
`Category`

**Corresponding PRD:**
`category_prd.md` (Generic, Hierarchical version with Custom Fields)

**Depends On:**
`Timestamped`, `Auditable` (Abstract Base Models), `django-mptt` library.

**Key Features:**
Provides a generic, hierarchical structure for classifying various ERP entities (Products, Documents, etc.). Uses `django-mptt` for tree management. Includes type discrimination, status, and custom fields.

**Primary Location(s):**
`api/v1/base_models/common/` (Assuming `common` app for shared entities)

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`) are implemented.
[ ] Ensure the `common` app structure exists (`api/v1/base_models/common/`).
[ ] Install required library: `pip install django-mptt`.
[ ] Add `'mptt'` to `INSTALLED_APPS` in `config/settings/base.py`.
[ ] Ensure `factory-boy` is set up. Basic User factory exists.
[ ] Define `category_type` choices (e.g., in `common/choices.py` or directly in the model).

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `common`) verifying:
      *   A `Category` instance can be created with required fields (`name`, `category_type`).
      *   `slug` is auto-generated from name if blank (requires overriding `save` or using a library like `django-autoslug`). Test unique constraint on `slug`.
      *   `parent` ForeignKey works (can assign parent category).
      *   `unique_together` constraint (`parent`, `name`, `category_type`) is enforced.
      *   Default values (`is_active`, `custom_fields`) are set.
      *   MPTT fields (`lft`, `rght`, `tree_id`, `level`) are populated after save.
      *   `__str__` method returns name.
      *   Inherited `Timestamped`/`Auditable` fields exist.
      Run; expect failure (`Category` doesn't exist).
  [ ] Define the `Category` class in `api/v1/base_models/common/models.py`.
  [ ] Add required inheritance: `Timestamped`, `Auditable`, `MPTTModel`.
      ```python
      # api/v1/base_models/common/models.py
      from django.db import models
      from django.utils.text import slugify
      from django.utils.translation import gettext_lazy as _
      from mptt.models import MPTTModel, TreeForeignKey
      from core.models import Timestamped, Auditable # Adjust import path

      # Define choices centrally if preferred
      class CategoryType:
          PRODUCT = 'PRODUCT'
          DOCUMENT_TYPE = 'DOCUMENT_TYPE'
          ASSET_TYPE = 'ASSET_TYPE'
          ORG_COST_CENTER = 'ORG_COST_CENTER'
          OTHER = 'OTHER'
          CHOICES = [
              (PRODUCT, _('Product Category')),
              (DOCUMENT_TYPE, _('Document Type')),
              (ASSET_TYPE, _('Asset Type')),
              (ORG_COST_CENTER, _('Org/Cost Center')),
              (OTHER, _('Other')),
          ]

      class Category(Timestamped, Auditable, MPTTModel):
          name = models.CharField(
              _("Name"), max_length=255, db_index=True
          )
          # Consider unique=True based on whether slugs must be globally unique
          slug = models.SlugField(
              _("Slug"), max_length=255, unique=True, blank=True,
              help_text=_("Unique URL-friendly identifier. Auto-generated if blank.")
          )
          description = models.TextField(_("Description"), blank=True)
          parent = TreeForeignKey(
              'self',
              verbose_name=_("Parent Category"),
              on_delete=models.CASCADE, # Or PROTECT if children should prevent deletion
              null=True, blank=True, related_name='children', db_index=True
          )
          category_type = models.CharField(
              _("Category Type"), max_length=50, choices=CategoryType.CHOICES, db_index=True,
              help_text=_("The type of entity this category classifies.")
          )
          is_active = models.BooleanField(
              _("Is Active"), default=True, db_index=True
          )
          custom_fields = models.JSONField(
              _("Custom Fields"), default=dict, blank=True
          )

          class MPTTMeta:
              order_insertion_by = ['name']
              parent_attr = 'parent'

          class Meta:
              verbose_name = _("Category")
              verbose_name_plural = _("Categories")
              unique_together = ('parent', 'name', 'category_type')
              ordering = ['tree_id', 'lft'] # MPTT default

          def __str__(self):
              # Example showing hierarchy in string representation
              prefix = '---' * self.get_level()
              return f"{prefix} {self.name}".strip() if prefix else self.name

          def save(self, *args, **kwargs):
              # Auto-populate slug if blank
              if not self.slug:
                  self.slug = slugify(self.name)
                  # Handle potential slug collisions if slug is unique
                  # Add logic here to append numbers if slug exists (or use django-autoslug)
              super().save(*args, **kwargs)

      ```
  [ ] Run tests; expect pass. Refactor model code (especially slug generation/uniqueness handling).

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `CategoryFactory` in `api/v1/base_models/common/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from ..models import Category, CategoryType

      class CategoryFactory(DjangoModelFactory):
          class Meta:
              model = Category
              # django_get_or_create = ('slug',) # If slug is reliable unique identifier

          name = factory.Sequence(lambda n: f'Category {n}')
          # slug = factory.LazyAttribute(lambda o: slugify(o.name)) # Or let model save handle it
          parent = None # Set in tests for hierarchy
          category_type = factory.Iterator([choice[0] for choice in CategoryType.CHOICES])
          is_active = True
          custom_fields = {}
      ```
  [ ] **(Test)** Write simple tests ensuring the factory creates valid instances, including setting parents to test hierarchy creation.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Create/Update `api/v1/base_models/common/admin.py`.
  [ ] Define `CategoryAdmin` using `DraggableMPTTAdmin`:
      ```python
      from django.contrib import admin
      from mptt.admin import DraggableMPTTAdmin
      from .models import Category

      @admin.register(Category)
      class CategoryAdmin(DraggableMPTTAdmin):
          list_display = ('tree_actions', 'indented_title', 'slug', 'category_type', 'is_active')
          list_display_links = ('indented_title',)
          list_filter = ('category_type', 'is_active')
          search_fields = ('name', 'slug', 'description')
          prepopulated_fields = {'slug': ('name',)}
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
          # MPTT admin handles hierarchy display/editing
          # Add fieldsets for better layout if needed
      ```
  [ ] **(Manual Test):** Verify registration, CRUD, hierarchy management (drag-drop) in Django Admin locally.

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations api.v1.base_models.common`.
  [ ] **Review generated migration file carefully.** Check MPTT fields, FKs, unique constraints, indexes.
  [ ] Run `python manage.py migrate` locally.
  [ ] Run `python manage.py rebuild_category` (MPTT command) if needed (unlikely for new setup).

  ### 3.5 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write Unit/Integration Tests (`tests/unit/test_serializers.py`, etc.) for `CategorySerializer`. Test validation (unique constraints), representation (include necessary fields, potentially parent ID/children count), custom field handling, hierarchy fields if needed.
  [ ] Define `CategorySerializer` in `api/v1/base_models/common/serializers.py`. Consider using `rest_framework_mptt.serializers.MPTTModelSerializer` if available/needed for easy hierarchy representation.
      ```python
      from rest_framework import serializers
      # from rest_framework_mptt.serializers import MPTTModelSerializer # Option
      from ..models import Category

      class CategorySerializer(serializers.ModelSerializer): # Or MPTTModelSerializer
          # Example: Add children count (read-only)
          # children_count = serializers.IntegerField(source='get_children.count', read_only=True)
          # Example: Represent parent by slug or ID
          parent_slug = serializers.SlugRelatedField(
              slug_field='slug', source='parent', queryset=Category.objects.all(),
              allow_null=True, required=False
          )

          class Meta:
              model = Category
              fields = [
                  'id', 'name', 'slug', 'description',
                  'parent', # Or parent_slug / parent_id
                  'category_type', 'is_active',
                  # MPTT fields if needed: 'lft', 'rght', 'tree_id', 'level'
                  # 'children_count', # Example computed field
                  'custom_fields', 'created_at', 'updated_at',
              ]
              read_only_fields = ('id', 'created_at', 'updated_at') # Slug might be read-only after creation
              # If using MPTTSerializer, configure parent/child fields as needed
      ```
  [ ] Implement `validate_custom_fields`, `validate` (e.g., ensure parent has same `category_type` if required).
  [ ] Run tests; expect pass. Refactor.

  ### 3.6 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests checking URL existence, permissions for `/api/v1/categories/`.
  [ ] Define `CategoryViewSet` in `api/v1/base_models/common/views.py`:
      ```python
      from rest_framework import viewsets, permissions
      from rest_framework.decorators import action
      from rest_framework.response import Response
      from ..models import Category
      from ..serializers import CategorySerializer
      # Import filters, permissions etc.

      class CategoryViewSet(viewsets.ModelViewSet): # Full CRUD likely needed
          serializer_class = CategorySerializer
          permission_classes = [permissions.IsAuthenticatedOrReadOnly] # Adjust as needed
          queryset = Category.objects.filter(is_active=True) # Default to active
          lookup_field = 'slug' # Use slug for retrieval/update/delete
          filter_backends = [...] # Add filtering (django-filter, search, ordering)
          filterset_fields = ['category_type', 'parent__slug'] # Filter by type, parent slug
          search_fields = ['name', 'slug', 'description']
          ordering_fields = ['name', 'lft'] # Order by name or tree order

          # Add custom actions for hierarchy if needed beyond standard MPTT helpers
          # E.g., get full tree for a type
          @action(detail=False, methods=['get'], url_path='tree/(?P<type>[^/.]+)')
          def get_tree_by_type(self, request, type=None):
              queryset = self.get_queryset().filter(category_type=type)
              # Use serializer with recursive handling or specific tree logic
              # ... implementation needed ...
              return Response(...)
      ```
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.7 URL Routing (`urls.py`)

  [ ] Import `CategoryViewSet` in `api/v1/base_models/common/urls.py`.
  [ ] Register with router: `router.register(r'categories', views.CategoryViewSet)`.
  [ ] **(Test):** Rerun basic API tests; expect 2xx/4xx codes.

  ### 3.8 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests covering:
      *   LIST (with filters for `category_type`, `parent__slug`).
      *   CREATE (valid/invalid, setting parent).
      *   RETRIEVE (by slug).
      *   UPDATE (PUT/PATCH).
      *   DELETE (test PROTECT/CASCADE based on `on_delete` choice for `parent`).
      *   Permissions.
      *   Hierarchy actions (if any custom ones added).
      *   Saving/Validating `custom_fields`.
  [ ] Implement/Refine ViewSet/Serializer logic.
  [ ] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/base_models/common`). Review uncovered lines.
[ ] Manually test via API client and Django Admin (especially hierarchy drag-drop).
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs (slug collision handling, specific hierarchy API actions).
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Ensure other models (Product, Document, etc.) correctly add FK/M2M to `Category` using `limit_choices_to`.

--- END OF FILE category_implementation_steps.md ---
### Tax



# Tax Definition Models - Implementation Steps

## 1. Overview

**Model Name(s):**
`TaxJurisdiction`, `TaxCategory`, `TaxRate`

**Corresponding PRD:**
`tax_prd.md` (Simplified version focusing on definitions + Custom Fields)

**Depends On:**
`Timestamped`, `Auditable`. Potentially `django-mptt` (for `TaxJurisdiction` hierarchy).

**Key Features:**
Defines the foundational data for tax calculations: geographic jurisdictions (potentially hierarchical), categories for classifying items, and specific tax rates linked to jurisdictions/categories with validity periods. Includes custom fields for extensibility.

**Primary Location(s):**
`api/v1/base_models/common/` (Assuming `common` app) or potentially a dedicated `taxes` app (`api/v1/taxes/`). Let's assume **`common`** for now.

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`) are implemented.
[ ] Ensure the `common` app structure exists.
[ ] **Decision:** Use `django-mptt` for `TaxJurisdiction` hierarchy (Country->State->County)? (Steps assume **YES** initially for flexibility). If yes:
    [ ] Install `django-mptt`: `pip install django-mptt`.
    [ ] Add `'mptt'` to `INSTALLED_APPS`.
[ ] Ensure `factory-boy` is set up. Basic User factory exists.

## 3. Implementation Steps (TDD Workflow)

  *(Implement Jurisdiction & Category first, then Rate)*

  ### 3.1 `TaxJurisdiction` Model Definition (`models.py`)

  [ ] **(Test First)** Write Unit Tests (`tests/unit/test_models.py`) verifying:
      *   `TaxJurisdiction` creation with required fields (`code`, `name`, `jurisdiction_type`).
      *   Unique `code`. Hierarchical `parent` field works (if using MPTT). Default `is_active`. `custom_fields` default. `__str__` works. Inheritance. MPTT fields populated (if used).
      Run; expect failure.
  [ ] Define `TaxJurisdiction` in `api/v1/base_models/common/models.py`.
  [ ] Add inheritance: `Timestamped`, `Auditable`, `MPTTModel`.
      ```python
      # api/v1/base_models/common/models.py
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from mptt.models import MPTTModel, TreeForeignKey
      from core.models import Timestamped, Auditable # Adjust path

      class JurisdictionType:
          COUNTRY = 'COUNTRY'
          STATE = 'STATE_PROVINCE' # Avoid slash in code
          COUNTY = 'COUNTY'
          CITY = 'CITY'
          OTHER = 'OTHER'
          CHOICES = [...] # Define choices tuples

      class TaxJurisdiction(Timestamped, Auditable, MPTTModel):
          code = models.CharField( # Using CharField instead of Slug for codes like 'US-CA'
              _("Code"), max_length=50, unique=True, db_index=True, primary_key=True
          )
          name = models.CharField(_("Name"), max_length=255)
          jurisdiction_type = models.CharField(
              _("Jurisdiction Type"), max_length=20, choices=JurisdictionType.CHOICES, db_index=True
          )
          parent = TreeForeignKey(
              'self', verbose_name=_("Parent Jurisdiction"),
              on_delete=models.PROTECT, null=True, blank=True, related_name='children', db_index=True
          )
          is_active = models.BooleanField(_("Is Active"), default=True, db_index=True)
          custom_fields = models.JSONField(_("Custom Fields"), default=dict, blank=True)

          class MPTTMeta: order_insertion_by = ['name']; parent_attr = 'parent'
          class Meta: verbose_name = _("Tax Jurisdiction"); verbose_name_plural = _("Tax Jurisdictions")

          def __str__(self): return self.name
      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.2 `TaxCategory` Model Definition (`models.py`)

  [ ] **(Test First)** Write Unit Tests verifying:
      *   `TaxCategory` creation (`code`, `name`). Unique `code`/`name`. Default `is_active`. `custom_fields` default. `__str__`. Inheritance.
      Run; expect failure.
  [ ] Define `TaxCategory` in `api/v1/base_models/common/models.py`.
  [ ] Add inheritance: `Timestamped`, `Auditable`.
      ```python
      class TaxCategory(Timestamped, Auditable):
          code = models.SlugField( # Slug often suitable here
              _("Code"), max_length=50, primary_key=True
          )
          name = models.CharField(_("Name"), max_length=100, unique=True, db_index=True)
          description = models.TextField(_("Description"), blank=True)
          is_active = models.BooleanField(_("Is Active"), default=True, db_index=True)
          custom_fields = models.JSONField(_("Custom Fields"), default=dict, blank=True)

          class Meta: verbose_name = _("Tax Category"); verbose_name_plural = _("Tax Categories"); ordering=['name']
          def __str__(self): return self.name
      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.3 `TaxRate` Model Definition (`models.py`)

  [ ] **(Test First)** Write Unit Tests verifying:
      *   `TaxRate` creation (`jurisdiction`, `rate`, `tax_type`).
      *   FKs (`jurisdiction`, `tax_category`) work. `tax_category` can be null.
      *   Defaults (`is_compound`, `priority`, `is_active`). `custom_fields` default.
      *   `rate` field stores Decimal correctly. `valid_from`/`to` store Date.
      *   `__str__`. Inheritance.
      Run; expect failure.
  [ ] Define `TaxRate` in `api/v1/base_models/common/models.py`.
  [ ] Add inheritance: `Timestamped`, `Auditable`.
      ```python
      class TaxType:
          VAT = 'VAT'; GST = 'GST'; SALES = 'SALES'; OTHER = 'OTHER'
          CHOICES = [...]

      class TaxRate(Timestamped, Auditable):
          # Consider UUIDField as PK if rates might change frequently needing history
          jurisdiction = models.ForeignKey(TaxJurisdiction, on_delete=models.CASCADE)
          tax_category = models.ForeignKey(TaxCategory, on_delete=models.CASCADE, null=True, blank=True)
          name = models.CharField(_("Name"), max_length=100, help_text=_("e.g., CA State Sales Tax"))
          rate = models.DecimalField(_("Rate"), max_digits=10, decimal_places=5, help_text=_("e.g., 0.0825 for 8.25%"))
          tax_type = models.CharField(_("Tax Type"), max_length=10, choices=TaxType.CHOICES, db_index=True)
          is_compound = models.BooleanField(_("Is Compound"), default=False)
          priority = models.IntegerField(_("Priority"), default=0, help_text=_("Apply lower priorities first for compounding"))
          valid_from = models.DateField(_("Valid From"), null=True, blank=True, db_index=True)
          valid_to = models.DateField(_("Valid To"), null=True, blank=True, db_index=True)
          is_active = models.BooleanField(_("Is Active"), default=True, db_index=True)
          custom_fields = models.JSONField(_("Custom Fields"), default=dict, blank=True)

          class Meta:
              verbose_name = _("Tax Rate"); verbose_name_plural = _("Tax Rates")
              ordering = ['jurisdiction__code', 'priority', '-valid_from']
              indexes = [models.Index(fields=['jurisdiction', 'tax_category', 'valid_from', 'valid_to'])]

          def __str__(self): return self.name or f"{self.jurisdiction.code} {self.rate * 100}%"
      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.4 Factory Definitions (`tests/factories.py`)

  [ ] Define `TaxJurisdictionFactory`, `TaxCategoryFactory`, `TaxRateFactory`.
      ```python
      # Define factories for TaxJurisdiction, TaxCategory, TaxRate
      class TaxJurisdictionFactory(...): ...
      class TaxCategoryFactory(...): ...
      class TaxRateFactory(DjangoModelFactory):
          class Meta: model = TaxRate
          jurisdiction = factory.SubFactory(TaxJurisdictionFactory)
          # tax_category = factory.SubFactory(TaxCategoryFactory) # Optional
          name = factory.Sequence(lambda n: f'Tax Rate {n}')
          rate = factory.Faker('pydecimal', left_digits=1, right_digits=4, positive=True) # e.g., 0.xxxx
          tax_type = factory.Iterator([choice[0] for choice in TaxType.CHOICES])
          is_active = True
          # valid_from / valid_to ...
          custom_fields = {}
      ```
  [ ] **(Test)** Write tests ensuring factories create valid instances.

  ### 3.5 Admin Registration (`admin.py`)

  [ ] Define Admins for `TaxJurisdiction` (using `MPTTModelAdmin`), `TaxCategory`, `TaxRate`.
  [ ] Use `list_display`, `list_filter`, `search_fields`, `readonly_fields`.
  [ ] Consider `list_editable` for `TaxRate.rate`, `is_active`, `valid_to`.
  [ ] Register models.
  [ ] **(Manual Test):** Verify Admin interfaces.

  ### 3.6 Initial Data Population (Migration)

  [ ] Create Data Migration(s) (`..._populate_tax_defs.py`) to load common jurisdictions (e.g., US States, major countries), basic categories ('STANDARD', 'EXEMPT'), and potentially known standard rates if applicable.

  ### 3.7 Migrations

  [ ] Run `python manage.py makemigrations api.v1.base_models.common`.
  [ ] **Review migration file(s) carefully.** Check MPTT, FKs, indexes, data migration.
  [ ] Run `python manage.py migrate` locally. Verify initial data.
  [ ] Run `python manage.py rebuild_taxjurisdiction` (MPTT command) if needed.

  ### 3.8 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write tests for `TaxJurisdictionSerializer`, `TaxCategorySerializer`, `TaxRateSerializer` (representation, custom fields). Validation minimal if API is read-only.
  [ ] Define read-only serializers. Include `custom_fields`. Handle FKs (PK or nested).
  [ ] Run tests; expect pass. Refactor.

  ### 3.9 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API tests for `/api/v1/tax-jurisdictions/`, `/tax-categories/`, `/tax-rates/`. Test read access.
  [ ] Define `ReadOnlyModelViewSet`s for each. Implement filtering (by jurisdiction, category, active status, validity date for rates). Secure appropriately (likely `IsAuthenticatedOrReadOnly` or `IsAdminUser` if sensitive).
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.10 URL Routing (`urls.py`)

  [ ] Import and register ViewSets with the router in `common/urls.py`.
  [ ] **(Test):** Rerun basic API tests; expect 200 OK.

  ### 3.11 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First)** Write API tests for LIST/RETRIEVE for each endpoint. Test filtering parameters extensively (especially date ranges and relations for TaxRate).
  [ ] Ensure ViewSet querysets and filters work correctly.
  [ ] Run tests; expect pass. Refactor.
  [ ] *(Test CRUD APIs if management endpoints are implemented)*.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/base_models/common`).
[ ] Manually test via API client and Django Admin. Verify initial data and relationships.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Ensure models needing tax info (Product, OrderLine) add necessary FKs (e.g., `Product.tax_category`).
[ ] Plan implementation of Tax Calculation Engine/Service integration.

--- END OF FILE tax_implementation_steps.md ---
### Currency


# Currency - Implementation Steps

## 1. Overview

**Model Name:**
`Currency`

**Corresponding PRD:**
`currency_prd.md` (Simplified version with Custom Fields)

**Depends On:**
`Timestamped`, `Auditable` (Abstract Base Models)

**Key Features:**
Defines world currencies based on ISO 4217, including code, name, symbol, decimal places, active status, and custom fields. Provides foundational reference data for financial operations.

**Primary Location(s):**
`api/v1/base_models/common/currency/` (Assuming `common` app within `base_models` for shared entities like Currency, Address, Contact, etc., based on project structure)

## 2. Prerequisites

[x] Verify prerequisite models/mixins (`Timestamped`, `Auditable`) are implemented.
[x] Ensure the `common` app structure exists (`api/v1/base_models/common/currency/`).
[x] Ensure `factory-boy` is set up. Basic User factory exists (needed for Auditable).
[ ] Decision made on source for initial currency data (e.g., `pycountry` library, manual list, external file).

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [x] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `common`) verifying:
      *   A `Currency` instance can be created with required fields (`code`, `name`).
      *   `code` is the primary key.
      *   Unique constraints (`name`, `numeric_code`) are present (checked via `_meta`).
      *   Default values (`decimal_places`, `is_active`) are set correctly.
      *   `custom_fields` defaults to an empty dict.
      *   `__str__` method returns the `code`.
      *   Inherited `Timestamped`/`Auditable` fields exist.
      Run; expect failure (`Currency` doesn't exist).
  [x] Define the `Currency` class in `api/v1/base_models/common/currency/models.py`.
  [x] Add required inheritance: `Timestamped`, `Auditable`.
      ```python
      # api/v1/base_models/common/currency/models.py
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from core.models import Timestamped, Auditable # Adjust import path

      class Currency(Timestamped, Auditable):
          code = models.CharField(
              _("ISO 4217 Code"),
              max_length=3,
              primary_key=True,
              help_text=_("ISO 4217 3-letter currency code.")
          )
          name = models.CharField(
              _("Name"),
              max_length=100,
              unique=True,
              db_index=True,
              help_text=_("Official name of the currency.")
          )
          symbol = models.CharField(
              _("Symbol"),
              max_length=5,
              blank=True, # Some currencies might not have a common symbol
              help_text=_("Common symbol for the currency (e.g., $, €).")
          )
          numeric_code = models.CharField(
              _("ISO 4217 Numeric Code"),
              max_length=3,
              unique=True,
              null=True, # Allow null as not all might have it / be known
              blank=True,
              db_index=True,
              help_text=_("ISO 4217 3-digit numeric currency code.")
          )
          decimal_places = models.PositiveSmallIntegerField(
              _("Decimal Places"),
              default=2,
              help_text=_("Number of decimal places commonly used.")
          )
          is_active = models.BooleanField(
              _("Is Active"),
              default=True,
              db_index=True,
              help_text=_("Is this currency available for use?")
          )
          custom_fields = models.JSONField(
              _("Custom Fields"),
              default=dict,
              blank=True,
              help_text=_("Custom data associated with this currency.")
          )

          class Meta:
              verbose_name = _("Currency")
              verbose_name_plural = _("Currencies")
              ordering = ['code']

          def __str__(self):
              return self.code
      ```
  [ ] Run tests; expect pass. Refactor model code if needed.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [x] Define `CurrencyFactory` in `api/v1/base_models/common/currency/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from ..models import Currency

      class CurrencyFactory(DjangoModelFactory):
          class Meta:
              model = Currency
              # Use code as the lookup field for get_or_create
              django_get_or_create = ('code',)

          code = factory.Iterator(['USD', 'EUR', 'JPY', 'GBP', 'CAD', 'AUD'])
          name = factory.LazyAttribute(lambda o: {
              'USD': 'US Dollar', 'EUR': 'Euro', 'JPY': 'Japanese Yen',
              'GBP': 'Pound Sterling', 'CAD': 'Canadian Dollar', 'AUD': 'Australian Dollar'
          }.get(o.code, f'Currency {o.code}'))
          symbol = factory.LazyAttribute(lambda o: {
              'USD': '$', 'EUR': '€', 'JPY': '¥', 'GBP': '£', 'CAD': '$', 'AUD': '$'
          }.get(o.code, ''))
          decimal_places = 2
          is_active = True
          custom_fields = {}
      ```
  [x] **(Test)** Write a simple test ensuring `CurrencyFactory` creates valid `Currency` instances.

  ### 3.3 Admin Registration (`admin.py`)

  [x] Create/Update `api/v1/base_models/common/currency/admin.py`.
  [x] Define `CurrencyAdmin`:
      ```python
      from django.contrib import admin
      from .models import Currency

      @admin.register(Currency)
      class CurrencyAdmin(admin.ModelAdmin):
          list_display = ('code', 'name', 'symbol', 'decimal_places', 'is_active', 'numeric_code')
          search_fields = ('code', 'name', 'numeric_code')
          list_filter = ('is_active',)
          # Add custom_fields if needed/useful in admin list/form
      ```
  [x] **(Manual Test):** Verify registration and basic functionality in Django Admin locally.

  ### 3.4 Initial Data Population (Migration)

  [ ] **(Decision):** Choose source for ISO 4217 data (e.g., `pycountry` library or a predefined list/CSV).
  [ ] Create a new **Data Migration** file: `python manage.py makemigrations --empty --name populate_currencies api.v1.base_models.common`.
  [ ] Edit the generated migration file (`..._populate_currencies.py`). Add `RunPython` operations to load the currency data.
  [ ] Run `python manage.py migrate` locally to apply the data migration. Verify data loaded (e.g., via Admin or shell).

  ### 3.5 Serializer Definition (`serializers.py`)

  [x] **(Test First - Validation/Representation)** Write Unit/Integration Tests (`tests/unit/test_serializers.py`, `tests/integration/test_serializers.py`) for `CurrencySerializer`. Test validation (e.g., code length), representation (fields included), and custom field handling if applicable.
  [x] Define `CurrencySerializer` in `api/v1/base_models/common/currency/serializers.py`:
      ```python
      from rest_framework import serializers
      from ..models import Currency

      class CurrencySerializer(serializers.ModelSerializer):
          class Meta:
              model = Currency
              fields = [
                  'code',
                  'name',
                  'symbol',
                  'numeric_code',
                  'decimal_places',
                  'is_active',
                  'custom_fields',
                  # Include Timestamped/Auditable fields if needed by API consumers
                  # 'created_at',
                  # 'updated_at',
                  # 'created_by', # Often represented nested/read-only
                  # 'updated_by',
              ]
              read_only_fields = [] # Most fields managed via Admin/Migrations
              # Potentially make all read-only if API is only for listing
      ```
  [x] Implement `validate_custom_fields`
  [x] Run tests; expect pass. Refactor.

  ### 3.6 API ViewSet Definition (`views.py`)

  [x] **(Test First - Permissions/Basic Structure)** Write basic API Tests (`tests/api/test_endpoints.py`) for `/api/v1/currencies/`. Test unauthenticated access (allowed for read). Test authenticated access.
  [x] Define `CurrencyViewSet` in `api/v1/base_models/common/currency/views.py`:
      ```python
      from rest_framework import viewsets, permissions
      from ..models import Currency
      from ..serializers import CurrencySerializer
      # Import filtering backends if needed

      class CurrencyViewSet(viewsets.ReadOnlyModelViewSet): # ReadOnly often sufficient
          """
          API endpoint that allows currencies to be viewed.
          """
          queryset = Currency.objects.filter(is_active=True) # Show active by default
          serializer_class = CurrencySerializer
          permission_classes = [permissions.AllowAny] # Or IsAuthenticatedOrReadOnly
          filter_backends = [] # Add filtering if needed (e.g., by code, name)
          search_fields = ['code', 'name']
          ordering_fields = ['code', 'name']
          # Disable pagination if the list is always short, or use default
          # pagination_class = None
      ```
  [x] Run basic structure/permission tests; expect pass. Refactor.

  ### 3.7 URL Routing (`urls.py`)

  [x] Import the `CurrencyViewSet` in `api/v1/base_models/common/currency/urls.py`.
  [x] Register the ViewSet with the router: `router.register(r'currencies', views.CurrencyViewSet)`.
  [x] Ensure `common.urls` is included in `api/v1/base_models/urls.py`.
  [x] **(Test):** Rerun basic API tests; expect 200 OK for listing.

  ### 3.8 API Endpoint Testing (Read & Features) (`tests/api/test_endpoints.py`)

  [x] **(Test First - List)** Write test for `GET /api/v1/currencies/`. Assert 200, check pagination/structure, verify expected currencies (e.g., USD, EUR from factory/population) are present. Test filtering by `is_active=false` if applicable.
  [x] Ensure `queryset` in ViewSet is appropriate.
  [x] Run list tests; expect pass. Refactor.
  [x] **(Test First - Retrieve)** Write test for `GET /api/v1/currencies/{code}/`. Assert 200, check response body. Test non-existent code (expect 404).
  [x] Ensure lookup by code (PK) works.
  [x] Run retrieve tests; expect pass. Refactor.
  [ ] *(CRUD tests not applicable if using ReadOnlyModelViewSet)*.
  [ ] *(Test custom field validation/saving via API if management endpoints exist)*.

## 4. Final Checks

[x] Run the *entire* test suite (`pytest`).
[x] Run linters (`flake8`) and formatters (`black`).
[x] Check code coverage (`pytest --cov`).
[x] Manually test via API client and verify data in Django Admin.
[x] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request.
[x] Update API documentation.
[ ] Ensure other models (Organization, etc.) correctly add `ForeignKey` to `Currency`.

## 6. Current Status

**Completed:**
- Basic model implementation with all required fields
- Factory for test data generation
- Admin interface setup
- Serializer with proper validation
- ViewSet with read-only access
- URL routing configuration
- Comprehensive test suite with 95% coverage
- API documentation

**Pending:**
1. Initial data population (ISO 4217 currencies)
2. Integration with other models
3. Final review and PR creation

--- END OF FILE currency_implementation_steps.md ---
### Unit of Measure



# UnitOfMeasure (UoM) - Implementation Steps

## 1. Overview

**Model Name:**
`UnitOfMeasure`

**Corresponding PRD:**
`uom_prd.md` (Simplified version with Custom Fields)

**Depends On:**
`Timestamped`, `Auditable` (Abstract Base Models)

**Key Features:**
Defines distinct units of measure (e.g., KG, M, EA) with core attributes like code, name, type/category, symbol, active status, and custom fields. Serves as reference data for product/inventory/order models.

**Primary Location(s):**
`api/v1/base_models/common/` (Assuming `common` app for shared entities)

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`) are implemented.
[ ] Ensure the `common` app structure exists (`api/v1/base_models/common/`).
[ ] Ensure `factory-boy` is set up. Basic User factory exists.
[ ] **Decision:** Define a list of standard `uom_type` choices (e.g., 'Length', 'Mass', 'Volume', 'Count', 'Time', 'Area') or create a separate `UomType` model? (Steps assume `CharField` with choices initially for simplicity).

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `common`) verifying:
      *   A `UnitOfMeasure` instance can be created with required fields (`code`, `name`, `uom_type`).
      *   `code` is the primary key.
      *   Unique constraints (`code`, `name`) are present.
      *   Default values (`is_active`, `custom_fields`) are set.
      *   `__str__` method works as expected.
      *   Inherited `Timestamped`/`Auditable` fields exist.
      Run; expect failure (`UnitOfMeasure` doesn't exist).
  [ ] Define the `UnitOfMeasure` class in `api/v1/base_models/common/models.py`.
  [ ] Add required inheritance: `Timestamped`, `Auditable`.
      ```python
      # api/v1/base_models/common/models.py
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from core.models import Timestamped, Auditable # Adjust import path

      class UnitType: # Define choices centrally
          LENGTH = 'Length'
          MASS = 'Mass'
          VOLUME = 'Volume'
          COUNT = 'Count'
          TIME = 'Time'
          AREA = 'Area'
          OTHER = 'Other'

          CHOICES = [
              (LENGTH, _('Length')),
              (MASS, _('Mass')),
              (VOLUME, _('Volume')),
              (COUNT, _('Count/Each')),
              (TIME, _('Time')),
              (AREA, _('Area')),
              (OTHER, _('Other')),
          ]

      class UnitOfMeasure(Timestamped, Auditable):
          code = models.CharField(
              _("Code"),
              max_length=20, # Allow for codes like BOX_12, etc.
              primary_key=True,
              help_text=_("Unique code for the unit (e.g., KG, M, EA, BOX_12).")
          )
          name = models.CharField(
              _("Name"),
              max_length=100,
              unique=True,
              db_index=True,
              help_text=_("Full name of the unit (e.g., Kilogram, Meter, Each).")
          )
          uom_type = models.CharField(
              _("Type"),
              max_length=50,
              choices=UnitType.CHOICES,
              db_index=True,
              help_text=_("Category of measurement (e.g., Length, Mass, Count).")
          )
          symbol = models.CharField(
              _("Symbol"),
              max_length=10,
              blank=True,
              help_text=_("Common symbol (e.g., kg, m, L).")
          )
          is_active = models.BooleanField(
              _("Is Active"),
              default=True,
              db_index=True,
              help_text=_("Is this unit available for use?")
          )
          custom_fields = models.JSONField(
              _("Custom Fields"),
              default=dict,
              blank=True,
              help_text=_("Custom data associated with this unit definition.")
          )

          class Meta:
              verbose_name = _("Unit of Measure")
              verbose_name_plural = _("Units of Measure")
              ordering = ['uom_type', 'name']

          def __str__(self):
              return self.name # Or self.code
      ```
  [ ] Run tests; expect pass. Refactor model code if needed.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `UnitOfMeasureFactory` in `api/v1/base_models/common/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from ..models import UnitOfMeasure, UnitType # Import choices class too

      class UnitOfMeasureFactory(DjangoModelFactory):
          class Meta:
              model = UnitOfMeasure
              django_get_or_create = ('code',)

          # Create more realistic examples based on type
          code = factory.Sequence(lambda n: f'UOM{n}')
          name = factory.Sequence(lambda n: f'Unit Name {n}')
          uom_type = factory.Iterator([choice[0] for choice in UnitType.CHOICES])
          symbol = factory.LazyAttribute(lambda o: o.code.lower())
          is_active = True
          custom_fields = {}
      ```
  [ ] **(Test)** Write a simple test ensuring `UnitOfMeasureFactory` creates valid instances.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Create/Update `api/v1/base_models/common/admin.py`.
  [ ] Define `UnitOfMeasureAdmin`:
      ```python
      from django.contrib import admin
      from .models import UnitOfMeasure

      @admin.register(UnitOfMeasure)
      class UnitOfMeasureAdmin(admin.ModelAdmin):
          list_display = ('code', 'name', 'uom_type', 'symbol', 'is_active', 'updated_at')
          search_fields = ('code', 'name', 'symbol')
          list_filter = ('uom_type', 'is_active')
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
          fieldsets = (
              (None, {'fields': ('code', 'name', 'symbol', 'uom_type', 'is_active')}),
              ('Custom Data', {'fields': ('custom_fields',)}),
              ('Audit Info', {'classes': ('collapse',), 'fields': readonly_fields}),
          )
      ```
  [ ] **(Manual Test):** Verify registration and basic CRUD in Django Admin locally.

  ### 3.4 Initial Data Population (Migration)

  [ ] Create a new **Data Migration** file: `python manage.py makemigrations --empty --name populate_initial_uoms api.v1.base_models.common`.
  [ ] Edit the generated migration file (`..._populate_initial_uoms.py`). Add `RunPython` operations to load essential common units.
      ```python
      from django.db import migrations

      INITIAL_UOMS = [
          # Code, Name, Type, Symbol (Optional)
          ('EA', 'Each', 'Count', ''),
          ('BOX', 'Box', 'Count', ''),
          ('KG', 'Kilogram', 'Mass', 'kg'),
          ('G', 'Gram', 'Mass', 'g'),
          ('LB', 'Pound', 'Mass', 'lb'),
          ('OZ', 'Ounce', 'Mass', 'oz'),
          ('M', 'Meter', 'Length', 'm'),
          ('CM', 'Centimeter', 'Length', 'cm'),
          ('MM', 'Millimeter', 'Length', 'mm'),
          ('FT', 'Foot', 'Length', 'ft'),
          ('IN', 'Inch', 'Length', 'in'),
          ('L', 'Liter', 'Volume', 'L'),
          ('ML', 'Milliliter', 'Volume', 'mL'),
          ('GAL', 'Gallon', 'Volume', 'gal'),
          # Add others (Area, Time, etc.) as needed
      ]

      def populate_uoms(apps, schema_editor):
          UnitOfMeasure = apps.get_model('common', 'UnitOfMeasure')
          UnitType = apps.get_model('common', 'UnitType') # Get choices if needed, or use strings directly
          db_alias = schema_editor.connection.alias

          uoms_to_add = []
          for code, name, uom_type_str, symbol in INITIAL_UOMS:
              # Find the correct type value if using choices class
              uom_type_val = next((val for val, display in UnitType.CHOICES if val == uom_type_str), UnitType.OTHER)

              uoms_to_add.append(
                  UnitOfMeasure(
                      code=code, name=name, uom_type=uom_type_val, symbol=symbol or ''
                  )
              )
          UnitOfMeasure.objects.using(db_alias).bulk_create(uoms_to_add, ignore_conflicts=True)
          print(f"\nPopulated/updated {len(uoms_to_add)} Units of Measure.")

      def remove_uoms(apps, schema_editor):
          pass

      class Migration(migrations.Migration):
          dependencies = [
              ('common', '000X_auto_...'), # Depends on UoM model creation
          ]
          operations = [
              migrations.RunPython(populate_uoms, reverse_code=remove_uoms),
          ]
      ```

  ### 3.5 Migrations (Apply Initial Model & Data)

  [ ] Run `python manage.py makemigrations api.v1.base_models.common`.
  [ ] **Review generated migration file(s) carefully.**
  [ ] Run `python manage.py migrate` locally. Verify data loaded via Admin.

  ### 3.6 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write Unit/Integration Tests (`tests/unit/test_serializers.py`, etc.) for `UnitOfMeasureSerializer`. Test representation, custom field handling.
  [ ] Define `UnitOfMeasureSerializer` in `api/v1/base_models/common/serializers.py`:
      ```python
      from rest_framework import serializers
      from ..models import UnitOfMeasure

      class UnitOfMeasureSerializer(serializers.ModelSerializer):
          class Meta:
              model = UnitOfMeasure
              fields = [
                  'code',
                  'name',
                  'uom_type',
                  'symbol',
                  'is_active',
                  'custom_fields',
                  # Include Timestamped/Auditable fields if needed
              ]
              # Generally read-only from an API perspective
              read_only_fields = fields
      ```
  [ ] Implement `validate_custom_fields` if applicable.
  [ ] Run tests; expect pass. Refactor.

  ### 3.7 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests (`tests/api/test_endpoints.py`) for `/api/v1/uoms/`. Test unauthenticated access (likely allowed for read).
  [ ] Define `UnitOfMeasureViewSet` in `api/v1/base_models/common/views.py`:
      ```python
      from rest_framework import viewsets, permissions
      from rest_framework import filters
      from ..models import UnitOfMeasure
      from ..serializers import UnitOfMeasureSerializer

      class UnitOfMeasureViewSet(viewsets.ReadOnlyModelViewSet):
          """
          API endpoint allowing Units of Measure to be viewed.
          Management is typically done via Admin or initial data loads.
          """
          queryset = UnitOfMeasure.objects.filter(is_active=True) # Show active only
          serializer_class = UnitOfMeasureSerializer
          permission_classes = [permissions.IsAuthenticatedOrReadOnly]
          lookup_field = 'code' # Use code (PK) for retrieval
          filter_backends = [filters.SearchFilter, filters.OrderingFilter]
          search_fields = ['code', 'name', 'symbol', 'uom_type']
          ordering_fields = ['uom_type', 'name', 'code']
          # pagination_class = None # Optional: Disable pagination if list is manageable
      ```
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.8 URL Routing (`urls.py`)

  [ ] Import `UnitOfMeasureViewSet` in `api/v1/base_models/common/urls.py`.
  [ ] Register with router: `router.register(r'uoms', views.UnitOfMeasureViewSet)`.
  [ ] **(Test):** Rerun basic API tests; expect 200 OK for listing/retrieving.

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - List/Retrieve)** Write tests for `GET /api/v1/uoms/` and `GET /api/v1/uoms/{code}/`. Assert 200, check structure, verify initial UoMs present. Test search filters.
  [ ] Ensure ViewSet query/filtering works.
  [ ] Run list/retrieve tests; expect pass. Refactor.
  [ ] *(Test custom field validation/saving via API if management endpoints were added)*.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/base_models/common`). Review uncovered lines.
[ ] Manually test via API client and Django Admin. Verify initial UoMs exist.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Ensure models needing a UoM reference (e.g., Product) add the `ForeignKey` correctly using `on_delete=PROTECT`.
[ ] Plan for implementation of the separate Unit Conversion mechanism/library integration.

--- END OF FILE uom_implementation_steps.md ---
### Warehouse


# Warehouse - Implementation Steps

## 1. Overview

**Model Name:**
`Warehouse`

**Corresponding PRD:**
`warehouse_prd.md` (Simplified version)

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationScoped` (Abstract Base Models), `Organization`, `Address`, `django-taggit` (if using tags). Requires Custom Field Definition mechanism if used.

**Key Features:**
Defines physical or logical inventory storage locations (Warehouses). Includes code, name, type, status, link to Address, tags, and custom fields. Scoped by Organization. Foundation for Inventory Management and Stock Locations.

**Primary Location(s):**
`api/v1/features/inventory/` (Assuming a dedicated `inventory` feature app/group, which might also contain StockLocation, StockLevel etc.) or potentially `api/v1/base_models/common/`. Let's assume **`inventory`** for this example.

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `OrganizationScoped`, `Organization`, `Address`) are implemented and migrated.
[ ] Install libraries if needed: `pip install django-taggit`. Add to `INSTALLED_APPS`.
[ ] Create the `inventory` app structure: `api/v1/features/inventory/`.
[ ] Add `'api.v1.features.inventory'` (adjust path) to `INSTALLED_APPS`.
[ ] Ensure `factory-boy` is set up. Factories for `Organization`, `Address`, `User` exist.
[ ] Define `WarehouseType` choices (e.g., in `inventory/choices.py`).

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `inventory`) verifying:
      *   `Warehouse` creation with required fields (`name`, `code`, `organization`, `warehouse_type`).
      *   `unique_together` constraint (`organization`, `code`) is enforced.
      *   Default values (`is_active`, `custom_fields`) are set.
      *   FK to `Address` works (can be null).
      *   `tags` manager exists.
      *   `__str__` method works.
      *   Inherited fields (`Timestamped`, `Auditable`, `OrganizationScoped`) exist.
      Run; expect failure (`Warehouse` doesn't exist).
  [ ] Define the `Warehouse` class in `api/v1/features/inventory/models.py`.
  [ ] Add inheritance: `Timestamped`, `Auditable`, `OrganizationScoped`.
      ```python
      # api/v1/features/inventory/models.py
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from taggit.managers import TaggableManager
      from core.models import Timestamped, Auditable, OrganizationScoped # Adjust path
      from api.v1.base_models.common.models import Address # Adjust path

      # Define choices (or import from choices.py)
      class WarehouseType:
          DC = 'DISTRIBUTION_CENTER'
          RETAIL = 'RETAIL_STORE'
          MFG = 'MANUFACTURING'
          VIRTUAL = 'VIRTUAL_DROPSHIP'
          THIRD_PARTY = 'THIRD_PARTY_LOGISTICS'
          TRANSIT = 'TRANSIT'
          OTHER = 'OTHER'
          CHOICES = [...] # Define choices tuple

      class Warehouse(Timestamped, Auditable, OrganizationScoped):
          name = models.CharField(_("Name"), max_length=255, db_index=True)
          code = models.CharField(_("Code"), max_length=50, db_index=True)
          warehouse_type = models.CharField(
              _("Warehouse Type"), max_length=50, choices=WarehouseType.CHOICES, db_index=True
          )
          address = models.ForeignKey(
              Address,
              verbose_name=_("Address"),
              on_delete=models.PROTECT, # Protect address if warehouse uses it
              null=True, blank=True # Allow virtual warehouses without physical address
          )
          is_active = models.BooleanField(
              _("Is Active"), default=True, db_index=True
          )
          tags = TaggableManager(blank=True, verbose_name=_("Tags"))
          custom_fields = models.JSONField(
              _("Custom Fields"), default=dict, blank=True
          )

          class Meta:
              verbose_name = _("Warehouse")
              verbose_name_plural = _("Warehouses")
              unique_together = (('organization', 'code'),)
              ordering = ['name']
              indexes = [
                  models.Index(fields=['organization', 'code']),
                  models.Index(fields=['name']),
                  models.Index(fields=['warehouse_type']),
                  models.Index(fields=['is_active']),
              ]

          def __str__(self):
              return f"{self.name} ({self.code})"

      # StockLocation model will be defined later in this file or separate file
      ```
  [ ] Run tests; expect pass. Refactor model code if needed.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `WarehouseFactory` in `api/v1/features/inventory/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from ..models import Warehouse, WarehouseType
      from api.v1.base_models.organization.tests.factories import OrganizationFactory
      from api.v1.base_models.common.tests.factories import AddressFactory

      class WarehouseFactory(DjangoModelFactory):
          class Meta:
              model = Warehouse
              # django_get_or_create = ('organization', 'code') # Use if needed

          name = factory.Sequence(lambda n: f'Warehouse {n}')
          code = factory.Sequence(lambda n: f'WH{n:03}')
          organization = factory.SubFactory(OrganizationFactory)
          warehouse_type = factory.Iterator([choice[0] for choice in WarehouseType.CHOICES])
          address = factory.SubFactory(AddressFactory) # Create an address by default
          is_active = True
          custom_fields = {}

          # Handle tags if needed
      ```
  [ ] **(Test)** Write simple tests ensuring the factory creates valid instances.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Create `api/v1/features/inventory/admin.py`.
  [ ] Define `WarehouseAdmin`:
      ```python
      from django.contrib import admin
      from .models import Warehouse

      @admin.register(Warehouse)
      class WarehouseAdmin(admin.ModelAdmin):
          list_display = ('code', 'name', 'organization', 'warehouse_type', 'address', 'is_active')
          list_filter = ('organization', 'warehouse_type', 'is_active')
          search_fields = ('code', 'name', 'address__city', 'address__postal_code') # Search related address
          list_select_related = ('organization', 'address')
          autocomplete_fields = ['address'] # If AddressAdmin is registered
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
          fieldsets = (
              (None, {'fields': ('organization', ('code', 'name'), 'warehouse_type', 'is_active')}),
              ('Location', {'fields': ('address',)}),
              ('Extended Data', {'classes': ('collapse',), 'fields': ('tags', 'custom_fields')}),
              ('Audit Info', {'classes': ('collapse',), 'fields': readonly_fields}),
          )
      ```
  [ ] **(Manual Test):** Verify registration, CRUD, filtering, search in Django Admin locally.

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations api.v1.features.inventory`.
  [ ] **Review generated migration file carefully.** Check FKs, `unique_together`, indexes.
  [ ] Run `python manage.py migrate` locally.

  ### 3.5 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write Unit/Integration Tests (`tests/unit/test_serializers.py`, etc.) for `WarehouseSerializer`. Test validation (`unique_together`), representation (including address link, tags, custom fields), field permissions.
  [ ] Define `WarehouseSerializer` in `api/v1/features/inventory/serializers.py`. Inherit necessary mixins (Taggit, FieldPermission).
      ```python
      from rest_framework import serializers
      from taggit.serializers import TagListSerializerField, TaggitSerializer
      from ..models import Warehouse
      # Import AddressSerializer, FieldPermission mixin etc.
      from api.v1.base_models.common.serializers import AddressSerializer
      # from core.serializers import FieldPermissionSerializerMixin

      class WarehouseSerializer(TaggitSerializer, serializers.ModelSerializer): # Add FieldPermissionSerializerMixin
          tags = TagListSerializerField(required=False)
          # Example: Nested Address read, PK write
          address_details = AddressSerializer(source='address', read_only=True)
          address = serializers.PrimaryKeyRelatedField(
              queryset=Address.objects.all(), # Scope queryset if needed
              allow_null=True, required=False # Allow null for virtual WH
          )
          organization = serializers.PrimaryKeyRelatedField(read_only=True) # Set by OrgScoped mixin
          organization_name = serializers.CharField(source='organization.name', read_only=True)

          class Meta:
              model = Warehouse
              fields = [
                  'id', 'name', 'code', 'warehouse_type',
                  'address', 'address_details', # Write via ID, read nested
                  'is_active', 'tags', 'custom_fields',
                  'organization', 'organization_name',
                  'created_at', 'updated_at',
              ]
              read_only_fields = ('id', 'organization', 'organization_name', 'created_at', 'updated_at', 'address_details')

          # Add validate_custom_fields if needed
          # Add validate_code uniqueness check within organization if needed
      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.6 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests checking `/api/v1/warehouses/` URL, authentication, Org Scoping, basic permissions.
  [ ] Define `WarehouseViewSet` in `api/v1/features/inventory/views.py`. Inherit `OrganizationScopedViewSetMixin`.
      ```python
      from rest_framework import viewsets, permissions
      from core.views import OrganizationScopedViewSetMixin # Adjust path
      from ..models import Warehouse
      from ..serializers import WarehouseSerializer
      # Import filters, permissions

      class WarehouseViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
          serializer_class = WarehouseSerializer
          permission_classes = [permissions.IsAuthenticated] # Add specific Warehouse permissions
          # queryset automatically filtered by OrganizationScopedViewSetMixin
          queryset = Warehouse.objects.select_related('organization', 'address').prefetch_related('tags').all()

          filter_backends = [...] # Add filtering/search/ordering
          # filterset_fields = ['warehouse_type', 'is_active', 'tags__name', 'address__country']
          search_fields = ['name', 'code', 'address__city']
          ordering_fields = ['name', 'code', 'created_at']
      ```
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.7 URL Routing (`urls.py`)

  [ ] Create `api/v1/features/inventory/urls.py`. Import `WarehouseViewSet`. Register with router: `router.register(r'warehouses', views.WarehouseViewSet)`.
  [ ] Include `inventory.urls` in `api/v1/features/urls.py`.
  [ ] **(Test):** Rerun basic API tests; expect 2xx/4xx codes.

  ### 3.8 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests covering:
      *   LIST (with filters). **Verify Org Scoping works.**
      *   CREATE (valid/invalid data, check org auto-set, linking address). Test permission checks (model & field).
      *   RETRIEVE (check permissions, org scoping).
      *   UPDATE (PUT/PATCH, check permissions, field permissions).
      *   DELETE (check permissions, test PROTECT if StockLocations/StockLevels exist).
      *   Saving/Validating `custom_fields`.
      *   Tag assignment/filtering via API.
  [ ] Implement/Refine ViewSet methods and Serializer logic.
  [ ] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/features/inventory`).
[ ] Manually test via API client and Django Admin. Focus on Org Scoping and address linking.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Proceed with `StockLocation` implementation.
[ ] Ensure Inventory models correctly add FKs to `Warehouse`.

--- END OF FILE warehouse_implementation_steps.md ---
### Stock Location


# StockLocation - Implementation Steps

## 1. Overview

**Model Name:**
`StockLocation`

**Corresponding PRD:**
`stock_location_prd.md`

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationScoped`, `Warehouse`, `django-mptt` library. Requires Custom Field Definition mechanism if used.

**Key Features:**
Defines specific, hierarchical storage locations (Zone, Aisle, Bin, etc.) within a `Warehouse`. Uses `django-mptt`. Includes barcode, type, status, and custom fields. Essential for granular inventory tracking. Scoped by Organization.

**Primary Location(s):**
`api/v1/features/inventory/` (Same app as `Warehouse`)

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `OrganizationScoped`, `Warehouse`) are implemented and migrated.
[ ] Verify `django-mptt` is installed and added to `INSTALLED_APPS`.
[ ] Ensure the `inventory` app structure exists (`api/v1/features/inventory/`).
[ ] Ensure `factory-boy` is set up. Factories for `Warehouse`, `User`, `Organization` exist.
[ ] Define `LocationType` choices (e.g., in `inventory/choices.py`).

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `inventory`) verifying:
      *   `StockLocation` creation with required fields (`name`, `warehouse`).
      *   `unique_together` constraints (`warehouse`, `barcode` and `warehouse`, `parent`, `name`) are enforced.
      *   Default values (`is_active`, `custom_fields`).
      *   FKs (`warehouse`, `parent`) work. `parent` links to self and respects MPTT.
      *   `barcode` field works (optional, unique within warehouse).
      *   `location_type` field works with choices.
      *   MPTT fields populated after save. `__str__` works. Inheritance works.
      Run; expect failure (`StockLocation` doesn't exist).
  [ ] Define the `StockLocation` class in `api/v1/features/inventory/models.py`.
  [ ] Add inheritance: `Timestamped`, `Auditable`, `OrganizationScoped`, `MPTTModel`.
      ```python
      # api/v1/features/inventory/models.py
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from mptt.models import MPTTModel, TreeForeignKey
      from core.models import Timestamped, Auditable, OrganizationScoped # Adjust path
      from .models import Warehouse # Assumes Warehouse in same app

      # Define choices (or import)
      class LocationType:
          ZONE = 'ZONE'; AISLE = 'AISLE'; RACK = 'RACK'; SHELF = 'SHELF'; BIN = 'BIN'; DOCK = 'DOCK'; STAGING = 'STAGING_AREA'; OTHER = 'OTHER'
          CHOICES = [...] # Define choices tuples

      class StockLocation(Timestamped, Auditable, OrganizationScoped, MPTTModel):
          name = models.CharField(
              _("Name/Identifier"), max_length=255,
              help_text=_("e.g., Aisle A, Rack 01-03, Bin A-01-03-05")
          )
          barcode = models.CharField(
              _("Barcode"), max_length=100, blank=True, db_index=True
          )
          warehouse = models.ForeignKey(
              Warehouse,
              verbose_name=_("Warehouse"),
              on_delete=models.CASCADE, # Locations deleted if Warehouse is deleted
              related_name='stock_locations'
          )
          parent = TreeForeignKey(
              'self',
              verbose_name=_("Parent Location"),
              on_delete=models.CASCADE, # Delete children if parent location deleted
              null=True, blank=True, related_name='children', db_index=True
          )
          location_type = models.CharField(
              _("Location Type"), max_length=20, choices=LocationType.CHOICES,
              blank=True, db_index=True
          )
          is_active = models.BooleanField(
              _("Is Active"), default=True, db_index=True,
              help_text=_("Can inventory be stored here?")
          )
          custom_fields = models.JSONField(
              _("Custom Fields"), default=dict, blank=True,
              help_text=_("E.g., dimensions, weight capacity, environment.")
          )

          class MPTTMeta:
              order_insertion_by = ['name']
              parent_attr = 'parent'

          class Meta:
              verbose_name = _("Stock Location")
              verbose_name_plural = _("Stock Locations")
              unique_together = (
                  # Barcode optional, but unique within its warehouse if provided
                  ('warehouse', 'barcode'),
                  # Name unique under the same parent within the same warehouse
                  ('warehouse', 'parent', 'name'),
              )
              ordering = ['warehouse__code', 'tree_id', 'lft'] # Order by warehouse then tree structure

          def __str__(self):
              # Basic representation, admin might use indented title
              return f"{self.warehouse.code} / {self.name}"

          def clean(self):
              # Enforce that parent belongs to the same warehouse
              if self.parent and self.parent.warehouse != self.warehouse:
                  from django.core.exceptions import ValidationError
                  raise ValidationError(_("Parent location must belong to the same warehouse."))
              super().clean()

      ```
  [ ] Run tests; expect pass. Refactor (especially the `clean` method validation).

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `StockLocationFactory` in `api/v1/features/inventory/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from ..models import StockLocation, LocationType, Warehouse
      from .factories import WarehouseFactory # Assumes WarehouseFactory exists

      class StockLocationFactory(DjangoModelFactory):
          class Meta:
              model = StockLocation
              # Avoid creating duplicates based on name/parent/warehouse during tests?
              # django_get_or_create = ('warehouse', 'parent', 'name')

          name = factory.Sequence(lambda n: f'Location {n}')
          # barcode = factory.Sequence(lambda n: f'BC-{n:06}') # If needed
          warehouse = factory.SubFactory(WarehouseFactory)
          parent = None # Explicitly set in tests for hierarchy
          location_type = factory.Iterator([choice[0] for choice in LocationType.CHOICES if choice[0]]) # Skip blank
          is_active = True
          custom_fields = {}

          # Link organization through warehouse factory automatically
          organization = factory.SelfAttribute('warehouse.organization')
      ```
  [ ] **(Test)** Write simple tests ensuring the factory creates valid instances and hierarchy.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Create/Update `api/v1/features/inventory/admin.py`.
  [ ] Define `StockLocationAdmin` using `DraggableMPTTAdmin`.
      ```python
      from django.contrib import admin
      from mptt.admin import DraggableMPTTAdmin
      from .models import StockLocation # Assuming WarehouseAdmin registered already

      @admin.register(StockLocation)
      class StockLocationAdmin(DraggableMPTTAdmin):
          list_display = ('tree_actions', 'indented_title', 'warehouse', 'barcode', 'location_type', 'is_active')
          list_display_links = ('indented_title',)
          list_filter = ('warehouse', 'location_type', 'is_active')
          search_fields = ('name', 'barcode', 'warehouse__name', 'warehouse__code')
          autocomplete_fields = ['warehouse', 'parent'] # Make linking easier
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
          fieldsets = (
              (None, {'fields': ('warehouse', 'parent', 'name', 'barcode', 'location_type', 'is_active')}),
              ('Custom Data', {'classes': ('collapse',), 'fields': ('custom_fields',)}),
              ('Audit Info', {'classes': ('collapse',), 'fields': readonly_fields}),
          )
      ```
  [ ] **(Manual Test):** Verify Admin CRUD, hierarchy management, filtering by warehouse. Check parent validation.

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations api.v1.features.inventory`.
  [ ] **Review generated migration file carefully.** Check MPTT fields, FKs (`warehouse`, `parent`), `unique_together`, indexes.
  [ ] Run `python manage.py migrate` locally.
  [ ] Run `python manage.py rebuild_stocklocation` (MPTT command) if needed.

  ### 3.5 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write Unit/Integration Tests for `StockLocationSerializer`. Test validation (`unique_together`, parent warehouse check), representation (including hierarchy fields like `parent`), custom field handling, field permissions.
  [ ] Define `StockLocationSerializer` in `api/v1/features/inventory/serializers.py`. Consider `MPTTModelSerializer`.
      ```python
      from rest_framework import serializers
      # from rest_framework_mptt.serializers import MPTTModelSerializer
      from ..models import StockLocation, Warehouse
      # from .serializers import WarehouseSerializer # For nesting reads
      # from core.serializers import FieldPermissionSerializerMixin

      class StockLocationSerializer(serializers.ModelSerializer): # Or MPTTModelSerializer, add FieldPermissionSerializerMixin
          # Parent can be represented by ID or barcode/name for writing? PK safer.
          parent = serializersPrimaryKeyRelatedField(
              queryset=StockLocation.objects.all(), allow_null=True, required=False
          )
          # Warehouse likely set via URL or context, or provided by ID
          warehouse = serializers.PrimaryKeyRelatedField(queryset=Warehouse.objects.all())
          warehouse_code = serializers.CharField(source='warehouse.code', read_only=True)
          # Add fields from MPTTModelSerializer if using it (e.g., children)

          class Meta:
              model = StockLocation
              fields = [
                  'id', 'name', 'barcode', 'warehouse', 'warehouse_code', 'parent',
                  'location_type', 'is_active', 'custom_fields',
                  'organization', # From OrgScoped mixin (usually read-only in serializer)
                  'created_at', 'updated_at',
                  # Add MPTT fields if needed: 'lft', 'rght', 'tree_id', 'level'
              ]
              read_only_fields = ('id', 'organization', 'created_at', 'updated_at', 'warehouse_code')

          def validate_parent(self, value):
              """Ensure parent belongs to the same warehouse if updating."""
              warehouse = self.initial_data.get('warehouse') or getattr(self.instance, 'warehouse_id', None)
              if value and warehouse and value.warehouse_id != warehouse:
                   raise serializers.ValidationError(_("Parent location must be in the same warehouse."))
              # MPTT handles circular dependency check
              return value

          def validate(self, data):
              """Ensure warehouse consistency if parent is also being set."""
              parent = data.get('parent', getattr(self.instance, 'parent', None))
              warehouse = data.get('warehouse', getattr(self.instance, 'warehouse', None))
              if parent and warehouse and parent.warehouse != warehouse:
                   raise serializers.ValidationError(_("Parent location must belong to the same warehouse."))
              # Call model's clean method? Not standard in DRF, logic often repeated here.
              return data

          # Add validate_custom_fields
      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.6 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests checking `/api/v1/stock-locations/` URL, authentication, Org Scoping, basic permissions. Consider nested URL `/api/v1/warehouses/{wh_id}/stock-locations/`.
  [ ] Define `StockLocationViewSet` in `api/v1/features/inventory/views.py`. Inherit `OrganizationScopedViewSetMixin`. Handle potential nesting.
      ```python
      from rest_framework import viewsets, permissions
      from core.views import OrganizationScopedViewSetMixin # Adjust path
      from ..models import StockLocation
      from ..serializers import StockLocationSerializer
      # Import filters, permissions

      class StockLocationViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
          serializer_class = StockLocationSerializer
          permission_classes = [permissions.IsAuthenticated] # Add specific inventory permissions
          # Base queryset filtered by org via mixin
          queryset = StockLocation.objects.select_related('warehouse', 'parent').all()

          filter_backends = [...] # Filtering/Search/Ordering
          # filterset_fields = ['warehouse', 'location_type', 'is_active', 'parent']
          search_fields = ['name', 'barcode', 'warehouse__code', 'warehouse__name']
          ordering_fields = ['name', 'barcode', 'lft'] # Order by tree structure

          # Optional: Handle nested route - filter by warehouse from URL
          # def get_queryset(self):
          #     qs = super().get_queryset()
          #     warehouse_id = self.kwargs.get('warehouse_pk') # If URL is nested
          #     if warehouse_id:
          #         qs = qs.filter(warehouse_id=warehouse_id)
          #     return qs

          # Optional: Custom actions for hierarchy (get descendants etc.)
      ```
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.7 URL Routing (`urls.py`)

  [ ] Import `StockLocationViewSet` in `api/v1/features/inventory/urls.py`.
  [ ] Register with router: `router.register(r'stock-locations', views.StockLocationViewSet)`.
  [ ] *(Optional Nested)* Use `drf-nested-routers` or manual patterns for `/warehouses/{warehouse_pk}/stock-locations/`.
  [ ] **(Test):** Rerun basic API tests; expect 2xx/4xx codes.

  ### 3.8 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests covering:
      *   LIST (with filters for warehouse, type, parent). **Verify Org Scoping.**
      *   CREATE (valid/invalid data, setting warehouse/parent). Test permission checks.
      *   RETRIEVE.
      *   UPDATE (PUT/PATCH, including changing parent).
      *   DELETE (test CASCADE if deleting parent).
      *   Hierarchy actions (if any).
      *   Saving/Validating `custom_fields`.
  [ ] Implement/Refine ViewSet methods and Serializer logic. Ensure Field-Level permissions checked if applicable.
  [ ] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/features/inventory`).
[ ] Manually test via API client and Django Admin (hierarchy, link to warehouse).
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs (e.g., admin field name widget).
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Ensure Inventory models correctly add FKs to `StockLocation`.

--- END OF FILE stocklocation_implementation_steps.md ---
## Communication & Collaboration


### Chat


# Chat System - Implementation Steps

## 1. Overview

**System Name:**
Chat System

**Corresponding PRD:**
`chat_prd.md` (Simplified version)

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `Organization`, `FileStorage`, `Notification` System, potentially `Search` System, Celery, Redis (for Channel Layer), ASGI Server (Daphne/Uvicorn). Requires `django-channels`, `channels-redis`.

**Key Features:**
Real-time direct and group messaging (`ChatRoom`, `ChatMessage` models). Uses Django Channels/WebSockets for real-time delivery. Supports basic threading, file attachments, presence, typing indicators. Integrates with notifications and search. Scoped by Organization.

**Primary Location(s):**
*   Models, Serializers, Views, Consumers, Routing: `chat/` (New dedicated app)
*   ASGI Setup: `config/asgi.py`, `config/settings/base.py`
*   API URLs: `api/v1/chat/` (New dedicated API structure)

## 2. Prerequisites

[ ] Verify all prerequisite models/mixins (`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `Organization`, `FileStorage`) are implemented and migrated.
[ ] Verify Celery & Redis infrastructure is operational.
[ ] Verify Notification system (`send_notification` service) is available.
[ ] Verify FileStorage upload API exists.
[ ] **Install Channels libraries:** `pip install django-channels channels-redis`.
[ ] **Create new Django app:** `python manage.py startapp chat`.
[ ] Add `'chat'` and `'channels'` to `INSTALLED_APPS` in `config/settings/base.py`.
[ ] Ensure `factory-boy` is set up. Factories for `User`, `Organization`, `FileStorage` exist.
[ ] Configure **ASGI Application** in `config/asgi.py`.
[ ] Configure **Channel Layer** (`CHANNEL_LAYERS`) in `config/settings/base.py` (using `channels_redis`).

## 3. Implementation Steps (TDD Workflow)

  *(Models -> Channels Setup -> API -> WebSocket Logic)*

  ### 3.1 Core Model Definitions (`chat/models.py`)

  [ ] **(Test First - ChatRoom)** Write Unit Tests (`chat/tests/unit/test_models.py`) verifying `ChatRoom` creation, fields, defaults, M2M `participants`, inheritance, `__str__`.
  [ ] Define `ChatRoom` model. Inherit `Timestamped`, `Auditable`, `OrganizationScoped`. Add `name`, `room_type`, `participants` (M2M to User), `is_active`, `custom_fields`. Define Meta.
  [ ] Run ChatRoom tests; expect pass. Refactor.
  [ ] **(Test First - ChatMessage)** Write Unit Tests verifying `ChatMessage` creation, fields, defaults, FKs (`room`, `sender`, `parent`), M2M `attachments`, inheritance, `__str__`.
  [ ] Define `ChatMessage` model. Inherit `Timestamped`, `Auditable`, `OrganizationScoped`. Add `room` (FK), `sender` (FK), `content`, `parent` (FK to self), `attachments` (M2M to FileStorage), `is_edited`, `is_deleted`, `custom_fields`. Define Meta, indexes.
  [ ] Run ChatMessage tests; expect pass. Refactor.
  [ ] *(Optional: Define `ChatParticipant` through model if per-user room state needed)*.

  ### 3.2 Factory Definitions (`chat/tests/factories.py`)

  [ ] Define `ChatRoomFactory` and `ChatMessageFactory`. Handle `participants` M2M and `attachments` M2M in factories (e.g., using post-generation). Ensure `ChatMessageFactory` links correctly to `ChatRoom` and `sender`. Handle `parent` for replies. Ensure Org scoping inherited/set.
  [ ] **(Test)** Write simple tests ensuring factories create valid instances and relationships.

  ### 3.3 Admin Registration (`chat/admin.py`)

  [ ] Create `chat/admin.py`.
  [ ] Define `ChatMessageInline` (TabularInline) showing sender, content snippet, created_at.
  [ ] Define `ChatRoomAdmin`. Use `filter_horizontal` for `participants`. Include `ChatMessageInline`. Configure `list_display`, `search_fields`, `list_filter`.
  [ ] Register models.
  [ ] **(Manual Test):** Verify Admin interface for viewing rooms, participants, and messages.

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations chat`.
  [ ] **Review generated migration file(s) carefully.** Check models, FKs, M2Ms, indexes.
  [ ] Run `python manage.py migrate` locally.

  ### 3.5 Channels Routing (`chat/routing.py` & `config/asgi.py`)

  [ ] Create `chat/routing.py`. Define `websocket_urlpatterns` using `re_path` or `path` pointing to the Chat Consumer (to be created).
      ```python
      # chat/routing.py
      from django.urls import re_path
      from . import consumers

      websocket_urlpatterns = [
          re_path(r'ws/chat/(?P<room_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
          # Add other consumers if needed (e.g., general notification socket)
      ]
      ```
  [ ] Update `config/asgi.py` to include the `chat.routing.websocket_urlpatterns`:
      ```python
      # config/asgi.py
      import os
      from django.core.asgi import get_asgi_application
      from channels.routing import ProtocolTypeRouter, URLRouter
      from channels.auth import AuthMiddlewareStack # For user auth in websockets
      import chat.routing # Import chat routing

      os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev') # Adjust

      application = ProtocolTypeRouter({
          "http": get_asgi_application(),
          "websocket": AuthMiddlewareStack( # Wrap with auth middleware
              URLRouter(
                  chat.routing.websocket_urlpatterns # Add chat patterns
                  # Add other app websocket patterns here if needed
              )
          ),
      })
      ```

  ### 3.6 Channels Consumer (`chat/consumers.py`)

  [ ] **(Test First - WebSocket Lifecycle)** Write Integration Tests (`chat/tests/integration/test_consumers.py`) using `channels.testing.WebsocketCommunicator`.
      *   Test connection attempts (unauthenticated -> reject, authenticated -> accept).
      *   Test joining/leaving a Channels group associated with a valid `room_id` on connect/disconnect. Verify user needs to be a participant.
      *   Test receiving a valid message -> verify `ChatMessage` is created, broadcast is triggered (mock broadcast call).
      *   Test receiving invalid message data -> verify error returned over WebSocket.
      *   Test handling of typing indicators.
      Run; expect failure.
  [ ] Create `chat/consumers.py`. Define `ChatConsumer` inheriting from `AsyncWebsocketConsumer`.
      ```python
      # chat/consumers.py
      import json
      from channels.generic.websocket import AsyncWebsocketConsumer
      from channels.db import database_sync_to_async # For DB operations
      from django.contrib.contenttypes.models import ContentType
      # Import models, FileStorage, serializers etc.
      from .models import ChatRoom, ChatMessage
      from api.v1.base_models.common.models import FileStorage # Adjust path

      class ChatConsumer(AsyncWebsocketConsumer):
          async def connect(self):
              self.room_id = self.scope['url_route']['kwargs']['room_id']
              self.room_group_name = f'chat_{self.room_id}'
              self.user = self.scope['user']

              if not self.user or not self.user.is_authenticated:
                  await self.close()
                  return

              # Check if user is participant (requires DB access)
              is_participant = await self.check_user_participation(self.room_id, self.user)
              if not is_participant:
                   await self.close()
                   return

              # Join room group
              await self.channel_layer.group_add(
                  self.room_group_name,
                  self.channel_name
              )
              await self.accept()
              # TODO: Broadcast user presence update?

          async def disconnect(self, close_code):
              # Leave room group
              if hasattr(self, 'room_group_name'):
                  await self.channel_layer.group_discard(
                      self.room_group_name,
                      self.channel_name
                  )
              # TODO: Broadcast user presence update?

          # Receive message from WebSocket
          async def receive(self, text_data=None, bytes_data=None):
              try:
                  text_data_json = json.loads(text_data)
                  message_type = text_data_json.get('type')
                  # Example: Simple message send
                  if message_type == 'chat_message':
                      content = text_data_json.get('message', '').strip()
                      attachment_ids = text_data_json.get('attachment_ids', [])
                      parent_id = text_data_json.get('parent_id')

                      if not content and not attachment_ids:
                          await self.send_error("Message content or attachment required.")
                          return

                      # Save message to DB (use database_sync_to_async)
                      message_obj = await self.save_message(
                          content=content,
                          attachment_ids=attachment_ids,
                          parent_id=parent_id
                      )
                      if not message_obj: # Save failed (e.g., permission)
                           await self.send_error("Failed to send message.")
                           return

                      # Broadcast message to room group (requires serialization)
                      await self.channel_layer.group_send(
                          self.room_group_name,
                          {
                              'type': 'broadcast_chat_message', # Corresponds to method below
                              'message': await self.serialize_message(message_obj) # Serialize async
                          }
                      )
                  elif message_type == 'typing_indicator':
                      # Broadcast typing status to others in the group
                      await self.channel_layer.group_send(
                           self.room_group_name,
                           {
                               'type': 'broadcast_typing_indicator',
                               'user_id': self.user.pk,
                               'username': self.user.username,
                               'is_typing': text_data_json.get('is_typing', False)
                           },
                           # Exclude sender? Sometimes needed
                           # exclude_channel=self.channel_name
                       )
                  # Handle other message types (edit, delete notifications?)

              except json.JSONDecodeError:
                  await self.send_error("Invalid JSON format.")
              except Exception as e:
                  # Log unexpected errors
                  import logging
                  logging.getLogger(__name__).error(f"ChatConsumer receive error: {e}", exc_info=True)
                  await self.send_error("An unexpected error occurred.")

          # --- Broadcasting Helpers ---
          async def broadcast_chat_message(self, event):
              """ Sends message from group down to specific websocket connection """
              message_data = event['message']
              # Send message to WebSocket client
              await self.send(text_data=json.dumps({
                  'type': 'chat_message',
                  'message': message_data
              }))

          async def broadcast_typing_indicator(self, event):
              """ Sends typing indicator to websocket connection """
              # Don't send typing indicator back to the user who is typing
              if event['user_id'] != self.user.pk:
                  await self.send(text_data=json.dumps({
                      'type': 'typing_indicator',
                      'user_id': event['user_id'],
                      'username': event['username'],
                      'is_typing': event['is_typing']
                  }))

          async def send_error(self, message):
               """ Sends an error message back to the client """
               await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': message
               }))

          # --- Database Interaction (must be async) ---
          @database_sync_to_async
          def check_user_participation(self, room_id, user):
               try:
                   room = ChatRoom.objects.get(pk=room_id, organization=user.profile.primary_organization) # Add Org scope check
                   return room.participants.filter(pk=user.pk).exists()
               except ChatRoom.DoesNotExist:
                   return False

          @database_sync_to_async
          def save_message(self, content, attachment_ids, parent_id):
               try:
                   room = ChatRoom.objects.get(pk=self.room_id)
                   # Check user can send in this room (already checked participation on connect)
                   # Check parent exists and is in same room if parent_id provided
                   parent = None
                   if parent_id:
                       parent = ChatMessage.objects.filter(pk=parent_id, room=room).first()
                       if not parent: raise ValueError("Parent comment not found or in different room.")

                   # Create message (organization scope inherited)
                   message = ChatMessage.objects.create(
                       room=room,
                       sender=self.user,
                       content=content,
                       parent=parent,
                       organization=room.organization # Explicitly set org
                       # Set created_by/updated_by automatically via Auditable mixin
                   )
                   # Handle attachments M2M
                   if attachment_ids:
                       # Validate attachment IDs belong to user/org?
                       attachments = FileStorage.objects.filter(pk__in=attachment_ids, organization=room.organization)
                       message.attachments.set(attachments)
                   return message
               except Exception as e:
                   # Log error
                   import logging
                   logging.getLogger(__name__).error(f"Failed to save chat message: {e}", exc_info=True)
                   return None

          @database_sync_to_async
          def serialize_message(self, message_obj):
              # Use DRF serializer (needs async adaptation or run_sync)
              # Simplistic dict for now:
              # TODO: Use proper DRF serializer (may need tweaking for async context)
              return {
                  'id': message_obj.pk,
                  'room_id': message_obj.room_id,
                  'sender_id': message_obj.sender_id,
                  'sender_username': getattr(message_obj.sender, 'username', 'System'),
                  'content': message_obj.content,
                  'parent_id': message_obj.parent_id,
                  'attachment_ids': list(message_obj.attachments.values_list('pk', flat=True)),
                  'is_edited': message_obj.is_edited,
                  'created_at': message_obj.created_at.isoformat(),
              }
      ```
      *(Note: This is a complex component. Error handling, detailed permission checks, serialization, presence, and read receipts need careful implementation and testing.)*
  [ ] Run consumer tests; expect pass. Refactor consumer logic.

  ### 3.7 API ViewSet/Serializer Definition (`chat/serializers.py`, `chat/views.py`, `chat/urls.py`)

  [ ] **(Test First)** Write API tests (`chat/tests/api/test_endpoints.py`) for:
      *   `GET /rooms/` (list user's rooms).
      *   `POST /rooms/` (create group room).
      *   `GET /rooms/{id}/messages/` (get history, test pagination).
      *   `POST /rooms/{id}/messages/` (send message via API - alternative to WebSocket).
      *   `PUT/DELETE /messages/{id}/` (edit/delete own message).
      *   `POST/DELETE /rooms/{id}/participants/` (add/remove users).
      *   Test permissions and Org Scoping for all endpoints.
  [ ] Define `ChatRoomSerializer`, `ChatMessageSerializer` (potentially reusing parts of consumer serialization logic). Handle nested participants/messages appropriately.
  [ ] Define `ChatRoomViewSet` and `ChatMessageViewSet` (or combined). Implement necessary actions (list rooms, get messages, create room, manage participants, edit/delete message). Use `OrganizationScopedViewSetMixin`. Apply permissions.
  [ ] Define URL routing for these API endpoints.
  [ ] Run API tests; expect pass. Refactor.

  ### 3.8 Integration with Other Systems

  [ ] **(Test First - Notifications)** Test scenario where user is offline, message sent -> verify `send_notification` task is queued.
  [ ] Integrate calls to `Notification` service (async task) from consumer/signal when offline message/mention occurs.
  [ ] **(Test First - Search)** Test scenario where message sent -> verify message content appears in Search Engine index (mock ES).
  [ ] Integrate calls to update Search index (async task) from `ChatMessage` `post_save` signal.
  [ ] **(Test First - Audit)** Test room creation, participant changes -> verify `AuditLog` created.
  [ ] Integrate calls to `AuditLogging` system for relevant events.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`), including Channels tests.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=chat`). Review uncovered consumer/signal/task logic.
[ ] Manually test core chat functionality: connecting multiple clients, sending/receiving messages, basic history, group chat, file attachments via WebSocket/API. Test Org Scoping.
[ ] Review API and WebSocket documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs (Presence implementation, read receipts, rich content, mentions, advanced error handling).
[ ] Create Pull Request.
[ ] Update API and WebSocket documentation.
[ ] Deploy ASGI server (Daphne/Uvicorn) and configure Channel Layer (Redis) in deployment strategy.

--- END OF FILE chat_implementation_steps.md ---
### Comment


# Comment - Implementation Steps

## 1. Overview

**Model Name:**
`Comment`

**Corresponding PRD:**
`comment_prd.md` (Simplified version)

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `FileStorage`, `Organization`, `ContentType` framework, `django-taggit` (if using tags). Requires Custom Field Definition mechanism if used.

**Key Features:**
Allows users to add threaded comments (replies) with optional file attachments to various business objects using Generic Relations. Includes basic status/moderation, custom fields, and organization scoping.

**Primary Location(s):**
`api/v1/features/collaboration/` (Assuming a new `collaboration` feature app/group) or `api/v1/base_models/common/`. Let's assume **`collaboration`**.

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `FileStorage`, `Organization`, `ContentType`) are implemented and migrated.
[ ] Ensure `django-taggit` is installed/configured if using tags (though not explicitly listed in final PRD fields, `tags` might be added later).
[ ] **Create new Django app:** `python manage.py startapp collaboration`.
[ ] Add `'api.v1.features.collaboration'` (adjust path) to `INSTALLED_APPS`.
[ ] Ensure `factory-boy` is set up. Factories for `User`, `Organization`, `FileStorage`, and representative parent objects (e.g., `Product`) exist.
[ ] Define `CommentStatus` choices (e.g., in `collaboration/choices.py`).

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `collaboration`) verifying:
      *   `Comment` creation with required fields (`user`, `content`, `content_type`, `object_id`, `organization`).
      *   FKs (`user`, `parent`, `content_type`) work.
      *   GFK (`content_object`) resolves correctly to a parent instance.
      *   M2M (`attachments`) works.
      *   Default values (`is_edited`, `status`, `custom_fields`).
      *   `parent` link creates basic thread structure.
      *   `__str__` method works. Inheritance works.
      Run; expect failure (`Comment` doesn't exist).
  [ ] Define the `Comment` class in `api/v1/features/collaboration/models.py`.
  [ ] Add inheritance: `Timestamped`, `Auditable`, `OrganizationScoped`.
      ```python
      # api/v1/features/collaboration/models.py
      from django.conf import settings
      from django.contrib.contenttypes.fields import GenericForeignKey
      from django.contrib.contenttypes.models import ContentType
      from django.db import models
      from django.utils.translation import gettext_lazy as _

      from core.models import Timestamped, Auditable, OrganizationScoped # Adjust path
      # Adjust path based on FileStorage location
      from api.v1.base_models.common.models import FileStorage

      class CommentStatus:
          VISIBLE = 'VISIBLE'
          HIDDEN = 'HIDDEN' # e.g., deleted by user or moderator
          PENDING = 'PENDING_MODERATION'
          CHOICES = [
              (VISIBLE, _('Visible')),
              (HIDDEN, _('Hidden/Deleted')),
              (PENDING, _('Pending Moderation')),
          ]

      class Comment(Timestamped, Auditable, OrganizationScoped):
          # user field from Auditable.created_by is sufficient
          # organization field from OrganizationScoped

          content = models.TextField(_("Content"))

          # Generic relation to parent object
          content_type = models.ForeignKey(
              ContentType, verbose_name=_("Parent Type"), on_delete=models.CASCADE
          )
          object_id = models.CharField( # Use CharField for flexibility (UUIDs)
              _("Parent ID"), max_length=255, db_index=True
          )
          content_object = GenericForeignKey('content_type', 'object_id')

          # Basic Threading (Replies)
          parent = models.ForeignKey(
              'self', verbose_name=_("Parent Comment"),
              on_delete=models.CASCADE, # Delete replies if parent deleted
              null=True, blank=True, related_name='replies', db_index=True
          )

          is_edited = models.BooleanField(_("Is Edited"), default=False)
          status = models.CharField(
              _("Status"), max_length=20, choices=CommentStatus.CHOICES,
              default=CommentStatus.VISIBLE, db_index=True
          )
          attachments = models.ManyToManyField(
              FileStorage, verbose_name=_("Attachments"), blank=True, related_name="comment_attachments"
          )
          custom_fields = models.JSONField(
              _("Custom Fields"), default=dict, blank=True
          )

          class Meta:
              verbose_name = _("Comment")
              verbose_name_plural = _("Comments")
              ordering = ['created_at'] # Oldest first for threads
              indexes = [
                  models.Index(fields=["content_type", "object_id"]), # For GFK lookup
                  models.Index(fields=["status"]),
                  models.Index(fields=["parent"]),
              ]

          def __str__(self):
              # Truncate content for display
              limit = 50
              truncated_content = (self.content[:limit] + '...') if len(self.content) > limit else self.content
              return f"Comment by {self.created_by or 'System'} on {self.content_object or 'Unknown'}: '{truncated_content}'"

          # Add permission checks here if needed (e.g., can_edit, can_delete)
          # def user_can_edit(self, user): ...
          # def user_can_delete(self, user): ...
      ```
  [ ] Run tests; expect pass. Refactor model code if needed.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `CommentFactory` in `api/v1/features/collaboration/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from django.contrib.contenttypes.models import ContentType
      from ..models import Comment, CommentStatus
      from api.v1.base_models.user.tests.factories import UserFactory
      from api.v1.base_models.organization.tests.factories import OrganizationFactory
      # Import a factory for a sample commentable object, e.g., Product
      # from api.v1.features.products.tests.factories import ProductFactory

      class CommentFactory(DjangoModelFactory):
          class Meta:
              model = Comment

          # user = factory.SubFactory(UserFactory) # Handled by Auditable mixin usually
          content = factory.Faker('paragraph', nb_sentences=3)
          parent = None # Set explicitly for replies

          # Needs a concrete object to attach to by default for GFK
          # Option 1: Default to a specific type (e.g., Product)
          # content_object = factory.SubFactory(ProductFactory)
          # Option 2: Pass object in test setup
          content_type = factory.LazyAttribute(lambda o: ContentType.objects.get_for_model(o.content_object) if o.content_object else None)
          object_id = factory.SelfAttribute('content_object.pk')

          status = CommentStatus.VISIBLE
          custom_fields = {}

          # Link organization (should likely come from content_object or user context)
          organization = factory.SelfAttribute('content_object.organization') # If parent is OrgScoped
          # organization = factory.SubFactory(OrganizationFactory) # Or set directly if needed

          # Handle attachments M2M post-generation if needed
          # @factory.post_generation
          # def attachments(self, create, extracted, **kwargs): ...
      ```
  [ ] **(Test)** Write simple tests ensuring the factory creates valid instances, including replies (setting `parent`) and linking to different `content_object` types.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Create `api/v1/features/collaboration/admin.py`.
  [ ] Define `CommentAdmin`:
      ```python
      from django.contrib import admin
      from django.contrib.contenttypes.admin import GenericStackedInline # Or Tabular
      from .models import Comment

      @admin.register(Comment)
      class CommentAdmin(admin.ModelAdmin):
          list_display = (
              'id', 'content_type', 'object_id', 'content_object_link',
              'user_display', 'parent', 'status', 'created_at', 'is_edited'
          )
          list_filter = ('status', 'content_type', 'created_at', 'organization')
          search_fields = ('content', 'object_id', 'created_by__username')
          list_select_related = ('content_type', 'created_by', 'organization', 'parent') # Use created_by from Auditable
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by', 'content_object', 'is_edited')
          raw_id_fields = ('parent', 'content_type') # Helpful for linking
          fields = (
              'organization', ('content_type', 'object_id'), 'parent',
              'status', 'content', 'attachments', 'custom_fields',
              ('created_at', 'created_by'), ('updated_at', 'updated_by'), 'is_edited'
          )
          filter_horizontal = ('attachments',) # Better widget for M2M

          @admin.display(description='Author')
          def user_display(self, obj):
              return obj.created_by or 'System'

          @admin.display(description='Parent Object')
          def content_object_link(self, obj):
              # Link to parent object admin if possible
              if obj.content_object:
                  # ... logic to get admin URL ...
                  return obj.content_object
              return "-"

      # Optional: Inline for showing comments on parent model admin (e.g., ProductAdmin)
      # class CommentInline(GenericStackedInline): # Or GenericTabularInline
      #     model = Comment
      #     fields = ('created_by', 'content', 'status', 'attachments') # etc
      #     readonly_fields = ('created_by',)
      #     ct_field = "content_type"
      #     ct_fk_field = "object_id"
      #     extra = 0
      ```
  [ ] **(Manual Test):** Verify Admin CRUD (esp. GFK display), filtering. Test creating replies via admin.

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations collaboration`.
  [ ] **Review generated migration file carefully.** Check GFK fields, FKs (`parent`, `user`), M2M (`attachments`), indexes.
  [ ] Run `python manage.py migrate` locally.

  ### 3.5 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write Unit/Integration Tests for `CommentSerializer`. Test validation (content required, parent exists and belongs to same thread), representation (user details, parent ID, attachments, custom fields), GFK handling, nested replies (optional).
  [ ] Define `CommentSerializer` in `api/v1/features/collaboration/serializers.py`. Handle nested replies if needed.
      ```python
      from rest_framework import serializers
      from django.contrib.contenttypes.models import ContentType
      from ..models import Comment, CommentStatus
      # Import User/FileStorage serializers if nesting
      # from api.v1.base_models.user.serializers import UserSummarySerializer
      # from api.v1.base_models.common.serializers import FileStorageSerializer
      # from core.serializers import FieldPermissionSerializerMixin

      class ReplySerializer(serializers.ModelSerializer): # Minimal serializer for nested replies
          # user = UserSummarySerializer(read_only=True)
          user_id = serializers.IntegerField(source='created_by_id', read_only=True) # Use Auditable field

          class Meta:
              model = Comment
              fields = ['id', 'user_id', 'content', 'is_edited', 'status', 'created_at', 'updated_at']
              read_only_fields = fields

      class CommentSerializer(serializers.ModelSerializer): # Add FieldPermissionMixin?
          # user = UserSummarySerializer(read_only=True) # Nested user info
          user_id = serializers.IntegerField(source='created_by_id', read_only=True) # Use Auditable field
          replies = ReplySerializer(many=True, read_only=True) # Show direct replies nested
          # attachments = FileStorageSerializer(many=True, read_only=True) # Nested file info
          attachment_ids = serializers.PrimaryKeyRelatedField(
              queryset=FileStorage.objects.all(), # Scope by org/permissions?
              source='attachments', many=True, write_only=True, required=False
          )
          parent_id = serializers.PrimaryKeyRelatedField(
              queryset=Comment.objects.all(), source='parent', allow_null=True, required=False, write_only=True
          )
          # Fields for writing the GFK target on create
          content_type_id = serializers.PrimaryKeyRelatedField(
              queryset=ContentType.objects.all(), write_only=True, required=True
          )
          object_id = serializers.CharField(write_only=True, required=True)

          class Meta:
              model = Comment
              fields = [
                  'id', 'user_id', #'user',
                  'content_type_id', 'object_id', # Write-only for linking
                  'parent', 'parent_id', # Read parent PK, write parent ID
                  'content', 'is_edited', 'status',
                  'attachments', 'attachment_ids', # Read nested, write IDs
                  'custom_fields',
                  'replies', # Read-only nested replies
                  'created_at', 'updated_at',
              ]
              read_only_fields = ('id', 'parent', 'is_edited', 'status', 'attachments', 'replies', 'created_at', 'updated_at', 'user_id')
              # Note: status might be updatable via specific moderation actions

          def validate(self, data):
              # Validate parent comment belongs to the same content_object if parent is set
              parent = data.get('parent')
              content_type = data.get('content_type_id') # This is the ContentType instance now
              object_id = data.get('object_id')

              if parent:
                   if parent.content_type != content_type or str(parent.object_id) != str(object_id):
                       raise serializers.ValidationError("Reply must belong to the same parent object thread.")
                   if parent.parent_id is not None: # Limit to one level of reply nesting?
                       raise serializers.ValidationError("Direct replies only; nesting deeper is not supported.")

              # Add custom_fields validation here
              # Add permission checks if needed (e.g., user can comment on target object)
              return data

          def create(self, validated_data):
              # Pop M2M fields before super().create()
              attachments_data = validated_data.pop('attachments', None)
              # GFK fields already validated/converted by PrimaryKeyRelatedField/CharField
              comment = super().create(validated_data)
              if attachments_data:
                  comment.attachments.set(attachments_data)
              return comment
          # Override update similarly if allowing edits, handle attachments M2M
      ```
  [ ] Run tests; expect pass. Refactor (especially GFK setting and nested write handling).

  ### 3.6 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests checking `/api/v1/comments/` URL, authentication, Org Scoping, basic permissions. Test listing comments for a specific parent object.
  [ ] Define `CommentViewSet` in `api/v1/features/collaboration/views.py`. Inherit `OrganizationScopedViewSetMixin`. Implement filtering by parent object.
      ```python
      from rest_framework import viewsets, permissions
      from django.contrib.contenttypes.models import ContentType
      from core.views import OrganizationScopedViewSetMixin # Adjust path
      from ..models import Comment
      from ..serializers import CommentSerializer
      # Import filters, permissions

      class CommentViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
          serializer_class = CommentSerializer
          permission_classes = [permissions.IsAuthenticated] # Add specific comment permissions
          # Base queryset filtered by org via mixin
          queryset = Comment.objects.filter(status=CommentStatus.VISIBLE) \
                                    .select_related('created_by', 'parent') \
                                    .prefetch_related('replies', 'attachments')

          filter_backends = [...] # Add filtering backend (e.g., django-filter)
          # filterset_fields = ['content_type', 'object_id', 'user'] # Define FilterSet class

          def get_queryset(self):
              qs = super().get_queryset()
              # Allow filtering by parent object via query params
              parent_type_id = self.request.query_params.get('content_type_id')
              parent_object_id = self.request.query_params.get('object_id')

              if parent_type_id and parent_object_id:
                  try:
                      # Validate content_type exists?
                      # ContentType.objects.get_for_id(parent_type_id)
                      qs = qs.filter(content_type_id=parent_type_id, object_id=parent_object_id, parent__isnull=True) # Only top-level comments
                  except (ValueError, ContentType.DoesNotExist):
                      return qs.none() # Invalid type ID

              # Add permission filtering - ensure user can VIEW the parent object? Complex.
              # Rely on scoping + specific permissions for now.
              return qs

          def perform_create(self, serializer):
              # Set user from request, check permission to comment on parent object
              parent_object = None
              try:
                   ctype = ContentType.objects.get_for_id(serializer.validated_data['content_type_id'].id)
                   parent_object = ctype.get_object_for_this_type(pk=serializer.validated_data['object_id'])
              except Exception:
                   raise serializers.ValidationError("Invalid parent object specified.")

              # Example permission check (assumes view perm implies comment perm)
              if not self.request.user.has_perm(f'{ctype.app_label}.view_{ctype.model}', parent_object):
                   raise PermissionDenied("You do not have permission to comment on this object.")

              # Check parent comment validity moved to serializer validate()

              serializer.save(created_by=self.request.user) # Set author

          # Override perform_update/perform_destroy for edit/delete permissions
      ```
  [ ] Run basic tests; expect pass. Refactor (especially GFK filtering and permission checks).

  ### 3.7 URL Routing (`urls.py`)

  [ ] Create `api/v1/features/collaboration/urls.py`. Import `CommentViewSet`. Register with router: `router.register(r'comments', views.CommentViewSet)`.
  [ ] Include `collaboration.urls` in `api/v1/features/urls.py`.
  [ ] **(Test):** Rerun basic API tests; expect 2xx/4xx codes.

  ### 3.8 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests covering:
      *   LIST: Test filtering by `content_type_id` & `object_id`. Verify only top-level comments returned by default. Verify nested `replies` are present. Test pagination. **Verify Org Scoping.**
      *   CREATE: Test creating top-level comments and replies (providing `parent_id`). Test associating with different parent object types. Test attachment uploads with comments. Test validation errors (missing content, invalid parent). Test permissions (can user comment on target object?).
      *   RETRIEVE (if needed, usually list is sufficient).
      *   UPDATE/PATCH: Test editing own comment (check `is_edited` flag). Test permissions.
      *   DELETE: Test deleting own comment (check status becomes HIDDEN or row deleted). Test permissions.
      *   Test moderation actions if implemented.
      *   Saving/Validating `custom_fields`.
  [ ] Implement/Refine ViewSet/Serializer logic (especially `perform_create`, permission checks, GFK handling).
  [ ] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/features/collaboration`).
[ ] Manually test creating/viewing comments and replies via API client on different objects. Check attachments.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs (Refine GFK validation/setting in API, single primary logic for channels, nested update logic).
[ ] Implement notification triggers for new comments/replies.
[ ] Create Pull Request.
[ ] Update API documentation.

--- END OF FILE comment_implementation_steps.md ---
### Notification


# Notification System - Implementation Steps

## 1. Overview

**System Name:**
Notification System

**Corresponding PRD:**
`notification_prd.md` (Simplified version)

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `UserProfile` (for preferences), `Organization`, `ContentType` (for GFKs), Celery infrastructure, Django Email Backend configuration.

**Key Features:**
Provides in-app notifications (`Notification` model) and triggers asynchronous email sending via Celery. Includes optional templating (`NotificationTemplate`) and respects user preferences stored on `UserProfile`. Exposes APIs for users to view/manage their notifications.

**Primary Location(s):**
*   Models: `notifications/models.py` (New dedicated app recommended)
*   Service Function: `notifications/services.py`
*   Celery Tasks: `notifications/tasks.py`
*   Admin: `notifications/admin.py`
*   API: `api/v1/notifications/` (New app or within an existing API structure)
*   Templates (Email): `notifications/templates/notifications/email/`

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `UserProfile`, `Organization`, `ContentType`) are implemented and migrated.
[ ] Verify Celery infrastructure (Broker like Redis, worker setup) is configured and operational.
[ ] Verify Django Email Backend is configured in settings (e.g., Console backend for dev, SMTP/API service for prod).
[ ] Verify `UserProfile` model has the `notification_preferences` JSONField defined.
[ ] **Create new Django app:** `python manage.py startapp notifications`.
[ ] Add `'notifications'` to `INSTALLED_APPS`.
[ ] Ensure `factory-boy` is set up. Factories for `User`, `UserProfile`, `Organization` exist.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 `NotificationTemplate` Model Definition (Optional but Recommended)

  [ ] **(Test First)** Write Unit Tests (`notifications/tests/unit/test_models.py`) verifying `NotificationTemplate` creation, unique `template_key`, field storage, `__str__`.
  [ ] Define `NotificationTemplate` in `notifications/models.py`. Inherit `Timestamped`, `Auditable`.
      ```python
      # notifications/models.py
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from core.models import Timestamped, Auditable # Adjust path

      class NotificationTemplate(Timestamped, Auditable):
          template_key = models.CharField(
              _("Template Key"), max_length=100, unique=True, db_index=True,
              help_text=_("Unique key to identify this template (e.g., 'invoice_approved_email').")
          )
          name = models.CharField(_("Template Name"), max_length=255) # For admin identification
          subject_template = models.TextField(
              _("Subject Template"), help_text=_("Django template syntax for email subject.")
          )
          body_template_txt = models.TextField(
              _("Text Body Template"), help_text=_("Django template syntax for plain text email body.")
          )
          body_template_html = models.TextField(
              _("HTML Body Template"), blank=True,
              help_text=_("Django template syntax for HTML email body (optional).")
          )

          class Meta:
              verbose_name = _("Notification Template")
              verbose_name_plural = _("Notification Templates")
              ordering = ['template_key']

          def __str__(self):
              return self.name or self.template_key
      ```
  [ ] Run template model tests; expect pass. Refactor.

  ### 3.2 `Notification` Model Definition (`notifications/models.py`)

  [ ] **(Test First)** Write Unit Tests (`notifications/tests/unit/test_models.py`) verifying:
      *   `Notification` creation with required fields (`recipient`).
      *   Defaults (`level`, `status`). `read_at` is null initially.
      *   FKs (`recipient`, `organization`, `content_type`) work.
      *   GFK (`content_object`) works.
      *   `__str__` works. Inheritance works.
      Run; expect failure.
  [ ] Define `Notification` model in `notifications/models.py`. Inherit `Timestamped`, `Auditable`, `OrganizationScoped`.
      ```python
      # notifications/models.py
      # ... (imports for models, Timestamped, Auditable, OrganizationScoped, User, Org, ContentType) ...
      from django.utils import timezone

      class NotificationLevel:
          INFO = 'INFO'; SUCCESS = 'SUCCESS'; WARNING = 'WARNING'; ERROR = 'ERROR'; ACTION = 'ACTION'
          CHOICES = [...]
      class NotificationStatus:
          UNSENT = 'UNSENT'; SENT = 'SENT'; DELIVERED = 'DELIVERED'; READ = 'READ'; ACTIONED = 'ACTIONED'; ERROR = 'ERROR'
          CHOICES = [...]

      class Notification(Timestamped, Auditable, OrganizationScoped):
          # organization field from OrganizationScoped
          # created_by/updated_by from Auditable (often system/triggering user)
          # created_at/updated_at from Timestamped

          recipient = models.ForeignKey(
              settings.AUTH_USER_MODEL, verbose_name=_("Recipient"),
              on_delete=models.CASCADE, related_name='notifications', db_index=True
          )
          level = models.CharField(
              _("Level"), max_length=10, choices=NotificationLevel.CHOICES,
              default=NotificationLevel.INFO, db_index=True
          )
          title = models.CharField(_("Title"), max_length=255, blank=True)
          message = models.TextField(_("Message"))
          status = models.CharField(
              _("Status"), max_length=10, choices=NotificationStatus.CHOICES,
              default=NotificationStatus.UNSENT, db_index=True
          )
          read_at = models.DateTimeField(_("Read At"), null=True, blank=True)
          action_url = models.URLField(_("Action URL"), blank=True, max_length=1024)
          action_text = models.CharField(_("Action Text"), max_length=50, blank=True)

          # Generic link to originating object
          content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
          object_id = models.CharField(_("Object ID"), max_length=255, null=True, blank=True, db_index=True)
          content_object = GenericForeignKey('content_type', 'object_id')

          # For filtering and user preferences
          notification_type = models.CharField(
              _("Notification Type Code"), max_length=100, blank=True, db_index=True,
              help_text=_("Code identifying the event type (e.g., 'invoice_approved').")
          )

          class Meta:
              verbose_name = _("Notification")
              verbose_name_plural = _("Notifications")
              ordering = ['-created_at']
              indexes = [
                  models.Index(fields=['recipient', 'status']),
                  models.Index(fields=['recipient', 'read_at']),
                  models.Index(fields=['content_type', 'object_id']),
                  models.Index(fields=['notification_type']),
              ]

          def __str__(self):
              return self.title or f"Notification for {self.recipient_id}"

          def mark_as_read(self):
              if not self.read_at:
                  self.status = NotificationStatus.READ
                  self.read_at = timezone.now()
                  self.save(update_fields=['status', 'read_at', 'updated_at']) # Optimize save

          def mark_as_unread(self): # If needed
              if self.read_at:
                  self.status = NotificationStatus.DELIVERED # Or SENT?
                  self.read_at = None
                  self.save(update_fields=['status', 'read_at', 'updated_at'])
      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.3 Factory Definitions (`notifications/tests/factories.py`)

  [ ] Define `NotificationTemplateFactory` (if using templates) and `NotificationFactory`.
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from ..models import Notification, NotificationTemplate, NotificationLevel, NotificationStatus
      from api.v1.base_models.user.tests.factories import UserFactory
      from api.v1.base_models.organization.tests.factories import OrganizationFactory

      class NotificationTemplateFactory(DjangoModelFactory): ...

      class NotificationFactory(DjangoModelFactory):
          class Meta: model = Notification

          recipient = factory.SubFactory(UserFactory)
          organization = factory.LazyAttribute(lambda o: o.recipient.profile.primary_organization) # Needs profile link setup
          level = factory.Iterator([choice[0] for choice in NotificationLevel.CHOICES])
          title = factory.Faker('sentence', nb_words=4)
          message = factory.Faker('paragraph')
          status = NotificationStatus.SENT # Or UNSENT
          notification_type = factory.Sequence(lambda n: f'test_event_{n}')
          # Add content_object if needed for tests
      ```
  [ ] **(Test)** Write simple tests ensuring factories create valid instances.

  ### 3.4 Admin Registration (`notifications/admin.py`)

  [ ] Create `notifications/admin.py`. Register `NotificationTemplate` (if used) and `Notification`.
      ```python
      from django.contrib import admin
      from .models import Notification, NotificationTemplate

      @admin.register(NotificationTemplate)
      class NotificationTemplateAdmin(admin.ModelAdmin): ... # Basic setup

      @admin.register(Notification)
      class NotificationAdmin(admin.ModelAdmin):
          list_display = ('id', 'recipient', 'organization', 'level', 'title', 'notification_type', 'status', 'created_at')
          list_filter = ('status', 'level', 'notification_type', 'organization', 'created_at')
          search_fields = ('recipient__username', 'title', 'message', 'notification_type')
          list_select_related = ('recipient', 'organization')
          readonly_fields = [f.name for f in Notification._meta.fields if f.name != 'status'] # Allow changing status? Or only via API?
          # Make read_only usually, as they are system generated
          def has_add_permission(self, request): return False
          def has_change_permission(self, request, obj=None): return True # Allow status change?
          def has_delete_permission(self, request, obj=None): return True # Allow deletion?
      ```
  [ ] **(Manual Test):** Verify Admin interface.

  ### 3.5 Migrations

  [ ] Run `python manage.py makemigrations notifications`.
  [ ] **Review generated migration file(s) carefully.** Check FKs, indexes, choices.
  [ ] Run `python manage.py migrate` locally.
  [ ] Create data migration to populate initial `NotificationTemplate`s if needed. Run migrate again.

  ### 3.6 Notification Service/Function (`notifications/services.py`)

  [ ] **(Test First)** Write Unit Tests (`notifications/tests/unit/test_services.py`) for the `send_notification` function.
      *   Mock `Notification.objects.create`. Mock Celery `task.delay()`. Mock `UserProfile.notification_preferences`.
      *   Test case where user opted out -> assert nothing created/queued.
      *   Test case requesting 'in_app' -> assert `Notification.objects.create` called.
      *   Test case requesting 'email' -> assert `send_email_notification_task.delay` called with correct args.
      *   Test template rendering logic if applicable.
      Run; expect failure.
  [ ] Create `notifications/services.py`. Implement `send_notification` logic.
      ```python
      # notifications/services.py
      from django.template.loader import render_to_string
      from .models import Notification, NotificationTemplate, NotificationLevel, NotificationStatus
      from .tasks import send_email_notification_task # Import celery task

      def send_notification(recipient, notification_type, context=None,
                          level=NotificationLevel.INFO, title=None, message=None,
                          action_url=None, action_text=None,
                          content_object=None, organization=None,
                          channels=['in_app', 'email']):
          """
          Central function to create and dispatch notifications.
          Checks user preferences before sending.
          """
          if not recipient or not recipient.is_active: return
          context = context or {}

          # 1. Check User Preferences
          prefs = getattr(recipient, 'profile', {}).notification_preferences or {}
          type_prefs = prefs.get(notification_type, {'in_app': True, 'email': True}) # Default to True

          active_channels = [
              ch for ch in channels
              if type_prefs.get(ch, True) # Send if preference exists and is True, or if no preference set
          ]
          if not active_channels: return # User opted out of all requested channels

          # 2. Determine Organization context
          if not organization:
              organization = getattr(recipient, 'profile', None).primary_organization # Example lookup

          # 3. Prepare Content (Use defaults or Template)
          final_title = title
          final_message = message
          subject = None
          html_message = None

          # Try finding a template if message/title not provided directly
          template_key_base = f"{notification_type}"
          if not final_message:
               try:
                   template = NotificationTemplate.objects.get(template_key=template_key_base+"_email") # Or logic to find appropriate template
                   subject = render_to_string(None, template.subject_template, context).strip()
                   final_message = render_to_string(None, template.body_template_txt, context)
                   if template.body_template_html:
                       html_message = render_to_string(None, template.body_template_html, context)
                   if not final_title: final_title = subject # Use subject as title if needed
               except NotificationTemplate.DoesNotExist:
                    # Fallback or error if direct message also not provided
                    if not final_message: # Ensure we have content
                         import logging
                         logger = logging.getLogger(__name__)
                         logger.warning(f"No message or template found for notification type {notification_type}")
                         return

          # 4. Create In-App Notification
          notification_instance = None
          if 'in_app' in active_channels:
               try:
                   notification_instance = Notification.objects.create(
                       recipient=recipient,
                       organization=organization,
                       level=level,
                       title=final_title or '',
                       message=final_message,
                       status=NotificationStatus.DELIVERED, # Assume delivered if created
                       action_url=action_url or '',
                       action_text=action_text or '',
                       content_object=content_object,
                       notification_type=notification_type,
                       # created_by might be system or triggering user if passed in context
                   )
               except Exception as e: # Catch DB errors etc.
                   import logging; logging.getLogger(__name__).error(f"Failed to save in-app notification: {e}", exc_info=True)


          # 5. Queue External Notifications (Email)
          if 'email' in active_channels and recipient.email:
               # Queue Celery task
               send_email_notification_task.delay(
                   recipient_pk=recipient.pk,
                   subject=subject or final_title or "Notification", # Ensure subject exists
                   text_body=final_message,
                   html_body=html_message,
                   notification_pk=getattr(notification_instance, 'pk', None) # Pass PK to update status
               )

          # 6. Queue other channels (SMS, Push) later

          return notification_instance
      ```
  [ ] Run service tests; expect pass. Refactor.

  ### 3.7 Celery Task Definition (`notifications/tasks.py`)

  [ ] **(Test First)** Write Unit Tests (`notifications/tests/unit/test_tasks.py`) for `send_email_notification_task`. Mock Django's `send_mail` function and the `Notification.objects.get/save` calls. Verify `send_mail` is called with correct args. Verify `Notification` status is updated on success/failure.
  [ ] Create `notifications/tasks.py`. Define the Celery task:
      ```python
      # notifications/tasks.py
      from celery import shared_task
      from django.core.mail import send_mail
      from django.conf import settings
      from django.contrib.auth import get_user_model
      from .models import Notification, NotificationStatus
      import logging

      logger = logging.getLogger(__name__)
      User = get_user_model()

      @shared_task(bind=True, max_retries=3, default_retry_delay=60) # Example retry config
      def send_email_notification_task(self, recipient_pk, subject, text_body, html_body=None, notification_pk=None):
          """Sends an email notification asynchronously."""
          try:
              recipient = User.objects.get(pk=recipient_pk)
              if not recipient.email:
                  logger.warning(f"Recipient User {recipient_pk} has no email address.")
                  return # Or update notification status?

              send_mail(
                  subject=subject,
                  message=text_body,
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=[recipient.email],
                  html_message=html_body,
                  fail_silently=False, # Let Celery handle retries on failure
              )

              # Optionally update Notification status if PK provided
              if notification_pk:
                  try:
                      notification = Notification.objects.get(pk=notification_pk)
                      notification.status = NotificationStatus.SENT # Or DELIVERED? Depends on email provider feedback
                      notification.save(update_fields=['status', 'updated_at'])
                  except Notification.DoesNotExist:
                      logger.warning(f"Notification {notification_pk} not found to update status after email send.")

              logger.info(f"Email notification sent successfully to user {recipient_pk}.")

          except User.DoesNotExist:
              logger.error(f"Recipient User {recipient_pk} not found for email notification.")
              # No retry if user doesn't exist
          except Exception as exc:
              logger.error(f"Error sending email notification to user {recipient_pk}: {exc}", exc_info=True)
              # Update notification status to ERROR if possible
              if notification_pk:
                   try:
                      Notification.objects.filter(pk=notification_pk).update(status=NotificationStatus.ERROR)
                   except Exception: pass # Ignore secondary error
              # Retry based on Celery task decorator settings
              raise self.retry(exc=exc)

      ```
  [ ] Ensure Celery workers discover tasks from this file.
  [ ] Run task tests; expect pass. Refactor.

  ### 3.8 API ViewSet Definition (`api/v1/notifications/views.py`)

  [ ] **(Test First)** Write API Tests (`api/v1/notifications/tests/test_endpoints.py`) for:
      *   `GET /notifications/`: List user's own notifications, test pagination, test filtering by read/unread. Verify Org Scoping implicitly via user.
      *   `POST /notifications/{id}/mark-read/`: Test marking specific notification read, check status change. Test permissions (only owner).
      *   `POST /notifications/mark-all-read/`: Test marking all read.
  [ ] Create `api/v1/notifications/views.py`. Define `NotificationViewSet`.
      ```python
      # api/v1/notifications/views.py
      from rest_framework import viewsets, permissions, status, mixins
      from rest_framework.decorators import action
      from rest_framework.response import Response
      from notifications.models import Notification # Adjust import path
      from notifications.serializers import NotificationSerializer # Need a serializer

      class NotificationViewSet(mixins.ListModelMixin,
                              mixins.RetrieveModelMixin,
                              viewsets.GenericViewSet):
          """
          API endpoint for viewing and managing user's notifications.
          """
          serializer_class = NotificationSerializer
          permission_classes = [permissions.IsAuthenticated]
          # No filter backends needed if only filtering by recipient

          def get_queryset(self):
              """Only return notifications for the current authenticated user."""
              return Notification.objects.filter(
                  recipient=self.request.user
              ).select_related('organization') # Add other selects if needed by serializer

          @action(detail=True, methods=['post'], url_path='mark-read')
          def mark_read(self, request, pk=None):
              notification = self.get_object() # Gets notification filtered by user via get_queryset
              notification.mark_as_read()
              serializer = self.get_serializer(notification)
              return Response(serializer.data)

          @action(detail=False, methods=['post'], url_path='mark-all-read')
          def mark_all_read(self, request):
              updated_count = Notification.objects.filter(
                  recipient=request.user, status=NotificationStatus.DELIVERED # Or SENT?
              ).update(status=NotificationStatus.READ, read_at=timezone.now())
              return Response({'status': 'success', 'updated_count': updated_count})

      ```
  [ ] Create `NotificationSerializer`.
  [ ] Run API tests; expect pass. Refactor.

  ### 3.9 URL Routing (`api/v1/notifications/urls.py`)

  [ ] Create `api/v1/notifications/urls.py`. Import `NotificationViewSet`. Register with router.
  [ ] Include notification URLs in main `api/v1/urls.py`.
  [ ] **(Test):** Rerun basic API tests.

  ### 3.10 Trigger Integration

  [ ] **(Test First)** In integration tests for *other* features (e.g., Workflow transitions, Comment creation), add assertions verifying that the `send_notification` service (or Celery task) was called correctly.
  [ ] Integrate calls to `notifications.services.send_notification` at appropriate points in the codebase (signal receivers, workflow actions, views).
  [ ] Run tests; expect pass.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=notifications`).
[ ] Manually trigger events that should create notifications. Check in-app list via API. Check emails (using console/mailhog locally). Check Admin UI.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs (Robust change calculation for audit logs, dynamic signal connection, M2M auditing in Audit system if needed).
[ ] Refine user preferences model/API.
[ ] Implement other delivery channels (SMS, Push) as needed.
[ ] Create Pull Request.
[ ] Update API documentation.

--- END OF FILE notification_implementation_steps.md ---
### Video Meeting


# Video Meeting Integration - Implementation Steps

## 1. Overview

**Feature Name:**
Video Meeting Integration

**Corresponding PRD:**
`video_meeting_prd.md` (Simplified - Integration focus)

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `Organization`, `ContentType` (for GFKs), `FileStorage` (if downloading recordings), `Notification` System, Celery infrastructure, Secure way to store external API keys.

**Key Features:**
Integrates with a chosen third-party video conferencing provider. Implements ERP models (`Meeting`, `MeetingParticipant`) to store metadata. Provides APIs to schedule/manage meetings (proxying to provider). Handles webhooks for status updates and recording links.

**Primary Location(s):**
*   Models, Serializers, Views: `video_meetings/` (New dedicated app recommended)
*   API Client/Service: `video_meetings/services.py` or `core/integrations/`
*   Webhook View: `video_meetings/views.py`
*   Celery Tasks: `video_meetings/tasks.py` (for async API calls or recording downloads)
*   API URLs: `api/v1/meetings/` (New dedicated API structure)

## 2. Prerequisites

[ ] Verify all prerequisite models/mixins (`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `Organization`, `ContentType`, `FileStorage` - if downloading recordings) are implemented.
[ ] Verify Celery infrastructure is operational.
[ ] Verify Notification system is available.
[ ] **Select External Video Provider:** Choose the specific provider (e.g., Zoom, Daily.co, Vonage).
[ ] **Obtain Provider Credentials:** Get API Keys/Secrets/Credentials from the chosen provider's developer portal.
[ ] **Store Credentials Securely:** Configure environment variables or secrets manager for storing provider API keys (as per `security_strategy.md`).
[ ] **Create new Django app:** `python manage.py startapp video_meetings`.
[ ] Add `'video_meetings'` to `INSTALLED_APPS`.
[ ] Ensure `factory-boy` is set up. Factories for `User`, `Organization` exist.
[ ] Define `MeetingStatus` choices.

## 3. Implementation Steps (TDD Workflow)

  *(Models -> Provider Service -> API -> Webhooks)*

  ### 3.1 Core Model Definitions (`video_meetings/models.py`)

  [ ] **(Test First - Meeting)** Write Unit Tests (`tests/unit/test_models.py`) verifying `Meeting` creation, fields (topic, times, status, provider, provider_id, join_url, GFK, custom fields), defaults, inheritance, `__str__`.
  [ ] Define `Meeting` model. Inherit `Timestamped`, `Auditable`, `OrganizationScoped`. Include fields from PRD 3.1 (topic, times, status, host FK, provider, provider_id, join_url, GFK fields, `custom_fields`). Define `Meta`. Add `recording_links` (JSONField, default=list) if storing URLs (Option A). Add `recording_files` (M2M to FileStorage) if downloading (Option B).
  [ ] Run Meeting tests; expect pass. Refactor.
  [ ] **(Test First - Participant)** Write Unit Tests verifying `MeetingParticipant` creation, fields (meeting FK, user FK, role), `unique_together`, inheritance, `__str__`.
  [ ] Define `MeetingParticipant` model. Inherit `Timestamped`, `Auditable`, `OrganizationScoped`. Include fields from PRD 3.1 (meeting FK, user FK, role, join/leave times). Define `Meta`.
  [ ] Run Participant tests; expect pass. Refactor.

  ### 3.2 Factory Definitions (`video_meetings/tests/factories.py`)

  [ ] Define `MeetingFactory` and `MeetingParticipantFactory`. Handle FKs, GFKs (potentially passing a target object to MeetingFactory). Set default provider name.
  [ ] **(Test)** Write simple tests ensuring factories create valid instances.

  ### 3.3 Provider API Client/Service (`video_meetings/services.py`)

  [ ] **(Test First)** Write Unit Tests for the service functions. **Mock external HTTP requests** (using `requests-mock` or `unittest.mock.patch`).
      *   Test `create_provider_meeting(topic, start_time, ...)`: Verify it makes the correct API call (URL, method, headers, payload) to the *mocked* provider endpoint and returns expected data (provider ID, join URL). Test error handling for provider API failures.
      *   Test `update_provider_meeting(provider_meeting_id, ...)`: Verify correct mock API call.
      *   Test `cancel_provider_meeting(provider_meeting_id)`: Verify correct mock API call.
      *   Test functions for adding/removing participants via provider API if applicable.
  [ ] Create `video_meetings/services.py`. Implement functions that encapsulate calls to the chosen external provider's API using a library like `requests` or the provider's official SDK.
      *   Load API keys/secrets securely from settings/environment.
      *   Handle request formatting, authentication headers, and response parsing specific to the provider.
      *   Include error handling and logging for API calls.
  [ ] Run service tests; expect pass. Refactor.

  ### 3.4 Admin Registration (`video_meetings/admin.py`)

  [ ] Create `video_meetings/admin.py`.
  [ ] Define `MeetingParticipantInline`.
  [ ] Define `MeetingAdmin`. Make provider fields read-only. Add participant inline. Configure display/filters.
  [ ] Register models.
  [ ] **(Manual Test):** Verify basic viewing/metadata editing in Admin.

  ### 3.5 Migrations

  [ ] Run `python manage.py makemigrations video_meetings`.
  [ ] **Review generated migration file(s) carefully.** Check models, FKs, GFKs, indexes.
  [ ] Run `python manage.py migrate` locally.

  ### 3.6 Serializer Definition (`video_meetings/serializers.py`)

  [ ] **(Test First)** Write Unit/Integration Tests for `MeetingSerializer` and `MeetingParticipantSerializer`. Test representation, validation, `custom_fields`, read-only fields. Test nested participant representation (if needed).
  [ ] Define serializers. Handle read-only provider fields, GFK representation, `custom_fields`. Inherit `FieldPermissionSerializerMixin` if needed.
  [ ] Implement `validate_custom_fields` if applicable.
  [ ] Run tests; expect pass. Refactor.

  ### 3.7 API ViewSet Definition (`video_meetings/views.py`)

  [ ] **(Test First)** Write basic API Tests checking `/api/v1/meetings/` URL, authentication, Org Scoping, basic permissions.
  [ ] Define `MeetingViewSet` in `video_meetings/views.py`. Inherit `OrganizationScopedViewSetMixin`, `viewsets.ModelViewSet`.
  [ ] Implement `perform_create`:
      1.  Call `create_provider_meeting` service function.
      2.  Save `Meeting` instance with provider data.
      3.  Create `MeetingParticipant` records for host and initial invitees.
      4.  **(Async)** Queue notification task for invites.
  [ ] Implement `perform_update`: Call `update_provider_meeting` service. Save local changes.
  [ ] Implement `perform_destroy`: Call `cancel_provider_meeting` service. Update local status to `CANCELLED` (or delete).
  [ ] Override `get_queryset` to filter meetings accessible to the user (hosted or participant). Apply `select/prefetch_related`.
  [ ] Add filtering/search/ordering backends.
  [ ] Secure endpoints with appropriate permissions (`IsAuthenticated` + custom permission checks).
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.8 Webhook Handler View (`video_meetings/views.py`)

  [ ] **(Test First)** Write Integration Tests for the webhook endpoint (`POST /api/v1/webhooks/video-provider/`).
      *   **Requires mocking request signature verification.**
      *   Send mock payloads simulating `meeting.started`, `meeting.ended`, `participant.joined`, `participant.left`, `recording.completed` events.
      *   Verify the handler correctly identifies the `Meeting` via `provider_meeting_id`.
      *   Verify `Meeting` status and `actual_start/end_time` are updated.
      *   Verify `MeetingParticipant` join/leave times are updated.
      *   Verify recording links/files are processed correctly (check `Meeting.recording_links` or queued Celery task for download).
      *   Test invalid signatures/payloads -> Assert appropriate error response (e.g., 400, 403).
      Run; expect failure.
  [ ] Create a new Django View (e.g., `VideoProviderWebhookView(APIView)`) for handling incoming webhooks.
  [ ] Implement webhook signature verification specific to the provider.
  [ ] Implement logic within the `post` method to parse the payload, identify the event type, find the corresponding `Meeting`/`Participant`, and update records accordingly.
  [ ] For potentially slow operations (like recording downloads - Option B), queue a Celery task from the webhook handler.
  [ ] Return appropriate HTTP status codes (e.g., 200 OK on success, 400 on bad payload, 403 on bad signature).
  [ ] Run webhook tests; expect pass. Refactor.

  ### 3.9 URL Routing (`video_meetings/urls.py` & `api/v1/urls.py`)

  [ ] Create `api/v1/video_meetings/urls.py`. Import `MeetingViewSet`. Register with router: `router.register(r'meetings', views.MeetingViewSet)`.
  [ ] Define URL pattern for the webhook handler view. Ensure this URL is *not* included in standard API auth/prefixing if the provider requires a simple public endpoint (security handled by signature).
  [ ] Include `video_meetings.urls` in main `api/v1/urls.py`.
  [ ] **(Test):** Rerun basic API tests; expect 2xx/4xx codes.

  ### 3.10 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests for `MeetingViewSet` CRUD operations (List, Create, Retrieve, Update, Delete/Cancel).
      *   **Mock the provider service calls** (`create_provider_meeting`, etc.) to avoid external dependencies. Verify the service functions are called with correct arguments.
      *   Verify local `Meeting` and `MeetingParticipant` records are created/updated correctly.
      *   Verify responses match the API spec.
      *   Test permissions and Org Scoping rigorously.
      *   Test filtering/pagination on LIST endpoint.
      *   Test saving/validating `custom_fields`.
  [ ] Implement/Refine ViewSet methods and Serializer logic.
  [ ] Run all API tests; expect pass. Refactor.

  ### 3.11 Recording Download Task (Optional - If using Option B)

  [ ] **(Test First)** Write Unit Tests for Celery task `download_meeting_recording`. Mock `FileStorage` save and external download call.
  [ ] Implement Celery task `download_meeting_recording(meeting_id, recording_url)`. Fetches recording, saves using `FileStorage`, links `FileStorage` object to `Meeting.recording_files` M2M. Handles errors.
  [ ] Ensure webhook handler queues this task.
  [ ] Run tests; expect pass.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`), ensuring external services are mocked appropriately.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=video_meetings`).
[ ] Manually test the end-to-end flow in staging with the *actual* video provider: Schedule via API/UI -> Join Meeting -> Record -> End Meeting -> Verify webhook updates status and recording link/file appears.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs (Refine error handling, implement optional calendar sync).
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Securely deploy webhook endpoint and configure provider settings.

--- END OF FILE videomeeting_implementation_steps.md ---
## Document Management


### Document System


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
### File Storage

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
### Export/Import



# Data Import/Export Framework - Implementation Steps

## 1. Overview

**Framework Name:**
Data Import/Export Framework

**Corresponding PRD:**
`export_import_framework_prd.md` (Final Refined v2)

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `Organization`, `FileStorage`, `ContentType`, Celery infrastructure (Workers + Beat), Redis (Broker), `django-import-export`, `tablib[xlsx]`, Advanced Filtering System (parser + backend). PDF generation library required later.

**Key Features:**
Establishes framework for async import (CSV/XLSX) & export (CSV/XLSX/PDF). Uses `DataJob` model for tracking. Leverages Advanced Filtering for export datasets. Provides a generic resource factory as fallback for basic cases, uses custom `ModelResource` for specifics. Handles row errors and unmapped column warnings during import.

**Primary Location(s):**
*   Models (`DataJob`): `data_jobs/models.py` (New app).
*   Celery Tasks: `data_jobs/tasks.py`.
*   Generic Resource Factory: `core/import_export_utils.py` (Example).
*   Custom Resources (`ModelResource`): In relevant feature app (e.g., `api/v1/features/products/resources.py`).
*   API Views/URLs: `/api/v1/data-jobs/` (in `data_jobs`), plus actions in specific model ViewSets.

## 2. Prerequisites

[ ] Verify all prerequisite models/mixins and systems (Celery, Redis, FileStorage, Advanced Filtering parser) are implemented/configured.
[ ] **Install Libraries:** `pip install django-import-export tablib[xlsx]`.
[ ] **Create new Django app:** `python manage.py startapp data_jobs`.
[ ] Add `'import_export'` and `'data_jobs'` to `INSTALLED_APPS`.
[ ] Ensure `factory-boy` setup. Factories for core models exist.
[ ] Define `JobType` and `JobStatus` choices (e.g., in `data_jobs/choices.py`).

## 3. Implementation Steps (TDD Workflow)

  *(Job Model -> Generic Resource Factory -> Celery Tasks -> API Integration -> Custom Resources)*

  ### 3.1 `DataJob` Model Definition (`data_jobs/models.py`)

  [ ] **(Test First)** Write Unit Tests (`data_jobs/tests/unit/test_models.py`) verifying: `DataJob` creation, fields (type, status, FKs, GFK target, JSON params/log, task ID), defaults, inheritance, `__str__`.
  [ ] Define the `DataJob` class in `data_jobs/models.py`. Inherit `Timestamped`, `Auditable`, `OrganizationScoped`. Include fields from PRD 3.4.
  [ ] Run tests; expect pass. Refactor.

  ### 3.2 Factory Definition (`data_jobs/tests/factories.py`)

  [ ] Define `DataJobFactory` in `data_jobs/tests/factories.py`. Handle FKs.
  [ ] **(Test)** Write simple tests ensuring factory creates valid instances.

  ### 3.3 Generic Resource Factory Utility (`core/import_export_utils.py`)

  [ ] **(Test First)** Write Unit Tests (`core/tests/unit/test_import_export_utils.py`) for `get_resource_class_for_model`:
      *   Test finding a *custom* resource defined in `app.resources`.
      *   Test generating a *generic* resource when no custom one exists.
      *   Test generic resource includes expected direct fields (and excludes relations/sensitive fields).
      *   Test generic resource handles basic FK ID import/export (optional).
      *   Test generic resource sets basic `Meta` options (`model`, `import_id_fields=['id']`).
      Run; expect failure.
  [ ] Create `core/import_export_utils.py`. Implement `get_resource_class_for_model(model_class)`:
      *   Use `importlib` or convention to look for `app_label.resources.ModelNameResource`.
      *   If found, return it.
      *   If not found, use introspection (`model_class._meta.get_fields()`) to identify simple, direct, non-sensitive fields and direct `_id` FK fields.
      *   Dynamically create a `ModelResource` subclass (`type(...)`) in memory using these fields and basic `Meta` options. Handle potential naming collisions.
      *   Return the dynamically created class.
  [ ] Run tests; expect pass. Refactor.

  ### 3.4 Celery Task Definitions (`data_jobs/tasks.py`)

  [ ] **(Test First - Export)** Write Unit Tests (`data_jobs/tests/unit/test_tasks.py`) for `run_export_job`.
      *   Mock `DataJob.objects.get/save`, `FileStorage.objects.create`/`file.save`, `get_resource_class_for_model`, the resource's `export()` method, the **Advanced Filtering parser**, PDF generator calls.
      *   Test finding/using custom vs generic resource.
      *   Test parsing filter params -> applying Q object to queryset mock.
      *   Test calling resource `export()` with filtered queryset.
      *   Test handling CSV/XLSX output via resource dataset.
      *   Test placeholder/call for PDF generation logic.
      *   Test saving output file to mock storage.
      *   Test `DataJob` status updates (RUNNING, COMPLETED, FAILED) and `output_file`/`result_log` population. Test error handling.
      Run; expect failure.
  [ ] Create `data_jobs/tasks.py`. Define `run_export_job(job_id)` Celery task:
      *   Fetch `DataJob`. Set status to RUNNING.
      *   Get `model_class` from `target_model_content_type`.
      *   Parse `input_params['filters']` using Advanced Filtering parser -> `q_object`.
      *   Build initial `queryset` for the model, apply org scope, apply `q_object`. Add relevant `select/prefetch_related`.
      *   Call `get_resource_class_for_model` to get the resource class. Instantiate `resource`.
      *   If `export_format` is CSV/XLSX: call `resource.export(queryset)`, get data bytes, get content type.
      *   If `export_format` is PDF: Call specific PDF generator function `generate_pdf(queryset, job.input_params)`, get data bytes, set content type. *(Implement generator later)*.
      *   Create `FileStorage` instance, save `ContentFile` with data bytes, link to `job.output_file`.
      *   Update `DataJob` to COMPLETED with result summary.
      *   Use `try...except...finally` to catch errors, update `DataJob` to FAILED with error message in `result_log`.
  [ ] Run export task tests; expect pass. Refactor.
  [ ] **(Test First - Import)** Write Unit Tests for `run_import_job`.
      *   Mock `DataJob`, `FileStorage` (`input_file.file.read`), `get_resource_class_for_model`, resource `import_data()`, Celery retries.
      *   Test finding/using custom vs generic resource.
      *   Test calling `resource.import_data()` (mock its return `Result` object with various totals/errors/skipped rows).
      *   Test processing the `Result` object to populate `DataJob.result_log` correctly, including row errors and **unmapped column warnings**.
      *   Test `DataJob` status updates (RUNNING, COMPLETED, FAILED). Test error handling.
      Run; expect failure.
  [ ] Define `run_import_job(job_id)` Celery task:
      *   Fetch `DataJob`. Set status to RUNNING.
      *   Get `input_file` content. Determine format (CSV/XLSX).
      *   Call `get_resource_class_for_model`. Instantiate `resource`.
      *   Load data into `tablib.Dataset`.
      *   **(Optional)** Check for unmapped headers by comparing `dataset.headers` with `resource.get_export_headers()` or resource fields; store warnings.
      *   Call `resource.import_data(dataset, dry_run=False, ...)`.
      *   Process `import_result` object: extract totals, row errors. Format into `job.result_log`. Add unmapped header warnings to log.
      *   Set `DataJob` status based on `import_result.has_errors()`.
      *   Use `try...except...finally` for robust error handling.
  [ ] Run import task tests; expect pass. Refactor.

  ### 3.5 Admin Registration (`data_jobs/admin.py`)

  [ ] Create `data_jobs/admin.py`. Define `DataJobAdmin`. Make fields read-only, provide links to files/related objects, display status nicely.
  [ ] **(Manual Test):** Verify Admin interface for monitoring jobs.

  ### 3.6 Migrations

  [ ] Run `python manage.py makemigrations data_jobs`.
  [ ] **Review generated migration file carefully.** Check `DataJob` model, FKs, indexes.
  [ ] Run `python manage.py migrate` locally.

  ### 3.7 API Integration (Views, Serializers, URLs)

  [ ] **(Test First - Job Status API)** Write API tests for `/api/v1/data-jobs/` (LIST) and `/api/v1/data-jobs/{id}/` (RETRIEVE). Test filtering by user (implicit), status, type. Test permissions (user sees own jobs). Verify `output_file` link/URL generation (requires `FileStorage` serializer/logic). Verify `result_log` structure.
  [ ] Define `DataJobSerializer` (read-only) in `data_jobs/serializers.py`. Include method field for `output_file_url`.
  [ ] Define `DataJobViewSet` (ReadOnlyModelViewSet) in `data_jobs/views.py`. Filter queryset by `request.user`. Add standard filtering. Apply permissions.
  [ ] Define URL routing for `DataJobViewSet`.
  [ ] Run job status API tests; expect pass. Refactor.
  [ ] **(Test First - Trigger APIs)** Write API tests for `@action` endpoints on model ViewSets (e.g., `POST /products/export/`, `POST /products/import/`).
      *   Mock Celery `task.delay()`.
      *   Test successful request -> Assert 202 Accepted, check response body has `job_id`. Verify `DataJob` created correctly in DB. Verify task queued with correct `job_id`. Test passing filters (export) or file upload (import).
      *   Test permission failures (user lacks `can_export_model` / `can_import_model`). Test validation errors (invalid format, missing file).
  [ ] Add `@action` methods (`export_data`, `import_data`) to relevant model ViewSets (e.g., `ProductViewSet`). Logic: Check permissions, create `DataJob`, queue Celery task, return 202 response. Parse filters from request for export params. Handle file upload for import params.
  [ ] Run trigger API tests; expect pass. Refactor action views.

  ### 3.8 Model Resource Implementation (`resources.py`)

  [ ] **(Optional - Initially)** Implement *custom* `ModelResource` subclasses (e.g., `ProductResource`) only for models identified as needing complex import/export logic immediately. Test these resources thoroughly.
  [ ] **(Ongoing)** Implement custom `ModelResource` classes incrementally as needed for other models.

  ### 3.9 PDF Generation Logic (Deferred)

  [ ] Implement specific PDF generation functions/classes when required.
  [ ] Update `run_export_job` task to call the correct generator. Add tests.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`), ensuring Celery tasks run eagerly or are correctly mocked. Test with both generic and custom resources (if any).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=data_jobs --cov=core/import_export_utils`). Review uncovered areas.
[ ] Manually test end-to-end: Trigger export (CSV/XLSX) with filters via API -> check job status -> download file. Upload CSV/XLSX -> trigger import -> check job status -> check `result_log` for successes, errors, warnings -> verify data in DB.
[ ] Review API documentation draft for job management and trigger endpoints.

## 5. Follow-up Actions

[ ] Address TODOs (PDF implementation, robust error details in result_log, advanced resource features).
[ ] Create Pull Request(s).
[ ] Update API documentation.
[ ] Implement custom `ModelResource` classes for key models as needed.

--- END OF FILE exportimport_implementation_steps.md ---
## System Features


### Search


# Search System Integration - Implementation Steps

## 1. Overview

**Feature Name:**
Search System Integration

**Corresponding PRD:**
`search_prd.md` (Simplified - Integration focus)

**Depends On:**
Target models to be indexed (e.g., `Product`, `Organization`, `Contact`, `Document`), Celery infrastructure, Search Engine instance (Elasticsearch/OpenSearch), `django-elasticsearch-dsl` library, `elasticsearch-dsl` library.

**Key Features:**
Integrates the ERP with Elasticsearch/OpenSearch. Defines indexed documents based on Django models. Implements automatic index updates via signals/Celery. Provides a core Search API endpoint with basic filtering and permission-based result trimming.

**Primary Location(s):**
*   Search Engine Infrastructure: External (needs deployment/management).
*   Library Installation: `requirements/*.txt`, `settings.py`.
*   Index Definitions (`documents.py`): Within each app containing indexed models (e.g., `api/v1/features/products/documents.py`).
*   Signal Handlers (`signals.py`): Within each app containing indexed models OR a central location.
*   Celery Tasks (`tasks.py`): For async indexing (e.g., `core/tasks.py` or per-app).
*   Management Commands: `core/management/commands/` (for bulk indexing).
*   API View/Serializer/URL: Dedicated `search` app (`api/v1/search/`) or within `core`/`common`. Assume **new `search` app**.

## 2. Prerequisites

[ ] **Set up Search Engine:** Deploy and configure Elasticsearch or OpenSearch instance accessible from the Django application. Note connection URL(s) and any necessary credentials.
[ ] **Install Libraries:** `pip install django-elasticsearch-dsl elasticsearch-dsl elasticsearch` (or `opensearch-py opensearch-dsl`).
[ ] **Configure Connection:** Define search engine connection details in `config/settings/base.py` (loaded from environment variables):
    ```python
    # config/settings/base.py
    ELASTICSEARCH_DSL = {
        'default': {
            'hosts': env('ELASTICSEARCH_HOSTS', default='localhost:9200'), # Comma-separated for cluster
            # Add http_auth, use_ssl, ca_certs etc. if needed
            # 'http_auth': (env('ELASTICSEARCH_USER', default=None), env('ELASTICSEARCH_PASSWORD', default=None)),
        },
    }
    # Optional: django-elasticsearch-dsl specific settings
    # ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = 'django_elasticsearch_dsl.signals.RealTimeSignalProcessor' # Sync (default)
    ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = 'core.search.signals.CelerySignalProcessor' # If using async via Celery (custom class needed)
    ```
[ ] Ensure Celery infrastructure is operational (for async indexing).
[ ] Verify target models to be indexed exist and are migrated.
[ ] **Create new Django app:** `python manage.py startapp search`.
[ ] Add `'django_elasticsearch_dsl'` and `'search'` to `INSTALLED_APPS`.
[ ] Ensure `factory-boy` is set up. Factories for indexed models exist.

## 3. Implementation Steps (TDD Workflow)

  *(Index Definitions -> Indexing Logic -> API Endpoint)*

  ### 3.1 Index/Document Definitions (`documents.py`)

  [ ] **(Test First - Document Structure)** Write **Unit Test(s)** (`tests/unit/test_documents.py` in relevant app, e.g., `products`) verifying:
      *   The `ProductDocument` (doesn't exist yet) defines the correct index name.
      *   It includes the expected fields (`name`, `sku`, `description`, `tags`, `organization_id`).
      *   Fields have appropriate ES types (`Text`, `Keyword`, `Object`, `Integer`).
      *   The `prepare_tags` method (if needed) formats tags correctly.
      *   The `get_queryset` method returns active products.
      Run; expect failure.
  [ ] Create `documents.py` file within each app containing models to be indexed (e.g., `api/v1/features/products/documents.py`).
  [ ] Define `Document` classes inheriting from `django_elasticsearch_dsl.Document`.
      ```python
      # api/v1/features/products/documents.py
      from django_elasticsearch_dsl import Document, fields
      from django_elasticsearch_dsl.registries import registry
      from ..models import Product # Import the Django model

      @registry.register_document
      class ProductDocument(Document):
          # Include fields needed for searching AND filtering/displaying results
          organization_id = fields.IntegerField() # For filtering results by org
          category_slug = fields.KeywordField(attr='category.slug') # Example related field
          tags = fields.KeywordField() # Store tag names as keywords

          class Index:
              # Name of the Elasticsearch index
              name = 'products'
              # See Elasticsearch Indices API reference for available settings
              settings = {'number_of_shards': 1,
                          'number_of_replicas': 0}

          class Django:
              model = Product # The model associated with this Document

              # The fields of the model you want to be indexed in Elasticsearch
              fields = [
                  'name',
                  'sku',
                  'description',
                  'status', # Often keyword for filtering
                  'product_type', # Often keyword
                  'created_at', # Date field
              ]
              # Ignore auto updating of Elasticsearch when a model is saved
              # or deleted:
              # ignore_signals = True
              # Don't perform an index refresh after every update (sync setting):
              # auto_refresh = False
              # Paginate the django queryset used to populate the index with the specified size
              # (by default it uses the database driver's default setting)
              # queryset_pagination = 5000

          def prepare_tags(self, instance):
              # Convert M2M tags to list of names for indexing
              return [tag.name for tag in instance.tags.all()]

          def get_queryset(self):
              """Prevent indexing inactive products."""
              # Optimize with select/prefetch related needed for prepare methods
              return super().get_queryset().select_related('category').prefetch_related('tags').filter(is_active=True) # Example filter

          # Add prepare_organization_id if needed (if source field isn't simple FK)
          def prepare_organization_id(self, instance):
               return instance.organization_id

      ```
  [ ] Repeat for other models (`Organization`, `Contact`, `Document` etc.) in their respective app's `documents.py`.
  [ ] Run document structure tests; expect pass. Refactor.

  ### 3.2 Indexing Pipeline (Signals & Tasks)

  [ ] **(Test First - Signals/Tasks)** Write **Integration Test(s)** (`core/tests/integration/test_search_signals.py` or similar) using `@pytest.mark.django_db`.
      *   Mock the Celery task queue (`mocker.patch('core.search.tasks.update_search_index_task.delay')`).
      *   Create/Save/Delete an instance of an indexed model (e.g., `Product`).
      *   Assert that the `update_search_index_task.delay` mock was called with the correct model info (app_label, model_name, pk).
      *   Write Unit tests for the Celery task `update_search_index_task`. Mock the `django_elasticsearch_dsl` `update()` method. Verify it's called correctly for create/update/delete actions.
      Run; expect failure.
  [ ] **Option A (Sync - Default `django-elasticsearch-dsl`):** If using the default `RealTimeSignalProcessor`, signals are connected automatically. Skip defining custom signals/tasks for basic sync.
  [ ] **Option B (Async - Recommended):**
      1.  Create a custom signal processor (e.g., in `core/search/signals.py`):
          ```python
          # core/search/signals.py
          from django_elasticsearch_dsl.signals import BaseSignalProcessor
          from .tasks import update_search_index_task # Import Celery task

          class CelerySignalProcessor(BaseSignalProcessor):
              def handle_save(self, sender, instance, **kwargs):
                  # Queue task on save/update
                  update_search_index_task.delay(
                      sender._meta.app_label, sender._meta.model_name, instance.pk
                  )

              def handle_delete(self, sender, instance, **kwargs):
                  # Queue task on delete
                  update_search_index_task.delay(
                      sender._meta.app_label, sender._meta.model_name, instance.pk, action='delete'
                  )

              # Optional: Handle M2M changes if needed for indexing
              # def handle_m2m_changed(self, sender, instance, action, pk_set, **kwargs): ...
          ```
      2.  Configure settings to use it: `ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = 'core.search.signals.CelerySignalProcessor'`
      3.  Create the Celery task (`core/tasks.py` or `search/tasks.py`):
          ```python
          # core/tasks.py
          from celery import shared_task
          from django.apps import apps
          from django_elasticsearch_dsl.registries import registry
          import logging

          logger = logging.getLogger(__name__)

          @shared_task(bind=True, max_retries=3, default_retry_delay=30)
          def update_search_index_task(self, app_label, model_name, pk, action='index'):
              """Updates Elasticsearch index for a given model instance."""
              try:
                  model = apps.get_model(app_label, model_name)
                  instance = model._default_manager.get(pk=pk)

                  if action == 'index':
                      logger.info(f"Indexing {model_name} {pk}")
                      registry.update(instance)
                      registry.update_related(instance) # Update related docs if needed
                  elif action == 'delete':
                      logger.info(f"Deleting {model_name} {pk} from index")
                      registry.delete(instance, raise_on_error=False) # Don't fail task if already deleted

              except model.DoesNotExist:
                   # Object might have been deleted between signal and task execution
                   if action == 'index': # If update/create fails because it's gone, try deleting from index
                       try:
                           logger.warning(f"Object {app_label}.{model_name} {pk} not found for indexing, attempting delete from index.")
                           # Create a dummy instance with just PK for deletion signal processing
                           dummy_instance = model(pk=pk)
                           registry.delete(dummy_instance, raise_on_error=False)
                       except Exception as e:
                           logger.error(f"Error deleting non-existent object {pk} from index: {e}", exc_info=True)
                   else: # If delete fails because it's already gone, that's fine
                       logger.info(f"Object {app_label}.{model_name} {pk} not found for deletion from index (likely already deleted).")

              except Exception as exc:
                   logger.error(f"Error updating search index for {app_label}.{model_name} {pk}: {exc}", exc_info=True)
                   raise self.retry(exc=exc)

          ```
  [ ] Run signal/task tests; expect pass. Refactor.

  ### 3.3 Management Commands (Bulk Indexing)

  [ ] **(Test First)** Write tests for management commands (requires careful setup/mocking or integration test with ES). Test `populate` and `rebuild` commands.
  [ ] Create management commands (e.g., `core/management/commands/search_index.py`):
      ```python
      # core/management/commands/search_index.py
      from django.core.management.base import BaseCommand
      from django_elasticsearch_dsl.management.commands import search_index

      class Command(search_index.Command):
          help = 'Custom wrapper for Elasticsearch index management provided by django-elasticsearch-dsl'
          # Inherits create, delete, populate options from base command
          # Add custom logic or arguments if needed
      ```
  [ ] **(Manual Test)** Run `python manage.py search_index --populate -f` locally against test ES instance. Verify data appears in index using Kibana/Cerebro or ES API calls. Run `search_index --delete -f` and `search_index --create`.

  ### 3.4 Search API View/Serializer/URL (`search/`)

  [ ] **(Test First)** Write **API Test(s)** (`search/tests/api/test_endpoints.py`):
      *   Test `GET /api/v1/search/?q=...` with various query terms.
      *   Mock the search engine call initially. Verify the view constructs the correct ES Query DSL based on `q` and filters (`type`, `organization_id`, `status`).
      *   Later, integration test against a test ES instance: Seed index with data, perform search via API, verify results from mock ES match expected structure (title, snippet, score, link).
      *   **Crucially**, test the **security post-filtering**: Mock ES returning results for OrgA and OrgB. Make API call as UserA (in OrgA). Verify final API response *only* contains OrgA results. Test with superuser -> should see both.
      *   Test pagination in search results.
      *   Test error handling for invalid queries or ES connection issues.
      Run; expect failure.
  [ ] Create `search/serializers.py` (for formatting results):
      ```python
      # search/serializers.py
      from rest_framework import serializers

      class SearchResultSerializer(serializers.Serializer):
          # Represents one item in the search results list
          app_label = serializers.CharField()
          model_name = serializers.CharField()
          pk = serializers.CharField() # Use CharField for UUIDs etc.
          score = serializers.FloatField()
          title = serializers.CharField() # Primary display field
          snippet = serializers.CharField(allow_null=True) # Highlighted excerpt
          # Add other fields needed for display (e.g., timestamp, status)
          detail_url = serializers.CharField(allow_null=True) # Link to object's API detail view
      ```
  [ ] Create `search/views.py` with `SearchView(APIView)`:
      ```python
      # search/views.py
      from rest_framework.views import APIView
      from rest_framework.response import Response
      from rest_framework import permissions
      from rest_framework.exceptions import ParseError
      from django.conf import settings
      from django.apps import apps
      from django.urls import reverse
      from elasticsearch_dsl import Search, Q as ES_Q
      from elasticsearch_dsl.connections import connections
      from elasticsearch import ElasticsearchException
      from .serializers import SearchResultSerializer
      # Assuming base viewset mixin has logic or we get org from user
      # from core.views import OrganizationScopedViewSetMixin

      class SearchView(APIView):
          permission_classes = [permissions.IsAuthenticated] # Must be logged in

          def get(self, request, *args, **kwargs):
              query_term = request.query_params.get('q', '').strip()
              if not query_term:
                   return Response({"results": [], "count": 0})

              # --- Build Elasticsearch Query ---
              # Get default ES connection
              es = connections.get_connection()
              # Base search across relevant indices (e.g., products, organizations...)
              # Improve this: get index names dynamically or from settings
              s = Search(using=es, index=['products', 'organizations', 'contacts']) # TODO: Dynamic index list

              # Apply core query (e.g., multi_match across common text fields)
              # TODO: Define searchable fields per index/model more robustly
              search_fields = ["name", "description", "code", "sku", "tags", "first_name", "last_name"]
              q_query = ES_Q("multi_match", query=query_term, fields=search_fields, fuzziness="AUTO")
              s = s.query(q_query)

              # Apply Filters from query params
              filter_clauses = []
              allowed_types = request.query_params.getlist('type') # e.g., ?type=product&type=organization
              if allowed_types:
                    # Need mapping from 'product' string to index name 'products'
                    # filter_clauses.append(ES_Q('terms', _index=mapped_allowed_types)) # Filter by index
                    filter_clauses.append(ES_Q('terms', model_type_field=allowed_types)) # If using dedicated field

              # Apply Org Scoping (Crucial for pre-filtering if possible)
              user = request.user
              if not user.is_superuser:
                    user_orgs = user.get_organizations() # Assumes this exists
                    org_ids = [org.pk for org in user_orgs]
                    if not org_ids: return Response({"results": [], "count": 0}) # No access
                    # Assumes 'organization_id' field exists in ALL indexed documents
                    filter_clauses.append(ES_Q('terms', organization_id=org_ids))

              status_filter = request.query_params.get('status')
              if status_filter:
                   filter_clauses.append(ES_Q('term', status=status_filter)) # Assumes 'status' is keyword field

              date_after = request.query_params.get('created_after')
              # TODO: Add date range filters if needed (requires parsing, 'created_at' field in index)

              if filter_clauses:
                  s = s.filter(ES_Q('bool', must=filter_clauses))

              # Add Highlighting (optional)
              s = s.highlight('name', 'description', number_of_fragments=1, fragment_size=100) # Example

              # Add Sorting (e.g., by relevance score `_score` (default) or date)
              # s = s.sort('-created_at')

              # Pagination (Use ES pagination from/size)
              # TODO: Integrate with DRF pagination class? Or handle manually.
              try:
                   page_num = int(request.query_params.get('page', 1))
                   page_size = int(request.query_params.get('page_size', 20))
                   start = (page_num - 1) * page_size
                   end = start + page_size
                   s = s[start:end]
              except ValueError:
                   raise ParseError("Invalid pagination parameters.")

              # --- Execute Search ---
              try:
                  response = s.execute()
                  total_hits = response.hits.total.value
              except ElasticsearchException as e:
                  # Log error, return 500 or appropriate error
                  import logging
                  logging.getLogger(__name__).error(f"Elasticsearch query failed: {e}", exc_info=True)
                  return Response({"errors": [{"detail": "Search service unavailable."}]}, status=503)

              # --- Process Results & Post-Filter Security ---
              results_data = []
              object_ids_by_type = {} # { 'app_label.modelname': [pk1, pk2], ... }

              for hit in response.hits:
                  app_label, model_name = hit.meta.index.split('_')[-1].split('-') # Simple split, needs robust mapping
                  pk = hit.meta.id
                  model_key = f"{app_label}.{model_name}"
                  if model_key not in object_ids_by_type: object_ids_by_type[model_key] = []
                  object_ids_by_type[model_key].append(pk)
                  # Store temporary data needed for serializer
                  results_data.append({
                       'app_label': app_label, 'model_name': model_name, 'pk': pk,
                       'score': hit.meta.score,
                       'title': getattr(hit, 'name', getattr(hit, 'title', hit.meta.id)), # Get display title
                       'snippet': ' '.join(hit.meta.highlight.description) if hasattr(hit.meta, 'highlight') and 'description' in hit.meta.highlight else None # Example snippet
                  })

              # ** CRUCIAL: Post-filter based on DB permissions **
              allowed_objects = {} # { 'app_label.modelname': {pk1, pk2}, ... }
              for model_key, pks in object_ids_by_type.items():
                   try:
                        Model = apps.get_model(model_key)
                        # Apply Org Scoping and View Permissions from DB query
                        # This query MUST be efficient (uses __in lookup)
                        allowed_pks = set(Model.objects.filter(
                            pk__in=pks,
                            # Add Org Scoping filter based on user orgs HERE
                            # Add permission checks if needed (e.g., using django-guardian querysets)
                        ).values_list('pk', flat=True))
                        allowed_objects[model_key] = allowed_pks
                   except LookupError:
                        continue # Model not found

              # Filter results based on allowed objects
              final_results = []
              for res in results_data:
                   model_key = f"{res['app_label']}.{res['model_name']}"
                   if res['pk'] in allowed_objects.get(model_key, set()):
                        # Add detail URL (example)
                        try:
                            res['detail_url'] = request.build_absolute_uri(
                                reverse(f"v1:{res['app_label']}:{res['model_name']}-detail", args=[res['pk']]) # Needs URL names setup
                            )
                        except Exception:
                            res['detail_url'] = None
                        final_results.append(res)

              # Serialize results
              serializer = SearchResultSerializer(final_results, many=True)
              # TODO: Build proper paginated response structure matching DRF default
              return Response({
                  "count": total_hits, # Note: this is total found by ES, might be > len(serializer.data) after permission filter
                  "results": serializer.data
              })
      ```
  [ ] Run tests; expect pass. Refactor (especially query building, permission filtering, result formatting, pagination).

  ### 3.9 URL Routing (`search/urls.py` & `api/v1/urls.py`)

  [ ] Create `api/v1/search/urls.py`. Define URL pattern for `SearchView`.
  [ ] Include search URLs in main `api/v1/urls.py`.
  [ ] **(Test):** Rerun basic API tests.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`), mocking ES or using a test ES instance.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=search`). Ensure index/signal/task/view logic covered.
[ ] Manually test search via API client: various queries, filters, check results, check permissions by logging in as different users. Check indexing updates after model changes.
[ ] Review API documentation draft for the search endpoint.

## 5. Follow-up Actions

[ ] Address TODOs (Dynamic index list, robust searchable fields definition, robust permission post-filtering integration, document content indexing if needed, advanced search features).
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Set up Search Engine cluster and indexing pipeline in deployment environments.

--- END OF FILE search_implementation_steps.md ---
### Filtering


# Advanced Filtering System - Implementation Steps

## 1. Overview

**Feature Name:**
Advanced Filtering System

**Corresponding PRD:**
`advanced_filtering_prd.md` (Revised version)

**Depends On:**
Django Rest Framework, Django ORM (`Q` objects), `ContentType` framework. Potentially JSON parsing libraries if standard `json` module isn't sufficient (unlikely).

**Key Features:**
Provides complex, nested (AND/OR) filtering on API list endpoints via a structured JSON query parameter (`?filter=...`). Includes a custom DRF FilterBackend and a parser to translate JSON definitions into Django `Q` objects. Restricts filtering to configured fields.

**Primary Location(s):**
*   Filter Backend & Parser: `core/filtering/` (New directory within `core` app) or dedicated `filtering` app. Assume `core/filtering/`.
*   Configuration: `config/settings/base.py`.
*   Integration: Applied to ViewSets via `filter_backends`.

## 2. Prerequisites

[ ] Confirm **Option A (JSON in Query Parameter)** is the chosen syntax (Section 3.2 of PRD). Example: `?filter={"and": [{"field":"status", "op":"eq", "value":"active"}, ... ]}`.
[ ] Confirm **`StoredFilter` Model (Section 3.4)** is **deferred** for initial implementation.
[ ] Define initial **Configuration for Allowed Fields** (Section 3.5). Example structure in `settings.py`:
    ```python
    # config/settings/base.py
    ALLOWED_FILTER_FIELDS = {
        # Format: 'app_label.modelname': ['field1', 'related__field2', ...]
        'products.product': ['sku', 'name', 'status', 'product_type', 'category__slug', 'tags__name', 'created_at'],
        'organizations.organization': ['code', 'name', 'status', 'organization_type__name', 'tags__name'],
        # Add other models and their filterable fields
    }
    ```
[ ] Ensure DRF is installed and configured.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Filter Parser Implementation (`core/filtering/parser.py`)

  [ ] **(Test First - Parser Logic)**
      Write extensive **Unit Test(s)** (`core/tests/unit/test_filter_parser.py`) for the parsing logic:
      *   Test parsing simple conditions (`{"field": "name", "op": "icontains", "value": "test"}`) -> generates correct `Q(name__icontains='test')`.
      *   Test all supported operators (`eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `contains`, `icontains`, `startswith`, `endswith`, `in`, `notin`, `isnull`). Test correct Django lookup generation (e.g., `eq` -> `exact` or field name directly, `isnull` -> `__isnull`).
      *   Test handling of different value types (string, int, float, boolean, list for `in`/`notin`).
      *   Test parsing nested `AND` conditions (`{"and": [...]}`) -> generates `Q(...) & Q(...)`.
      *   Test parsing nested `OR` conditions (`{"or": [...]}`) -> generates `Q(...) | Q(...)`.
      *   Test deeply nested conditions (`{"and": [..., {"or": [...]}]}`).
      *   Test handling related field lookups (`field`: `category__slug`).
      *   Test error handling: invalid JSON input, unknown operator, unknown field (should be checked later by backend), invalid value type for operator. Raise a specific custom exception (e.g., `InvalidFilterError`).
      Run; expect failure (`parse_filter_json` function/class doesn't exist).
  [ ] Create `core/filtering/parser.py`. Implement the parser function/class `parse_filter_json(filter_dict)`:
      *   Takes the parsed JSON dictionary as input.
      *   Recursively traverses the dictionary structure.
      *   Identifies logical operators (`and`, `or`) and condition objects (`field`, `op`, `value`).
      *   Maps API operators (`eq`, `icontains`, etc.) to Django ORM lookup expressions (`exact`, `icontains`, etc.). Handles `isnull` specially.
      *   Constructs corresponding Django `Q` objects.
      *   Combines `Q` objects using `&` (for `and`) and `|` (for `or`).
      *   Perform basic type validation on values based on operator (e.g., `in` requires list).
      *   Raise `InvalidFilterError` for syntax errors or unknown operators.
      ```python
      # core/filtering/parser.py (Simplified Example Structure)
      from django.db.models import Q
      from django.core.exceptions import ValidationError # Or custom exception

      class InvalidFilterError(ValidationError):
          pass

      OPERATOR_MAP = {
          'eq': 'exact', 'neq': 'exact', # Handle negation later
          'gt': 'gt', 'gte': 'gte', 'lt': 'lt', 'lte': 'lte',
          'contains': 'contains', 'icontains': 'icontains',
          'startswith': 'startswith', 'istartswith': 'istartswith',
          'endswith': 'endswith', 'iendswith': 'iendswith',
          'in': 'in', 'notin': 'in', # Handle negation later
          'isnull': 'isnull',
          # Add others like exact, iexact if needed
      }

      def parse_filter_json(filter_dict):
          if not isinstance(filter_dict, dict):
              raise InvalidFilterError("Filter definition must be an object.")

          for logic_op, conditions in filter_dict.items():
              logic_op = logic_op.lower()
              if logic_op in ('and', 'or'):
                  if not isinstance(conditions, list):
                      raise InvalidFilterError(f"'{logic_op}' value must be a list.")
                  if not conditions: return Q() # Empty AND/OR is neutral

                  q_objects = [parse_filter_json(cond) for cond in conditions]

                  combined_q = Q()
                  if q_objects:
                      combiner = Q.AND if logic_op == 'and' else Q.OR
                      combined_q = q_objects[0]
                      for i in range(1, len(q_objects)):
                           combined_q.connector = combiner
                           combined_q.add(q_objects[i], combiner)
                  return combined_q

              elif logic_op == 'not': # Optional NOT support
                   if not isinstance(conditions, dict):
                       raise InvalidFilterError("'not' value must be an object.")
                   return ~parse_filter_json(conditions) # Negate the inner Q

              elif logic_op == 'field':
                  # This is a leaf condition: {"field": "f", "op": "o", "value": "v"}
                  op = filter_dict.get('op')
                  value = filter_dict.get('value') # Value might be absent for isnull
                  field_name = conditions # The value associated with "field" key

                  if not isinstance(field_name, str) or not op:
                      raise InvalidFilterError("Condition must have 'field' and 'op'.")

                  orm_lookup = OPERATOR_MAP.get(op.lower())
                  if not orm_lookup:
                      raise InvalidFilterError(f"Unsupported operator: {op}")

                  # Basic type checks and handling isnull/in
                  is_negated = op.lower().startswith('n') or op.lower() == 'neq'
                  if orm_lookup == 'isnull':
                      if not isinstance(value, bool):
                           raise InvalidFilterError("'isnull' operator requires boolean value (true/false).")
                      orm_value = value
                  elif orm_lookup == 'in':
                       if not isinstance(value, list):
                           raise InvalidFilterError("'in'/'notin' operator requires a list value.")
                       orm_value = value
                  else:
                       # Allow basic types, further validation might be needed
                       if isinstance(value, (dict, list)):
                            raise InvalidFilterError(f"Invalid value type for operator '{op}'.")
                       orm_value = value

                  q_filter = Q(**{f"{field_name}__{orm_lookup}": orm_value})

                  if is_negated:
                      return ~q_filter
                  else:
                      return q_filter
              else:
                  raise InvalidFilterError(f"Unknown filter key: {logic_op}")

          raise InvalidFilterError("Invalid filter structure.") # Should not be reached

      ```
  [ ] Run parser tests; expect pass. Refactor parser logic for robustness and clarity.

  ### 3.2 Custom Filter Backend Implementation (`core/filtering/backends.py`)

  [ ] **(Test First - Backend Logic)**
      Write **Integration Test(s)** (`core/tests/integration/test_filter_backends.py`) using `@pytest.mark.django_db`.
      *   Simulate an HTTP request (`RequestFactory`) with a valid JSON filter string in query params (`?filter=...`).
      *   Instantiate the `AdvancedFilterBackend` (doesn't exist yet).
      *   Call `backend.filter_queryset(request, initial_queryset, view)`.
      *   Assert the returned queryset contains only the expected filtered objects.
      *   Test with invalid JSON -> expect specific exception (e.g., `InvalidFilterError`).
      *   Test filtering on a disallowed field -> expect specific exception or empty result.
      *   Test with nested AND/OR logic.
      Run; expect failure.
  [ ] Create `core/filtering/backends.py`. Implement `AdvancedFilterBackend`:
      ```python
      # core/filtering/backends.py
      import json
      from urllib.parse import unquote
      from django.conf import settings
      from django.core.exceptions import FieldDoesNotExist, ValidationError
      from rest_framework.filters import BaseFilterBackend
      from rest_framework.exceptions import ParseError
      from .parser import parse_filter_json, InvalidFilterError # Import parser

      def get_allowed_fields_for_model(model):
          """Helper to get allowed fields from settings."""
          app_label = model._meta.app_label
          model_name = model._meta.model_name
          return settings.ALLOWED_FILTER_FIELDS.get(f"{app_label}.{model_name}", [])

      def validate_filter_fields(filter_dict, allowed_fields):
          """Recursively check if all fields in the filter are allowed."""
          if not isinstance(filter_dict, dict): return True # Let parser handle basic structure error

          for key, value in filter_dict.items():
              key = key.lower()
              if key in ('and', 'or'):
                  if not isinstance(value, list): return True # Parser handles
                  for condition in value:
                      if not validate_filter_fields(condition, allowed_fields):
                          return False
              elif key == 'not':
                   if not validate_filter_fields(value, allowed_fields):
                       return False
              elif key == 'field':
                  # Check the field name (value associated with 'field' key)
                  # Basic check: ignore __ lookups for now, or split and check base field?
                  base_field = value.split('__')[0]
                  if base_field not in allowed_fields:
                       # More robust check: try getting the field from model._meta
                       # to handle relations implicitly allowed via model definition
                       try:
                           # This check might be too slow, config list is safer
                           # model_class._meta.get_field(value)
                           if value not in allowed_fields: # Check full path if needed
                               raise InvalidFilterError(f"Filtering on field '{value}' is not allowed for this resource.")
                       except (FieldDoesNotExist, InvalidFilterError) as e:
                           raise InvalidFilterError(f"Filtering on field '{value}' is not allowed or invalid: {e}")
                  # Field is allowed (or is a relation we assume is allowed)
              # Ignore 'op', 'value' keys
          return True


      class AdvancedFilterBackend(BaseFilterBackend):
          """
          Applies complex, nested filters from a 'filter' query parameter
          containing URL-encoded JSON.
          """
          query_param = 'filter'

          def filter_queryset(self, request, queryset, view):
              filter_param_json = request.query_params.get(self.query_param, None)

              if not filter_param_json:
                  return queryset

              try:
                  # URL Decode before JSON parsing
                  decoded_json_str = unquote(filter_param_json)
                  filter_definition = json.loads(decoded_json_str)
              except (json.JSONDecodeError, TypeError) as e:
                  raise ParseError(f"Invalid JSON in '{self.query_param}' parameter: {e}")

              # Validate allowed fields before parsing to Q objects
              model_class = queryset.model
              allowed_fields = get_allowed_fields_for_model(model_class)
              if not allowed_fields: # If model not configured, disallow filtering
                   # Or maybe allow if empty list means "no restrictions"? Be explicit.
                   return queryset # Or raise configuration error?

              try:
                   validate_filter_fields(filter_definition, allowed_fields)
                   q_object = parse_filter_json(filter_definition)
              except InvalidFilterError as e:
                  raise ParseError(str(e)) # Return 400
              except Exception as e:
                  # Log unexpected parser errors
                  import logging
                  logger = logging.getLogger(__name__)
                  logger.error(f"Unexpected error parsing filter: {e}", exc_info=True)
                  raise ParseError("Error processing filter definition.")

              if q_object:
                   try:
                       return queryset.filter(q_object)
                   except (FieldError, ValueError) as e: # Catch ORM errors from invalid lookups/values
                       raise ParseError(f"Invalid filter application: {e}")
              else:
                   return queryset # Empty filter definition
      ```
  [ ] Run backend tests; expect pass. Refactor backend logic (esp. `validate_filter_fields` and error handling).

  ### 3.3 Integrate Backend into ViewSets

  [ ] **(Test First)** Add API tests for specific ViewSets (e.g., `ProductViewSet`) using the `?filter={...}` query parameter with valid JSON structures relevant to that model. Verify correct filtering and error handling for disallowed fields specific to that model.
  [ ] Add the custom backend to DRF settings or base ViewSet:
      ```python
      # config/settings/base.py (Example global default)
      REST_FRAMEWORK = {
          # ... other settings
          'DEFAULT_FILTER_BACKENDS': [
              # 'django_filters.rest_framework.DjangoFilterBackend', # Keep if using both
              'core.filtering.backends.AdvancedFilterBackend', # Adjust import path
              'rest_framework.filters.SearchFilter',
              'rest_framework.filters.OrderingFilter',
          ],
          # ...
      }
      # OR add to specific ViewSets/Base classes:
      # class MyBaseViewSet(OrganizationScopedViewSetMixin, ...):
      #    filter_backends = [AdvancedFilterBackend, OrderingFilter, SearchFilter]
      ```
  [ ] Run API tests for specific ViewSets; expect pass.

  ### 3.4 Stored Filters (Deferred)

  [ ] *(Skip these steps if Stored Filters are deferred)*
  [ ] **(Test First)** Write tests for `StoredFilter` model, serializer, and API endpoints (CRUD, permissions). Write tests for applying stored filters via `?apply_filter=...` param.
  [ ] Implement `StoredFilter` model, serializer, ViewSet, URLs.
  [ ] Modify `AdvancedFilterBackend` to check for `apply_filter` param, fetch definition from `StoredFilter`, parse it, and potentially combine with ad-hoc `filter` param.
  [ ] Implement permissions for managing/using stored filters.
  [ ] Run tests; expect pass.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`). Ensure filter tests pass for multiple models.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=core/filtering`). Review parser and backend logic coverage.
[ ] Manually test complex queries via API client against various endpoints. Test URL encoding/decoding. Test error handling.
[ ] Review API documentation draft for the chosen filter syntax and allowed fields per model.

## 5. Follow-up Actions

[ ] Address TODOs (Refine field validation, parser error details).
[ ] Decide on and document the **official query parameter syntax** (Option A/B/C) clearly in API docs.
[ ] Document the `ALLOWED_FILTER_FIELDS` setting and process for adding fields/models.
[ ] Create Pull Request.
[ ] Update API documentation with detailed examples.
[ ] Implement `StoredFilter` functionality if/when required.

--- END OF FILE advanced_filtering_implementation_steps.md ---
### Tagging


# Tagging System Integration - Implementation Steps

## 1. Overview

**Model Name(s):**
`taggit.models.Tag`, `taggit.models.TaggedItem` (provided by library), potentially `CustomTag` (if custom fields needed)

**Corresponding PRD:**
`tagging_prd.md` (Simplified - Integration focus)

**Depends On:**
`django-taggit` library, Models that need to be tagged (e.g., `Product`, `Contact`, `Document`), `Timestamped`/`Auditable` (if creating custom `Tag` model).

**Key Features:**
Integrates `django-taggit` to allow applying keyword tags to various models. Provides `TaggableManager` for easy association. Supports basic tag management via Admin and potentially API. Optionally supports custom fields on Tags via a custom Tag model.

**Primary Location(s):**
*   Library integration: `settings.py`, `requirements/*.txt`.
*   `TaggableManager` field added to models in: `api/v1/*/models.py`.
*   Custom `Tag` model (if used): `core/models.py` or `common/models.py` or dedicated `tags/models.py`.
*   Admin: `tags/admin.py` (if custom model) or relies on `taggit` admin.
*   Serializers: Integration within serializers of taggable models.

## 2. Prerequisites

[ ] Install required library: `pip install django-taggit`.
[ ] Add `'taggit'` to `INSTALLED_APPS` in `config/settings/base.py`.
[ ] **Decision:** Will custom fields on Tags be required initially?
    *   If NO: Proceed using default `taggit.models.Tag`.
    *   If YES: Plan to create a custom Tag model (Step 3.2). Ensure `Timestamped`/`Auditable` exist if the custom tag model needs them.
[ ] Ensure `factory-boy` is set up.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Initial `taggit` Migration

  [ ] Run `python manage.py makemigrations taggit`. (Only needed the first time `taggit` is added).
  [ ] **Review generated migration file(s).**
  [ ] Run `python manage.py migrate taggit` locally. This creates the default `taggit_tag` and `taggit_taggeditem` tables.

  ### 3.2 Custom Tag Model Definition (Optional - Only if Custom Fields Required)

  [ ] **(Skip if not using custom fields on Tags)**
  [ ] **(Test First)** Write Unit Tests (`core/tests/test_models.py` or `tags/tests/unit/test_models.py`) verifying:
      *   `CustomTag` model inherits required fields (`name`, `slug`).
      *   `custom_fields` JSONField exists and defaults to `{}`.
      *   Inherits `Timestamped`/`Auditable` if specified in PRD.
      Run; expect failure.
  [ ] Define `CustomTag` model (e.g., in `core/models.py`):
      ```python
      # core/models.py (or tags/models.py)
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from taggit.models import TagBase, GenericTaggedItemBase
      from .models import Timestamped, Auditable # If inheriting base models

      class CustomTag(TagBase, Timestamped, Auditable): # Add Timestamped/Auditable if needed
          # Inherits name and slug fields from TagBase

          custom_fields = models.JSONField(
              _("Custom Fields"), default=dict, blank=True
          )
          # Add other fields if necessary

          class Meta:
              verbose_name = _("Tag")
              verbose_name_plural = _("Tags")
              # Add unique constraints or indexes if needed beyond name/slug
              # Ordering is often by name (handled by TagBase?)

      # If using a custom tag model, you might need a custom Through model too,
      # inheriting GenericTaggedItemBase, although TaggableManager often handles this.
      # Check taggit docs if intermediate model customization is needed.
      # class TaggedWhatever(GenericTaggedItemBase):
      #     tag = models.ForeignKey(
      #         CustomTag,
      #         on_delete=models.CASCADE,
      #         related_name="%(app_label)s_%(class)s_items",
      #     )
      ```
  [ ] Configure Django settings to use the custom model in `config/settings/base.py`:
      ```python
      TAGGIT_TAG_MODEL = "core.CustomTag" # Adjust path as needed
      # If using custom through model:
      # TAGGIT_TAGGED_ITEM_MODEL = "core.TaggedWhatever"
      ```
  [ ] Run `makemigrations core` (or `tags`).
  [ ] **Review migration:** Ensure it creates the `core_customtag` table correctly.
  [ ] Run `migrate`.
  [ ] Run tests for `CustomTag` model; expect pass. Refactor.

  ### 3.3 Factory Definition (`tests/factories.py`)

  [ ] Define `TagFactory` (or `CustomTagFactory`) in a relevant `tests/factories.py` (e.g., `core/tests/factories.py` or `common/tests/factories.py`).
      ```python
      import factory
      from factory.django import DjangoModelFactory
      # Import default Tag or CustomTag model based on decision
      # from taggit.models import Tag # Option A
      from core.models import CustomTag # Option B - Adjust import path

      # Option A: Factory for default Tag
      # class TagFactory(DjangoModelFactory):
      #     class Meta:
      #         model = Tag
      #         django_get_or_create = ('name',)
      #     name = factory.Sequence(lambda n: f'Tag {n}')

      # Option B: Factory for CustomTag
      class CustomTagFactory(DjangoModelFactory):
          class Meta:
              model = CustomTag
              django_get_or_create = ('name',) # Use name or slug

          name = factory.Sequence(lambda n: f'Tag {n}')
          # slug = factory.LazyAttribute(lambda o: slugify(o.name)) # Auto-generated by taggit usually
          custom_fields = {}
      ```
  [ ] **(Test)** Write simple tests ensuring the factory creates valid Tag instances.

  ### 3.4 Adding `TaggableManager` to Models

  [ ] **(Test First)** For *each* model requiring tagging (e.g., `Product`):
      *   Write **Integration Test(s)** (`tests/integration/test_models.py` for that model) verifying:
          *   The model instance has a `tags` attribute which is a `TaggableManager`.
          *   You can add tags using `instance.tags.add("tag1", "tag2")`.
          *   You can retrieve tags using `instance.tags.all()`.
          *   You can filter the model using `Model.objects.filter(tags__name__in=["tag1"])`.
      Run; expect failure (attribute error).
  [ ] Add the `TaggableManager` to the target model definition:
      ```python
      # api/v1/base_models/common/models.py (Example for Product)
      from taggit.managers import TaggableManager
      # ... other imports

      class Product(Timestamped, Auditable, OrganizationScoped): # Add other inheritance
          # ... other fields ...
          tags = TaggableManager(blank=True, verbose_name=_("Tags"))
          # ...
      ```
  [ ] Run `makemigrations` for the app containing the modified model(s). Taggit usually doesn't require schema changes here, but it's good practice.
  [ ] Run `migrate`.
  [ ] Run tests for the target model's tagging functionality; expect pass. Refactor.
  [ ] **Repeat Step 3.4 for all models needing tagging.**

  ### 3.5 Admin Registration (`admin.py`)

  [ ] `django-taggit` usually makes tags editable in the admin automatically for models using `TaggableManager`.
  [ ] **If using CustomTag:** Register `CustomTag` with the admin (e.g., in `core/admin.py` or `tags/admin.py`).
      ```python
      from django.contrib import admin
      from .models import CustomTag # Adjust import

      @admin.register(CustomTag)
      class CustomTagAdmin(admin.ModelAdmin):
          list_display = ('name', 'slug') # Add custom_fields if needed
          search_fields = ('name',)
          # Add fieldsets if editing custom_fields in admin
      ```
  [ ] **(Manual Test):** Verify tags can be added/edited via the admin interface for tagged models (e.g., Product admin page). Verify `CustomTag` admin works if implemented.

  ### 3.6 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** For serializers of taggable models (e.g., `ProductSerializer`):
      *   Write Unit/Integration Tests verifying that the `tags` field accepts a list of strings on input (create/update) and outputs a list of strings on representation.
      *   If using custom tags with custom fields, test validation/representation of those fields.
  [ ] Integrate tag handling into relevant serializers using `taggit.serializers`:
      ```python
      # api/v1/base_models/common/serializers.py (Example for ProductSerializer)
      from rest_framework import serializers
      from taggit.serializers import TagListSerializerField, TaggitSerializer
      from ..models import Product # Assuming Product is in common

      class ProductSerializer(TaggitSerializer, serializers.ModelSerializer): # Add TaggitSerializer
          tags = TagListSerializerField(required=False) # Handles list of strings <-> tags

          class Meta:
              model = Product
              fields = [..., 'tags', ...] # Include tags field

          # TaggitSerializer handles create/update for tags if field is named 'tags'
          # If using custom tag model with custom fields, may need custom handling
      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.7 API ViewSet Definition (`views.py`)

  [ ] Ensure ViewSets for taggable models (e.g., `ProductViewSet`) use serializers that handle tags (like `ProductSerializer` above).
  [ ] Add filtering by tags using `django-filter` integration with `taggit`. Define a `FilterSet`:
      ```python
      # api/v1/base_models/common/filters.py (Example)
      import django_filters
      from taggit.forms import TagField # Use form field for filtering
      from taggit.managers import TaggableManager
      from ..models import Product

      class ProductFilter(django_filters.FilterSet):
          # Allows filtering like ?tags=tag1,tag2 (find products with ALL these tags)
          # Or potentially use a custom filter for ANY tag match (tags__name__in)
          tags = django_filters.ModelMultipleChoiceFilter(
              field_name='tags__name',
              to_field_name='name',
              lookup_expr='in', # Find products matching ANY of the tags in the list
              label='Tags (any of)',
              queryset=Product.tags.tag_model.objects.all() # Get tags from correct model
          )
          # Alternative using basic TagField for AND logic:
          # tags = TagField(required=False)

          class Meta:
              model = Product
              fields = ['tags', ...] # Add other filter fields
      ```
      ```python
      # api/v1/base_models/common/views.py (Example ProductViewSet)
      from django_filters.rest_framework import DjangoFilterBackend
      from .filters import ProductFilter # Import FilterSet

      class ProductViewSet(viewsets.ModelViewSet):
          # ... serializer_class, queryset, permissions ...
          filter_backends = [DjangoFilterBackend, ...] # Add DjangoFilterBackend
          filterset_class = ProductFilter # Use the defined filterset
          # ...
      ```
  [ ] **(Test First)** Write API tests specifically for filtering list endpoints by tags (e.g., `GET /api/v1/products/?tags__name__in=tag1,tag2` or `GET /api/v1/products/?tags=tag1,tag2`). Assert correct filtering.

  ### 3.8 URL Routing (`urls.py`)

  [ ] No specific changes usually needed for tagging itself, relies on existing model endpoints. Optionally add `/api/v1/tags/` endpoint if managing global tags via API is needed.

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] Test adding/updating tags via `POST`/`PUT`/`PATCH` requests to taggable model endpoints (e.g., Product). Verify the `tags` list is correctly saved and returned.
  [ ] Test filtering list endpoints using the defined tag filter parameters.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov`). Ensure tagging integration points are tested.
[ ] Manually test adding/removing tags and filtering via API client and Admin UI.
[ ] Review API documentation regarding tag handling and filtering.

## 5. Follow-up Actions

[ ] Address TODOs (e.g., custom field handling for custom tags, tag merging admin action).
[ ] Create Pull Request.
[ ] Update API documentation for relevant endpoints, showing how to use tags.
[ ] Add `TaggableManager` to other models as required in subsequent phases.

--- END OF FILE tagging_implementation_steps.md ---
### Workflow


# Workflow/State Machine Integration - Implementation Steps

## 1. Overview

**Feature Name:**
Workflow / State Machine Integration

**Corresponding PRD:**
`workflow_prd.md` (Simplified - Integration focus using `django-fsm`)

**Depends On:**
`Status` model (for state definitions), `AuditLogging` system (for logging transitions), `RBAC` system (for transition permissions), Celery (optional, for async side-effects), Target Models (e.g., `Product`, `Invoice`) that will have workflows applied.

**Key Features:**
Integrates `django-fsm` to add state machine capabilities to existing Django models. Defines transitions, conditions, and permissions in model methods. Triggers transitions via API actions. Logs transitions.

**Primary Location(s):**
*   Library installation: `requirements/*.txt`, `settings.py` (`INSTALLED_APPS` if needed by library features like admin integration).
*   State field (`status`): Added to target models (e.g., `api/v1/.../models.py`).
*   Transition methods (`@fsm.transition`): Added to target models.
*   Condition/Permission functions: Defined in target model's file or shared utils.
*   API Actions (`@action`): Added to target model's ViewSet (`api/v1/.../views.py`).
*   Signal receiver for Audit Log: `audit/signals.py` (or similar).

## 2. Prerequisites

[ ] Verify `Status` model is implemented and populated with necessary status slugs.
[ ] Verify `AuditLogging` system is implemented (specifically the `log_audit_event` helper or similar).
[ ] Verify `RBAC` system is implemented (specifically the ability to check permissions like `user.has_perm`).
[ ] Install required library: `pip install django-fsm`.
[ ] Add `'django_fsm'` to `INSTALLED_APPS` in `config/settings/base.py` (needed for template tags, admin integration if used).
[ ] Ensure Celery is set up if any transition side-effects need to run asynchronously.

## 3. Implementation Steps (Applied Per Target Model)

  *(These steps are performed for *each* model that requires a workflow, e.g., Product, Invoice)*

  ### 3.1 Add State Field to Target Model (`models.py`)

  [ ] **(Refactor Model)** Modify the target model (e.g., `Product` in `api/v1/features/products/models.py`).
  [ ] Ensure it has a `status` field suitable for `django-fsm`. A `CharField` referencing `Status.slug` values is common.
      ```python
      # Example modification for Product model
      from django_fsm import FSMField # Import FSMField
      # ... other imports ...
      from api.v1.base_models.common.models import Status # Import Status for reference/initial value

      class Product(Timestamped, Auditable, OrganizationScoped):
          # ... other fields ...
          status = FSMField( # Use FSMField instead of CharField
              _("Status"),
              max_length=50,
              default=Status.objects.get(slug='draft').slug, # Or use choices default 'draft'
              # choices=ProductStatus.CHOICES, # Keep choices for admin/validation if desired
              db_index=True,
              protected=True, # Prevents direct modification; changes must go through transitions
          )
          # ... rest of model ...
      ```
      *(Note: Using `FSMField` with `protected=True` is best practice)*.
  [ ] Run `makemigrations` and `migrate` for the app containing the modified model.

  ### 3.2 Define Transition Methods (`models.py`)

  [ ] **(Test First - Transitions)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` for the target model) verifying:
      *   Transitions between valid states succeed (e.g., `product.activate()` changes status from 'draft' to 'active').
      *   Attempting invalid transitions raises `django_fsm.TransitionNotAllowed`.
      *   Transitions check conditions correctly (mock condition functions).
      *   Transitions check permissions correctly (mock `user.has_perm` or the permission check function used).
      Run; expect failure (methods don't exist).
  [ ] Define methods on the target model, decorated with `@transition`.
      ```python
      # Example transitions on Product model
      from django.utils.translation import gettext_lazy as _
      from django_fsm import transition, TransitionNotAllowed
      # Assuming Status slugs 'draft', 'active', 'discontinued' exist

      # Example condition function (can be method or standalone)
      def can_activate_product(instance):
          # Example: Check if required fields are filled
          return bool(instance.description and instance.category)

      class Product(Timestamped, Auditable, OrganizationScoped):
          # ... fields including status = FSMField(...) ...

          @transition(field=status, source='draft', target='active',
                      conditions=[can_activate_product],
                      permission='products.can_activate_product') # Example permission codename
          def activate(self, user=None, reason=""): # Pass user for permission checks
              """Activates the product if conditions and permissions met."""
              # Actions DURING transition (before status changes) can go here
              print(f"Product {self.sku} being activated by {user}.")
              # Don't call self.save() here - FSMField handles it

          @transition(field=status, source='active', target='discontinued')
          def discontinue(self, reason=""):
              """Discontinues an active product."""
              # Actions DURING transition
              print(f"Product {self.sku} discontinued. Reason: {reason}")

          @transition(field=status, source='*', target='draft') # Allow moving back to draft?
          def reset_to_draft(self):
              """Resets product back to draft state."""
              print(f"Product {self.sku} reset to draft.")

          # ... rest of model ...
      ```
      *(Note: Define custom model permissions like `can_activate_product` in the model's `Meta.permissions` if using string-based permissions)*.
  [ ] Run transition tests; expect pass. Refactor.

  ### 3.3 Implement Side Effects (Signals/Hooks)

  [ ] **(Test First)** Write **Integration Test(s)** (`tests/integration/test_workflows.py` or similar) verifying side effects:
      *   Trigger a successful transition (e.g., `product.activate()`).
      *   Assert that expected side effects occurred (e.g., a notification task was queued, an AuditLog entry was created). Mock external calls (like notification service).
      Run; expect failure (side effects not implemented).
  [ ] Implement side effect logic. **Recommended: Use `django-fsm` signals.**
      ```python
      # audit/signals.py (Example connecting to FSM signal)
      from django_fsm.signals import post_transition
      from django.dispatch import receiver
      from crum import get_current_user
      from .models import AuditLog, AuditActionType
      from .utils import log_audit_event
      # Import models involved in workflows
      from api.v1.features.products.models import Product # Example

      @receiver(post_transition)
      def audit_state_transition(sender, instance, name, source, target, **kwargs):
          """Log any successful state transition managed by django-fsm."""
          # Filter specific models if needed, e.g. if not issubclass(sender, Auditable): return
          user = get_current_user()
          organization = getattr(instance, 'organization', None) # If instance is OrgScoped

          # Create context for the log
          context = {
              'transition_name': name, # Name of the transition method called
              'source_state': source,
              'target_state': target,
          }
          # Optionally add transition kwargs if passed and relevant

          log_audit_event(
              user=user,
              organization=organization,
              action_type='STATUS_CHANGE', # Or more specific like 'PRODUCT_ACTIVATED'
              content_object=instance,
              context=context
          )

          # --- Trigger other side effects (e.g., notifications) ---
          # if isinstance(instance, Product) and target == ProductStatus.ACTIVE:
          #    from services.notifications import send_product_active_notification # Example
          #    send_product_active_notification.delay(instance.pk) # Use Celery task

      ```
  [ ] Ensure this signal receiver is connected (e.g., in `audit/apps.py`).
  [ ] Run side effect tests; expect pass. Refactor.

  ### 3.4 API Integration (Views & URLs)

  [ ] **(Test First)** Write **API Test(s)** (`tests/api/test_endpoints.py` for the target model) for the transition actions:
      *   Test `POST /api/v1/products/{id}/activate/` with an authenticated user who *has* permission -> Assert 200 OK, check response status is 'active', verify AuditLog created.
      *   Test `POST /api/v1/products/{id}/activate/` when product is not in 'draft' state -> Assert 400/409 Bad Request (TransitionNotAllowed).
      *   Test `POST /api/v1/products/{id}/activate/` with user *lacking* permission -> Assert 403 Forbidden.
      *   Test transition where conditions fail -> Assert 400/409 Bad Request.
      Run; expect failure (API actions don't exist).
  [ ] Add `@action` methods to the target model's ViewSet (e.g., `ProductViewSet`).
      ```python
      # api/v1/features/products/views.py
      from rest_framework.decorators import action
      from rest_framework.response import Response
      from rest_framework import status
      from django_fsm import TransitionNotAllowed
      # ... other imports ...

      class ProductViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
          # ... queryset, serializer_class, permissions ...

          @action(detail=True, methods=['post'], url_path='activate',
                  # Add specific permission check for the action endpoint itself if needed
                  # permission_classes=[IsAuthenticated, CanActivateProductPermission]
                  )
          def activate_product(self, request, pk=None): # Use slug if lookup_field='slug'
              product = self.get_object() # Handles 404 and object permissions
              try:
                  # Pass user for permission checks within the transition decorator
                  product.activate(user=request.user)
                  # Optional: Reload instance if save didn't update the one in memory
                  # product.refresh_from_db() # If needed
                  serializer = self.get_serializer(product)
                  return Response(serializer.data)
              except TransitionNotAllowed as e:
                  return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

          @action(detail=True, methods=['post'], url_path='discontinue')
          def discontinue_product(self, request, pk=None):
              product = self.get_object()
              reason = request.data.get('reason', '') # Optional reason from payload
              try:
                  product.discontinue(user=request.user, reason=reason)
                  serializer = self.get_serializer(product)
                  return Response(serializer.data)
              except TransitionNotAllowed as e:
                  return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

          # Optional: Get available transitions
          @action(detail=True, methods=['get'], url_path='available-transitions')
          def available_transitions(self, request, pk=None):
              product = self.get_object()
              # Use django-fsm helper to get transitions allowed for the current user
              transitions = [
                  t.name for t in product.get_available_user_transitions(request.user)
              ]
              return Response({'available_transitions': transitions})

      ```
  [ ] Update URL routing (`urls.py`) in the target model's app to include the new actions if using standard DRF router (it usually handles `@action` automatically).
  [ ] Run API action tests; expect pass. Refactor.

  ### 3.5 Admin Integration (Optional)

  [ ] Install `django-fsm-admin` (`pip install django-fsm-admin`).
  [ ] Add `'fsm_admin'` to `INSTALLED_APPS`.
  [ ] Inherit from `FSMAdminMixin` in the target model's Admin class (e.g., `ProductAdmin`).
      ```python
      # api/v1/features/products/admin.py
      from fsm_admin.mixins import FSMAdminMixin
      # ... other imports ...

      @admin.register(Product)
      class ProductAdmin(FSMAdminMixin, admin.ModelAdmin): # Add FSMAdminMixin
          # ... existing admin config ...
          # Specify the state field for the admin buttons
          fsm_field = ['status',]
      ```
  [ ] **(Manual Test):** Verify transition buttons appear in the Django Admin detail view for the model and that they work correctly (respecting permissions/conditions if the admin user isn't superuser).

  ### 3.6 Repeat for Other Models

  [ ] Repeat steps 3.1 - 3.5 (and potentially 3.6 if needed) for other models requiring workflows (e.g., `Invoice`, `PurchaseOrder`).

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`). Verify workflow tests and audit log tests pass for transitions.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov`). Ensure transition methods, conditions, permissions, and signal handlers are covered.
[ ] Manually test key workflow transitions via API client and/or Admin UI. Check Audit Log entries.
[ ] Review API documentation draft for transition actions.

## 5. Follow-up Actions

[ ] Address TODOs (e.g., implement missing permission checks, condition logic, side effects).
[ ] Create Pull Request(s).
[ ] Update API documentation with details on transition endpoints and permissions.
[ ] Configure Celery workers if async side effects were implemented.

--- END OF FILE workflow_integration_steps.md ---
### Automation



# Automation Rule Engine - Implementation Steps

## 1. Overview

**System Name:**
Automation Rule Engine

**Corresponding PRD:**
`automation_prd.md` (Revised version including API management, complex conditions, scheduling, detailed logging)

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `Organization`, `ContentType`, Celery infrastructure (Workers + Beat), Redis (Broker), `django-crum` (or similar user middleware), crontab parsing library. Needs Notification system, other models for actions/conditions.

**Key Features:**
Defines and executes configurable automation rules triggered by model events or schedules. Supports complex conditions (cross-model, AND/OR) and actions (CRUD, notifications, webhooks). Includes detailed logging and API-based management for authorized users.

**Primary Location(s):**
*   Models, Tasks, Signals, Services: `automation/` (New dedicated app recommended)
*   API Views/Serializers/URLs: `api/v1/automations/` (New dedicated API structure)
*   Celery Beat Schedule Task: Defined in Celery config or `automation` app.

## 2. Prerequisites

[ ] Verify all prerequisite models/mixins (`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `Organization`, `ContentType`, `Notification` system service, target models for actions/conditions) are implemented.
[ ] Verify Celery (Workers + Beat) and Redis infrastructure is operational.
[ ] Verify user context middleware (`django-crum`) is active.
[ ] **Install Libraries:** `pip install python-crontab` (or `croniter`).
[ ] **Create new Django app:** `python manage.py startapp automation`.
[ ] Add `'automation'` to `INSTALLED_APPS`.
[ ] Ensure `factory-boy` is set up. Factories for core models exist.
[ ] Define choices for `trigger_type`, `trigger_event`, `condition_logic`, `operator`, `action_type`, `AutomationLog.status` (e.g., in `automation/choices.py`).

## 3. Implementation Steps (TDD Workflow)

  *(Models -> Actions/Conditions -> Triggers -> Task -> API)*

  ### 3.1 Core Model Definitions (`automation/models.py`)

  [ ] **(Test First - AutomationRule)** Write Unit Tests (`tests/unit/test_models.py`) verifying: `AutomationRule` creation, fields, defaults, unique name, FKs, schedule validation (if possible at model level), inheritance, `__str__`.
  [ ] Define `AutomationRule` model. Inherit `Timestamped`, `Auditable`, `OrganizationScoped`. Include fields from PRD 3.1. Add validation for `schedule` field if `trigger_type` is 'SCHEDULED'.
  [ ] Run Rule tests; expect pass. Refactor.
  [ ] **(Test First - RuleCondition)** Write Unit Tests verifying: `RuleCondition` creation, FK to Rule, fields (`field_name`, `operator`, `value`), inheritance, `__str__`.
  [ ] Define `RuleCondition` model. Inherit `Timestamped`, `Auditable`. Include fields from PRD 3.1.
  [ ] Run Condition tests; expect pass. Refactor.
  [ ] **(Test First - RuleAction)** Write Unit Tests verifying: `RuleAction` creation, FK to Rule, fields (`action_type`, `parameters`, `order`), inheritance, `__str__`.
  [ ] Define `RuleAction` model. Inherit `Timestamped`, `Auditable`. Include fields from PRD 3.1.
  [ ] Run Action tests; expect pass. Refactor.
  [ ] **(Test First - AutomationLog)** Write Unit Tests verifying: `AutomationLog` creation, fields, defaults, FKs, GFK representation, inheritance, `__str__`.
  [ ] Define `AutomationLog` model. Inherit `Timestamped`, `Auditable`, `OrganizationScoped`. Include fields from PRD 3.1, especially `action_logs` JSONField. Define Meta with indexes.
  [ ] Run Log tests; expect pass. Refactor.

  ### 3.2 Factory Definitions (`automation/tests/factories.py`)

  [ ] Define factories for `AutomationRule`, `RuleCondition`, `RuleAction`, `AutomationLog`. Handle relationships (use SubFactory, post-generation for related Conditions/Actions). Set required FKs like `organization`. Handle GFKs in `AutomationLogFactory`.
  [ ] **(Test)** Write simple tests ensuring factories create valid instances and relationships.

  ### 3.3 Action Registry & Condition Evaluator (`automation/actions.py`, `automation/conditions.py`)

  [ ] **(Test First - Actions)** Write Unit Tests for *each* planned action function (e.g., `test_update_record_action`, `test_send_notification_action`). Mock dependencies (ORM save, notification service call, webhook requests). Verify correct parameters are used and expected outcomes occur (or exceptions raised).
  [ ] Create `automation/actions.py`. Define placeholder functions for each `action_type` identified in the PRD (e.g., `update_record`, `create_record`, `delete_record`, `send_notification`, `call_webhook`). Implement the core logic for each, accepting standard arguments (`trigger_context`, `parameters`). Implement a registry dictionary mapping `action_type` strings to these functions.
  [ ] Run action tests; expect pass. Refactor actions.
  [ ] **(Test First - Conditions)** Write Unit Tests for the condition evaluation logic (`test_evaluate_conditions`). Test all operators, value types, AND/OR logic, **cross-model relationship lookups** (`__`), handling of `None` values, and error conditions (invalid field, invalid operator).
  [ ] Create `automation/conditions.py`. Implement the `evaluate_conditions(rule, instance)` function (or class). This function fetches the rule's conditions, iterates through them, performs the lookups and comparisons safely (handling potential `AttributeError`, `DoesNotExist`), combines results using `rule.condition_logic`, and returns `True` or `False`.
  [ ] Run condition tests; expect pass. Refactor evaluator.

  ### 3.4 Trigger Mechanisms (Signals, Scheduled Task)

  [ ] **(Test First - Signals)** Write Integration Tests (`tests/integration/test_triggers.py`) using `@pytest.mark.django_db`. Mock the Celery `evaluate_automation_rule.delay` task. Trigger `post_save`/`post_delete` on a sample model configured in a test `AutomationRule`. Assert the task is queued with correct arguments (rule_id, context).
  [ ] Create `automation/signals.py`. Implement generic `post_save`/`post_delete` signal receivers. Receivers query `AutomationRule` based on `sender`, `created`/event type, and `is_active`. For matching rules, queue `evaluate_automation_rule` task. Pass necessary context (PK, content_type ID, changed fields map, user ID).
  [ ] Connect signals in `automation/apps.py`.
  [ ] Run signal tests; expect pass. Refactor.
  [ ] **(Test First - Scheduler)** Write Integration Tests. Mock `evaluate_automation_rule.delay`. Use `freezegun` to simulate time. Set up a scheduled `AutomationRule`. Trigger the Celery Beat scheduler task manually or verify its configuration. Assert the evaluation task is queued at the correct time based on the rule's `schedule`.
  [ ] Create a periodic Celery task (e.g., in `automation/tasks.py`, scheduled via `django-celery-beat` or settings `CELERY_BEAT_SCHEDULE`) that runs frequently (e.g., every minute). This task queries active `AutomationRule`s with `trigger_type='SCHEDULED'`, parses their `schedule` field (using `python-crontab`), and queues `evaluate_automation_rule` for rules matching the current time.
  [ ] Configure Celery Beat to run this scheduler task.
  [ ] Run scheduler tests; expect pass. Refactor.

  ### 3.5 Core Evaluation Task (`automation/tasks.py`)

  [ ] **(Test First)** Write Unit/Integration Tests for the `evaluate_automation_rule` Celery task. Mock `AutomationLog` creation/updates, condition evaluator (`evaluate_conditions`), action function execution. Test different scenarios: conditions met/not met, action success/failure, error handling, `AutomationLog` status updates and `action_logs` population.
  [ ] Implement the `evaluate_automation_rule` task in `automation/tasks.py` following the logic outlined in PRD section 3.3 (Log start -> Fetch -> Evaluate Conditions -> Log result -> Execute Actions sequentially -> Log action details/state -> Update final log status). Use try/except blocks extensively for robustness.
  [ ] Run task tests; expect pass. Refactor task logic.

  ### 3.6 Admin Registration (`automation/admin.py`)

  [ ] Create `automation/admin.py`.
  [ ] Define Inlines for `RuleCondition`, `RuleAction` on `AutomationRuleAdmin`.
  [ ] Define `AutomationRuleAdmin`, `AutomationLogAdmin`. Configure displays, filters, search, readonly fields. Use `list_editable` for `AutomationRule.is_active`. Provide good display for `AutomationLog` fields (`changes`, `context`, `action_logs`).
  [ ] Register models.
  [ ] **(Manual Test):** Verify Admin interface for creating/managing rules, conditions, actions. View logs.

  ### 3.7 Migrations

  [ ] Run `python manage.py makemigrations automation`.
  [ ] **Review generated migration file(s) carefully.** Check all models, FKs, JSONFields, indexes.
  [ ] Run `python manage.py migrate` locally.

  ### 3.8 API Implementation (Management & Logging)

  [ ] **(Test First - Rule Management API)** Write API tests (`tests/api/test_endpoints.py`) for CRUD operations on `/api/v1/automations/rules/` (and potentially nested conditions/actions, or handle them via nested serializers). Test creating complex rules with conditions and actions. Test permissions (admin/power user only). Test Org Scoping.
  [ ] Define serializers for `AutomationRule`, `RuleCondition`, `RuleAction`. Handle nested writes carefully (e.g., using `drf-writable-nested` or custom `create`/`update`). Implement `validate_custom_fields` if applicable to these models.
  [ ] Define `AutomationRuleViewSet` (ModelViewSet). Apply appropriate permissions. Inherit `OrganizationScopedViewSetMixin`.
  [ ] Define URL routing for rule management.
  [ ] Run rule management API tests; expect pass. Refactor.
  [ ] **(Test First - Log API)** Write API tests for `GET /api/v1/automations/logs/` and `GET /api/v1/automations/logs/{id}/`. Test filtering by rule, status, date, parent object. Test permissions. Verify `action_logs` detail is present.
  [ ] Define `AutomationLogSerializer` (read-only).
  [ ] Define `AutomationLogViewSet` (ReadOnlyModelViewSet). Implement filtering. Apply appropriate permissions. Inherit `OrganizationScopedViewSetMixin`.
  [ ] Define URL routing for log viewing.
  [ ] Run log API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`), ensuring tasks run (eagerly), signals fire, conditions evaluate, actions execute (mocked), logs are created, and APIs work.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=automation`). Review uncovered areas in condition/action logic and task execution.
[ ] Manually create a simple rule (e.g., update description on Product status change) via API/Admin. Trigger the event and verify the action occurs and the `AutomationLog` is correct. Test a scheduled rule.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs (Implement all required Actions, refine condition evaluator, add more complex logic if needed, robust error handling/retries in tasks).
[ ] Create Pull Request(s).
[ ] Update API documentation (especially available actions and parameters).
[ ] Implement archiving/purging for `AutomationLog`.
[ ] Consider UI for rule building if needed in future.

--- END OF FILE automation_implementation_steps.md ---