# Contact & Communication Channels - Implementation Steps (Updated for Current Progress)

## 1. Overview

**Model Name(s):**
`Contact`, `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress`

**Corresponding PRD:**
`contact_prd.md` (Revised version)

**Depends On:**
`Timestamped`, `Auditable` (Done), `Address` (Done), `User` (Done). Requires `django-taggit`, `django-phonenumber-field`.
**Future Dependency:** `Organization` (#4 - Will be implemented *after* this).

**Key Features:**
Central model for individual contacts (`Contact`) with optional link to `Organization`. Includes related models for multiple communication channels.

**Primary Location(s):**
`api/v1/base_models/contact/` (Dedicated `contact` app)

## 2. Prerequisites

[x] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `Address`) are implemented and migrated.
[x] Ensure the `contact` app structure exists and is added to `INSTALLED_APPS`.
[x] Install required libraries: `pip install django-taggit django-phonenumber-field`. Add to `INSTALLED_APPS`.
[x] Ensure `factory-boy` setup. Factories for `Address`, `User` exist.
[x] Define TYPE choices (e.g., in `contact/choices.py`).

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definitions (`models.py`) - COMPLETED

  [x] **(Test First - Contact & Channels)** Write Unit Tests verifying all models (`Contact`, `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress`). Ensure `Contact.linked_organization` FK exists and is **nullable**.
  [x] Define the `Contact` model *first* in `api/v1/base_models/contact/models.py`. Ensure `linked_organization` uses `null=True, blank=True`. Include `TaggableManager`.
  [x] Define the communication channel models (`ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress`) *after* `Contact`. Ensure `ContactAddress` links correctly to `common.Address`.
  [x] Run tests for all models; expect pass. Refactor.

  ### 3.2 Single Primary Logic (Model `save` override) - COMPLETED

  [x] **(Test First)** Write Integration Tests verifying single primary logic for Email, Phone, and Address models.
  [x] Implement the `save()` override method on channel models.
  [x] Run single primary logic tests; expect pass. Refactor.

  ### 3.3 Factory Definitions (`tests/factories.py`) - COMPLETED

  [x] Define `ContactFactory`. Ensure `linked_organization` is `None` by default.
  [x] Define factories for `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress`.
  [x] **(Test)** Write simple tests ensuring factories create valid instances.

  ### 3.4 Admin Registration (`admin.py`) - COMPLETED

  [x] Create `api/v1/base_models/contact/admin.py`.
  [x] Define `InlineModelAdmin` classes for channels.
  [x] Define `ContactAdmin` including the inlines. Use `raw_id_fields` for `linked_organization`.
  [x] **(Manual Test):** Verify Admin interface works.

  ### 3.5 Migrations - COMPLETED

  [x] Run `python manage.py makemigrations contact`.
  [x] **Review generated migration file(s) carefully.** Ensure `linked_organization_id` column is **nullable**.
  [x] Run `python manage.py migrate` locally.

  ### 3.6 Serializer Definition (`serializers.py`) - COMPLETED

  [x] **(Test First)** Write tests for channel serializers and `ContactSerializer`. Test nested writes. Test accepting `linked_organization_id` (nullable integer).
  [x] Create `api/v1/base_models/contact/serializers.py`.
  [x] Define channel serializers.
  [x] Define `ContactSerializer` with:
      - Proper validation for `organization_id` and `linked_organization_id`
      - Nested serializers for email addresses, phone numbers, and addresses
      - Tag support via `TaggitSerializer`
      - Custom field validation
      - Proper handling of primary flags
      - Comprehensive logging
  [x] Run serializer tests; expect pass. Refactor.

  ### 3.7 API ViewSet Definition (`views.py`) - COMPLETED

  [x] **(Test First)** Write basic API Tests for `/api/v1/contacts/`. Test basic CRUD structure.
  [x] Create `api/v1/base_models/contact/views.py`. Define `ContactViewSet`. Prefetch related channels. Add filtering/search/ordering.
  [x] Run basic API tests; expect pass. Refactor.

  ### 3.8 URL Routing (`urls.py`) - COMPLETED

  [x] Create `api/v1/base_models/contact/urls.py`. Import `ContactViewSet`. Register with router.
  [x] Include `contact.urls` in `api/v1/base_models/urls.py`.
  [x] **(Test):** Rerun basic API tests.

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`) - COMPLETED

  [x] **(Test First - All)** Write comprehensive API tests for `Contact` CRUD via `/api/v1/contacts/`.
      *   Test creating/updating contacts **with nested channel data**.
      *   Test primary flag logic via API updates.
      *   Test LIST with filtering.
      *   Test setting/unsetting optional `linked_organization_id`.
      *   Test validation errors. Test permissions. Test custom fields/tags.
  [x] Implement/Refine ViewSet and Serializer logic, especially nested create/update.
  [x] Run all API tests; expect pass. Refactor.

## 4. Final Checks - COMPLETED

[x] Run the *entire* test suite (`pytest`).
[x] Run linters (`flake8`) and formatters (`black`).
[x] Check code coverage (`pytest --cov=api.v1.base_models.contact`).
[x] Manually test Contact CRUD via API client and Admin UI, including nested channels and setting `linked_organization_id`.

## 5. Dependency Refinement / Post-Requisite Steps - PENDING

*   **After `Organization` (#4) is implemented:**
    1.  **Refactor `ContactSerializer`:**
        *   Remove the temporary `linked_organization_id` field and its `validate_` method.
        *   Add the standard `PrimaryKeyRelatedField`:
            ```python
            linked_organization = serializers.PrimaryKeyRelatedField(
                queryset=Organization.objects.all(), # Now Org exists!
                allow_null=True, # Optional field
                required=False
            )
            ```
        *   Update the `fields` list in `Meta` to include `linked_organization` instead of `linked_organization_id`.
        *   Adjust `create`/`update` methods if they were directly using `linked_organization_id`. `validated_data` will now contain the `Organization` instance or `None`.
    2.  **Update API Tests:** Modify API tests to send `linked_organization` (with a valid Org PK or null) instead of `linked_organization_id`. Ensure validation against existing Orgs works.
    3.  **Rerun Tests:** Ensure all `contact` tests (Unit, Serializer, API) pass after the refactor.

## 6. Follow-up Actions

[x] Address TODOs (Nested write logic refinement, primary flag enforcement during nested create/update).
[ ] **Complete the Refactoring Step in #5 above after Organization is implemented.**
[x] Create Pull Request for the `contact` app models and API (initial version).
[ ] Create separate Pull Request for the refactoring step later.
[x] Update API documentation.

---

## Current Status Summary

- All core functionality is implemented and tested
- All tests are passing (209 passed, 2 skipped)
- Code coverage is at 94% overall
- The implementation includes proper validation for organization IDs
- Nested serialization for communication channels is working
- Primary flag logic is properly enforced
- Comprehensive logging is in place
- The only pending item is the Organization dependency refactoring

The implementation is stable and production-ready, with the only remaining task being the Organization model integration refactoring.