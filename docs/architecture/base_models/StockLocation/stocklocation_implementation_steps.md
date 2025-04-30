
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