
# UserProfile - Implementation Steps (CLEANED - V5)

## 1. Overview

**Model Name:**
`UserProfile`

**Corresponding PRD:**
`UserProfile.md` (Refined version with Username Login + Custom Fields, excluding direct primary organization link)

**Depends On:**
Django `User` model (`settings.AUTH_USER_MODEL`), `Timestamped`, `Auditable`.
**Future Dependencies:** `FileStorage` (#7 in ranking).

**Key Features:**
Extends Django User with ERP-specific fields (job title, phone, manager), preferences (language, timezone), custom fields, and signals for auto-creation. User-Organization linkage is managed exclusively via `OrganizationMembership`.

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

  [x] **(Test First - Basic)**
      Write **Unit Test(s)** (`api/v1/base_models/user/tests/unit/test_models.py`) verifying:
      *   A `UserProfile` instance can be created and linked to a `User` instance.
      *   The `__str__` method returns `user.username`.
      *   Inherited `Timestamped`/`Auditable` fields exist.
      *   `profile_picture` field exists and is nullable.
      *   Confirm necessary fields like `job_title`, `phone_number`, `manager`, preferences, `custom_fields` exist.
  [x] Define the `UserProfile` class in `api/v1/base_models/user/models.py`.
  [x] Add required inheritance: `Timestamped`, `Auditable`.
  [x] Define the core `OneToOneField` link to `User`.
  [x] Define basic attribute fields, Preferences Fields, Profile Picture Field (initially nullable), and `custom_fields`.
  [x] Run basic tests; expect pass. Refactor.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [x] Define `UserFactory` if not already done.
  [x] Define `UserProfileFactory` in `api/v1/base_models/user/tests/factories.py`. Ensure `profile_picture` is `None` by default.
  [x] **(Test)** Write tests ensuring `UserProfileFactory` creates valid instances.

  ### 3.3 Signal for Auto-Creation (`signals.py` or `models.py`)

  [x] **(Test First)** Write **Integration Test(s)** verifying automatic profile creation on `User` save.
  [x] Define `post_save` receiver for `User` model.
  [x] Connect the signal receiver in `apps.py`.
  [x] Run signal tests; expect pass. Refactor.

  ### 3.4 Admin Registration (`admin.py`)

  [x] Define `UserProfileInline(admin.StackedInline)`. Include `profile_picture` (using `raw_id_fields`).
  [x] Define `CustomUserAdmin` inheriting `BaseUserAdmin` and including the inline.
  [x] **(Test)** Write tests for admin registration and inline configuration.
  [x] Run admin tests; expect pass. Refactor.

  ### 3.5 Migrations

  [x] Run `python manage.py makemigrations api.v1.base_models.user`.
  [x] **Review generated migration file carefully.** `profile_picture_id` is created as nullable.
  [x] Run `python manage.py migrate` locally.

  ### 3.6 Serializer Definition (`serializers.py`)

  [x] **(Test First)** Write tests for `UserProfileSerializer`. Handle nullable `profile_picture`.
  [x] Define `UserProfileSerializer`. Ensure `profile_picture` field is `required=False, allow_null=True`.
  [x] Implement `validate_custom_fields`.
  [x] Run serializer tests; expect pass. Refactor.

  ### 3.7 API ViewSet Definition (`views.py`)

  [x] **(Test First)** Write basic API Tests for profile endpoints (e.g., `/profiles/me/`).
  [x] Define `MyProfileView` (`RetrieveUpdateAPIView`) with proper authentication.
  [x] Run basic tests; expect pass. Refactor.

  ### 3.8 URL Routing (`urls.py`)

  [x] Define URL patterns in `api/v1/base_models/user/urls.py` for the chosen views (e.g., `path('profiles/me/', views.MyProfileView.as_view(), name='my-profile')`).
  [x] Include these URLs in `api/v1/base_models/urls.py`.
  [x] **(Test):** Rerun basic API tests.

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [x] **(Test First - MyProfile)** Write tests for `GET` and `PUT`/`PATCH` on `/profiles/me/`. Test updating fields, including setting/unsetting `profile_picture`.
  [x] Implement view logic as needed.
  [x] Run MyProfile tests; expect pass. Refactor.

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
        *   **Serializer Update:** Update `queryset` in `PrimaryKeyRelatedField` for `profile_picture` in `UserProfileSerializer` to `FileStorage.objects.all()` (or scoped queryset if needed). Adjust `read_only` status based on how the picture is intended to be set/updated (e.g., make it `required=False` if allowing update via profile endpoint, or keep `read_only=True` if using a separate upload URL).
        *   **Rerun Tests:** Ensure tests covering profile picture linking via API pass according to the chosen update mechanism.

## 6. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request for the `UserProfile` implementation.
[ ] Update relevant documentation.
[ ] Note that user-organization linkage is handled solely by `OrganizationMembership`.

--- END OF FILE userprofile_implementation_steps.md (CLEANED - V5) ---

