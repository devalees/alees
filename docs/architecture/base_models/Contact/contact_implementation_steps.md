
# Contact & Communication Channels - Implementation Steps (Consolidated, REVISED FOR ORG DEPENDENCY)

*(Reflecting the pragmatic approach to handle the Org dependency)*

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

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `Address`) are implemented and migrated.
[ ] Ensure the `contact` app structure exists and is added to `INSTALLED_APPS`.
[ ] Install required libraries: `pip install django-taggit django-phonenumber-field`. Add to `INSTALLED_APPS`.
[ ] Ensure `factory-boy` setup. Factories for `Address`, `User` exist.
[ ] Define TYPE choices (e.g., in `contact/choices.py`).

## 3. Implementation Steps (TDD Workflow)

  *(Models -> Single Primary Logic -> Factories -> Admin -> Migrations -> **Serializer (w/ Workaround)** -> API -> **Serializer Refactor (Later)**)*

  ### 3.1 Model Definitions (`models.py`)

  [ ] **(Test First - Contact & Channels)** Write Unit Tests verifying all models (`Contact`, `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress`). Ensure `Contact.linked_organization` FK exists and is **nullable**.
  [ ] Define the `Contact` model *first* in `api/v1/base_models/contact/models.py`. Ensure `linked_organization` uses `null=True, blank=True`. Include `TaggableManager`.
  [ ] Define the communication channel models (`ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress`) *after* `Contact`. Ensure `ContactAddress` links correctly to `common.Address`.
  [ ] Run tests for all models; expect pass. Refactor.

  ### 3.2 Single Primary Logic (Model `save` override)

  [ ] **(Test First)** Write Integration Tests verifying single primary logic for Email, Phone, and Address models.
  [ ] Implement the `save()` override method on channel models.
  [ ] Run single primary logic tests; expect pass. Refactor.

  ### 3.3 Factory Definitions (`tests/factories.py`)

  [ ] Define `ContactFactory`. Ensure `linked_organization` is `None` by default.
  [ ] Define factories for `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress`.
  [ ] **(Test)** Write simple tests ensuring factories create valid instances.

  ### 3.4 Admin Registration (`admin.py`)

  [ ] Create `api/v1/base_models/contact/admin.py`.
  [ ] Define `InlineModelAdmin` classes for channels.
  [ ] Define `ContactAdmin` including the inlines. Use `raw_id_fields` for `linked_organization`.
  [ ] **(Manual Test):** Verify Admin interface works.

  ### 3.5 Migrations

  [ ] Run `python manage.py makemigrations contact`.
  [ ] **Review generated migration file(s) carefully.** Ensure `linked_organization_id` column is **nullable**.
  [ ] Run `python manage.py migrate` locally.

  ### 3.6 Serializer Definition (`serializers.py`) - ***Initial Version***

  [ ] **(Test First)** Write tests for channel serializers and `ContactSerializer`. Test nested writes. Test accepting `linked_organization_id` (nullable integer).
  [ ] Create `api/v1/base_models/contact/serializers.py`.
  [ ] Define channel serializers.
  [ ] Define `ContactSerializer`. **Use a temporary workaround for `linked_organization`**: Accept/validate the ID directly. Include `TaggitSerializer`. Implement nested write logic.
      ```python
      # api/v1/base_models/contact/serializers.py
      from rest_framework import serializers
      from taggit.serializers import TagListSerializerField, TaggitSerializer
      from django.apps import apps # Needed for lazy model loading

      from ..models import Contact, ContactEmailAddress, ContactPhoneNumber, ContactAddress
      from api.v1.base_models.common.models import Address # For nested Address in ContactAddressSerializer
      from api.v1.base_models.common.serializers import AddressSerializer # For nested Address

      # --- Channel Serializers ---
      class ContactEmailAddressSerializer(...): ...
      class ContactPhoneNumberSerializer(...): ...
      class ContactAddressSerializer(...):
          # Include nested AddressSerializer potentially
          # address = AddressSerializer() # Or PrimaryKeyRelatedField for write
          ...

      class ContactSerializer(TaggitSerializer, serializers.ModelSerializer):
          tags = TagListSerializerField(required=False)
          email_addresses = ContactEmailAddressSerializer(many=True, required=False)
          phone_numbers = ContactPhoneNumberSerializer(many=True, required=False)
          addresses = ContactAddressSerializer(many=True, required=False)

          # --- Temporary Workaround for Organization Link ---
          # TODO: [POST-ORGANIZATION] Refactor to use PrimaryKeyRelatedField once Organization model exists.
          linked_organization_id = serializers.IntegerField(
              source='linked_organization_id', # Link directly to the FK field ID
              allow_null=True,
              required=False,
              write_only=True # ID is only for writing
          )
          # --- End Workaround ---

          # Read-only representation of the linked org name (if link exists)
          linked_organization_name = serializers.CharField(
              source='linked_organization.name', read_only=True, allow_null=True
          )

          class Meta:
              model = Contact
              fields = [
                  'id', 'first_name', 'last_name', 'title', 'organization_name',
                  'linked_organization_id', # Temporary Write Field
                  'linked_organization_name', # Read Field
                  'contact_type', 'status', 'source', 'notes', 'tags', 'custom_fields',
                  'email_addresses', 'phone_numbers', 'addresses', # Nested fields
                  'created_at', 'updated_at',
              ]
              read_only_fields = ('id', 'linked_organization_name', 'created_at', 'updated_at')

          def validate_linked_organization_id(self, value):
              """Manual validation until Organization model is implemented."""
              if value is not None:
                  # Basic check - can't fully validate existence yet
                  if not isinstance(value, int) or value <= 0:
                       raise serializers.ValidationError("Invalid Organization ID provided.")
                  # Real validation happens post-refactor with PrimaryKeyRelatedField
              return value

          # **CRITICAL:** Implement create/update to handle nested writes for channels
          # and to correctly set linked_organization_id from the input data.
          def create(self, validated_data):
              # Pop nested data
              emails_data = validated_data.pop('email_addresses', [])
              phones_data = validated_data.pop('phone_numbers', [])
              addresses_data = validated_data.pop('addresses', [])
              # linked_organization_id is already in validated_data due to source mapping

              contact = Contact.objects.create(**validated_data)

              # Create nested objects... (implement this logic)
              self._create_nested_channels(contact, emails_data, phones_data, addresses_data)

              return contact

          def update(self, instance, validated_data):
              # Pop nested data
              emails_data = validated_data.pop('email_addresses', None)
              phones_data = validated_data.pop('phone_numbers', None)
              addresses_data = validated_data.pop('addresses', None)

              # Update instance fields
              instance = super().update(instance, validated_data)

              # Update/Create/Delete nested objects... (implement this complex logic)
              if emails_data is not None: self._update_nested_emails(instance, emails_data)
              # ... similar for phones and addresses ...

              return instance

          # --- Helper methods for nested writes (implement these) ---
          def _create_nested_channels(self, contact, emails_data, phones_data, addresses_data): ...
          def _update_nested_emails(self, contact, emails_data): ...
          # ...

          # Add validate_custom_fields
      ```
  [ ] Run serializer tests; expect pass (mocking Org validation if needed). Refactor (especially nested writes).

  ### 3.7 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests for `/api/v1/contacts/`. Test basic CRUD structure.
  [ ] Create `api/v1/base_models/contact/views.py`. Define `ContactViewSet`. Prefetch related channels. Add filtering/search/ordering.
  [ ] Run basic API tests; expect pass. Refactor.

  ### 3.8 URL Routing (`urls.py`)

  [ ] Create `api/v1/base_models/contact/urls.py`. Import `ContactViewSet`. Register with router.
  [ ] Include `contact.urls` in `api/v1/base_models/urls.py`.
  [ ] **(Test):** Rerun basic API tests.

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests for `Contact` CRUD via `/api/v1/contacts/`.
      *   Test creating/updating contacts **with nested channel data**.
      *   Test primary flag logic via API updates.
      *   Test LIST with filtering.
      *   Test setting/unsetting optional `linked_organization_id`.
      *   Test validation errors. Test permissions. Test custom fields/tags.
  [ ] Implement/Refine ViewSet and Serializer logic, especially nested create/update.
  [ ] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api.v1.base_models.contact`).
[ ] Manually test Contact CRUD via API client and Admin UI, including nested channels and setting `linked_organization_id`.

## 5. Dependency Refinement / Post-Requisite Steps - ***CRITICAL***

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

[ ] Address TODOs (Nested write logic refinement, primary flag enforcement during nested create/update).
[ ] **Complete the Refactoring Step in #5 above after Organization is implemented.**
[ ] Create Pull Request for the `contact` app models and API (initial version).
[ ] Create separate Pull Request for the refactoring step later.
[ ] Update API documentation.

---

This updated plan implements `Contact` first, acknowledges the dependency, provides a specific workaround for the serializer, and crucially adds the step to refactor the serializer once `Organization` is available.