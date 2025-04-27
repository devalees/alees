
# OrganizationScoped Mechanism - Implementation Steps (Revised for Simple Org-Aware RBAC)

## 1. Overview

**Component Name:**
`OrganizationScoped` (Abstract Base Model) & `OrganizationScopedViewSetMixin`

**Corresponding PRD:**
`organizationscoped_prd.md` (Revised for Simple Org-Aware RBAC)

**Depends On:**
`Organization` model, `User` model, `OrganizationMembership` model, Org-Aware RBAC check function (`has_perm_in_org`), DRF (`viewsets`, `mixins`), Base API View structure.

**Key Features:**
Provides multi-tenancy via an `organization` ForeignKey (Abstract Base Model) and automatic queryset filtering in ViewSets based on user's `OrganizationMembership`. Ensures creation happens within authorized organizations using Org-Aware RBAC.

**Primary Location(s):**
*   Abstract Model: `core/models.py`
*   ViewSet Mixin: `core/views.py` or `api/v1/base_views.py`

## 2. Prerequisites

[ ] Verify `Organization`, `User`, `UserProfile`, `OrganizationMembership` models implemented/migrated.
[ ] Verify helper method `user.get_organizations()` (querying `OrganizationMembership`) is implemented and tested.
[ ] Verify the Org-Aware RBAC permission checking mechanism (`has_perm_in_org` or similar function/backend method) is implemented.
[ ] Ensure `core` app (or shared location) exists.
[ ] Ensure basic DRF ViewSet structure established.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Abstract Base Model Definition (`core/models.py`)

  [ ] **(Test First - Model Structure)** Write Unit Tests (`core/tests/test_orgscoped_model.py`) using a concrete test model inheriting `OrganizationScoped`. Verify `organization` FK exists, links to `Organization`, `on_delete=PROTECT`, non-nullable, `db_index=True`. Test `IntegrityError` on create without org. *(This step likely already done based on previous iteration)*.
  [ ] Define/Verify the `OrganizationScoped` abstract base model in `core/models.py`:
      ```python
      # core/models.py
      # ... other imports ...
      from api.v1.base_models.organization.models import Organization # Adjust path

      class OrganizationScoped(models.Model):
          organization = models.ForeignKey(
              Organization,
              verbose_name=_("Organization"),
              on_delete=models.PROTECT,
              related_name='%(app_label)s_%(class)s_set',
              db_index=True, # Ensure index is added via abstract model if possible
              help_text=_("The Organization this record belongs to.")
          )
          class Meta: abstract = True
      ```
  [ ] Run tests; expect pass.

  ### 3.2 Base ViewSet Mixin Definition (`core/views.py` or `api/base_views.py`)

  [ ] **(Test First - ViewSet Logic)**
      Write **Integration Test(s)** (`core/tests/test_orgscoped_views.py`) using `@pytest.mark.django_db`.
      *   Setup Orgs (A, B), Users (UserA in OrgA via Membership+Role, UserB in OrgB, Superuser). Give UserA `view_concretescopedmodel` permission *only* via their role in OrgA membership.
      *   Create test data using `ConcreteScopedModel` in OrgA and OrgB.
      *   Create test ViewSet (`ConcreteScopedViewSet`) inheriting `OrganizationScopedViewSetMixin` + `ReadOnlyModelViewSet`. Register with router.
      *   Test `GET` list as UserA -> Assert **only OrgA data** returned.
      *   Test `GET` list as UserB -> Assert **only OrgB data** returned (if they have view perm in OrgB).
      *   Test `GET` list as Superuser -> Assert **OrgA and OrgB data** returned.
      *   Test `GET` list as User belonging to *no* orgs -> Assert empty list.
      *   Test `GET` list as User belonging to *both* OrgA and OrgB -> Assert data from *both* orgs returned.
      *   **Add Test for Create:**
          *   Use a test ViewSet inheriting the Mixin + `CreateModelMixin`.
          *   `POST` as UserA with payload specifying `organization=OrgA.pk`. Mock the Org-Aware `has_perm` check to return `True`. Assert 201 Created, verify `instance.organization` is OrgA.
          *   `POST` as UserA with payload specifying `organization=OrgB.pk`. Mock Org-Aware `has_perm` check to return `False`. Assert 403 Forbidden or appropriate validation error from `perform_create`.
          *   `POST` as UserA *without* specifying `organization` in payload. Assert appropriate error (e.g., 400 Bad Request) because target org cannot be determined.
      Run; expect failure. **(Red)**
  [ ] Define/Refine the `OrganizationScopedViewSetMixin`:
      ```python
      # core/views.py (Example location)
      from rest_framework.exceptions import PermissionDenied, ValidationError
      from django.shortcuts import get_object_or_404
      # Import Organization based on final location
      from api.v1.base_models.organization.models import Organization
      # Import your Org-Aware permission checker
      from rbac.permissions import has_perm_in_org # Example import path

      class OrganizationScopedViewSetMixin:
          """
          DRF ViewSet Mixin for Organization Scoped data.
          - Filters querysets in get_queryset() based on user's memberships.
          - Validates/sets organization in perform_create() based on request data and permissions.
          """
          def get_queryset(self):
              queryset = super().get_queryset()
              user = self.request.user

              if not user or not user.is_authenticated: return queryset.none()
              if user.is_superuser: return queryset

              user_organizations = user.get_organizations() # Queries OrganizationMembership
              if not user_organizations.exists(): return queryset.none()

              # Filter by the organizations the user is an active member of
              return queryset.filter(organization__in=user_organizations)

          def perform_create(self, serializer):
              user = self.request.user
              # --- Determine Target Organization ---
              # Option 1: Explicitly require 'organization' in request data
              org_pk = serializer.validated_data.get('organization', None) # Assuming it's validated if present
              if not org_pk:
                  # Try getting from URL kwarg if nested route like /orgs/{org_pk}/items/
                  org_pk = self.kwargs.get('organization_pk') # Adjust kwarg name as needed

              if not org_pk:
                   raise ValidationError({'organization': ['This field is required for scoped creation.']})

              # Fetch the target organization instance
              target_organization = get_object_or_404(Organization, pk=org_pk)

              # --- Permission Check ---
              # Get the required model 'add' permission codename
              model_meta = self.queryset.model._meta
              add_perm = f'{model_meta.app_label}.add_{model_meta.model_name}'

              # Check permission using the Org-Aware RBAC function
              if not has_perm_in_org(user, add_perm, target_organization):
                   raise PermissionDenied(f"You do not have permission to add '{model_meta.model_name}' records in organization '{target_organization.name}'.")

              # Save with validated organization
              serializer.save(organization=target_organization) # Pass org to serializer save

          def get_serializer_context(self):
               """ Add org context for serializers if needed"""
               context = super().get_serializer_context()
               # If needed, determine target org for validation based on request/instance
               # target_organization = ... logic to determine context ...
               # context['target_organization'] = target_organization
               return context
      ```
      *   **Note on `perform_create`:** This example assumes the `organization` PK is passed in the request body. Adjust logic if using nested URLs or other context methods. The key is to **identify the target org** and **check permission *for that org***.
      *   **Note on Serializer:** The serializer for the inheriting model might need `serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all(), write_only=True, required=True)` for the `organization` field to accept input during POST/PUT, or it could be excluded and set only by `perform_create`.
  [ ] Run ViewSet logic tests; expect pass. **(Green)**
  [ ] Refactor the mixin. **(Refactor)**

  ### 3.3 Applying to Concrete Models/Views

  [ ] **(Test First - Real ViewSet)** Write comprehensive API tests for actual scoped models (`Product`, `Warehouse`, `Document`, etc.). Ensure LIST, RETRIEVE, CREATE, UPDATE, DELETE respect Org Scoping and Org-Aware permissions. Test creating objects by providing the target `organization` PK in the payload.
  [ ] Ensure concrete models inherit `OrganizationScoped`.
  [ ] Ensure concrete ViewSets inherit `OrganizationScopedViewSetMixin`.
  [ ] Ensure concrete Serializers handle the `organization` field appropriately (e.g., read-only for output, potentially writeable input field for create, validated in view `perform_create`).
  [ ] Run tests; expect pass.

  ### 3.4 Migrations

  [ ] Ensure `makemigrations` is run for apps containing models inheriting `OrganizationScoped`.
  [ ] **Review:** Verify `organization_id` column and index are added.
  [ ] Run `migrate`.

  ### 3.5 Documentation Updates

  [ ] Update documentation (API Strategy, Developer Guides) about Org Scoped models/views. Emphasize how target org is determined on create and how permissions are checked.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`). Verify all Org Scoping and permission tests pass for various users and organizations.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov`). Ensure mixin logic is covered.
[ ] Manually test API endpoints for scoped models with different users (Superuser, User in Org A, User in Org B, User in no Org). Verify data isolation and create permissions.

## 5. Follow-up Actions

[ ] Address TODOs (Refine `perform_create` org determination if needed).
[ ] Create Pull Request.
[ ] Update relevant documentation.
[ ] Apply mixins to all necessary future models.

--- END OF FILE organizationscoped_implementation_steps.md (Revised for Simple Org-Aware RBAC) ---