from functools import lru_cache
from typing import Any, Union, Optional

from django.core.cache import caches
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
import logging # Import logging

# Adjust path (using the correct path based on project structure)
from api.v1.base_models.organization.models import OrganizationMembership, Organization

User = get_user_model()
logger = logging.getLogger(__name__) # Get logger instance

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
    # <<< Start Logging >>>
    logger.info(f"[has_perm_in_org] Args: user='{user}', perm='{perm_codename}', org/obj='{org_or_obj}'")
    # <<< End Logging >>>

    if not user or not getattr(user, 'is_authenticated', False):
        # <<< Logging >>>
        logger.info(f"[has_perm_in_org] Result: False (User not authenticated)")
        # <<< End Logging >>>
        return False
    if getattr(user, 'is_superuser', False):
        # <<< Logging >>>
        logger.info(f"[has_perm_in_org] Result: True (User is superuser)")
        # <<< End Logging >>>
        return True

    # Determine the organization
    organization = None
    if isinstance(org_or_obj, Organization):
        organization = org_or_obj
        # <<< Logging >>>
        logger.info(f"[has_perm_in_org] Org determined directly: {organization.pk}")
        # <<< End Logging >>>
    elif hasattr(org_or_obj, 'organization') and isinstance(getattr(org_or_obj, 'organization'), Organization):
        organization = getattr(org_or_obj, 'organization')
        # <<< Logging >>>
        logger.info(f"[has_perm_in_org] Org determined from obj attribute: {organization.pk}")
        # <<< End Logging >>>
    else:
        # Cannot determine organization context
        # <<< Logging >>>
        logger.warning(f"[has_perm_in_org] Cannot determine organization context for obj: {org_or_obj}")
        logger.info(f"[has_perm_in_org] Result: False (Org context indeterminable)")
        # <<< End Logging >>>
        return False

    # --- Check Cache ---
    user_pk = getattr(user, 'pk', None)
    if user_pk is None: return False # Should not happen
    cache_key = f'rbac:perms:user:{user_pk}:org:{organization.pk}'
    cached_perms_set: Optional[set[str]] = permission_cache.get(cache_key)
    # Use the codename part only (e.g., 'add_contact' from 'contact.add_contact')
    actual_perm_codename = perm_codename.split('.')[-1]

    if cached_perms_set is not None:
        # <<< Logging >>>
        logger.info(f"[has_perm_in_org] Cache HIT for key '{cache_key}'")
        # <<< End Logging >>>
        has_perm = actual_perm_codename in cached_perms_set
        # <<< Logging >>>
        logger.info(f"[has_perm_in_org] Result from cache: {has_perm} (Checking '{actual_perm_codename}' in {cached_perms_set})")
        # <<< End Logging >>>
        return has_perm
    else:
        # <<< Logging >>>
        logger.info(f"[has_perm_in_org] Cache MISS for key '{cache_key}'")
        # <<< End Logging >>>
        pass
    # --- End Cache Check ---

    # --- Cache Miss: Fetch from DB --- 
    permissions_set: set[str] = set()
    # Find active membership for this specific org
    try:
        membership = OrganizationMembership.objects.select_related('role') \
                                             .get(user=user, organization=organization, is_active=True)
        # <<< Logging >>>
        logger.info(f"[has_perm_in_org] Found membership {membership.pk} with role '{membership.role}'")
        # <<< End Logging >>>
        if membership.role:
            permissions_set = set(
                membership.role.permissions.values_list('codename', flat=True)
            )
            # <<< Logging >>>
            logger.info(f"[has_perm_in_org] Fetched permissions for role '{membership.role.name}': {permissions_set}")
            # <<< End Logging >>>
    except OrganizationMembership.DoesNotExist:
        # <<< Logging >>>
        logger.warning(f"[has_perm_in_org] No active membership found for user {user_pk} in org {organization.pk}")
        # <<< End Logging >>>
        pass # permissions_set remains empty

    # --- Set Cache --- 
    permission_cache.set(cache_key, permissions_set, timeout=CACHE_TIMEOUT)
    # <<< Logging >>>
    logger.info(f"[has_perm_in_org] Set cache '{cache_key}' with perms: {permissions_set}")
    # <<< End Logging >>>
    # --- End Set Cache --- 

    # Check if the required permission exists in the (newly cached) set
    has_perm = actual_perm_codename in permissions_set
    # <<< Logging >>>
    logger.info(f"[has_perm_in_org] Result from DB check: {has_perm} (Checking '{actual_perm_codename}' in {permissions_set})")
    # <<< End Logging >>>
    return has_perm

# --- Cache Invalidation (Simplified Example - needs refinement) --- 