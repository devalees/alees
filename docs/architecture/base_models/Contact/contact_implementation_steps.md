
# Contact & Communication Channels - Implementation Steps (Consolidated, FINAL REVISED)

## 1. Overview

**Model Name(s):**
`Contact`, `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress`

**Corresponding PRD:**
`contact_prd.md` (Simplified version with Custom Fields and related Channel models)

**Depends On:**
`Timestamped`, `Auditable` (Done), `Address` (Done, in `common` app), `Organization` (#4 - Future), `django-taggit`, `django-phonenumber-field`. Requires `User` model.

**Key Features:**
Central model for individual contacts (`Contact`) with core details, status, tags, custom fields. `linked_organization` is **optional**. Separate related models handle multiple email addresses, phone numbers, and physical addresses (linking to `Address` model), each with type and primary flags.

**Primary Location(s):**
`api/v1/base_models/contact/` (Dedicated `contact` app)

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `Address` [in `common` app]) are implemented and migrated.
[ ] Ensure the `contact` app structure exists (`api/v1/base_models/contact/`). Add `'api.v1.base_models.contact'` to `INSTALLED_APPS`.
[ ] Install required libraries: `pip install django-taggit django-phonenumber-field`. Add `'taggit'` and `'phonenumber_field'` to `INSTALLED_APPS`.
[ ] Ensure `factory-boy` is set up. Factories for `Address` (in `common` app), `User` exist.
[ ] Define TYPE choices for Contact Status, Contact Type, and Channel Types (e.g., in `contact/choices.py`).

