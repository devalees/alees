Okay, let's generate the implementation steps for the `Currency` model based on its refined PRD, following the TDD checklist format.

This includes the model definition, factory, admin setup, initial data loading considerations, and basic API (likely read-only for general users).

--- START OF FILE currency_implementation_steps.md ---

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
`api/v1/base_models/common/` (Assuming `common` app within `base_models` for shared entities like Currency, Address, Contact, etc., based on project structure)

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`) are implemented.
[ ] Ensure the `common` app structure exists (`api/v1/base_models/common/`).
[ ] Ensure `factory-boy` is set up. Basic User factory exists (needed for Auditable).
[ ] Decision made on source for initial currency data (e.g., `pycountry` library, manual list, external file).

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `common`) verifying:
      *   A `Currency` instance can be created with required fields (`code`, `name`).
      *   `code` is the primary key.
      *   Unique constraints (`name`, `numeric_code`) are present (checked via `_meta`).
      *   Default values (`decimal_places`, `is_active`) are set correctly.
      *   `custom_fields` defaults to an empty dict.
      *   `__str__` method returns the `code`.
      *   Inherited `Timestamped`/`Auditable` fields exist.
      Run; expect failure (`Currency` doesn't exist).
  [ ] Define the `Currency` class in `api/v1/base_models/common/models.py`.
  [ ] Add required inheritance: `Timestamped`, `Auditable`.
      ```python
      # api/v1/base_models/common/models.py
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

  [ ] Define `CurrencyFactory` in `api/v1/base_models/common/tests/factories.py`:
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
  [ ] **(Test)** Write a simple test ensuring `CurrencyFactory` creates valid `Currency` instances.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Create/Update `api/v1/base_models/common/admin.py`.
  [ ] Define `CurrencyAdmin`:
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
  [ ] **(Manual Test):** Verify registration and basic functionality in Django Admin locally.

  ### 3.4 Initial Data Population (Migration)

  [ ] **(Decision):** Choose source for ISO 4217 data (e.g., `pycountry` library or a predefined list/CSV).
  [ ] Create a new **Data Migration** file: `python manage.py makemigrations --empty --name populate_currencies api.v1.base_models.common`.
  [ ] Edit the generated migration file (`..._populate_currencies.py`). Add `RunPython` operations to load the currency data.
      ```python
      # Example using pycountry (install first: pip install pycountry)
      from django.db import migrations

      def populate_currencies(apps, schema_editor):
          Currency = apps.get_model('common', 'Currency') # Use app_label from apps.py
          db_alias = schema_editor.connection.alias
          try:
              import pycountry
          except ImportError:
              print("\nSkipping currency population: pycountry not installed.")
              return # Or raise an error if it's essential

          currencies_to_add = []
          for pc_currency in pycountry.currencies:
              # pycountry might throw KeyError if numeric is not found
              numeric = getattr(pc_currency, 'numeric', None)
              currencies_to_add.append(
                  Currency(
                      code=pc_currency.alpha_3,
                      name=pc_currency.name,
                      numeric_code=numeric,
                      # Defaults for symbol/decimal_places are okay, or try to map if possible
                      # symbol = ... mapping ...
                      # decimal_places = ... mapping ...
                  )
              )
          # Use bulk_create for efficiency
          Currency.objects.using(db_alias).bulk_create(currencies_to_add, ignore_conflicts=True)
          print(f"\nPopulated/updated {len(currencies_to_add)} currencies.")

      def remove_currencies(apps, schema_editor):
          # Optional: Define reverse operation if needed, often just pass
          pass

      class Migration(migrations.Migration):

          dependencies = [
              # Ensure this runs after the initial migration creating the Currency model
              ('common', '000X_initial_or_previous'),
          ]

          operations = [
              migrations.RunPython(populate_currencies, reverse_code=remove_currencies),
          ]
      ```
  [ ] Run `python manage.py migrate` locally to apply the data migration. Verify data loaded (e.g., via Admin or shell).

  ### 3.5 Serializer Definition (`serializers.py`)

  [ ] **(Test First - Validation/Representation)** Write Unit/Integration Tests (`tests/unit/test_serializers.py`, `tests/integration/test_serializers.py`) for `CurrencySerializer`. Test validation (e.g., code length), representation (fields included), and custom field handling if applicable.
  [ ] Define `CurrencySerializer` in `api/v1/base_models/common/serializers.py`:
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
  [ ] Implement `validate_custom_fields` if applicable.
  [ ] Run tests; expect pass. Refactor.

  ### 3.6 API ViewSet Definition (`views.py`)

  [ ] **(Test First - Permissions/Basic Structure)** Write basic API Tests (`tests/api/test_endpoints.py`) for `/api/v1/currencies/`. Test unauthenticated access (likely allowed for read). Test authenticated access.
  [ ] Define `CurrencyViewSet` in `api/v1/base_models/common/views.py`:
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
  [ ] Run basic structure/permission tests; expect pass. Refactor.

  ### 3.7 URL Routing (`urls.py`)

  [ ] Import the `CurrencyViewSet` in `api/v1/base_models/common/urls.py`.
  [ ] Register the ViewSet with the router: `router.register(r'currencies', views.CurrencyViewSet)`.
  [ ] Ensure `common.urls` is included in `api/v1/base_models/urls.py`.
  [ ] **(Test):** Rerun basic API tests; expect 200 OK for listing.

  ### 3.8 API Endpoint Testing (Read & Features) (`tests/api/test_endpoints.py`)

  [ ] **(Test First - List)** Write test for `GET /api/v1/currencies/`. Assert 200, check pagination/structure, verify expected currencies (e.g., USD, EUR from factory/population) are present. Test filtering by `is_active=false` if applicable.
  [ ] Ensure `queryset` in ViewSet is appropriate.
  [ ] Run list tests; expect pass. Refactor.
  [ ] **(Test First - Retrieve)** Write test for `GET /api/v1/currencies/{code}/`. Assert 200, check response body. Test non-existent code (expect 404).
  [ ] Ensure lookup by code (PK) works.
  [ ] Run retrieve tests; expect pass. Refactor.
  [ ] *(CRUD tests not applicable if using ReadOnlyModelViewSet)*.
  [ ] *(Test custom field validation/saving via API if management endpoints exist)*.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov`).
[ ] Manually test via API client and verify data in Django Admin.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Ensure other models (Organization, etc.) correctly add `ForeignKey` to `Currency`.

--- END OF FILE currency_implementation_steps.md ---