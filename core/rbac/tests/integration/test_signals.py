import pytest
from django.core.cache import cache

# Assuming factories are available
from api.v1.base_models.user.tests.factories import UserFactory
from api.v1.base_models.organization.tests.factories import (
    OrganizationFactory,
    OrganizationMembershipFactory,
)

# Assuming the helper function exists and works for setting the initial cache
from core.rbac.utils import get_user_request_context


@pytest.mark.django_db
def test_membership_save_invalidates_active_org_ids_cache():
    """Verify saving an OrganizationMembership invalidates the active_org_ids cache."""
    user = UserFactory()
    org = OrganizationFactory()
    membership = OrganizationMembershipFactory(user=user, organization=org, is_active=True)

    # Prime the cache by calling the helper function
    org_ids_cache_key = f'user:{user.pk}:active_org_ids'
    cache.delete(org_ids_cache_key) # Ensure cache is clear initially
    initial_ids, _ = get_user_request_context(user) 
    assert cache.get(org_ids_cache_key) is not None # Cache should be primed now
    assert initial_ids == [org.pk]

    # Modify and save the membership (e.g., deactivate)
    membership.is_active = False
    membership.save()

    # Assert that the active_org_ids cache was invalidated (deleted)
    assert cache.get(org_ids_cache_key) is None, \
        "active_org_ids cache should be invalidated after membership save"

@pytest.mark.django_db
def test_membership_delete_invalidates_active_org_ids_cache():
    """Verify deleting an OrganizationMembership invalidates the active_org_ids cache."""
    user = UserFactory()
    org = OrganizationFactory()
    membership = OrganizationMembershipFactory(user=user, organization=org, is_active=True)

    # Prime the cache
    org_ids_cache_key = f'user:{user.pk}:active_org_ids'
    cache.delete(org_ids_cache_key)
    initial_ids, _ = get_user_request_context(user)
    assert cache.get(org_ids_cache_key) is not None
    assert initial_ids == [org.pk]

    # Delete the membership
    membership_pk = membership.pk
    membership.delete()

    # Assert that the active_org_ids cache was invalidated (deleted)
    assert cache.get(org_ids_cache_key) is None, \
        "active_org_ids cache should be invalidated after membership delete" 