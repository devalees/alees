import pytest
from django.urls import reverse
from rest_framework import status
from django.core.cache import cache, caches
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

# Assuming factories are available from these locations based on structure
from api.v1.base_models.user.tests.factories import UserFactory
from api.v1.base_models.organization.tests.factories import (
    OrganizationFactory,
    OrganizationMembershipFactory,
)

# Use the specific 'rbac' cache
permission_cache = caches['rbac']

@pytest.fixture
def group_content_type():
    """Fixture to provide the ContentType for the Group model."""
    return ContentType.objects.get_for_model(Group)

@pytest.fixture
def view_group_perm(group_content_type):
    """Fixture to ensure view_group permission exists."""
    perm, _ = Permission.objects.get_or_create(
        codename='view_group',
        name='Can view group',
        content_type=group_content_type,
    )
    return perm

@pytest.fixture
def change_group_perm(group_content_type):
    """Fixture to ensure change_group permission exists."""
    perm, _ = Permission.objects.get_or_create(
        codename='change_group',
        name='Can change group',
        content_type=group_content_type,
    )
    return perm

@pytest.mark.django_db
def test_login_populates_rbac_cache_single_org(client, view_group_perm):
    """Verify RBAC caches are populated correctly on login for a single-org user."""
    password = 'strongpassword'
    user = UserFactory(password=password)
    org = OrganizationFactory()
    role = Group.objects.create(name='TestMemberRoleSingle') # Use unique role name
    # Assign the permission from the fixture
    role.permissions.add(view_group_perm)

    # Create active membership
    membership = OrganizationMembershipFactory(user=user, organization=org, is_active=True)
    membership.roles.add(role)

    # Use absolute path reverse lookup (adjust based on actual root inclusion)
    # Assuming common.urls is included within api.v1 path
    login_url = reverse('v1:base_models:common:token_obtain_pair') # Try full inferred path

    # --- Pre-login cache check --- 
    org_ids_cache_key = f'user:{user.pk}:active_org_ids'
    perms_cache_key = f'rbac:perms:user:{user.pk}:org:{org.pk}'
    # Clear caches before test for isolation
    cache.delete(org_ids_cache_key)
    permission_cache.delete(perms_cache_key)
    assert cache.get(org_ids_cache_key) is None
    assert permission_cache.get(perms_cache_key) is None

    # --- Perform Login --- 
    response = client.post(login_url, {'username': user.username, 'password': password})

    # --- Post-login cache assertion --- 
    assert response.status_code == status.HTTP_200_OK
    assert 'access' in response.data
    assert 'refresh' in response.data

    # Check that caches are now populated
    cached_org_ids = cache.get(org_ids_cache_key)
    assert cached_org_ids is not None, f"Cache key {org_ids_cache_key} not found after login"
    assert cached_org_ids == [org.pk]

    cached_perms = permission_cache.get(perms_cache_key)
    assert cached_perms is not None, f"Cache key {perms_cache_key} not found after login"
    assert cached_perms == {'view_group'} # Check for the specific permission codename

@pytest.mark.django_db
def test_login_populates_rbac_cache_multi_org(client, change_group_perm, view_group_perm):
    """Verify RBAC caches are populated correctly on login for a multi-org user."""
    password = 'strongpassword'
    user = UserFactory(password=password)
    org1 = OrganizationFactory()
    org2 = OrganizationFactory()
    role1 = Group.objects.create(name='TestManagerRoleMulti') # Unique role names
    role2 = Group.objects.create(name='TestViewerRoleMulti')

    # Assign permissions from fixtures
    role1.permissions.add(change_group_perm)
    role2.permissions.add(view_group_perm)

    # Create active memberships
    membership1 = OrganizationMembershipFactory(user=user, organization=org1, is_active=True)
    membership1.roles.add(role1)
    
    membership2 = OrganizationMembershipFactory(user=user, organization=org2, is_active=True)
    membership2.roles.add(role2)
    
    # Create an inactive membership - should be ignored
    org3 = OrganizationFactory()
    role3 = Group.objects.create(name='TestInactiveRoleMulti')
    membership3 = OrganizationMembershipFactory(user=user, organization=org3, is_active=False)
    membership3.roles.add(role3)

    login_url = reverse('v1:base_models:common:token_obtain_pair') # Try full inferred path

    # --- Pre-login cache check --- 
    org_ids_cache_key = f'user:{user.pk}:active_org_ids'
    perms_cache_key1 = f'rbac:perms:user:{user.pk}:org:{org1.pk}'
    perms_cache_key2 = f'rbac:perms:user:{user.pk}:org:{org2.pk}'
    perms_cache_key3 = f'rbac:perms:user:{user.pk}:org:{org3.pk}'
    # Clear caches before test for isolation
    cache.delete(org_ids_cache_key)
    permission_cache.delete(perms_cache_key1)
    permission_cache.delete(perms_cache_key2)
    permission_cache.delete(perms_cache_key3)
    assert cache.get(org_ids_cache_key) is None
    assert permission_cache.get(perms_cache_key1) is None
    assert permission_cache.get(perms_cache_key2) is None
    assert permission_cache.get(perms_cache_key3) is None # For inactive org

    # --- Perform Login --- 
    response = client.post(login_url, {'username': user.username, 'password': password})

    # --- Post-login cache assertion --- 
    assert response.status_code == status.HTTP_200_OK

    cached_org_ids = cache.get(org_ids_cache_key)
    assert cached_org_ids is not None
    # Order might not be guaranteed, sort for comparison
    assert sorted(cached_org_ids) == sorted([org1.pk, org2.pk])

    cached_perms1 = permission_cache.get(perms_cache_key1)
    assert cached_perms1 is not None
    assert cached_perms1 == {'change_group'}

    cached_perms2 = permission_cache.get(perms_cache_key2)
    assert cached_perms2 is not None
    assert cached_perms2 == {'view_group'}

    # Ensure cache for inactive membership org was NOT populated
    assert permission_cache.get(perms_cache_key3) is None 