## 3. Implementation Steps (TDD Workflow)

  *(Models -> Single Primary Logic -> Factories -> Admin -> Migrations -> Serializer -> API)*

  ### 3.1 Model Definitions (`models.py`)

  [ ] **(Test First - Contact & Channels)**
      Write **Unit Test(s)** (`api/v1/base_models/contact/tests/unit/test_models.py`) verifying all four models (`Contact`, `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress`).
      *   Verify `Contact` creation, fields, inheritance. Ensure `linked_organization` FK exists and is **nullable**.
      *   Verify Channel models creation, fields, FKs (to `Contact`, `common.Address`), `unique_together`, `__str__`, inheritance.
      Run; expect failure.
  [ ] Define the `Contact` model *first* in `api/v1/base_models/contact/models.py`. Include `TaggableManager`. Ensure `linked_organization` uses `null=True, blank=True`.
  [ ] Define the communication channel models (`ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress`) *after* `Contact` in the same file. Ensure `ContactAddress` links correctly to `common.Address`.
      ```python
      # api/v1/base_models/contact/models.py
      # ... (imports as defined previously) ...

      class Contact(Timestamped, Auditable):
          # ... fields as defined previously ...
          linked_organization = models.ForeignKey(
              ORGANIZATION_MODEL, # Defined as 'organization.Organization'
              verbose_name=_("Linked Organization"),
              on_delete=models.SET_NULL,
              null=True, # Optional field - confirmed
              blank=True,
              related_name='contacts',
              # TODO: [POST-ORGANIZATION] Update related logic/querysets when Org exists.
          )
          # ... rest of Contact model ...

      # --- Communication Channel Models ---
      class ContactEmailAddress(Timestamped, Auditable): ... # As defined previously
      class ContactPhoneNumber(Timestamped, Auditable): ... # As defined previously
      class ContactAddress(Timestamped, Auditable): ... # As defined previously, links to 'common.Address'
      ```
  [ ] Run tests for all models; expect pass. Refactor.

  ### 3.2 Single Primary Logic (Model `save` override)

  [ ] **(Test First)** Write Integration Tests verifying single primary logic for Email, Phone, and Address models.
  [ ] Implement the `save()` override method on `ContactEmailAddress`, `ContactPhoneNumber`, and `ContactAddress` (as shown previously).
  [ ] Run single primary logic tests; expect pass. Refactor.

  ### 3.3 Factory Definitions (`tests/factories.py`)

  [ ] Define `ContactFactory` in `api/v1/base_models/contact/tests/factories.py`. Ensure `linked_organization` is `None` by default.
  [ ] Define factories for `ContactEmailAddress`, `ContactPhoneNumber`, `ContactAddress` in the same file. Ensure `ContactAddressFactory` uses `AddressFactory` from the `common` app.
      ```python
      # api/v1/base_models/contact/tests/factories.py
      # ... (imports as previously defined) ...

      class ContactFactory(DjangoModelFactory):
          class Meta: model = Contact
          # ... fields ...
          linked_organization = None # Optional field default
          # ...

      class ContactEmailAddressFactory(DjangoModelFactory): ... # As before
      class ContactPhoneNumberFactory(DjangoModelFactory): ... # As before
      class ContactAddressFactory(DjangoModelFactory): ... # As before
      ```
  [ ] **(Test)** Write simple tests ensuring factories create valid instances.

  ### 3.4 Admin Registration (`admin.py`)

  [ ] Create `api/v1/base_models/contact/admin.py`.
  [ ] Define `InlineModelAdmin` classes for channels.
  [ ] Define `ContactAdmin` including the inlines. Use `raw_id_fields` for `linked_organization`.
      ```python
      # api/v1/base_models/contact/admin.py
      # ... (definitions as previously shown) ...

      @admin.register(Contact)
      class ContactAdmin(admin.ModelAdmin):
          # ... (display, search, filter as before) ...
          raw_id_fields = ('linked_organization',) # Make optional FK easier
          inlines = [
              ContactEmailAddressInline,
              ContactPhoneNumberInline,
              ContactAddressInline,
          ]
          # ... rest of admin ...
      ```
  [ ] **(Manual Test):** Verify Admin interface works, including inline channels.

  ### 3.5 Migrations

  [ ] Run `python manage.py makemigrations contact`.
  [ ] **Review generated migration file(s) carefully.** Ensure `linked_organization_id` is nullable.
  [ ] Run `python manage.py migrate` locally.

  ### 3.6 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write tests for channel serializers and `ContactSerializer`. Handle nullable `linked_organization`. Test nested writes.
  [ ] Create `api/v1/base_models/contact/serializers.py`.
  [ ] Define channel serializers.
  [ ] Define `ContactSerializer`. Handle `linked_organization` as `required=False, allow_null=True`. Include `TaggitSerializer`. Implement/test nested write logic.
      ```python
      # api/v1/base_models/contact/serializers.py
      # ... (imports as defined previously) ...
      from api.v1.base_models.organization.models import Organization # For queryset

      # ... Channel Serializers ...

      class ContactSerializer(TaggitSerializer, serializers.ModelSerializer):
          # ... nested channel serializers ...
          linked_organization = serializers.PrimaryKeyRelatedField(
              queryset=Organization.objects.all(), # TODO: [POST-ORGANIZATION] Verify queryset.
              allow_null=True, # Optional field
              required=False
          )
          linked_organization_name = serializers.CharField(source='linked_organization.name', read_only=True, allow_null=True)
          # ... rest of Meta and fields ...

          # **CRITICAL:** Implement/test create/update to handle nested writes for channels
          # Add validate_custom_fields
      ```
  [ ] Run serializer tests; expect pass. Refactor (especially nested writes).

  ### 3.7 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests for `/api/v1/contacts/`.
  [ ] Create `api/v1/base_models/contact/views.py`. Define `ContactViewSet`. Prefetch related channels and `linked_organization`.
      ```python
      # api/v1/base_models/contact/views.py
      from rest_framework import viewsets, permissions
      from ..models import Contact
      from ..serializers import ContactSerializer
      # Import filters, permissions etc

      class ContactViewSet(viewsets.ModelViewSet): # Add OrgScoped mixin later IF contacts are scoped
          serializer_class = ContactSerializer
          permission_classes = [permissions.IsAuthenticated] # Add RBAC later
          queryset = Contact.objects.prefetch_related(
              'email_addresses', 'phone_numbers', 'addresses__address', 'tags' # Prefetch address via link model
          ).select_related('linked_organization').all()
          filter_backends = [...]
          # filterset_fields = [...]
          search_fields = [...]
          ordering_fields = [...]
      ```
  [ ] Run basic API tests; expect pass. Refactor.

  ### 3.8 URL Routing (`urls.py`)

  [ ] Create `api/v1/base_models/contact/urls.py`. Import `ContactViewSet`. Register with router: `router.register(r'contacts', views.ContactViewSet)`.
  [ ] Include `contact.urls` in `api/v1/base_models/urls.py`.
  [ ] **(Test):** Rerun basic API tests.

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests for `Contact` CRUD via `/api/v1/contacts/`.
      *   Test creating/updating contacts **with nested channel data**.
      *   Test primary flag logic via API updates.
      *   Test LIST with filtering.
      *   Test setting/unsetting optional `linked_organization`.
      *   Test validation errors. Test permissions. Test custom fields/tags.
  [ ] Implement/Refine ViewSet and Serializer logic, especially nested create/update.
  [ ] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api.v1.base_models.contact`).
[ ] Manually test Contact CRUD via API client and Admin UI, including nested channels.

## 5. Dependency Refinement / Post-Requisite Steps

*   **After `Organization` (#4) is implemented:**
    1.  **Refine `Contact.linked_organization` ForeignKey:**
        *   **(Decision):** Field is **Optional (nullable)** - confirmed.
        *   **Model Change:** No change needed.
        *   **Serializer Update:** Ensure `queryset=Organization.objects.all()` is correct in `ContactSerializer`.
        *   **Factory Update:** Update `ContactFactory` default for `linked_organization` to use `factory.SubFactory(OrganizationFactory)` if desired for typical test cases.
        *   **Rerun Tests:** Ensure tests pass, especially those involving creating/updating contacts with the organization link.

## 6. Follow-up Actions

[ ] Address TODOs (Nested write logic refinement, primary flag enforcement during nested create/update).
[ ] Create Pull Request for the `contact` app models and API.
[ ] Update API documentation.
[ ] Ensure other models needing contact links (e.g., `Organization`) add their FKs.

--- END OF FILE contact_implementation_steps.md (Consolidated, FINAL REVISED) ---