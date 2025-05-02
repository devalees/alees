import pytest
from unittest import mock

from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from rest_framework import viewsets

# Adjust imports based on actual locations
from api.v1.base_models.organization.models import Organization
from api.v1.base_models.user.tests.factories import UserFactory
from api.v1.base_models.organization.tests.factories import (
    OrganizationFactory,
    OrganizationTypeFactory
)

# This import will fail until the class is created (TDD)
from core.rbac.drf_permissions import HasModelPermissionInOrg

# --- Mocks and Fixtures --- 

@pytest.fixture
def org_type():
    return OrganizationTypeFactory()

@pytest.fixture
def org_a(org_type):
    return OrganizationFactory(organization_type=org_type)

@pytest.fixture
def org_b(org_type):
    return OrganizationFactory(organization_type=org_type)

@pytest.fixture
def user():
    return UserFactory()

@pytest.fixture
def super_user():
    return UserFactory(is_superuser=True)

@pytest.fixture
def factory():
    return APIRequestFactory()

# Mock ViewSet simulating one that uses Organization model
class MockOrganizationViewSet(viewsets.ViewSet):
    queryset = Organization.objects.none() # Needs a queryset for model meta access
    permission_classes = [HasModelPermissionInOrg] # Apply the permission

    # Simulate standard actions
    def list(self, request): pass
    def create(self, request): pass
    def retrieve(self, request, pk=None): pass
    def update(self, request, pk=None): pass
    def partial_update(self, request, pk=None): pass
    def destroy(self, request, pk=None): pass

# --- Tests --- 

@pytest.mark.django_db
class TestHasModelPermissionInOrg:

    @pytest.mark.parametrize(
        "action, method, expected_perm_check, setup_object, should_have_perm, expected_result",
        [
            # === has_permission (List/Create) ===
            # List: Should rely on viewset filtering, so basic auth allows
            ("list", "get", None, False, True, True),
            # Create: Defers org-specific check to perform_create, allows basic access
            ("create", "post", None, False, True, True),
            # === has_object_permission (Retrieve/Update/Delete) ===
            # Retrieve (View) - Has Perm
            ("retrieve", "get", "api_v1_organization.view_organization", True, True, True),
            # Retrieve (View) - Lacks Perm
            ("retrieve", "get", "api_v1_organization.view_organization", True, False, False),
            # Update (Change) - Has Perm
            ("update", "put", "api_v1_organization.change_organization", True, True, True),
            # Update (Change) - Lacks Perm
            ("update", "put", "api_v1_organization.change_organization", True, False, False),
            # Partial Update (Change) - Has Perm
            ("partial_update", "patch", "api_v1_organization.change_organization", True, True, True),
            # Partial Update (Change) - Lacks Perm
            ("partial_update", "patch", "api_v1_organization.change_organization", True, False, False),
            # Destroy (Delete) - Has Perm
            ("destroy", "delete", "api_v1_organization.delete_organization", True, True, True),
            # Destroy (Delete) - Lacks Perm
            ("destroy", "delete", "api_v1_organization.delete_organization", True, False, False),
        ]
    )
    def test_permission_checks(
        self, mocker, factory, user, org_a,
        action, method, expected_perm_check, setup_object, should_have_perm, expected_result
    ):
        """Tests both has_permission and has_object_permission scenarios."""
        view_instance = MockOrganizationViewSet() # Get an instance for direct method call if needed
        view_instance.action = action # Set action manually for permission class
        # Add mock get_queryset needed by has_permission
        view_instance.get_queryset = lambda: Organization.objects.none()

        request = factory.generic(method, f'/mock/{org_a.pk if setup_object else ""}')
        request.user = user

        # Mock the core permission checker
        mock_has_perm = mocker.patch('core.rbac.drf_permissions.has_perm_in_org', return_value=should_have_perm)

        permission = HasModelPermissionInOrg()

        obj = org_a if setup_object else None

        if not setup_object:
            # Test has_permission (for list/create)
            result = permission.has_permission(request, view_instance)
            assert result is expected_result
            # has_perm_in_org shouldn't be called directly for list/create in this implementation
            mock_has_perm.assert_not_called()
        else:
            # Test has_object_permission (for retrieve/update/delete)
            result = permission.has_object_permission(request, view_instance, obj)
            assert result is expected_result
            # Check if the correct permission was checked via the helper
            mock_has_perm.assert_called_once_with(user, expected_perm_check, obj)

    def test_superuser_access(self, factory, super_user, org_a):
        """Superusers should always have access."""
        view = MockOrganizationViewSet.as_view({'get': 'list', 'post': 'create', 'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})
        view_instance = MockOrganizationViewSet()
        request = factory.get('/mock/') # Example: list view
        request.user = super_user
        view_instance.action = 'list'
        permission = HasModelPermissionInOrg()
        assert permission.has_permission(request, view_instance) is True

        request = factory.get(f'/mock/{org_a.pk}/') # Example: retrieve view
        request.user = super_user
        view_instance.action = 'retrieve'
        assert permission.has_object_permission(request, view_instance, org_a) is True

    def test_unauthenticated_user(self, factory, org_a):
        """Unauthenticated users should be denied."""
        view = MockOrganizationViewSet.as_view({'get': 'list', 'get': 'retrieve'})
        view_instance = MockOrganizationViewSet()
        request = factory.get('/mock/')
        request.user = UserFactory.build() # Anonymous user
        view_instance.action = 'list'
        permission = HasModelPermissionInOrg()
        assert permission.has_permission(request, view_instance) is False

        request = factory.get(f'/mock/{org_a.pk}/')
        request.user = UserFactory.build() # Anonymous user
        view_instance.action = 'retrieve'
        assert permission.has_object_permission(request, view_instance, org_a) is False 