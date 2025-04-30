

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