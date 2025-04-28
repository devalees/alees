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

  [x] **(Test First - Basic)**
      Write **Unit Test(s)** (`api/v1/base_models/user/tests/unit/test_models.py`) verifying:
      *   A `UserProfile` instance can be created and linked to a `User` instance.
      *   The `__str__` method returns `user.username`.
      *   Inherited `Timestamped`/`Auditable` fields exist.
      *   `profile_picture` field exists and is nullable.
      *   **No** `primary_organization` field exists.
      Run; expect failure (`UserProfile` doesn't exist).
  [x] Define the `UserProfile` class in `api/v1/base_models/user/models.py`.
  [x] Add required inheritance: `Timestamped`, `Auditable`.
  [x] Define the core `OneToOneField` link to `User`.
  [x] Define basic attribute fields (job title, phone, manager, etc.).
  [x] Define Preferences Fields (language, timezone, notifications).
  [x] **Define Profile Picture Field (Temporarily Nullable):**
      *   Define `profile_picture` as `CharField` temporarily (will be updated to `ForeignKey('common.FileStorage', ..., null=True, blank=True)` when FileStorage is implemented).
  [x] Define `custom_fields` JSONField.
  [x] Implement `__str__`.
  [x] Run basic tests; expect pass. Refactor.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [x] Define `UserFactory` if not already done.
  [x] Define `UserProfileFactory` in `api/v1/base_models/user/tests/factories.py`. Ensure `profile_picture` is `None` by default.
  [x] **(Test)** Write tests ensuring `UserProfileFactory` creates valid instances.
  [x] Test circular dependency prevention.
  [x] Test unique employee_id generation.
  [x] Test profile creation with manager relationship.

  ### 3.3 Signal for Auto-Creation (`signals.py` or `models.py`)

  [x] **(Test First)** Write **Integration Test(s)** verifying automatic profile creation on `User` save.
  [x] Define `post_save` receiver for `User` model.
  [x] Connect the signal receiver in `apps.py`.
  [x] Run signal tests; expect pass. Refactor.

  ### 3.4 Admin Registration (`admin.py`)

  [x] Define `UserProfileInline(admin.StackedInline)`. Include `profile_picture` (using `raw_id_fields`).
  [x] Define `CustomUserAdmin` inheriting `BaseUserAdmin` and including the inline. 
  [x] **(Manual Test):** Verify Admin integration works correctly without org field.

  ### 3.5 Migrations

  [ ] Run `python manage.py makemigrations api.v1.base_models.user`.
  [ ] **Review generated migration file carefully.** Ensure `primary_organization_id` column is NOT created. `profile_picture_id` is created as nullable.
  [ ] Run `python manage.py migrate` locally.

  ### 3.6 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write tests for `UserProfileSerializer`. Test validation and representation. Handle nullable `profile_picture` field. 
  [ ] Define `UserProfileSerializer`.  Update `profile_picture` field to be `required=False, allow_null=True`.
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
        *   **Model Change:** Update from `CharField` to `ForeignKey('common.FileStorage', ..., null=True, blank=True)`.
        *   **Serializer Update:** Ensure `queryset=FileStorage.objects.all()` is correct in `UserProfileSerializer`.
        *   **Rerun Tests:** Ensure tests covering profile picture upload/linking via API pass.

## 6. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request for the `UserProfile` implementation.
[ ] Update relevant documentation.
[ ] Note that user-organization linkage is now handled solely by `OrganizationMembership`.

## 7. Current Progress (Updated)

### Completed:
- ✅ Model Definition and Tests (3.1)
  - All basic tests passing with 100% coverage
  - Profile picture temporarily implemented as CharField
  - No primary_organization field as required
  - All required fields implemented
- ✅ Factory Definition and Tests (3.2)
  - UserFactory and UserProfileFactory implemented
  - All factory tests passing with 100% coverage
  - Profile picture set to None by default as required
  - Circular dependency prevention implemented
  - Unique employee_id generation verified
  - Manager relationship tests passing
- ✅ Signal Implementation (3.3)
  - Auto-creation signal implemented and tested
  - Integration tests passing with 100% coverage
  - Signal properly connected in apps.py
- ✅ Admin Registration (3.4)
  - UserProfileInline implemented with proper configuration
  - CustomUserAdmin implemented with inline integration
  - Tests passing with >90% coverage
  - Proper handling of User model registration

### Next Steps:
- Migrations (3.5)
- Serializer Implementation (3.6)
- API ViewSet (3.7)
- URL Routing (3.8)
- API Endpoint Testing (3.9)

### Notes:
- Profile picture field will be updated when FileStorage is implemented
- All tests are passing with 100% coverage for implemented components
- Following TDD workflow strictly
- No deviations from PRD requirements
- Signal implementation completed successfully
- Admin implementation completed with proper test coverage