
# OrganizationScoped Mechanism - Implementation Steps

## 1. Overview

**Component Name:**
`OrganizationScoped` (Abstract Base Model) & `OrganizationScopedViewSetMixin`

**Corresponding PRD:**
`organizationscoped_prd.md` (Revised for Simple Org-Aware RBAC - Final)

**Depends On:**
`Organization` model (Done), `User` model (Done), `OrganizationMembership` model (Done), Org-Aware RBAC check function (`has_perm_in_org` - **To Be Implemented Next**), DRF (`viewsets`, `mixins`), Base API View structure.

**Key Features:**
Provides multi-tenancy via an `organization` ForeignKey (Abstract Base Model) and automatic queryset filtering in ViewSets based on user's `OrganizationMembership`. Validates creation permissions using Org-Aware RBAC.

**Primary Location(s):**
*   Abstract Model: `base_models/comon/OrganizationScoped/models.py`
*   ViewSet Mixin: `base_models/comon/OrganizationScoped/views.py` or `api/v1/base_views.py`

## 2. Prerequisites

[ ] Verify `Organization`, `User`, `UserProfile`, `OrganizationMembership` models implemented/migrated.
[ ] Verify helper method `user.get_organizations()` is implemented and tested.
[ ] Ensure `common` app (or shared location) exists.
[ ] Ensure basic DRF ViewSet structure established.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Abstract Base Model Definition (`base_models/comon/OrganizationScoped/models.py`)

  [ ] **(Test First - Model Structure)** Write Unit Tests (`base_models/comon/OrganizationScoped/tests/test_orgscoped_model.py`) using a concrete test model inheriting `OrganizationScoped`. Verify `organization` FK exists, links to `Organization`, `on_delete=PROTECT`, non-nullable, `db_index=True`. Test `IntegrityError` on create without org.
  [ ] Define/Verify the `OrganizationScoped` abstract base model in `base_models/comon/OrganizationScoped/models.py`:
      ```python
      # base_models/comon/OrganizationScoped/models.py
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from api.v1.base_models.organization.models import Organization # Adjust path

      class OrganizationScoped(models.Model):
          organization = models.ForeignKey(
              Organization,
              verbose_name=_("Organization"),
              on_delete=models.PROTECT,
              related_name='%(app_label)s_%(class)s_set', # Standard related name pattern
              db_index=True,
              help_text=_("The Organization this record belongs to.")
          )
          class Meta:
              abstract = True
      ```
  [ ] Run model tests; expect pass.

  ### 3.2 Base ViewSet Mixin Definition (`base_models/comon/OrganizationScoped/views.py`)

  [ ] **(Test First - ViewSet Logic - Phase 1: Read & Mocked Write)**
      Write **Integration Test(s)** (`base_models/comon/OrganizationScoped/tests/integration/test_orgscoped_views.py`) using `@pytest.mark.django_db`.
      *   Setup Orgs (A, B), Users (UserA in OrgA, UserB in OrgB, Superuser), Memberships.
      *   Create a simple concrete scoped test model (`ConcreteScopedModel`) inheriting `OrganizationScoped` within the test file.
      *   Create test data using `ConcreteScopedModel` in OrgA and OrgB.
      *   Create test ViewSet (`ConcreteScopedViewSet`) inheriting `OrganizationScopedViewSetMixin` + `ReadOnlyModelViewSet` (for read tests) and `CreateModelMixin` (for create tests). Register with router for testing.
      *   **Test `get_queryset`:**
          *   Test `GET` list as UserA -> Assert **only OrgA data** returned.
          *   Test `GET` list as UserB -> Assert **only OrgB data** returned (assuming view perm).
          *   Test `GET` list as Superuser -> Assert **OrgA and OrgB data** returned.
          *   Test `GET` list as User belonging to *no* orgs -> Assert empty list.
          *   Test `GET` list as User belonging to *both* OrgA and OrgB -> Assert data from *both* orgs returned.
      *   **Test `perform_create` (Mocking RBAC):**
          *   Use `mocker.patch('core.views.has_perm_in_org')` (adjust import path) to mock the permission check.
          *   `POST` as UserA with payload specifying `organization=OrgA.pk`. Set mock `has_perm_in_org` to return `True`. Assert 201 Created, verify `instance.organization` is OrgA.
          *   `POST` as UserA with payload specifying `organization=OrgB.pk`. Set mock `has_perm_in_org` to return `False`. Assert 403 Forbidden (or error from mixin).
          *   `POST` as UserA *without* specifying `organization` in payload (or with invalid PK). Assert 400 Bad Request from the mixin.
      Run tests; expect failure. **(Red)**
  [ ] Define/Refine the `OrganizationScopedViewSetMixin` in `base_models/comon/OrganizationScoped/views.py`:
      ```python
      # base_models/comon/OrganizationScoped/views.py (Example location)
      from rest_framework.exceptions import PermissionDenied, ValidationError
      from django.shortcuts import get_object_or_404
      from api.v1.base_models.organization.models import Organization # Adjust path
      # --- Temporarily import a placeholder for the RBAC check ---
      # from rbac.permissions import has_perm_in_org # Real import later
      def has_perm_in_org(user, perm, org): # Placeholder/Mock Target
          print(f"PERMISSION CHECK (Mocked): User {user} - Perm {perm} - Org {org.pk}")
          # This will be replaced by the real import after RBAC implementation
          # For testing, use mocker.patch('core.views.has_perm_in_org')
          # Default to True for basic structural tests, False for permission denial tests
          return True # Or raise NotImplementedError initially

      class OrganizationScopedViewSetMixin:
          """
          DRF ViewSet Mixin for Organization Scoped data.
          - Filters querysets in get_queryset() based on user's memberships.
          - Validates/sets organization in perform_create() based on request data and Org-Aware permissions.
          """
          def get_queryset(self):
              # --- Queryset Filtering Logic (as before) ---
              queryset = super().get_queryset()
              user = self.request.user

              if not user or not user.is_authenticated: return queryset.none()
              if user.is_superuser: return queryset

              user_organizations = user.get_organizations() # Queries OrganizationMembership
              if not user_organizations.exists(): return queryset.none()

              return queryset.filter(organization__in=user_organizations)

          def perform_create(self, serializer):
              # --- Creation Validation Logic (as before) ---
              user = self.request.user
              org_pk = serializer.validated_data.get('organization', None) # Assumes validated by serializer
              if not org_pk:
                  org_pk = self.kwargs.get('organization_pk') # Check URL if nested

              if not org_pk:
                   raise ValidationError({'organization': ['Organization context is required for creation.']})

              target_organization = get_object_or_404(Organization, pk=org_pk)

              # Check if user is even part of the target org (basic check)
              # Note: This check might be redundant if get_organizations() is comprehensive
              # but can be a safeguard. Consider if needed.
              # if not user.is_superuser and not user.get_organizations().filter(pk=target_organization.pk).exists():
              #      raise PermissionDenied(f"You are not a member of the target organization '{target_organization.name}'.")

              # Permission Check (using placeholder/mockable function initially)
              model_meta = self.queryset.model._meta
              add_perm = f'{model_meta.app_label}.add_{model_meta.model_name}'

              # *** Use the imported has_perm_in_org function ***
              if not has_perm_in_org(user, add_perm, target_organization):
                   raise PermissionDenied(f"You do not have permission to add '{model_meta.verbose_name}' records in organization '{target_organization.name}'.")

              # Save with validated organization - serializer MUST NOT require 'organization'
              # in validated_data if it's read_only or excluded, pass explicitly.
              serializer.save(organization=target_organization)

          # get_serializer_context can remain as before if needed by serializers
      ```
  [ ] Run ViewSet Mixin tests (mocking `has_perm_in_org`); expect pass. **(Green)**
  [ ] Refactor the mixin. **(Refactor)**

  ### 3.3 Deferred Steps (To be done AFTER RBAC Implementation - Ranking #9 & #10)

  [ ] **Implement RBAC Strategy & Org-Aware `has_perm`:** Define roles/permissions and implement the actual `rbac.permissions.has_perm_in_org` function (Ranking #8 & #9).
  [ ] **Apply Mixins to Concrete Models/Views:** Inherit `OrganizationScoped` in models (e.g., `Product`) and `OrganizationScopedViewSetMixin` in their ViewSets (e.g., `ProductViewSet`). Run `makemigrations`/`migrate`.
  [ ] **Full Integration Testing:**
      *   Remove mocking for `has_perm_in_org` in `base_models/comon/OrganizationScoped/tests/integration/test_orgscoped_views.py` and ensure tests pass with the *real* permission check.
      *   Add comprehensive API tests to *concrete ViewSets* (like `ProductViewSet`) verifying LIST filtering (data isolation) and CREATE/UPDATE/DELETE operations succeed/fail based on the user's *actual* role and permissions within the target organization, as checked by the integrated `OrganizationScopedViewSetMixin` and the real RBAC function.

  ### 3.4 Documentation Updates

  [ ] Update documentation to explain the mixin usage and the dependency on the RBAC function.

## 4. Final Checks (For this stage: Model & Mixin Definition/Testing)

[ ] Run the *entire* test suite (`pytest`). Verify model tests and mixin tests (with mocked RBAC) pass.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov`). Ensure mixin logic is covered by tests (including mocked permission paths).

## 5. Follow-up Actions

[ ] Create Pull Request for the `OrganizationScoped` abstract model and the `OrganizationScopedViewSetMixin` (tested with mocked RBAC).
[ ] Proceed with **implementing the RBAC Strategy and the Org-Aware `has_perm` function (Ranking #8, #9)**.
[ ] **After RBAC is done:** Proceed with **applying the mixins and performing full integration testing (Ranking #10)**.

