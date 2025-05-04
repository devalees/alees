from functools import lru_cache
from typing import Any, Union, Optional

from django.core.cache import caches
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
import logging # Import logging
from django.apps import apps # Import apps to get Organization model dynamically

# Adjust path (using the correct path based on project structure)
# Remove direct import to avoid potential circularity if Organization model itself needs permissions
# from api.v1.base_models.organization.models import OrganizationMembership, Organization

User = get_user_model()
logger = logging.getLogger(__name__) # Get logger instance

permission_cache = caches['rbac']
CACHE_TIMEOUT = settings.RBAC_CACHE_TIMEOUT if hasattr(settings, 'RBAC_CACHE_TIMEOUT') else 3600 # Default 1 hour

# @lru_cache(maxsize=...) # Simple in-memory cache (per process)
def has_perm_in_org(
    user: Union[User, AnonymousUser, None],
    perm_codename: str,
    org_or_obj_or_id: Union['Organization', Any, int] # Accept int ID
) -> bool:
    """
    Checks if a user has a specific model-level permission within the
    context of a given organization, org-scoped object, or organization ID.
    Handles permissions like 'view_mymodel' or 'app_label.view_mymodel'.
    Caches results per user per organization.
    """
    # <<< Start Logging >>>
    logger.debug(f"[has_perm_in_org] Args: user='{user}', perm='{perm_codename}', org/obj/id='{org_or_obj_or_id}'")
    # <<< End Logging >>>

    if not user or not getattr(user, 'is_authenticated', False):
        logger.debug("[has_perm_in_org] Result: False (User not authenticated)")
        return False
    if getattr(user, 'is_superuser', False):
        logger.debug("[has_perm_in_org] Result: True (User is superuser)")
        return True

    # --- Determine the organization ID --- 
    organization_id: Optional[int] = None
    # Dynamically get the Organization model to avoid direct import
    try:
        Organization = apps.get_model('api_v1_organization', 'Organization')
    except LookupError:
         logger.error("Could not load Organization model for permission check.")
         return False # Cannot proceed without Organization model

    if isinstance(org_or_obj_or_id, Organization):
        organization_id = org_or_obj_or_id.pk
        logger.debug(f"[has_perm_in_org] Org determined directly: {organization_id}")
    elif isinstance(org_or_obj_or_id, int):
        organization_id = org_or_obj_or_id
        logger.debug(f"[has_perm_in_org] Org ID provided directly: {organization_id}")
    elif hasattr(org_or_obj_or_id, 'organization_id') and getattr(org_or_obj_or_id, 'organization_id') is not None:
        # Check for organization_id first for efficiency if object is already loaded
        organization_id = getattr(org_or_obj_or_id, 'organization_id')
        logger.debug(f"[has_perm_in_org] Org ID determined from obj.organization_id attribute: {organization_id}")
    elif hasattr(org_or_obj_or_id, 'organization') and isinstance(getattr(org_or_obj_or_id, 'organization'), Organization):
        # Fallback to checking organization attribute
        organization_id = getattr(org_or_obj_or_id, 'organization').pk
        logger.debug(f"[has_perm_in_org] Org determined from obj.organization attribute: {organization_id}")
    else:
        # Cannot determine organization context
        logger.warning(f"[has_perm_in_org] Cannot determine organization context for: {org_or_obj_or_id}")
        logger.debug("[has_perm_in_org] Result: False (Org context indeterminable)")
        return False
    # --- End Organization ID determination ---

    # --- Check Cache --- 
    user_pk = getattr(user, 'pk', None)
    if user_pk is None: return False # Should not happen
    cache_key = f'rbac:perms:user:{user_pk}:org:{organization_id}'
    cached_perms_set: Optional[set[str]] = permission_cache.get(cache_key)
    # Use the codename part only (e.g., 'add_contact' from 'contact.add_contact')
    actual_perm_codename = perm_codename.split('.')[-1]

    if cached_perms_set is not None:
        logger.debug(f"[has_perm_in_org] Cache HIT for key '{cache_key}'")
        has_perm = actual_perm_codename in cached_perms_set
        logger.debug(f"[has_perm_in_org] Result from cache: {has_perm} (Checking '{actual_perm_codename}' in {cached_perms_set})")
        return has_perm
    else:
        logger.info(f"[has_perm_in_org] Cache MISS for key '{cache_key}'") # Log miss at info level
    # --- End Cache Check ---

    # --- Cache Miss: Fetch from DB --- 
    permissions_set: set[str] = set()
    # Dynamically get OrganizationMembership model
    try:
        OrganizationMembership = apps.get_model('api_v1_organization', 'OrganizationMembership')
    except LookupError:
         logger.error("Could not load OrganizationMembership model for permission check.")
         return False # Cannot proceed without OrganizationMembership model

    # Find active membership for this specific org
    try:
        membership = OrganizationMembership.objects.select_related('role') \
                                             .prefetch_related('role__permissions') \
                                             .get(user=user, organization_id=organization_id, is_active=True)
        logger.debug(f"[has_perm_in_org] Found membership {membership.pk} with role '{membership.role}'")
        if membership.role:
            # Permissions are pre-fetched
            permissions_set = {p.codename for p in membership.role.permissions.all()}
            logger.debug(f"[has_perm_in_org] Fetched permissions for role '{membership.role.name}': {permissions_set}")
    except OrganizationMembership.DoesNotExist:
        logger.info(f"[has_perm_in_org] No active membership found for user {user_pk} in org {organization_id}")
        pass # permissions_set remains empty
    except Exception as e:
        logger.error(f"[has_perm_in_org] Error fetching membership/permissions for user {user_pk}, org {organization_id}: {e}", exc_info=True)
        return False # Return False on error fetching perms

    # --- Set Cache --- 
    permission_cache.set(cache_key, permissions_set, timeout=CACHE_TIMEOUT)
    logger.info(f"[has_perm_in_org] Set cache '{cache_key}' with perms: {permissions_set}")
    # --- End Set Cache --- 

    # Check if the required permission exists in the (newly cached) set
    has_perm = actual_perm_codename in permissions_set
    logger.debug(f"[has_perm_in_org] Result from DB check: {has_perm} (Checking '{actual_perm_codename}' in {permissions_set})")
    return has_perm

# --- Cache Invalidation (Simplified Example - needs refinement) --- 