
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