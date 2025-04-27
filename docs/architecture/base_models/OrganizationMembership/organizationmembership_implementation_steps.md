

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

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `User`, `Organization`) are implemented and migrated.
[ ] Verify Django `auth` app (providing `Group`) and `contenttypes` app are configured.
[ ] Ensure the `organization` app structure exists (`api/v1/base_models/organization/`).
[ ] Ensure `factory-boy` is set up. Factories for `User`, `Organization`, `Group` exist.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `organization`) verifying:
      *   `OrganizationMembership` creation with required fields (`user`, `organization`, `role`).
      *   `unique_together` constraint (`user`, `organization`) is enforced.
      *   Default values (`is_active`). FKs work correctly.
      *   `__str__` method returns expected string.
      *   Inherited `Timestamped`/`Auditable` fields exist.
      Run; expect failure (`OrganizationMembership` doesn't exist).
  [ ] Define the `OrganizationMembership` class in `api/v1/base_models/organization/models.py`.
  [ ] Add required inheritance: `Timestamped`, `Auditable`.
      ```python
      # api/v1/base_models/organization/models.py
      # ... (other imports like Organization, OrganizationType) ...
      from django.conf import settings
      from django.contrib.auth.models import Group
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from core.models import Timestamped, Auditable # Adjust import path

      class OrganizationMembership(Timestamped, Auditable):
          user = models.ForeignKey(
              settings.AUTH_USER_MODEL,
              on_delete=models.CASCADE,
              related_name='organization_memberships'
          )
          organization = models.ForeignKey(
              'Organization', # Self-app reference ok if in same models.py
              on_delete=models.CASCADE,
              related_name='memberships'
          )
          role = models.ForeignKey(
              Group, # Link to Django Group representing the Role
              verbose_name=_("Role (Group)"),
              on_delete=models.PROTECT, # Don't delete Group if used in membership
              related_name='organization_memberships'
              # null=True, blank=True, # Make role optional? PRD implies required
          )
          is_active = models.BooleanField(
              _("Is Active Member"), default=True, db_index=True
          )
          # Add is_default or join_date here if needed per PRD optional fields

          class Meta:
              verbose_name = _("Organization Membership")
              verbose_name_plural = _("Organization Memberships")
              unique_together = ('user', 'organization') # User has one definition per org
              ordering = ['organization__name', 'user__username']
              indexes = [
                  models.Index(fields=['user', 'organization']),
                  models.Index(fields=['role']),
                  models.Index(fields=['is_active']),
              ]

          def __str__(self):
              role_name = self.role.name if self.role else 'N/A'
              user_name = self.user.username if self.user else 'N/A'
              org_name = self.organization.name if self.organization else 'N/A'
              return f"{user_name} in {org_name} as {role_name}"

      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `OrganizationMembershipFactory` in `api/v1/base_models/organization/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from django.contrib.auth.models import Group
      from ..models import OrganizationMembership, Organization
      # Import UserFactory, OrganizationFactory
      from api.v1.base_models.user.tests.factories import UserFactory
      from .factories import OrganizationFactory # Assuming in same file

      class GroupFactory(DjangoModelFactory): # Define basic Group factory if not done elsewhere
          class Meta:
              model = Group
              django_get_or_create = ('name',)
          name = factory.Sequence(lambda n: f'Role {n}')

      class OrganizationMembershipFactory(DjangoModelFactory):
          class Meta:
              model = OrganizationMembership
              # Ensure unique combination for tests using get_or_create
              django_get_or_create = ('user', 'organization')

          user = factory.SubFactory(UserFactory)
          organization = factory.SubFactory(OrganizationFactory)
          role = factory.SubFactory(GroupFactory)
          is_active = True
      ```
  [ ] **(Test)** Write simple tests ensuring the factory creates valid instances and respects `unique_together`.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Create/Update `api/v1/base_models/organization/admin.py`.
  [ ] Define `OrganizationMembershipAdmin`. Use `raw_id_fields` for easier selection.
      ```python
      from django.contrib import admin
      from .models import OrganizationMembership

      @admin.register(OrganizationMembership)
      class OrganizationMembershipAdmin(admin.ModelAdmin):
          list_display = ('user', 'organization', 'role', 'is_active', 'updated_at')
          list_filter = ('organization', 'role', 'is_active')
          search_fields = ('user__username', 'organization__name', 'role__name')
          list_select_related = ('user', 'organization', 'role')
          raw_id_fields = ('user', 'organization', 'role') # Better for large numbers
          list_editable = ('is_active', 'role')
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
      ```
  [ ] **(Manual Test):** Verify Admin CRUD operations for memberships.

  ### 3.4 Implement `User.get_organizations()` Helper

  [ ] **(Test First)** Write Unit Tests (`tests/unit/test_models.py` in `user` app) for the `User.get_organizations()` method:
      *   Test user with no memberships -> returns empty queryset.
      *   Test user with one active membership -> returns queryset containing that one organization.
      *   Test user with multiple active memberships -> returns queryset containing all linked organizations.
      *   Test user with only inactive memberships -> returns empty queryset (assuming `is_active` should be checked).
      Run; expect failure (method doesn't exist or is wrong).
  [ ] Add/Modify the `get_organizations` method on the `User` model (or a Manager/Mixin):
      ```python
      # api/v1/base_models/user/models.py (or wherever User model is defined/extended)
      # Assuming Organization model imported correctly
      from api.v1.base_models.organization.models import Organization

      # If extending AbstractUser:
      class User(AbstractUser):
          # ... other fields ...
          def get_organizations(self):
              """Returns a QuerySet of active Organizations the user is a member of."""
              return Organization.objects.filter(
                  memberships__user=self,
                  memberships__is_active=True # Only consider active memberships
              ).distinct()

      # If using signals/profile with default User:
      # Add this method dynamically or on a custom Manager/Proxy model if needed.
      # For simplicity, often added directly if extending AbstractUser.
      ```
  [ ] Run `get_organizations` tests; expect pass. Refactor.

  ### 3.5 Migrations

  [ ] Run `python manage.py makemigrations api.v1.base_models.organization`.
  [ ] **Review generated migration file carefully.** Check FKs, `unique_together`, indexes.
  [ ] Run `python manage.py migrate` locally.

  ### 3.6 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write tests for `OrganizationMembershipSerializer`. Test representation (including nested User/Org/Role names/IDs), validation (`unique_together` if creating via API), read-only fields.
  [ ] Define `OrganizationMembershipSerializer` in `api/v1/base_models/organization/serializers.py`.
      ```python
      from rest_framework import serializers
      from django.contrib.auth.models import Group
      from ..models import OrganizationMembership, Organization
      # Import simplified serializers for related objects if needed
      # from api.v1.base_models.user.serializers import UserSummarySerializer

      class GroupSerializer(serializers.ModelSerializer): # Simple serializer for Role/Group
          class Meta: model = Group; fields = ['id', 'name']

      class OrganizationMembershipSerializer(serializers.ModelSerializer):
          # Represent related objects by ID for writing, potentially nested/summary for reading
          user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all()) # Or UserSummarySerializer(read_only=True)
          organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all()) # Or OrgSummarySerializer(read_only=True)
          role = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all()) # Or GroupSerializer(read_only=True)

          # Read-only expanded versions for easier consumption
          username = serializers.CharField(source='user.username', read_only=True)
          organization_name = serializers.CharField(source='organization.name', read_only=True)
          role_name = serializers.CharField(source='role.name', read_only=True)

          class Meta:
              model = OrganizationMembership
              fields = [
                  'id', 'user', 'username', 'organization', 'organization_name',
                  'role', 'role_name', 'is_active',
                  # Add optional fields like join_date, is_default if implemented
                  'created_at', 'updated_at',
              ]
              read_only_fields = ('id', 'username', 'organization_name', 'role_name', 'created_at', 'updated_at')
              # Add unique_together validation if allowing creation via API
              validators = [
                  serializers.UniqueTogetherValidator(
                      queryset=OrganizationMembership.objects.all(),
                      fields=('user', 'organization'),
                      message=_("User already has a membership in this organization.")
                  )
              ]
      ```
  [ ] Run serializer tests; expect pass. Refactor.

  ### 3.7 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write API Tests for `/api/v1/organization-memberships/`. Test CRUD operations (likely admin-restricted). Test LIST filtering by user or organization. Test permissions.
  [ ] Define `OrganizationMembershipViewSet` in `api/v1/base_models/organization/views.py`.
      ```python
      from rest_framework import viewsets, permissions
      from ..models import OrganizationMembership
      from ..serializers import OrganizationMembershipSerializer
      # Import filters, admin permissions etc

      class OrganizationMembershipViewSet(viewsets.ModelViewSet):
          """
          API endpoint for managing Organization Memberships (Admin/Restricted).
          """
          serializer_class = OrganizationMembershipSerializer
          permission_classes = [permissions.IsAdminUser] # Example: Restrict to Admins
          queryset = OrganizationMembership.objects.select_related(
              'user', 'organization', 'role'
          ).all()
          filter_backends = [...] # Add filtering backend
          filterset_fields = ['user', 'organization', 'role', 'is_active']
          search_fields = ['user__username', 'organization__name', 'role__name']
      ```
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.8 URL Routing (`urls.py`)

  [ ] Import `OrganizationMembershipViewSet` in `api/v1/base_models/organization/urls.py`.
  [ ] Register with router: `router.register(r'organization-memberships', views.OrganizationMembershipViewSet)`.
  [ ] **(Test):** Rerun basic API tests; expect 2xx/4xx codes.

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests for Membership CRUD via API.
      *   LIST (test filtering by user/org).
      *   CREATE (assign user to org with role). Test `unique_together`.
      *   RETRIEVE.
      *   UPDATE (change role or `is_active`).
      *   DELETE.
      *   Test permissions rigorously (only admins can manage).
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

--- END OF FILE organizationmembership_implementation_steps.md ---