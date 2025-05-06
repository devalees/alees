""" RBAC utility functions for organization context handling. """

from django.core.cache import cache, caches
from django.core.exceptions import PermissionDenied, ValidationError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.apps import apps
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

# Use the same cache timeout as defined for permissions
CACHE_TIMEOUT = settings.RBAC_CACHE_TIMEOUT if hasattr(settings, 'RBAC_CACHE_TIMEOUT') else 3600 # Default 1 hour
permission_cache = caches['rbac'] # Assuming 'rbac' alias is defined

def get_user_request_context(user):
    """
    Retrieves the user's active organization context from cache.
    On cache miss, rebuilds the cache from the database.

    Returns:
        tuple: (list_of_active_org_ids, is_single_org_context)
        Returns ([], False) if no active orgs or invalid user.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return [], False

    cache_key = f'user:{user.pk}:active_org_ids'
    cached_ids = cache.get(cache_key)

    if cached_ids is None:
        logger.info(f"Cache MISS for active_org_ids for user {user.pk}. Rebuilding.")
        # Cache miss - rebuild
        try:
            # Ensure the user model has the required method
            if not hasattr(user, 'get_organizations'):
                logger.error(f"User model does not have 'get_organizations' method.")
                return [], False

            # Call the method defined in user/models.py
            # This should already filter for active memberships
            active_orgs = user.get_organizations()
            cached_ids = list(active_orgs.values_list('pk', flat=True))

            cache.set(cache_key, cached_ids, timeout=CACHE_TIMEOUT)
            logger.info(f"Set active_org_ids cache for user {user.pk}: {cached_ids}")

            # --- Optional: Pre-warm permission cache here too --- #
            # This duplicates logic from login, but ensures cache is warm if missed.
            # Consider if this is necessary or if login caching is sufficient.
            try:
                OrganizationMembership = apps.get_model('api_v1_organization', 'OrganizationMembership')
                memberships = OrganizationMembership.objects.filter(
                    user=user,
                    organization_id__in=cached_ids, # Already filtered for active orgs
                    is_active=True # Double check active membership here
                ).prefetch_related('roles', 'roles__permissions')

                for membership in memberships:
                    org_id = membership.organization_id
                    perms_set = set()
                    # Collect permissions from all roles
                    for role in membership.roles.all():
                        perms_set.update(role.permissions.values_list('codename', flat=True))
                    
                    perm_cache_key = f'rbac:perms:user:{user.pk}:org:{org_id}'
                    # Use the specific 'rbac' cache alias for permissions
                    permission_cache.set(perm_cache_key, perms_set, timeout=CACHE_TIMEOUT)
                    logger.info(f"Pre-warmed permission cache for user {user.pk}, org {org_id}")
            except LookupError:
                 logger.error("Could not load OrganizationMembership model to pre-warm permissions cache.")
            # --- End Optional Pre-warm --- #

        except Exception as e:
            # Handle potential errors during DB query or caching
            logger.error(f"Error rebuilding active_org_ids cache for user {user.pk}: {e}", exc_info=True)
            return [], False # Return empty on error
    else:
         logger.debug(f"Cache HIT for active_org_ids for user {user.pk}: {cached_ids}")

    is_single = len(cached_ids) == 1
    return cached_ids, is_single

def get_validated_request_org_id(request, required_for_action=True):
    """
    Determines the target organization ID based on user context and request data.
    Validates if the user has access to the specified organization.

    Args:
        request: The DRF request object.
        required_for_action (bool): If True, enforces org ID provision for multi-org users.
                                   If False, returns None if no org_id is provided by multi-org user.

    Returns:
        int or None: The validated organization ID.
        Raises PermissionDenied or ValidationError on failure.
    """
    user = request.user
    active_org_ids, is_single_org = get_user_request_context(user)

    if not active_org_ids:
        # This case should ideally be caught by a higher-level permission check,
        # but we check here defensively.
        raise PermissionDenied("You do not have access to any active organizations.")

    # Look in request data (POST/PUT/PATCH) first, then query params (GET)
    provided_org_id_str = request.data.get('organization') or request.query_params.get('organization')
    provided_org_id = None
    if provided_org_id_str:
         try:
             provided_org_id = int(provided_org_id_str)
         except (ValueError, TypeError):
             raise ValidationError({"organization": "Invalid organization ID format provided."}) # Field-specific error

    if is_single_org:
        # Single-org user: Automatically use their only org
        target_org_id = active_org_ids[0]
        if provided_org_id is not None and provided_org_id != target_org_id:
            # User provided an org ID, but it's either wrong or unnecessary
            raise ValidationError({"organization": "Organization ID must not be provided or must match your assigned organization."}) # Field-specific error
        logger.debug(f"Single-org user {user.pk}: Using automatically determined org_id {target_org_id}")
        return target_org_id
    else:
        # Multi-org user: Must provide a valid org ID if required
        if required_for_action and provided_org_id is None:
             raise ValidationError({"organization": "Organization ID must be provided for this action."}) # Field-specific error
        elif not required_for_action and provided_org_id is None:
             logger.debug(f"Multi-org user {user.pk}: No org_id provided and not required for action.")
             return None # Action doesn't strictly require one

        # If an ID was provided, validate it against the user's active orgs
        if provided_org_id not in active_org_ids:
            logger.warning(f"User {user.pk} denied access to provided org_id {provided_org_id}. Active orgs: {active_org_ids}")
            raise PermissionDenied("You do not have permission to access the specified organization.")

        logger.debug(f"Multi-org user {user.pk}: Using provided and validated org_id {provided_org_id}")
        return provided_org_id 