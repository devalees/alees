Okay, let's generate the implementation steps for the `Address` model, based on its simplified PRD (including custom fields) and following the TDD checklist format.

This covers the model for physical addresses, its fields, factory, admin, basic API (likely read-only or managed via related objects), and country code considerations.

--- START OF FILE address_implementation_steps.md ---

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

**Primary Location(s):**
`api/v1/base_models/common/` (Assuming `common` app for shared entities)

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`) are implemented.
[ ] Ensure the `common` app structure exists (`api/v1/base_models/common/`).
[ ] Ensure `factory-boy` is set up. Basic User factory exists.
[ ] **Decision:** How to handle the `country` field?
    *   Option A: Simple `CharField(max_length=2)`. Requires manual validation or choices list later.
    *   Option B: Use `django_countries.fields.CountryField`. Requires installing `django-countries`. Provides built-in choices and validation. **(Recommended)** Steps below assume **Option B**. Install: `pip install django-countries`. Add `'django_countries'` to `INSTALLED_APPS`.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `common`) verifying:
      *   An `Address` instance can be created with required fields (`country`).
      *   Optional fields can be set (`street_address_1`, `city`, etc.).
      *   `custom_fields` defaults to an empty dict.
      *   `latitude`/`longitude` accept Decimal values.
      *   `country` field stores/validates 2-char code (or validates based on `django-countries`).
      *   `__str__` method returns a reasonable string.
      *   Inherited `Timestamped`/`Auditable` fields exist.
      Run; expect failure (`Address` doesn't exist).
  [ ] Define the `Address` class in `api/v1/base_models/common/models.py`.
  [ ] Add required inheritance: `Timestamped`, `Auditable`.
      ```python
      # api/v1/base_models/common/models.py
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from core.models import Timestamped, Auditable # Adjust import path
      from django_countries.fields import CountryField # If using django-countries

      class Address(Timestamped, Auditable):
          street_address_1 = models.CharField(
              _("Street Address 1"), max_length=255
          )
          street_address_2 = models.CharField(
              _("Street Address 2"), max_length=255, blank=True
          )
          city = models.CharField(
              _("City"), max_length=100, db_index=True
          )
          state_province = models.CharField(
              _("State/Province/Region"), max_length=100, blank=True, db_index=True
          )
          postal_code = models.CharField(
              _("Postal/ZIP Code"), max_length=20, blank=True, db_index=True
          )
          # Option B: Using django-countries (Recommended)
          country = CountryField(
              _("Country"), db_index=True
          )
          # Option A: Simple CharField
          # country = models.CharField(
          #     _("Country"), max_length=2, db_index=True,
          #     help_text=_("ISO 3166-1 alpha-2 country code (e.g., US, GB).")
          # )

          latitude = models.DecimalField(
              _("Latitude"), max_digits=10, decimal_places=7, null=True, blank=True
          )
          longitude = models.DecimalField(
              _("Longitude"), max_digits=10, decimal_places=7, null=True, blank=True
          )
          status = models.CharField(
              _("Status"), max_length=20, blank=True, default='Active', db_index=True,
              # Define choices if needed, e.g., ('Active', 'Inactive', 'Needs Verification')
              # choices=STATUS_CHOICES,
              help_text=_("Optional status for the address.")
          )
          custom_fields = models.JSONField(
              _("Custom Fields"), default=dict, blank=True
          )

          class Meta:
              verbose_name = _("Address")
              verbose_name_plural = _("Addresses")
              # Example index - adjust based on common queries
              indexes = [
                  models.Index(fields=['country', 'postal_code']),
              ]

          def __str__(self):
              parts = [self.street_address_1, self.city, str(self.country)]
              return ", ".join(filter(None, parts)) # Join non-empty parts

      ```
  [ ] Run tests; expect pass. Refactor model code if needed.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `AddressFactory` in `api/v1/base_models/common/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from ..models import Address

      class AddressFactory(DjangoModelFactory):
          class Meta:
              model = Address

          street_address_1 = factory.Faker('street_address')
          city = factory.Faker('city')
          state_province = factory.Faker('state_abbr') # Or 'state' if full name needed
          postal_code = factory.Faker('postcode')
          country = factory.Faker('country_code') # Use 'country_code' if using django-countries
          # country = 'US' # Or fixed value if using CharField initially
          latitude = factory.Faker('latitude')
          longitude = factory.Faker('longitude')
          custom_fields = {}
          status = 'Active'
      ```
  [ ] **(Test)** Write a simple test ensuring `AddressFactory` creates valid `Address` instances.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Create/Update `api/v1/base_models/common/admin.py`.
  [ ] Define `AddressAdmin`:
      ```python
      from django.contrib import admin
      from .models import Address

      @admin.register(Address)
      class AddressAdmin(admin.ModelAdmin):
          list_display = (
              'id', '__str__', 'city', 'state_province',
              'postal_code', 'country', 'status', 'updated_at'
          )
          search_fields = (
              'street_address_1', 'street_address_2', 'city',
              'state_province', 'postal_code', 'country'
          )
          list_filter = ('country', 'status', 'state_province')
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
          fieldsets = (
              (None, {
                  'fields': (
                      'street_address_1', 'street_address_2', 'city',
                      'state_province', 'postal_code', 'country'
                  )
              }),
              ('Optional Info', {
                  'classes': ('collapse',),
                  'fields': ('latitude', 'longitude', 'status', 'custom_fields'),
              }),
              ('Audit Info', {
                   'classes': ('collapse',),
                   'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
              }),
          )
          # Add better widget for custom_fields JSON if needed (e.g., django-json-widget)
      ```
  [ ] **(Manual Test):** Verify registration and basic CRUD in Django Admin locally. Check country field works as expected.

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations api.v1.base_models.common`.
  [ ] **Review generated migration file carefully.** Check field definitions, indexes.
  [ ] Run `python manage.py migrate` locally.

  ### 3.5 Serializer Definition (`serializers.py`)

  [ ] **(Test First - Validation/Representation)** Write Unit/Integration Tests (`tests/unit/test_serializers.py`, `tests/integration/test_serializers.py`) for `AddressSerializer`. Test validation (country code format/choice, field lengths), representation, custom field handling.
  [ ] Define `AddressSerializer` in `api/v1/base_models/common/serializers.py`:
      ```python
      from rest_framework import serializers
      from django_countries.serializer_fields import CountryField # If using django-countries
      from ..models import Address

      class AddressSerializer(serializers.ModelSerializer):
          # If using django-countries, it provides a serializer field
          country = CountryField(country_dict=True) # Returns dict {'code': 'US', 'name': '...'}
          # Or if using simple CharField:
          # country = serializers.CharField(max_length=2)

          class Meta:
              model = Address
              fields = [
                  'id', # Usually include PK for reference
                  'street_address_1',
                  'street_address_2',
                  'city',
                  'state_province',
                  'postal_code',
                  'country',
                  'latitude',
                  'longitude',
                  'status',
                  'custom_fields',
                  'created_at', # Read-only
                  'updated_at', # Read-only
                  # Exclude created_by/updated_by unless specifically needed in API
              ]
              read_only_fields = ('id', 'created_at', 'updated_at')
      ```
  [ ] Implement `validate_custom_fields` method if applicable, validating against external schema.
  [ ] Implement `validate_country` if using simple CharField and need specific validation beyond length.
  [ ] Run tests; expect pass. Refactor.

  ### 3.6 API ViewSet Definition (`views.py`)

  [ ] **(Decision):** Will there be standalone `/api/v1/addresses/` endpoints, or will addresses *only* be managed nested under their owning objects (e.g., creating/updating an Organization updates its address)? **Assuming standalone management is NOT the primary pattern initially.** Address instances are created/updated *when needed* by other models. If standalone endpoints are needed later, they can be added.
  [ ] *(No ViewSet needed initially if addresses are managed via related objects)*.

  ### 3.7 URL Routing (`urls.py`)

  [ ] *(No URLs needed initially if no standalone ViewSet)*.

  ### 3.8 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] *(No direct API endpoint tests needed initially)*.
  [ ] **Indirect Testing:** Tests for *other* models' API endpoints (e.g., creating an Organization with an address payload) will implicitly test the `AddressSerializer` validation and creation/update of Address instances linked via ForeignKey. Ensure these tests cover address creation/validation scenarios.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov`).
[ ] Manually test address creation/editing via Django Admin and indirectly via API calls that manage related objects (e.g., UserProfile, Organization).
[ ] Review related documentation (Model fields, API Strategy on nested writes if applicable).

## 5. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request.
[ ] Update documentation.
[ ] Ensure other models (`UserProfile`, `Organization`, `Contact`, `Warehouse`, etc.) correctly add `ForeignKey` fields to `Address` as specified in their PRDs.

--- END OF FILE address_implementation_steps.md ---