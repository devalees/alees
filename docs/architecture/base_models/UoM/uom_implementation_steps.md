
# UnitOfMeasure (UoM) System - Implementation Steps

## 1. Overview

**Model Name(s):**
`UomType`, `UnitOfMeasure`

**Corresponding PRD:**
`uom_prd.md` (Revised - Using `UomType` Model)

**Depends On:**
`Timestamped`, `Auditable` (Abstract Base Models)

**Key Features:**
Defines UoM types (Length, Mass) via `UomType` model and specific units (KG, M, EA) via `UnitOfMeasure` model linked to a type. Includes code, name, symbol, status, custom fields.

**Primary Location(s):**
`api/v1/base_models/common/uom/` (Assuming `common` app for shared entities)

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`) are implemented.
[ ] Ensure the `common` app structure exists (`api/v1/base_models/common/uom/`).
[ ] Ensure `factory-boy` is set up. Basic User factory exists.

## 3. Implementation Steps (TDD Workflow)

  *(Implement UomType first, then UnitOfMeasure)*

  ### 3.1 `UomType` Model Definition (`models.py`)

  [ ] **(Test First)** Write Unit Tests (`tests/unit/test_models.py`) verifying: `UomType` creation (`code`, `name`), PK (`code`), uniqueness (`name`), defaults (`is_active`, `custom_fields`), inheritance, `__str__`.
  [ ] Define `UomType` class in `api/v1/base_models/common/uom/models.py`. Inherit `Timestamped`, `Auditable`.
      ```python
      # api/v1/base_models/common/uom/models.py
      # ... imports ...
      class UomType(Timestamped, Auditable):
          code = models.CharField( # Or SlugField
              _("Code"), max_length=50, primary_key=True,
              help_text=_("Unique code for the UoM Type (e.g., LENGTH, MASS).")
          )
          name = models.CharField(
              _("Name"), max_length=100, unique=True, db_index=True,
              help_text=_("Human-readable name (e.g., Length, Mass).")
          )
          description = models.TextField(_("Description"), blank=True)
          is_active = models.BooleanField(_("Is Active"), default=True, db_index=True)
          custom_fields = models.JSONField(_("Custom Fields"), default=dict, blank=True)

          class Meta:
              verbose_name = _("Unit of Measure Type")
              verbose_name_plural = _("Unit of Measure Types")
              ordering = ['name']

          def __str__(self): return self.name
      ```
  [ ] Run `UomType` tests; expect pass. Refactor.

  ### 3.2 `UnitOfMeasure` Model Definition (`models.py`)

  [ ] **(Test First)** Write Unit Tests (`tests/unit/test_models.py`) verifying: `UnitOfMeasure` creation (`code`, `name`, `uom_type` FK), PK (`code`), uniqueness (`name`), defaults (`is_active`, `custom_fields`), inheritance, `__str__`. Test FK link to `UomType`.
  [ ] Define `UnitOfMeasure` class *after* `UomType` in `api/v1/base_models/common/uom/models.py`. Inherit `Timestamped`, `Auditable`. Add FK to `UomType`.
      ```python
      # api/v1/base_models/common/uom/models.py (continued)
      class UnitOfMeasure(Timestamped, Auditable):
          code = models.CharField(
              _("Code"), max_length=20, primary_key=True,
              help_text=_("Unique code for the unit (e.g., KG, M, EA, BOX_12).")
          )
          name = models.CharField(
              _("Name"), max_length=100, unique=True, db_index=True,
              help_text=_("Full name of the unit (e.g., Kilogram, Meter, Each).")
          )
          uom_type = models.ForeignKey( # Changed from CharField
              UomType,
              verbose_name=_("Type"),
              related_name='units',
              on_delete=models.PROTECT, # Protect Type if Units reference it
              help_text=_("Category of measurement (e.g., Length, Mass, Count).")
          )
          symbol = models.CharField(
              _("Symbol"), max_length=10, blank=True,
              help_text=_("Common symbol (e.g., kg, m, L).")
          )
          is_active = models.BooleanField(_("Is Active"), default=True, db_index=True)
          custom_fields = models.JSONField(_("Custom Fields"), default=dict, blank=True)

          class Meta:
              verbose_name = _("Unit of Measure")
              verbose_name_plural = _("Units of Measure")
              ordering = ['uom_type__name', 'name'] # Order by type name then unit name

          def __str__(self): return self.name
      ```
  [ ] Run `UnitOfMeasure` tests; expect pass. Refactor.

  ### 3.3 Factory Definitions (`tests/factories.py`)

  [ ] Define `UomTypeFactory`.
  [ ] Define `UnitOfMeasureFactory`, ensuring `uom_type` uses `factory.SubFactory(UomTypeFactory)`.
      ```python
      # api/v1/base_models/common/uom/tests/factories.py
      class UomTypeFactory(DjangoModelFactory):
          class Meta: model = UomType; django_get_or_create = ('code',)
          code = factory.Iterator(['LENGTH', 'MASS', 'COUNT', 'VOLUME', 'TIME'])
          name = factory.LazyAttribute(lambda o: o.code.capitalize())
          is_active = True
          custom_fields = {}

      class UnitOfMeasureFactory(DjangoModelFactory):
          class Meta: model = UnitOfMeasure; django_get_or_create = ('code',)
          code = factory.Sequence(lambda n: f'UOM{n}')
          name = factory.Sequence(lambda n: f'Unit Name {n}')
          uom_type = factory.SubFactory(UomTypeFactory) # Link to type factory
          symbol = factory.LazyAttribute(lambda o: o.code.lower())
          is_active = True
          custom_fields = {}
      ```
  [ ] **(Test)** Write simple tests ensuring factories create valid instances and links.

  ### 3.4 Admin Registration (`admin.py`)

  [ ] Create/Update `api/v1/base_models/common/uom/admin.py`.
  [ ] Define `UomTypeAdmin`.
  [ ] Define `UnitOfMeasureAdmin`. Use `list_select_related` for `uom_type`. Filter by `uom_type`.
      ```python
      from django.contrib import admin
      from .models import UomType, UnitOfMeasure

      @admin.register(UomType)
      class UomTypeAdmin(admin.ModelAdmin):
          list_display = ('code', 'name', 'is_active')
          search_fields = ('code', 'name')
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')

      @admin.register(UnitOfMeasure)
      class UnitOfMeasureAdmin(admin.ModelAdmin):
          list_display = ('code', 'name', 'uom_type', 'symbol', 'is_active', 'updated_at')
          search_fields = ('code', 'name', 'symbol')
          list_filter = ('uom_type', 'is_active') # Filter by related type
          list_select_related = ('uom_type',) # Optimize list view query
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
          autocomplete_fields = ['uom_type'] # If UomTypeAdmin registered
          # ... fieldsets ...
      ```
  [ ] **(Manual Test):** Verify Admin interfaces for both models.

  ### 3.5 Initial Data Population (Migration)

  [ ] Create a new **Data Migration** file: `..._populate_initial_uom_types_and_uoms.py`.
  [ ] Edit the migration file. Add `RunPython` operations to:
      1.  Populate `UomType` records first (Length, Mass, Count, etc.).
      2.  Populate `UnitOfMeasure` records, linking them to the correct `UomType` instances just created.
      *(Modify the previous `populate_uoms` function to fetch/link the `UomType`)*.

  ### 3.6 Migrations (Apply Initial Models & Data)

  [ ] Run `python manage.py makemigrations api.v1.base_models.common`.
  [ ] **Review generated migration file(s) carefully.** Should include creation of `UomType`, `UnitOfMeasure`, and the data population.
  [ ] Run `python manage.py migrate` locally. Verify data loaded via Admin.

  ### 3.7 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write Tests for `UomTypeSerializer` and `UnitOfMeasureSerializer`. Test representation, relationship (`uom_type` in UoM serializer).
  [ ] Define `UomTypeSerializer`.
  [ ] Define `UnitOfMeasureSerializer`. Represent `uom_type` using `PrimaryKeyRelatedField` (or slug) or nested `UomTypeSerializer` for reads.
      ```python
      # api/v1/base_models/common/uom/serializers.py
      class UomTypeSerializer(serializers.ModelSerializer):
          class Meta: model = UomType; fields = ['code', 'name', 'description', 'is_active', 'custom_fields']; read_only_fields = fields

      class UnitOfMeasureSerializer(serializers.ModelSerializer):
          uom_type_details = UomTypeSerializer(source='uom_type', read_only=True) # Example nested read

          class Meta:
              model = UnitOfMeasure
              fields = [
                  'code', 'name', 'uom_type', # Write via PK (uom_type is FK)
                  'uom_type_details', # Read nested
                  'symbol', 'is_active', 'custom_fields',
              ]
              read_only_fields = ('code', 'name', 'symbol', 'is_active', 'custom_fields', 'uom_type_details') # Typically read-only via API
              # Add uom_type to read_only_fields if not allowing it to be set/changed via API
      ```
  [ ] Implement `validate_custom_fields` if needed.
  [ ] Run tests; expect pass. Refactor.

  ### 3.8 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests for `/api/v1/uom-types/` and `/api/v1/uoms/`. Test read access.
  [ ] Define `UomTypeViewSet` (ReadOnly).
  [ ] Define `UnitOfMeasureViewSet` (ReadOnly). Filter by `uom_type__code`.
      ```python
      # api/v1/base_models/common/uom/views.py
      # ... imports ...
      class UomTypeViewSet(viewsets.ReadOnlyModelViewSet):
          queryset = UomType.objects.filter(is_active=True)
          serializer_class = UomTypeSerializer
          permission_classes = [permissions.IsAuthenticatedOrReadOnly]
          lookup_field = 'code'
          filter_backends = [filters.SearchFilter, filters.OrderingFilter]
          search_fields = ['code', 'name']
          ordering_fields = ['name', 'code']

      class UnitOfMeasureViewSet(viewsets.ReadOnlyModelViewSet):
          queryset = UnitOfMeasure.objects.filter(is_active=True).select_related('uom_type')
          serializer_class = UnitOfMeasureSerializer
          permission_classes = [permissions.IsAuthenticatedOrReadOnly]
          lookup_field = 'code'
          filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
          filterset_fields = ['uom_type__code'] # Filter by type code
          search_fields = ['code', 'name', 'symbol', 'uom_type__name']
          ordering_fields = ['uom_type__name', 'name', 'code']
      ```
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.9 URL Routing (`urls.py`)

  [ ] Import and register both `UomTypeViewSet` and `UnitOfMeasureViewSet` with the router in `common/urls.py`.
  [ ] **(Test):** Rerun basic API tests; expect 200 OK for both endpoints.

  ### 3.10 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First)** Write LIST/RETRIEVE tests for `/uom-types/` and `/uoms/`. Test filtering UoMs by `uom_type__code`. Test search.
  [ ] Run list/retrieve tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/base_models/common`).
[ ] Manually test via API client and Django Admin. Verify initial data.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Ensure models needing a UoM reference (e.g., Product) add the `ForeignKey` to `UnitOfMeasure` correctly.
[ ] Plan for implementation of the separate Unit Conversion mechanism.

---