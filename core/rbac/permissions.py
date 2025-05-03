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

permission_cache = caches['rbac']
CACHE_TIMEOUT = settings.RBAC_CACHE_TIMEOUT if hasattr(settings, 'RBAC_CACHE_TIMEOUT') else 3600 # Default 1 hour

# @lru_cache(maxsize=...) # Simple in-memory cache (per process)
def has_perm_in_org(
    user: Union[User, AnonymousUser, None],
    perm_codename: str,
    org_or_obj: Union[Organization, Any]
) -> bool:
    """
    Checks if a user has a specific model-level permission within the
    context of a given organization or org-scoped object.
    """
    # print(f"[has_perm_in_org] Checking user '{user}' perm '{perm_codename}' for obj/org '{org_or_obj}'") # DEBUG
    if not user or not getattr(user, 'is_authenticated', False):
        # print("[has_perm_in_org] Denied: User not authenticated") # DEBUG
        return False
    if getattr(user, 'is_superuser', False):
        # print("[has_perm_in_org] Allowed: User is superuser") # DEBUG
        return True

    # Determine the organization
    organization = None
    if isinstance(org_or_obj, Organization):
        organization = org_or_obj
        # print(f"[has_perm_in_org] Determined org {organization.pk} directly") # DEBUG
    elif hasattr(org_or_obj, 'organization') and isinstance(getattr(org_or_obj, 'organization'), Organization):
        organization = getattr(org_or_obj, 'organization')
        # print(f"[has_perm_in_org] Determined org {organization.pk} from obj attribute") # DEBUG
    else:
        # Cannot determine organization context
        # print("[has_perm_in_org] Denied: Cannot determine organization context") # DEBUG
        return False

    # --- Check Cache ---
    user_pk = getattr(user, 'pk', None)
    if user_pk is None: return False # Should not happen
    cache_key = f'rbac:perms:user:{user_pk}:org:{organization.pk}'
    cached_perms_set: Optional[set[str]] = permission_cache.get(cache_key)
    actual_perm_codename = perm_codename.split('.')[-1] # Use only codename part for check

    if cached_perms_set is not None:
        # print(f"[has_perm_in_org] Cache hit for {cache_key}") # DEBUG
        has_perm = actual_perm_codename in cached_perms_set
        # print(f"[has_perm_in_org] Allowed from cache: {has_perm}") # DEBUG
        return has_perm
    # else:
    #     print(f"[has_perm_in_org] Cache miss for {cache_key}") # DEBUG
    # --- End Cache Check ---

    # --- Cache Miss: Fetch from DB --- 
    permissions_set: set[str] = set()
    # Find active membership for this specific org
    try:
        # Use select_related for the ForeignKey 'role', not the M2M 'permissions'
        membership = OrganizationMembership.objects.select_related('role') \
                                             .get(user=user, organization=organization, is_active=True)
        # print(f"[has_perm_in_org] Found membership {membership.pk} with role {membership.role}") # DEBUG
        if membership.role:
            # Get all permission codenames for the assigned role
            permissions_set = set(
                membership.role.permissions.values_list('codename', flat=True)
            )
            # print(f"[has_perm_in_org] Role '{membership.role.name}' perms: {permissions_set}") # DEBUG
    except OrganizationMembership.DoesNotExist:
        # print(f"[has_perm_in_org] Denied: No active membership for user {user_pk} in org {organization.pk}") # DEBUG
        pass # permissions_set remains empty

    # --- Set Cache --- 
    permission_cache.set(cache_key, permissions_set, timeout=CACHE_TIMEOUT)
    # print(f"[has_perm_in_org] Set cache {cache_key} with perms: {permissions_set}") # DEBUG
    # --- End Set Cache --- 

    # Check if the required permission exists in the (newly cached) set
    has_perm = actual_perm_codename in permissions_set
    # print(f"[has_perm_in_org] Permission result (after DB check): {has_perm}") # DEBUG
    return has_perm

# --- Cache Invalidation (Simplified Example - needs refinement) --- 