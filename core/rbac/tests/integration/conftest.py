import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.utils import IntegrityError
from rest_framework.test import APIClient

# Import factories (adjust path as needed)
from api.v1.base_models.organization.tests.factories import (
    OrganizationFactory,
    OrganizationTypeFactory,
    OrganizationMembershipFactory
)
from api.v1.base_models.user.tests.factories import UserFactory
from core.tests_app.models import ConcreteScopedModel

# --- Shared Fixtures for Integration Tests ---

@pytest.fixture(scope="module")
def api_client():
    """Provides an APIClient instance for the test module."""
    return APIClient()

@pytest.fixture
def org_type():
    return OrganizationTypeFactory()

@pytest.fixture
def org_a(org_type):
    return OrganizationFactory(organization_type=org_type, name="Integration Org A")

@pytest.fixture
def org_b(org_type):
    return OrganizationFactory(organization_type=org_type, name="Integration Org B")

@pytest.fixture
def permission_change():
    content_type = ContentType.objects.get_for_model(ConcreteScopedModel)
    try:
        perm, _ = Permission.objects.get_or_create(
            codename='change_concretescopedmodel', 
            content_type=content_type,
            defaults={'name': 'Can change concrete scoped model'}
        )
        return perm
    except IntegrityError: 
        return Permission.objects.get(
            codename='change_concretescopedmodel', 
            content_type=content_type
        )

@pytest.fixture
def permission_view():
    content_type = ContentType.objects.get_for_model(ConcreteScopedModel)
    try:
        perm, _ = Permission.objects.get_or_create(
            codename='view_concretescopedmodel', 
            content_type=content_type,
            defaults={'name': 'Can view concrete scoped model'}
        )
        return perm
    except IntegrityError:
        return Permission.objects.get(
            codename='view_concretescopedmodel', 
            content_type=content_type
        )

@pytest.fixture
def user_a(org_a, permission_change, permission_view):
    user = UserFactory(username="user_a_integration")
    membership = OrganizationMembershipFactory(user=user, organization=org_a)
    membership.role.permissions.add(permission_change, permission_view)
    return user

@pytest.fixture
def user_b(org_b, permission_view):
    user = UserFactory(username="user_b_integration")
    membership = OrganizationMembershipFactory(user=user, organization=org_b)
    membership.role.permissions.add(permission_view)
    return user

@pytest.fixture
def super_user():
    return UserFactory(username="super_integration", is_superuser=True)
    
@pytest.fixture
def user():
    """Generic user fixture for tests that don't need specific org roles."""
    return UserFactory()

@pytest.fixture
def obj_a1(org_a): # Renamed for clarity for viewset tests
    return ConcreteScopedModel.objects.create(name="Obj A1", organization=org_a)

@pytest.fixture
def obj_a2(org_a): # Renamed for clarity
    return ConcreteScopedModel.objects.create(name="Obj A2", organization=org_a)

@pytest.fixture
def obj_in_org_a(obj_a1):
    return obj_a1

@pytest.fixture
def obj_b1(org_b): # Renamed for clarity
    return ConcreteScopedModel.objects.create(name="Obj B1", organization=org_b)

@pytest.fixture
def obj_in_org_b(obj_b1):
    return obj_b1

# Add any other shared fixtures needed by both integration test files 