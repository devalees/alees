Okay, excellent. Based on your decisions:

1.  `UserProfile.primary_organization` will be **removed**.
2.  `UserProfile.profile_picture` will be **optional (nullable)**.
3.  `Contact.linked_organization` will be **optional (nullable)**.

I will now generate the updated implementation steps for `UserProfile` and `Contact` reflecting these final decisions.

--- START OF FILE userprofile_implementation_steps.md (FINAL REVISED) ---

# UserProfile - Implementation Steps (FINAL REVISED)

## 1. Overview

**Model Name:**
`UserProfile`

**Corresponding PRD:**
`UserProfile.md` (Refined version with Username Login + Custom Fields, **excluding** `primary_organization`)

**Depends On:**
Django `User` model (`settings.AUTH_USER_MODEL`), `Timestamped`, `Auditable`.
**Future Dependencies:** `FileStorage` (#7).

**Key Features:**
Extends Django User with ERP-specific fields (job title, phone, manager), preferences (language, timezone), custom fields, and signals for auto-creation. **Does not include a direct primary organization link.**

**Primary Location(s):**
`api/v1/base_models/user/` (Following chosen project structure)

## 2. Prerequisites

[x] Verify prerequisite models/mixins (`Timestamped`, `Auditable`) are implemented and migrated.
[x] Verify Django `auth` app is configured and `AUTH_USER_MODEL` is correctly set (default `auth.User`).
[x] Ensure the `user` app structure exists (`api/v1/base_models/user/`). Add `'api.v1.base_models.user'` to `INSTALLED_APPS`.
[x] Ensure `factory-boy` is set up. Create `UserFactory` if not already done.
[x] Ensure `FileStorage` model is planned for later implementation (#7). `profile_picture` will be initially nullable.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First - Basic)**
      Write **Unit Test(s)** (`api/v1/base_models/user/tests/unit/test_models.py`) verifying:
      *   A `UserProfile` instance can be created and linked to a `User` instance.
      *   The `__str__` method returns `user.username`.
      *   Inherited `Timestamped`/`Auditable` fields exist.
      *   `profile_picture` field exists and is nullable.
      *   **No** `primary_organization` field exists.
      Run; expect failure (`UserProfile` doesn't exist).
  [ ] Define the `UserProfile` class in `api/v1/base_models/user/models.py`.
  [ ] Add required inheritance: `Timestamped`, `Auditable`.
  [ ] Define the core `OneToOneField` link to `User`.
  [ ] Define basic attribute fields (job title, phone, manager, etc.).
  [ ] Define Preferences Fields (language, timezone, notifications).
  [ ] **Define Profile Picture Field (Temporarily Nullable):**
      *   Define `profile_picture` as `ForeignKey('common.FileStorage', ..., null=True, blank=True)`.
  [ ] Define `custom_fields` JSONField.
  [ ] Implement `__str__`.
      ```python
      # api/v1/base_models/user/models.py
      from django.conf import settings
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from core.models import Timestamped, Auditable # Assuming core app location

      # Forward reference string for FileStorage model
      FILESTORAGE_MODEL = 'common.FileStorage' # Adjust app_label if FileStorage is elsewhere

      class UserProfile(Timestamped, Auditable):
          user = models.OneToOneField(
              settings.AUTH_USER_MODEL,
              on_delete=models.CASCADE,
              related_name='profile',
              primary_key=True,
          )

          # Basic Attributes
          job_title = models.CharField(_("Job Title"), max_length=100, blank=True, null=True)
          employee_id = models.CharField(_("Employee ID"), max_length=50, unique=True, blank=True, null=True)
          phone_number = models.CharField(_("Phone Number"), max_length=30, blank=True, null=True) # Consider lib later
          manager = models.ForeignKey(
              settings.AUTH_USER_MODEL,
              verbose_name=_("Manager"),
              on_delete=models.SET_NULL,
              related_name='direct_reports',
              null=True,
              blank=True
          )
          date_of_birth = models.DateField(_("Date of Birth"), null=True, blank=True)
          employment_type = models.CharField(_("Employment Type"), max_length=50, blank=True, null=True) # Add choices later if needed

          # Profile Picture (Depends on FileStorage - Optional Field)
          profile_picture = models.ForeignKey(
              FILESTORAGE_MODEL,
              verbose_name=_("Profile Picture"),
              on_delete=models.SET_NULL,
              null=True, # Optional field
              blank=True
              # TODO: [POST-FILESTORAGE] Ensure FileStorage model exists and migrations run correctly.
          )

          # Preferences
          language = models.CharField(_("Language"), max_length=10, default=settings.LANGUAGE_CODE)
          timezone = models.CharField(_("Timezone"), max_length=60, default=settings.TIME_ZONE)
          notification_preferences = models.JSONField(_("Notification Preferences"), default=dict, blank=True)

          # Custom Fields
          custom_fields = models.JSONField(_("Custom Fields"), default=dict, blank=True)

          def __str__(self):
              return str(self.user.username)

          class Meta:
              verbose_name = _("User Profile")
              verbose_name_plural = _("User Profiles")
      ```
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `UserFactory` if not already done.
  [ ] Define `UserProfileFactory` in `api/v1/base_models/user/tests/factories.py`. Ensure `profile_picture` is `None` by default. **Remove** `primary_organization`.
      ```python
      # api/v1/base_models/user/tests/factories.py
      # ... UserFactory definition ...
      import factory
      from factory.django import DjangoModelFactory
      from ..models import UserProfile

      class UserProfileFactory(DjangoModelFactory):
          class Meta:
              model = UserProfile

          user = factory.SubFactory(UserFactory, profile=None)
          job_title = factory.Faker('job')
          phone_number = factory.Faker('phone_number') # Adjust if using phone lib factory integration
          language = 'en'
          timezone = 'UTC'
          profile_picture = None # Optional field
          manager = None # Optional field
          custom_fields = {}
          # Add other fields
      ```
  [ ] **(Test)** Write tests ensuring `UserProfileFactory` creates valid instances.

  ### 3.3 Signal for Auto-Creation (`signals.py` or `models.py`)

  [ ] **(Test First)** Write **Integration Test(s)** verifying automatic profile creation on `User` save.
  [ ] Define `post_save` receiver for `User` model (as shown previously).
  [ ] Connect the signal receiver in `apps.py` (as shown previously).
  [ ] Run signal tests; expect pass. Refactor.

  ### 3.4 Admin Registration (`admin.py`)

  [ ] Define `UserProfileInline(admin.StackedInline)`. **Remove** `primary_organization`. Include `profile_picture` (using `raw_id_fields`).
  [ ] Define `CustomUserAdmin` inheriting `BaseUserAdmin` and including the inline. **Remove** `get_organization` helper and related `list_select_related`/`list_display` entries for organization.
      ```python
      # api/v1/base_models/user/admin.py
      from django.contrib import admin
      from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
      from django.contrib.auth import get_user_model # Use getter
      from .models import UserProfile

      User = get_user_model()

      class UserProfileInline(admin.StackedInline):
          model = UserProfile
          can_delete = False
          verbose_name_plural = 'Profile'
          fk_name = 'user'
          fields = (
              'job_title', 'employee_id', 'phone_number', 'manager',
              'profile_picture', # Optional field
              'language', 'timezone', 'notification_preferences',
              'custom_fields'
          )
          raw_id_fields = ('manager', 'profile_picture') # Add profile picture here

      class CustomUserAdmin(BaseUserAdmin):
          inlines = (UserProfileInline,)
          # Adjust list_display - remove org reference
          list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
          # Adjust list_select_related - remove org reference
          list_select_related = ('profile',)

          def get_inline_instances(self, request, obj=None):
              if not obj:
                  return list()
              # Prevent error trying to show inline on user creation page before user is saved
              if obj.pk:
                  return super().get_inline_instances(request, obj)
              else:
                  return []

      admin.site.unregister(User)
      admin.site.register(User, CustomUserAdmin)
      ```
  [ ] **(Manual Test):** Verify Admin integration works correctly without org field.

  ### 3.5 Migrations

  [ ] Run `python manage.py makemigrations api.v1.base_models.user`.
  [ ] **Review generated migration file carefully.** Ensure `primary_organization_id` column is NOT created. `profile_picture_id` is created as nullable.
  [ ] Run `python manage.py migrate` locally.

  ### 3.6 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write tests for `UserProfileSerializer`. Test validation and representation. Handle nullable `profile_picture` field. **Remove** `primary_organization`.
  [ ] Define `UserProfileSerializer`. **Remove** `primary_organization` field. Update `profile_picture` field to be `required=False, allow_null=True`.
      ```python
      # api/v1/base_models/user/serializers.py
      from rest_framework import serializers
      from django.contrib.auth import get_user_model
      from .models import UserProfile
      # Import FileStorage for queryset when available
      from api.v1.base_models.common.models import FileStorage # Adjust path if needed

      User = get_user_model()

      class UserProfileSerializer(serializers.ModelSerializer):
          # ... read-only user fields ...
          username = serializers.CharField(source='user.username', read_only=True)
          email = serializers.EmailField(source='user.email', read_only=True)
          first_name = serializers.CharField(source='user.first_name', read_only=True)
          last_name = serializers.CharField(source='user.last_name', read_only=True)

          profile_picture = serializers.PrimaryKeyRelatedField(
              queryset=FileStorage.objects.all(), # TODO: [POST-FILESTORAGE] Verify queryset.
              allow_null=True, # Optional field
              required=False
          )
          manager = serializers.PrimaryKeyRelatedField(
              queryset=User.objects.all(), allow_null=True, required=False
          )

          class Meta:
              model = UserProfile
              fields = [
                  'user',
                  'username', 'email', 'first_name', 'last_name',
                  'job_title', 'employee_id', 'phone_number', # etc
                  'language', 'timezone', 'notification_preferences',
                  'profile_picture', # Optional field
                  'manager',
                  'custom_fields',
                  'created_at', 'updated_at',
              ]
              read_only_fields = ('user', 'created_at', 'updated_at')
      ```
  [ ] Implement `validate_custom_fields`.
  [ ] Run serializer tests; expect pass. Refactor.

  ### 3.7 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests for profile endpoints (e.g., `/profiles/me/`).
  [ ] Define `MyProfileView` (`RetrieveUpdateAPIView`) or admin ViewSet. No changes needed here due to `primary_organization` removal.
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.8 URL Routing (`urls.py`)

  [ ] Define URL patterns for profile views.
  [ ] **(Test):** Rerun basic API tests.

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - MyProfile)** Write tests for `GET` and `PUT`/`PATCH` on `/profiles/me/`. Test updating fields, including setting/unsetting `profile_picture`. **Remove** tests related to `primary_organization`.
  [ ] Implement view logic as needed.
  [ ] Run MyProfile tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api.v1.base_models.user`).
[ ] Manually test profile viewing/editing via API client and Django Admin.

## 5. Dependency Refinement / Post-Requisite Steps

*   **After `FileStorage` (#7) is implemented:**
    1.  **Refine `UserProfile.profile_picture` ForeignKey:**
        *   **(Decision):** Field is **Optional (nullable)** - confirmed.
        *   **Model Change:** No change needed.
        *   **Serializer Update:** Ensure `queryset=FileStorage.objects.all()` is correct in `UserProfileSerializer`.
        *   **Rerun Tests:** Ensure tests covering profile picture upload/linking via API pass.

## 6. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request for the `UserProfile` implementation.
[ ] Update relevant documentation.
[ ] Note that user-organization linkage is now handled solely by `OrganizationMembership`.

--- END OF FILE userprofile_implementation_steps.md (FINAL REVISED) ---

--- START OF FILE contact_implementation_steps.md (FINAL REVISED) ---

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