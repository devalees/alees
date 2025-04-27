Okay, understood completely. You need the implementation step files to be strictly executable in the defined order, managing any forward dependencies *within* the step file itself. This means if Model A depends on Model B (which is implemented later), Model A's steps must initially handle that dependency (e.g., by making the field nullable) and include a clear, separate section detailing the steps to finalize that field *after* Model B is done.

Let's apply this methodology. I will review the ranked list and generate the refined implementation steps for the *next* item, which is **`UserProfile.md`**, incorporating this dependency management strategy.

Here's the plan for refining `UserProfile`:

1.  **Identify Dependencies:**
    *   **Depends On:** `Timestamped`, `Auditable` (Abstract - OK), `User` (Built-in - OK), `Organization` (#4 in list - Future), `FileStorage` (#7 in list - Future).
2.  **Initial Implementation Modifications:**
    *   `primary_organization = ForeignKey(Organization, ...)`: This depends on `Organization`. It will be defined as `null=True, blank=True` initially.
    *   `profile_picture = ForeignKey(FileStorage, ...)`: This depends on `FileStorage`. It will be defined as `null=True, blank=True` initially.
3.  **Add Refinement Section:** A new section "Dependency Refinement / Post-Requisite Steps" will be added to `userprofile_implementation_steps.md`.
4.  **Populate Refinement Section:**
    *   Add steps to make `primary_organization` non-nullable (if required by final design) after `Organization` is implemented.
    *   Add steps to potentially make `profile_picture` non-nullable (if required) after `FileStorage` is implemented.

Let's generate the refined `userprofile_implementation_steps.md`:

--- START OF FILE userprofile_implementation_steps.md ---

# UserProfile - Implementation Steps (Revised for Dependencies)

## 1. Overview

**Model Name:**
`UserProfile`

**Corresponding PRD:**
`UserProfile_prd.md` (Refined version with Username Login + Custom Fields)

**Depends On:**
Django `User` model (`settings.AUTH_USER_MODEL`), `Timestamped`, `Auditable`.
**Future Dependencies:** `Organization` (#4), `FileStorage` (#7).

**Key Features:**
Extends Django User with ERP-specific fields (job title, phone, manager), preferences (language, timezone), organizational links, custom fields, and signals for auto-creation.

**Primary Location(s):**
`api/v1/base_models/user/` (Following chosen project structure)

## 2. Prerequisites

[x] Verify prerequisite models/mixins (`Timestamped`, `Auditable`) are implemented.
[x] Verify Django `auth` app is configured and `AUTH_USER_MODEL` is correctly set (default `auth.User`).
[x] Ensure the `user` app structure exists (`api/v1/base_models/user/`).
[x] Ensure `factory-boy` is set up. Create `UserFactory` if not already done.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First - Basic)**
      Write **Unit Test(s)** (`tests/unit/test_models.py`) verifying:
      *   A `UserProfile` instance can be created and linked to a `User` instance.
      *   The `__str__` method returns `user.username`.
      *   Inherited `Timestamped`/`Auditable` fields exist.
      *   Ensure tests handle temporarily nullable `primary_organization` and `profile_picture`.
      Run; expect failure (`UserProfile` doesn't exist).
  [ ] Define the `UserProfile` class in `api/v1/base_models/user/models.py`.
  [ ] Add required inheritance: `Timestamped`, `Auditable`.
  [ ] Define the core `OneToOneField` link to `User`.
  [ ] Define basic attribute fields (job title, phone, manager, etc.).
  [ ] Define Preferences Fields (language, timezone, notifications).
  [ ] **Define Organizational Relationship Field (Temporarily Nullable):**
      *   Define `primary_organization` as `ForeignKey('organization.Organization', ..., null=True, blank=True)`. Add `# TODO: [POST-ORGANIZATION]: Make primary_organization non-nullable if required.`
  [ ] **Define Profile Picture Field (Temporarily Nullable):**
      *   Define `profile_picture` as `ForeignKey('common.FileStorage', ..., null=True, blank=True)`. Add `# TODO: [POST-FILESTORAGE]: Make profile_picture non-nullable if required.`
  [ ] Define `custom_fields` JSONField.
  [ ] Implement `__str__`.
      ```python
      # api/v1/base_models/user/models.py
      from django.conf import settings
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from core.models import Timestamped, Auditable # Assuming core app location

      # Forward reference strings used for FKs to future models
      ORGANIZATION_MODEL = 'organization.Organization'
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
          phone_number = models.CharField(_("Phone Number"), max_length=30, blank=True, null=True)
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

          # Profile Picture (Depends on FileStorage)
          profile_picture = models.ForeignKey(
              FILESTORAGE_MODEL,
              verbose_name=_("Profile Picture"),
              on_delete=models.SET_NULL,
              null=True, # Initially nullable until FileStorage implemented
              blank=True
              # TODO: [POST-FILESTORAGE]: Make non-nullable if required and update tests/factories.
          )

          # Preferences
          language = models.CharField(_("Language"), max_length=10, default=settings.LANGUAGE_CODE)
          timezone = models.CharField(_("Timezone"), max_length=60, default=settings.TIME_ZONE)
          notification_preferences = models.JSONField(_("Notification Preferences"), default=dict, blank=True)

          # Organizational Relationships (Depends on Organization)
          primary_organization = models.ForeignKey(
              ORGANIZATION_MODEL,
              verbose_name=_("Primary Organization"),
              on_delete=models.PROTECT, # Protect Org if users linked
              related_name='primary_members',
              null=True, # Initially nullable until Organization implemented & requiredness confirmed
              blank=True
              # TODO: [POST-ORGANIZATION]: Make non-nullable if required and update tests/factories/migration.
          )

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
  [ ] Define `UserProfileFactory` in `api/v1/base_models/user/tests/factories.py`. Ensure `primary_organization` and `profile_picture` are handled correctly (likely `None` initially or require passing mocked IDs until the dependent models are ready).
      ```python
      # api/v1/base_models/user/tests/factories.py
      # ... UserFactory definition ...

      class UserProfileFactory(DjangoModelFactory):
          class Meta:
              model = UserProfile

          user = factory.SubFactory(UserFactory, profile=None)
          job_title = factory.Faker('job')
          phone_number = factory.Faker('phone_number')
          language = 'en'
          timezone = 'UTC'
          # Leave as None initially, or accept mocked instances/IDs in test setup
          primary_organization = None
          # profile_picture = None # If field exists
          custom_fields = {}
          # Add other fields, ensure manager is None by default or SubFactory(UserFactory)
      ```
  [ ] **(Test)** Write tests ensuring `UserProfileFactory` creates valid instances, handling the currently nullable FKs.

  ### 3.3 Signal for Auto-Creation (`signals.py` or `models.py`)

  [ ] **(Test First)** Write **Integration Test(s)** verifying automatic profile creation on `User` save.
  [ ] Define `post_save` receiver for `User` model (as shown previously).
  [ ] Connect the signal receiver in `apps.py` (as shown previously).
  [ ] Run signal tests; expect pass. Refactor.

  ### 3.4 Admin Registration (`admin.py`)

  [ ] Define `UserProfileInline(admin.StackedInline)`. Include temporarily nullable fields (`primary_organization`, `profile_picture`) but note they might become mandatory later. Use `raw_id_fields` for FKs like `manager`, `primary_organization`.
  [ ] Define `CustomUserAdmin` inheriting `BaseUserAdmin` and including the inline.
  [ ] Unregister default `UserAdmin` and register `CustomUserAdmin`.
      ```python
       # api/v1/base_models/user/admin.py
       # ... imports ...

       class UserProfileInline(admin.StackedInline):
           model = UserProfile
           can_delete = False
           verbose_name_plural = 'Profile'
           fk_name = 'user'
           fields = (
               'job_title', 'employee_id', 'phone_number', 'manager',
               'primary_organization', # Temporarily nullable
               # 'profile_picture', # Temporarily nullable/absent
               'language', 'timezone', 'notification_preferences',
               'custom_fields'
           )
           raw_id_fields = ('manager', 'primary_organization', 'profile_picture') # Add profile picture if field exists

       class CustomUserAdmin(BaseUserAdmin):
           # ... list_display etc from previous steps ...
           inlines = (UserProfileInline,)

           # Add 'primary_organization' to list_display using get_organization helper
           list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_organization')
           list_select_related = ('profile', 'profile__primary_organization')

           # ... get_inline_instances, get_organization methods ...

       # ... unregister/register User ...
      ```
  [ ] **(Manual Test):** Verify Admin integration.

  ### 3.5 Migrations

  [ ] Run `python manage.py makemigrations api.v1.base_models.user`.
  [ ] **Review generated migration file carefully.** Note `organization_id` and `profile_picture_id` columns are created as nullable.
  [ ] Run `python manage.py migrate` locally.

  ### 3.6 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write tests for `UserProfileSerializer` validation and representation. Handle nullable FKs correctly in tests.
  [ ] Define `UserProfileSerializer`. Include `primary_organization` and `profile_picture` fields. For writing, use `PrimaryKeyRelatedField(..., required=False, allow_null=True)`. For reading, consider nested serializers or exposing IDs.
      ```python
      # api/v1/base_models/user/serializers.py
      # ... imports ...

      class UserProfileSerializer(serializers.ModelSerializer):
          # ... user fields ...
          # Use PK fields for writing related models
          primary_organization = serializers.PrimaryKeyRelatedField(
              queryset=Organization.objects.all(), # Queryset will be empty until Org model exists
              allow_null=True, # Initially allow null
              required=False # Initially not required
              # TODO: [POST-ORGANIZATION] Update required/allow_null based on final design.
          )
          profile_picture = serializers.PrimaryKeyRelatedField(
              queryset=FileStorage.objects.all(), # Queryset will be empty until FS model exists
              allow_null=True,
              required=False
              # TODO: [POST-FILESTORAGE] Update required/allow_null.
          )
          manager = serializers.PrimaryKeyRelatedField(
              queryset=User.objects.all(), allow_null=True, required=False
          )

          class Meta:
              model = UserProfile
              fields = [
                  'user', # Read-only ID
                  # ... user fields ...
                  'job_title', # etc...
                  'language', 'timezone', 'notification_preferences',
                  'primary_organization', # Writable ID
                  'profile_picture',      # Writable ID
                  'manager',              # Writable ID
                  'custom_fields',
                  'created_at', 'updated_at',
              ]
              read_only_fields = ('user', 'created_at', 'updated_at')
      ```
  [ ] Implement `validate_custom_fields`.
  [ ] Run serializer tests; expect pass. Refactor.

  ### 3.7 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests for profile endpoints (e.g., `/profiles/me/`).
  [ ] Define `MyProfileView` (`RetrieveUpdateAPIView`) or admin ViewSet. Ensure tests pass with nullable FKs.
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.8 URL Routing (`urls.py`)

  [ ] Define URL patterns for profile views.
  [ ] **(Test):** Rerun basic API tests.

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - MyProfile)** Write tests for `GET` and `PUT`/`PATCH` on `/profiles/me/`. Test updating fields, including setting `primary_organization` and `profile_picture` to `None` or valid (mocked) IDs if possible during tests.
  [ ] Implement view logic as needed.
  [ ] Run MyProfile tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov`).
[ ] Manually test profile viewing/editing via API client and Django Admin.

## 5. Dependency Refinement / Post-Requisite Steps

*   **After `Organization` (#4) is implemented:**
    1.  **Refine `UserProfile.primary_organization` ForeignKey:**
        *   **(Decision):** Is `primary_organization` required? Assuming YES for this example.
        *   **(Test First):** Add/update unit tests for `UserProfile` ensuring `primary_organization` cannot be null. Update factory default. Update API tests ensuring `organization` is required on relevant profile updates/creates.
        *   **(Data Migration):** Create data migration (`makemigrations --empty ...`) to populate `primary_organization` for any existing `UserProfile` records that have `NULL`. Decide on a default org or raise error if assignment isn't clear.
        *   **Model Change:** Modify `UserProfile` model in `models.py`, remove `null=True, blank=True` from `primary_organization`.
        *   **Schema Migration:** Run `makemigrations user` and `migrate`.
        *   **Update Serializer:** Change `PrimaryKeyRelatedField` for `primary_organization` in `UserProfileSerializer` to `required=True, allow_null=False`.
        *   **Rerun Tests:** Ensure all tests pass.
*   **After `FileStorage` (#7) is implemented:**
    1.  **Refine `UserProfile.profile_picture` ForeignKey:**
        *   **(Decision):** Is `profile_picture` required? Assuming NO (it's optional).
        *   **(Test First):** Ensure tests cover setting and unsetting the profile picture correctly via API and factory.
        *   **Model Change:** No change needed if it remains nullable. If made required, follow similar steps as for `primary_organization`.
        *   **Update Serializer:** Ensure `PrimaryKeyRelatedField` for `profile_picture` points to the correct `FileStorage` queryset and has `required=False, allow_null=True`.
        *   **Rerun Tests:** Ensure all tests pass.

## 6. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request for the initial `UserProfile` implementation.
[ ] Update relevant documentation.
[ ] Ensure subsequent PRs address the "Dependency Refinement" steps after `Organization` and `FileStorage` are merged.

--- END OF FILE userprofile_implementation_steps.md ---

This revised structure explicitly handles the forward dependencies by making the relevant fields nullable initially and outlining the necessary steps to finalize them later in a dedicated section. This should provide the precision needed for sequential execution by the AI agent.