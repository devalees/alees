Okay, let's generate the implementation steps for the core `Organization` model. This is a central piece, incorporating hierarchy (MPTT), tagging (Taggit), custom fields, and several foreign key relationships established in previous steps.

--- START OF FILE organization_implementation_steps.md ---

# Organization - Implementation Steps

## 1. Overview

**Model Name:**
`Organization`

**Corresponding PRD:**
`organization_prd.md`

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationType`, `Currency`, `Contact`, `Address`. Requires libraries `django-mptt` and `django-taggit`.

**Key Features:**
Core ERP entity representing internal/external org units. Supports hierarchy (MPTT), tagging (Taggit), custom fields (JSONField), status, localization settings, links to Type, Contact, Address, Currency. Foundation for `OrganizationScoped`.

**Primary Location(s):**
`api/v1/base_models/organization/`

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `OrganizationType`, `Currency`, `Contact`, `Address`) are implemented and migrated.
[ ] Ensure the `organization` app structure exists (`api/v1/base_models/organization/`).
[ ] Install required libraries: `pip install django-mptt django-taggit`.
[ ] Add `'mptt'` and `'taggit'` to `INSTALLED_APPS` in `config/settings/base.py`.
[ ] Ensure `factory-boy` is set up. Factories for `OrganizationType`, `Currency`, `Contact`, `Address`, and `User` exist.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py`) verifying:
      *   An `Organization` can be created with required fields (`name`, `code`, `organization_type`).
      *   Unique constraints (`code`, potentially `unique_together` for name/parent) are enforced.
      *   Default values (`status`, `metadata`, `custom_fields`) are set.
      *   FK relationships (`organization_type`, `parent`, `primary_contact`, `primary_address`, `currency`) work.
      *   Inherited fields (`created_at`, `updated_at`, `created_by`, `updated_by`) exist.
      *   MPTT fields (`lft`, `rght`, `tree_id`, `level`) are present after save.
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

      from core.models import Timestamped, Auditable # Adjust import
      # Import related models from their locations
      from .models import OrganizationType # Assumes OrgType in same models.py
      from api.v1.base_models.common.models import Currency, Contact, Address # Adjust import path

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
              OrganizationType,
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

          # Contact Information
          primary_contact = models.ForeignKey(
              Contact, # Use direct import
              verbose_name=_("Primary Contact"),
              related_name='primary_for_organizations',
              on_delete=models.SET_NULL, null=True, blank=True
          )
          # Address Details - Consider multiple addresses (Billing, Shipping) maybe via M2M or separate FKs
          primary_address = models.ForeignKey(
              Address, # Use direct import
              verbose_name=_("Primary Address"),
              related_name='primary_for_organizations',
              on_delete=models.SET_NULL, null=True, blank=True
          )
          # Example: Separate Billing Address
          # billing_address = models.ForeignKey(Address, related_name='billing_for_organizations', ...)

          # Localization
          timezone = models.CharField(_("Timezone"), max_length=60, default=settings.TIME_ZONE)
          currency = models.ForeignKey(
              Currency, # Use direct import
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
              unique_together = (('parent', 'name'), ('code',)) # Code must be globally unique
              ordering = ['tree_id', 'lft'] # MPTT default ordering

          def __str__(self):
              return self.name

      ```
  [ ] Run tests; expect pass. Refactor model code if needed.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `OrganizationFactory` in `api/v1/base_models/organization/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from ..models import Organization, OrganizationType
      # Import factories for related models
      from .factories import OrganizationTypeFactory # Assumes in same file now
      from api.v1.base_models.common.tests.factories import CurrencyFactory, ContactFactory, AddressFactory

      class OrganizationFactory(DjangoModelFactory):
          class Meta:
              model = Organization
              django_get_or_create = ('code',) # Use code for uniqueness

          name = factory.Sequence(lambda n: f'Test Organization {n}')
          code = factory.Sequence(lambda n: f'ORG-{n:04}')
          organization_type = factory.SubFactory(OrganizationTypeFactory)
          status = Organization.STATUS_ACTIVE
          # parent = None # Set explicitly in tests if needed for hierarchy
          # primary_contact = factory.SubFactory(ContactFactory) # Add if needed by default
          # primary_address = factory.SubFactory(AddressFactory) # Add if needed by default
          # currency = factory.SubFactory(CurrencyFactory) # Add if needed by default
          timezone = 'UTC'
          language = 'en'
          metadata = {}
          custom_fields = {}

          # Example for tags:
          # @factory.post_generation
          # def tags(self, create, extracted, **kwargs):
          #     if not create:
          #         return
          #     if extracted:
          #         for tag in extracted:
          #             self.tags.add(tag)
      ```
  [ ] **(Test)** Write tests ensuring `OrganizationFactory` creates valid instances, including setting parent for hierarchy tests.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Create/Update `api/v1/base_models/organization/admin.py`.
  [ ] Define `OrganizationAdmin` using `DjangoMpttAdmin`:
      ```python
      from django.contrib import admin
      from mptt.admin import DraggableMPTTAdmin # Or MPTTModelAdmin
      from .models import Organization, OrganizationType # Ensure both imported

      # Register OrganizationType if not done separately
      # @admin.register(OrganizationType)
      # class OrganizationTypeAdmin(admin.ModelAdmin): ...

      @admin.register(Organization)
      class OrganizationAdmin(DraggableMPTTAdmin): # Provides tree view and drag-drop
          list_display = ('tree_actions', 'indented_title', 'code', 'organization_type', 'status', 'currency')
          list_display_links = ('indented_title',)
          list_filter = ('organization_type', 'status', 'currency')
          search_fields = ('name', 'code')
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
          # Add fieldsets or configure form for better layout
          # Consider adding Contact/Address inlines if desired
          # Note: TaggableManager usually works out-of-the-box with admin
          # Note: JSONField might need django-json-widget for better editing
      ```
  [ ] **(Manual Test):** Verify registration, CRUD operations, hierarchy management (drag-drop if using `DraggableMPTTAdmin`), and related fields in Django Admin.

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations api.v1.base_models.organization`.
  [ ] **Review generated migration file carefully.** Check MPTT setup, FKs, unique constraints, indexes.
  [ ] Run `python manage.py migrate` locally.
  [ ] Run `python manage.py rebuild_organization` (MPTT command) if needed, unlikely for new setup.

  ### 3.5 Serializer Definition (`serializers.py`)

  [ ] **(Test First - Validation/Representation)** Write Unit/Integration Tests (`tests/unit/test_serializers.py`, `tests/integration/test_serializers.py`) for `OrganizationSerializer`. Test validation (unique code, FK existence), representation (fields included, related objects maybe nested read-only), custom field handling.
  [ ] Define `OrganizationSerializer` in `api/v1/base_models/organization/serializers.py`:
      ```python
      from rest_framework import serializers
      from rest_framework_mptt.serializers import MPTTModelSerializer # If using drf-mptt
      from taggit.serializers import TagListSerializerField, TaggitSerializer # If using drf-taggit
      from ..models import Organization
      # Import related serializers if nesting
      # from api.v1.base_models.common.serializers import AddressSerializer, ContactSerializer

      class OrganizationSerializer(TaggitSerializer, serializers.ModelSerializer): # Or MPTTModelSerializer
          # Handle tags (requires TaggitSerializer mixin from drf-taggit)
          tags = TagListSerializerField(required=False)
          # Handle related fields - examples
          organization_type_name = serializers.CharField(source='organization_type.name', read_only=True)
          # primary_address = AddressSerializer(read_only=True) # Example nesting
          # primary_contact = ContactSerializer(read_only=True) # Example nesting
          parent_id = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all(), source='parent', allow_null=True, required=False)

          class Meta:
              model = Organization
              fields = [
                  'id', 'name', 'code', 'organization_type', 'organization_type_name',
                  'status', 'parent_id', 'effective_date', 'end_date',
                  'primary_contact', # ID for write, or nested obj for read
                  'primary_address', # ID for write, or nested obj for read
                  'timezone', 'currency', 'language',
                  'tags', 'metadata', 'custom_fields',
                  'created_at', 'updated_at', # Add created_by/updated_by if needed
              ]
              read_only_fields = ('id', 'created_at', 'updated_at', 'organization_type_name')
              # Add MPTT specific fields if using MPTTModelSerializer: 'lft', 'rght', 'tree_id', 'level'
      ```
  [ ] Implement `validate_custom_fields`, potentially `validate_code` (ensure uniqueness if not handled by DB), `validate` for cross-field rules.
  [ ] Run tests; expect pass. Refactor.

  ### 3.6 API ViewSet Definition (`views.py`)

  [ ] **(Test First - Permissions/Basic Structure)** Write basic API Tests checking URL existence, authentication, basic permissions (e.g., view).
  [ ] Define `OrganizationViewSet` in `api/v1/base_models/organization/views.py`:
      ```python
      from rest_framework import viewsets, permissions
      from rest_framework.decorators import action
      from rest_framework.response import Response
      from ..models import Organization
      from ..serializers import OrganizationSerializer
      # Import filtering, permissions etc.

      class OrganizationViewSet(viewsets.ModelViewSet):
          serializer_class = OrganizationSerializer
          permission_classes = [permissions.IsAuthenticated] # Add specific RBAC permissions
          authentication_classes = [...] # From API Strategy
          # queryset should handle Org Scoping if applicable at this level,
          # OR rely on OrganizationScoped mixin for related objects later
          # For now, assume users see all Orgs they have basic view permission for
          queryset = Organization.objects.all().select_related(
              'organization_type', 'currency', 'primary_contact', 'primary_address', 'parent'
          )
          filter_backends = [...] # Setup advanced filtering, search, ordering
          filterset_fields = ['organization_type', 'status', 'parent', 'tags__name']
          search_fields = ['name', 'code']
          ordering_fields = ['name', 'code', 'created_at']

          # Example custom action for hierarchy
          @action(detail=True, methods=['get'])
          def descendants(self, request, pk=None):
              organization = self.get_object()
              queryset = organization.get_descendants(include_self=False)
              # Apply filtering/pagination potentially
              serializer = self.get_serializer(queryset, many=True)
              return Response(serializer.data)

          # Add actions for ancestors, children, moving nodes etc. as needed
      ```
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.7 URL Routing (`urls.py`)

  [ ] Import `OrganizationViewSet` in `api/v1/base_models/organization/urls.py`.
  [ ] Register with router: `router.register(r'organizations', views.OrganizationViewSet)`.
  [ ] Include `organization.urls` in `api/v1/base_models/urls.py`.
  [ ] **(Test):** Rerun basic API tests; expect 2xx/4xx codes.

  ### 3.8 API Endpoint Testing (CRUD & Features) (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests covering:
      *   LIST (with filters for type, status, parent, tags)
      *   CREATE (valid/invalid data, permissions)
      *   RETRIEVE (including non-existent, permissions)
      *   UPDATE (PUT/PATCH, valid/invalid data, permissions)
      *   DELETE (permissions, check PROTECT constraints if deleting parent)
      *   Hierarchy actions (`/descendants/` etc.)
      *   Saving/Validating `metadata` and `custom_fields`.
      *   Tag assignment/filtering.
  [ ] Implement/Refine ViewSet methods (`get_queryset`, `perform_create`, custom actions) and Serializer logic (validation, representation) to make tests pass. Ensure Field-Level permissions checked by serializer.
  [ ] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/base_models/organization`). Review uncovered lines.
[ ] Manually test via API client and Django Admin, especially hierarchy operations.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Ensure `OrganizationScoped` implementation uses this model.

--- END OF FILE organization_implementation_steps.md ---