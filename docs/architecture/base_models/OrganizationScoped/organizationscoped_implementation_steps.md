Okay, let's generate the implementation steps for the `OrganizationScoped` mechanism. This is slightly different from a standard model, as it involves two key parts: defining the Abstract Base Model and implementing the enforcement logic (likely in a base ViewSet mixin).

--- START OF FILE organizationscoped_implementation_steps.md ---

# OrganizationScoped Mechanism - Implementation Steps

## 1. Overview

**Model Name:**
`OrganizationScoped` (Abstract Base Model) & `OrganizationScopedViewSetMixin` (Example name for enforcement logic)

**Corresponding PRD:**
`organization_scoped_prd.md`

**Depends On:**
`Organization` model, `User` model (and a way to get user's organizations), Django Rest Framework (`viewsets`, `mixins`), Base API View structure.

**Key Features:**
Provides multi-tenancy by linking inheriting models to an `Organization` via an Abstract Base Model and automatically filtering API querysets based on the requesting user's associated organization(s) via a ViewSet mixin.

**Primary Location(s):**
*   Abstract Model: `core/models.py` (or `common/models.py`)
*   ViewSet Mixin: `core/views.py` or `api/v1/base_views.py` (or similar shared API utility location)

## 2. Prerequisites

[ ] Verify `Organization` model is implemented and migrated.
[ ] Verify `User` model and `UserProfile` model (or alternative mechanism for linking users to organizations) are implemented.
[ ] **Define User-Organization Link:** Decide and implement the method for determining a user's organization(s). This might be:
    *   A direct `ForeignKey` or `ManyToManyField` on `UserProfile` (e.g., `UserProfile.primary_organization`, `UserProfile.organizations`).
    *   A separate `Membership` model linking User and Organization.
    *   A method on the `User` model (e.g., `user.get_organizations()`) that encapsulates this logic. **Steps below assume a `user.get_organizations()` method exists or can be added.**
[ ] Ensure the `core` app (or chosen shared location) exists.
[ ] Ensure DRF is installed and basic ViewSet structure is established.

## 3. Implementation Steps (TDD Workflow)

  *(Testing involves applying the abstract model and mixin to concrete test models/views)*

  ### 3.1 Abstract Base Model Definition (`core/models.py`)

  [ ] **(Test First - Model Structure)**
      Write **Unit Test(s)** (`core/tests/test_orgscoped_model.py`) using a concrete test model inheriting `OrganizationScoped`:
      *   Verify the `organization` ForeignKey field exists on the concrete model.
      *   Verify it links correctly to the `Organization` model.
      *   Verify `on_delete` behavior is `PROTECT` (or as specified).
      *   Verify it's non-nullable (`null=False`).
      ```python
      # core/tests/test_orgscoped_model.py
      from django.db import models
      from django.test import TestCase
      from core.models import OrganizationScoped # Will fail initially
      # Assuming Org model and factory exist
      from api.v1.base_models.organization.models import Organization
      from api.v1.base_models.organization.tests.factories import OrganizationFactory

      class ConcreteScopedModel(OrganizationScoped):
          name = models.CharField(max_length=100)
          # Add Timestamped/Auditable if needed for tests
          class Meta:
              app_label = 'core'

      class OrgScopedModelDefinitionTests(TestCase):
          def test_organization_field_exists(self):
              """Verify the organization field is added and configured."""
              try:
                  field = ConcreteScopedModel._meta.get_field('organization')
                  self.assertIsNotNone(field)
                  self.assertIsInstance(field, models.ForeignKey)
                  self.assertEqual(field.remote_field.model, Organization)
                  self.assertEqual(field.remote_field.on_delete, models.PROTECT)
                  self.assertFalse(field.null)
              except models.FieldDoesNotExist:
                  self.fail("Organization field does not exist on ConcreteScopedModel")

          def test_requires_organization_on_create(self):
              """Verify database enforces non-null organization."""
              from django.db import IntegrityError
              with self.assertRaises(IntegrityError):
                   # Attempt to create without org - should fail at DB level if field is NOT NULL
                   # Note: This might depend on exact DB backend, direct field check is better
                   ConcreteScopedModel.objects.create(name="test no org") # Error expected

              org = OrganizationFactory()
              instance = ConcreteScopedModel.objects.create(name="test with org", organization=org)
              self.assertEqual(instance.organization, org)

      ```
      Run; expect failure. **(Red)**
  [ ] Define the `OrganizationScoped` abstract base model in `core/models.py`:
      ```python
      # core/models.py
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      # Import Organization based on final location
      from api.v1.base_models.organization.models import Organization

      class OrganizationScoped(models.Model):
          """
          Abstract base model adding a required link to an Organization,
          used for multi-tenant data scoping.
          """
          organization = models.ForeignKey(
              Organization,
              verbose_name=_("Organization"),
              on_delete=models.PROTECT, # Or CASCADE if scoped objects die with org
              related_name='%(app_label)s_%(class)s_set', # Standard related name
              # null=False is default, no need to specify explicitly
              help_text=_("The Organization this record belongs to.")
          )

          class Meta:
              abstract = True
              # Add index for performance on concrete models
              # indexes = [ models.Index(fields=['organization']) ] # This goes in concrete model Meta
      ```
  [ ] Run tests; expect pass. **(Green)**
  [ ] Refactor. **(Refactor)**

  ### 3.2 User Organization Retrieval (`User` model or `UserProfile`)

  [ ] **(Test First)** Write **Unit Test(s)** for the `user.get_organizations()` method (or wherever this logic resides).
      *   Test user with no org assignments returns empty list/queryset.
      *   Test user assigned to one org returns list/queryset with that org.
      *   Test user assigned to multiple orgs (if supported) returns list/queryset with all assigned orgs.
  [ ] Implement the `get_organizations()` method on the `User` model (if extending AbstractUser) or `UserProfile`. This method needs to query the chosen relationship (Direct FK/M2M on Profile, or Membership model).
      ```python
      # Example assuming Direct FK on UserProfile
      # api/v1/base_models/user/models.py
      # class UserProfile(...):
      # ... fields ...
      #    def get_organizations(self):
      #        # Returns a list or QuerySet of Organization objects
      #        if self.primary_organization:
      #             # Simple case: user belongs to one primary org
      #             return [self.primary_organization]
      #        # Add logic here if using M2M or Membership model
      #        return [] # Or Organization.objects.none()

      # Add corresponding method on User model to delegate
      # class User(...):
      # ...
      #    def get_organizations(self):
      #        if hasattr(self, 'profile'):
      #            return self.profile.get_organizations()
      #        return [] # Or Organization.objects.none()
      ```
  [ ] Run tests for `get_organizations()`; expect pass. Refactor.

  ### 3.3 Base ViewSet Mixin Definition (`core/views.py` or `api/base_views.py`)

  [ ] **(Test First - ViewSet Logic)**
      Write **Integration Test(s)** (`core/tests/test_orgscoped_views.py` or similar) using `@pytest.mark.django_db`.
      *   Set up multiple Orgs (OrgA, OrgB) and Users (UserA in OrgA, UserB in OrgB, Superuser).
      *   Create test data using `ConcreteScopedModel` belonging to OrgA and OrgB.
      *   Create a simple test ViewSet (`ConcreteScopedViewSet`) inheriting `OrganizationScopedViewSetMixin` (doesn't exist yet) and `viewsets.ReadOnlyModelViewSet`. Register it with a test router.
      *   Use the `APIClient` (authenticated as UserA) to make a `GET` request to the test ViewSet's list endpoint. Assert only data from OrgA is returned.
      *   Repeat request authenticated as UserB. Assert only data from OrgB is returned.
      *   Repeat request authenticated as Superuser. Assert data from *both* OrgA and OrgB is returned.
      *   Test user belonging to no org -> gets empty list.
      Run; expect failure (`OrganizationScopedViewSetMixin` doesn't exist or logic fails). **(Red)**
  [ ] Define the `OrganizationScopedViewSetMixin` in a shared view location:
      ```python
      # core/views.py (Example location)
      from rest_framework.exceptions import PermissionDenied
      # Import Organization based on final location
      from api.v1.base_models.organization.models import Organization

      class OrganizationScopedViewSetMixin:
          """
          Mixin for DRF ViewSets to automatically filter querysets
          based on the request.user's associated organization(s).

          Assumes the ViewSet's model inherits from OrganizationScoped
          and the user model has a method get_organizations().
          """
          def get_queryset(self):
              # Start with the ViewSet's explicitly defined queryset
              queryset = super().get_queryset()
              user = self.request.user

              if not user or not user.is_authenticated:
                  # Deny access or return empty if unauthenticated access should be blocked entirely
                  # raise PermissionDenied("Authentication required.") # Option 1
                  return queryset.none() # Option 2: Return empty list

              if user.is_superuser:
                  # Superusers can see all organizations' data
                  return queryset

              # Get the list/queryset of organizations the user belongs to
              user_organizations = user.get_organizations() # Assumes this method exists

              if not user_organizations:
                   # User is authenticated but not linked to any org they can see data for
                   return queryset.none()

              # Filter the queryset to include only objects belonging to the user's orgs
              # Assumes the inheriting model has an 'organization' FK field
              organization_pks = [org.pk for org in user_organizations] # Get PKs if it returns objects
              # Or if get_organizations returns a QuerySet:
              # organization_pks = user_organizations.values_list('pk', flat=True)
              return queryset.filter(organization_id__in=organization_pks)

          def perform_create(self, serializer):
              # Automatically set organization on create based on user context
              # This assumes user belongs to ONE primary org for creation scope
              user = self.request.user
              # Note: Check add permission for the target org here using RBAC
              if user and user.is_authenticated:
                   user_orgs = user.get_organizations()
                   primary_org = user_orgs[0] if user_orgs else None # Simplistic: use first org

                   if primary_org:
                        # Check if user has permission to create for this org via RBAC?
                        # if check_permission(user, 'add_model', organization=primary_org): # Example check
                       serializer.save(organization=primary_org)
                       # else: raise PermissionDenied(...)
                   else:
                        # Handle case where user has no org to create data in
                        raise PermissionDenied("Cannot determine organization context for creation.")
              else:
                   # Handle anonymous creation? Usually disallowed for scoped models.
                   raise PermissionDenied("Authentication required to create scoped data.")
      ```
  [ ] Run ViewSet logic tests; expect pass. **(Green)**
  [ ] Refactor the mixin code (error handling, user org logic). **(Refactor)**

  ### 3.4 Applying to Concrete Models/Views

  [ ] **(Test First - Real ViewSet)** Write API tests for a *real* model that inherits `OrganizationScoped` (e.g., `Product`, `Warehouse` once implemented). Verify the org scoping works as expected for List, Retrieve, Create operations for that specific model's ViewSet.
  [ ] Ensure the concrete model (e.g., `Product`) inherits `OrganizationScoped`.
  [ ] Ensure the concrete ViewSet (e.g., `ProductViewSet`) inherits the `OrganizationScopedViewSetMixin`.
  [ ] Run tests; expect pass.

  ### 3.5 Migrations

  [ ] Migrations are generated when concrete models inherit `OrganizationScoped`, adding the `organization_id` column and index *to those concrete model tables*. Ensure `makemigrations` is run for apps containing models that now inherit `OrganizationScoped`.
  [ ] **Review:** Check that `db_index=True` is added to the `organization` ForeignKey in the migration for inheriting models (Django usually adds this automatically for FKs, but verify). Add manually via `Meta.indexes` on the concrete model if needed for certainty.
  [ ] Run `migrate`.

  ### 3.6 Documentation Updates

  [ ] Update API documentation strategy/template to note that endpoints for `OrganizationScoped` models are automatically filtered.
  [ ] Update developer onboarding/guidelines to instruct inheriting from `OrganizationScoped` (model) and `OrganizationScopedViewSetMixin` (view).

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`). Pay close attention to tests involving scoped models and different user types (regular user in org A, user in org B, superuser).
[ ] Run linters (`flake8`) and formatters (`black`) on relevant `core` files and any modified concrete models/views.
[ ] Check code coverage (`pytest --cov`). Ensure mixin logic and `get_organizations` helper are covered.
[ ] Manually test API endpoints for scoped models with different users locally.

## 5. Follow-up Actions

[ ] Address TODOs (e.g., refine `get_organizations` logic, add more robust org context handling in `perform_create`).
[ ] Create Pull Request.
[ ] Update relevant documentation (API docs, developer guides).
[ ] Ensure future models requiring org scoping correctly inherit the abstract model and use the ViewSet mixin.

--- END OF FILE organizationscoped_implementation_steps.md ---