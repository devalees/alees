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

  [ ] Create/Update `api/v1/base_models/organization/admin.py`.
  [ ] Define `OrganizationMembershipAdmin`. Use `raw_id_fields` for easier selection.
  [ ] **(Manual Test):** Verify Admin CRUD operations for memberships.

  ### 3.4 Implement `User.get_organizations()` Helper

  [ ] **(Test First)** Write Unit Tests (`tests/unit/test_models.py` in `user` app) for the `User.get_organizations()` method.
  [ ] Add/Modify the `get_organizations` method on the `User` model.
  [ ] Run `get_organizations` tests; expect pass. Refactor.

  ### 3.5 Migrations

  [x] Run `python manage.py makemigrations api.v1.base_models.organization`.
  [x] **Review generated migration file carefully.** Check FKs, `unique_together`, indexes.
  [x] Run `python manage.py migrate` locally.

  ### 3.6 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write tests for `OrganizationMembershipSerializer`. Test representation (including nested User/Org/Role names/IDs), validation (`unique_together` if creating via API), read-only fields.
  [ ] Define `OrganizationMembershipSerializer` in `api/v1/base_models/organization/serializers.py`.
  [ ] Run serializer tests; expect pass. Refactor.

  ### 3.7 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write API Tests for `/api/v1/organization-memberships/`. Test CRUD operations (likely admin-restricted). Test LIST filtering by user or organization. Test permissions.
  [ ] Define `OrganizationMembershipViewSet` in `api/v1/base_models/organization/views.py`.
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.8 URL Routing (`urls.py`)

  [ ] Import `OrganizationMembershipViewSet` in `api/v1/base_models/organization/urls.py`.
  [ ] Register with router: `router.register(r'organization-memberships', views.OrganizationMembershipViewSet)`.
  [ ] **(Test):** Rerun basic API tests; expect 2xx/4xx codes.

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests for Membership CRUD via API.
  [ ] Implement/Refine ViewSet and Serializer logic.
  [ ] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/base_models/organization`).
[ ] Manually test assigning/changing/removing user memberships via Django Admin. Test filtering/searching.
[ ] Review API documentation draft (if management API exposed).

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

### 6.2 Testing Strategy

1. **Unit Tests**: Focus on model behavior, validation, and constraints.
2. **Integration Tests**: Verify interactions with related models (User, Organization, Group).
3. **API Tests**: Will cover CRUD operations and permissions (pending implementation).

### 6.3 Next Steps

1. Complete the admin interface implementation.
2. Implement the `User.get_organizations()` helper method.
3. Develop the API layer (serializers, viewsets, and endpoints).
4. Add comprehensive API tests.

--- END OF FILE organizationmembership_implementation_steps.md ---