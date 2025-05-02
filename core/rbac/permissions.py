from functools import lru_cache
from typing import Any, Union, Optional

from django.core.cache import caches
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

# Adjust path (using the correct path based on project structure)
from api.v1.base_models.organization.models import OrganizationMembership, Organization

User = get_user_model()

permission_cache = caches['permissions']
CACHE_TIMEOUT = settings.RBAC_CACHE_TIMEOUT if hasattr(settings, 'RBAC_CACHE_TIMEOUT') else 3600 # Default 1 hour

# @lru_cache(maxsize=...) # Keep lru_cache commented for now, focus on Django cache
def has_perm_in_org(
    user: Union[User, AnonymousUser, None],
    perm_codename: str,
    org_or_obj: Union[Organization, models.Model, Any]
) -> bool:
    """
    Checks if a user has a specific model-level permission within the
    context of a given organization or org-scoped object, utilizing caching.

    Args:
        user: The user instance to check.
        perm_codename: The permission codename (e.g., 'app_label.codename').
        org_or_obj: An Organization instance or an object with an 'organization' attribute.

    Returns:
        True if the user has the permission in the organization context, False otherwise.
    """
    if not user or not getattr(user, 'is_authenticated', False): # Handles None and AnonymousUser
        return False
    if getattr(user, 'is_superuser', False):
        return True

    # Determine the organization
    organization: Optional[Organization] = None
    if isinstance(org_or_obj, Organization):
        organization = org_or_obj
    elif hasattr(org_or_obj, 'organization') and isinstance(getattr(org_or_obj, 'organization'), Organization):
        organization = getattr(org_or_obj, 'organization')

    if organization is None:
        # Cannot determine organization context
        return False

    # --- Check Cache --- (Caches the set of permission codenames for the user in this org)
    # Use getattr(user, 'pk', None) to safely access pk for AnonymousUser cases although they should be filtered out
    user_pk = getattr(user, 'pk', None)
    if user_pk is None:
         return False # Should not happen if is_authenticated check passed

    cache_key = f'rbac:perms:user:{user_pk}:org:{organization.pk}'
    cached_perms_set: Optional[set[str]] = permission_cache.get(cache_key)

    actual_perm_codename = perm_codename.split('.')[-1]

    if cached_perms_set is not None:
        # Cache hit: Check if the specific permission is in the cached set
        return actual_perm_codename in cached_perms_set
    # --- End Cache Check ---

    # --- Cache Miss: Fetch from DB --- 
    permissions_set: set[str] = set()
    try:
        membership = OrganizationMembership.objects.select_related('role')\
                                                 .prefetch_related('role__permissions')\
                                                 .get(user=user, organization=organization, is_active=True)
        if membership.role:
            # Get all permission codenames for the assigned role
            permissions_set = set(
                membership.role.permissions.values_list('codename', flat=True)
            )

    except OrganizationMembership.DoesNotExist:
        # User not an active member or no membership exists for this org
        pass # permissions_set remains empty

    # --- Set Cache --- 
    permission_cache.set(cache_key, permissions_set, timeout=CACHE_TIMEOUT)
    # --- End Set Cache --- 

    # Check if the required permission exists in the (newly cached) set
    return actual_perm_codename in permissions_set

# --- Cache Invalidation placeholder (Implementation in signals.py) --- 