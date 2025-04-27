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