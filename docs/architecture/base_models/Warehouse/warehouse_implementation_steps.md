Okay, here are the implementation steps for the `Warehouse` model, based on its simplified PRD including custom fields, following the TDD checklist format.

--- START OF FILE warehouse_implementation_steps.md ---

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