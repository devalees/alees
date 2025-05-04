import pytest
from django.core.cache import caches
from django.contrib.auth.models import Group, Permission, AnonymousUser
from django.contrib.contenttypes.models import ContentType

# Assuming factories are available
from api.v1.base_models.user.tests.factories import UserFactory
from api.v1.base_models.organization.tests.factories import (
    OrganizationFactory,
    OrganizationMembershipFactory,
)
from core.rbac.permissions import has_perm_in_org

permission_cache = caches['rbac']

@pytest.fixture
def setup_perms(django_user_model):
    """Common setup for user, org, role, and permissions."""
    user = UserFactory()
    org = OrganizationFactory()
    role = Group.objects.create(name='TestRoleForPermCheck')
    content_type = ContentType.objects.get_for_model(django_user_model)
    perm_view, _ = Permission.objects.get_or_create(
        codename='view_user', name='Can view user', content_type=content_type
    )
    perm_change, _ = Permission.objects.get_or_create(
        codename='change_user', name='Can change user', content_type=content_type
    )
    role.permissions.add(perm_view)

    membership = OrganizationMembershipFactory(
        user=user, organization=org, role=role, is_active=True
    )

    # Clear caches
    permission_cache.delete(f'rbac:perms:user:{user.pk}:org:{org.pk}')

    return user, org, role, membership, perm_view, perm_change

@pytest.mark.django_db
def test_has_perm_in_org_with_object(setup_perms):
    """Test has_perm_in_org using an org-scoped object."""
    user, org, _, _, perm_view, perm_change = setup_perms

    # Create a dummy object associated with the organization
    class MockOrgScopedObject:
        def __init__(self, org):
            self.organization = org
        def __str__(self):
             return f"MockObject(org={self.organization.pk})"

    mock_obj = MockOrgScopedObject(org)

    assert has_perm_in_org(user, 'view_user', mock_obj) is True
    assert has_perm_in_org(user, 'user.view_user', mock_obj) is True # Test with app label
    assert has_perm_in_org(user, 'change_user', mock_obj) is False
    assert has_perm_in_org(user, 'auth.change_user', mock_obj) is False # Test with app label

@pytest.mark.django_db
def test_has_perm_in_org_with_organization(setup_perms):
    """Test has_perm_in_org passing the Organization instance directly."""
    user, org, _, _, perm_view, perm_change = setup_perms

    assert has_perm_in_org(user, 'view_user', org) is True
    assert has_perm_in_org(user, 'user.view_user', org) is True
    assert has_perm_in_org(user, 'change_user', org) is False
    assert has_perm_in_org(user, 'auth.change_user', org) is False

@pytest.mark.django_db
def test_has_perm_in_org_with_org_id(setup_perms):
    """Test has_perm_in_org passing the organization ID (New Functionality)."""
    user, org, _, _, perm_view, perm_change = setup_perms

    org_id = org.pk

    # These should fail until has_perm_in_org is updated
    assert has_perm_in_org(user, 'view_user', org_id) is True
    assert has_perm_in_org(user, 'user.view_user', org_id) is True
    assert has_perm_in_org(user, 'change_user', org_id) is False
    assert has_perm_in_org(user, 'auth.change_user', org_id) is False

@pytest.mark.django_db
def test_has_perm_in_org_cache_hit(setup_perms):
    """Test cache hit scenario for has_perm_in_org."""
    user, org, _, _, perm_view, _ = setup_perms

    # First call populates cache
    assert has_perm_in_org(user, 'view_user', org) is True

    # TODO: Ideally, mock the DB query here to ensure it's not hit again.
    # For now, just check the result again, relying on the cache.
    assert has_perm_in_org(user, 'view_user', org) is True

@pytest.mark.django_db
def test_has_perm_in_org_no_membership(setup_perms):
    """Test user with no membership in the target org."""
    user, _, _, _, perm_view, _ = setup_perms
    other_org = OrganizationFactory()

    assert has_perm_in_org(user, 'view_user', other_org) is False

@pytest.mark.django_db
def test_has_perm_in_org_inactive_membership(setup_perms):
    """Test user with only an inactive membership in the target org."""
    user, org, role, membership, perm_view, _ = setup_perms
    membership.is_active = False
    membership.save()

    # Clear cache after save triggers invalidation
    permission_cache.delete(f'rbac:perms:user:{user.pk}:org:{org.pk}')

    assert has_perm_in_org(user, 'view_user', org) is False

@pytest.mark.django_db
def test_has_perm_in_org_superuser(setup_perms):
    """Test superuser always has permission."""
    user, org, _, _, _, perm_change = setup_perms
    user.is_superuser = True
    user.save()

    assert has_perm_in_org(user, 'change_user', org) is True
    assert has_perm_in_org(user, 'any_permission', org) is True

@pytest.mark.django_db
def test_has_perm_in_org_anonymous_user(setup_perms):
    """Test anonymous user never has permission."""
    _, org, _, _, perm_view, _ = setup_perms
    anon_user = AnonymousUser()

    assert has_perm_in_org(anon_user, 'view_user', org) is False 