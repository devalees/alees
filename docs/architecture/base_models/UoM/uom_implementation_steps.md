Okay, here are the implementation steps for the `UnitOfMeasure` (UoM) model, based on its simplified PRD including custom fields, following the TDD checklist format.

--- START OF FILE uom_implementation_steps.md ---

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