# OrganizationMembership - Implementation Steps

## 1. Overview

**Model Name:**
`OrganizationMembership`

**Corresponding PRD:**
`OrganizationMembership_prd.md`

**Depends On:**
`Timestamped`, `Auditable` (Abstract Base Models), `User` (`settings.AUTH_USER_MODEL`), `Organization`, Django `Group` (`django.contrib.auth.models.Group`).

**Key Features:**
Links Users to Organizations and assigns a specific Role (Django Group) for that membership. Enables multi-organization access and organization-specific roles. Core component for Org-Aware RBAC.

**Primary Location(s):**
`api/v1/base_models/organizations/` (Placing it within the organization app seems logical) or potentially a dedicated `memberships` app. Assume **`organizations` app** for this example.

## 2. Prerequisites

[x] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `User`, `Organization`) are implemented and migrated.
[x] Verify Django `auth` app (providing `Group`) and `contenttypes` app are configured.
[x] Ensure the `organization` app structure exists (`api/v1/base_models/organization/`).
[x] Ensure `factory-boy` is set up. Factories for `User`, `Organization`, `Group` exist.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [x] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `organization`) verifying:
      *   `OrganizationMembership` creation with required fields (`user`, `organization`, `role`).
      *   `unique_together` constraint (`user`, `organization`) is enforced.
      *   Default values (`is_active`). FKs work correctly.
      *   `__str__` method returns expected string.
      *   Inherited `Timestamped`/`Auditable` fields exist.
      Run; expect failure (`OrganizationMembership` doesn't exist).
  [x] Define the `OrganizationMembership` class in `api/v1/base_models/organization/models.py`.
  [x] Add required inheritance: `Timestamped`, `Auditable`.
  [x] Add model-level validation in `clean()` method to enforce unique constraint.
  [x] Run tests; all pass. Refactor complete.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [x] Define `OrganizationMembershipFactory` in `api/v1/base_models/organization/tests/factories.py`.
  [x] **(Test)** Write simple tests ensuring the factory creates valid instances and respects `unique_together`.

  ### 3.3 Admin Registration (`admin.py`)

  [x] Create/Update `api/v1/base_models/organization/admin.py`.
  [x] Define `OrganizationMembershipAdmin`. Use `raw_id_fields` for easier selection.
  [x] **(Manual Test):** Verify Admin CRUD operations for memberships.

  ### 3.4 Implement `User.get_organizations()` Helper

  [x] **(Test First)** Write Unit Tests (`tests/unit/test_models.py` in `user` app) for the `User.get_organizations()` method.
  [x] Add/Modify the `get_organizations` method on the `User` model.
  [x] Run `get_organizations` tests; expect pass. Refactor.

  ### 3.5 Migrations

  [x] Run `python manage.py makemigrations api.v1.base_models.organization`.
  [x] **Review generated migration file carefully.** Check FKs, `unique_together`, indexes.
  [x] Run `python manage.py migrate` locally.

  ### 3.6 Serializer Definition (`serializers.py`)

  [x] **(Test First)** Write tests for `OrganizationMembershipSerializer`. Test representation (including nested User/Org/Role names/IDs), validation (`unique_together` if creating via API), read-only fields.
  [x] Define `OrganizationMembershipSerializer` in `api/v1/base_models/organization/serializers.py`.
  [x] Run serializer tests; expect pass. Refactor.

  ### 3.7 API ViewSet Definition (`views.py`)

  [x] **(Test First)** Write API Tests for `/api/v1/organization-memberships/`. Test CRUD operations (likely admin-restricted). Test LIST filtering by user or organization. Test permissions.
  [x] Define `OrganizationMembershipViewSet` in `api/v1/base_models/organization/views.py`.
  [x] Run basic tests; expect pass. Refactor.

  ### 3.8 URL Routing (`urls.py`)

  [x] Import `OrganizationMembershipViewSet` in `api/v1/base_models/organization/urls.py`.
  [x] Register with router: `router.register(r'organization-memberships', views.OrganizationMembershipViewSet)`.
  [x] **(Test):** Rerun basic API tests; expect 2xx/4xx codes.

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [x] **(Test First - All)** Write comprehensive API tests for Membership CRUD via API.
  [x] Implement/Refine ViewSet and Serializer logic.
  [x] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[x] Run the *entire* test suite (`pytest`).
[x] Run linters (`flake8`) and formatters (`black`).
[x] Check code coverage (`pytest --cov=api/v1/base_models/organization`).
[x] Manually test assigning/changing/removing user memberships via Django Admin. Test filtering/searching.
[x] Review API documentation draft (if management API exposed).

## 5. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request.
[ ] Update documentation.
[ ] Ensure Org-Aware RBAC strategy and implementation uses this model correctly.
[ ] Ensure `OrganizationScoped` ViewSet Mixin correctly uses `user.get_organizations()` based on this model.

## 6. Implementation Notes

### 6.1 Key Decisions Made

1. **Model-Level Validation**: Added `clean()` method to enforce unique constraint at the model level, providing better user feedback than database-level constraints.
2. **Test Structure**: Using pytest fixtures and class-based tests for better organization and reusability.
3. **Fixture Organization**: Module-level fixtures for `user`, `organization`, and `role` to support multiple test classes.
4. **URL Namespace**: Implemented proper URL namespace handling with `v1:base_models:organization` prefix.
5. **Pagination**: Updated tests to handle paginated responses correctly.

### 6.2 Testing Strategy

1. **Unit Tests**: Focus on model behavior, validation, and constraints.
2. **Integration Tests**: Verify interactions with related models (User, Organization, Group).
3. **API Tests**: Comprehensive coverage of CRUD operations and permissions.

### 6.3 Current Status

1. All implementation steps completed successfully.
2. Test coverage exceeds requirements:
   - `models.py`: 83% coverage
   - `serializers.py`: 87% coverage
   - `views.py`: 96% coverage
   - `tests/api/test_endpoints.py`: 99% coverage
3. All tests passing with expected 2xx/4xx status codes.
4. URL routing properly configured with correct namespace handling.
5. Pagination implemented and tested.

### 6.4 Next Steps

1. Create Pull Request for review.
2. Update documentation with implementation details.
3. Integrate with Org-Aware RBAC system.
4. Implement `OrganizationScoped` ViewSet Mixin integration.

--- END OF FILE organizationmembership_implementation_steps.md ---