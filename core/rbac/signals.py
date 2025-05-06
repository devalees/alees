from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.cache import caches, cache
from django.conf import settings
from django.contrib.auth.models import Group

from api.v1.base_models.organization.models import OrganizationMembership

# Use the consistent 'rbac' cache alias for permissions
permission_cache = caches['rbac']
# Use the default cache for the active_org_ids list
default_cache = cache

def _invalidate_user_org_perm_cache(user_pk, org_pk):
    """Helper function to invalidate the permission cache for a specific user/org."""
    cache_key = f'rbac:perms:user:{user_pk}:org:{org_pk}'
    permission_cache.delete(cache_key)
    # print(f"DEBUG: Invalidated RBAC perm cache for user {user_pk}, org {org_pk}") # For debugging

def _invalidate_user_active_org_ids_cache(user_pk):
    """Helper function to invalidate the active org list cache for a user."""
    cache_key = f'user:{user_pk}:active_org_ids'
    default_cache.delete(cache_key)
    # print(f"DEBUG: Invalidated active_org_ids cache for user {user_pk}") # For debugging

@receiver(post_save, sender=OrganizationMembership)
def invalidate_on_membership_save(sender, instance: OrganizationMembership, **kwargs):
    """Invalidate cache when an OrganizationMembership is saved (active status changes)."""
    if instance.user_id:
        # Invalidate specific perm cache for the affected org (if active)
        if instance.organization_id:
             _invalidate_user_org_perm_cache(instance.user_id, instance.organization_id)
        # Always invalidate the user's list of active orgs as their status might have changed
        _invalidate_user_active_org_ids_cache(instance.user_id)

@receiver(post_delete, sender=OrganizationMembership)
def invalidate_on_membership_delete(sender, instance: OrganizationMembership, **kwargs):
    """Invalidate cache when an OrganizationMembership is deleted."""
    if instance.user_id:
        # Invalidate specific perm cache
        if instance.organization_id:
             _invalidate_user_org_perm_cache(instance.user_id, instance.organization_id)
        # Always invalidate the user's list of active orgs
        _invalidate_user_active_org_ids_cache(instance.user_id)

@receiver(m2m_changed, sender=OrganizationMembership.roles.through)
def invalidate_on_membership_roles_change(sender, instance: OrganizationMembership, action: str, pk_set: set, **kwargs):
    """Invalidate cache when roles for a membership change."""
    if action in ['post_add', 'post_remove', 'post_clear']:
        if instance.user_id and instance.organization_id:
            # Invalidate permission cache for this user/org combination
            _invalidate_user_org_perm_cache(instance.user_id, instance.organization_id)

@receiver(m2m_changed, sender=Group.permissions.through)
def invalidate_on_role_permission_change(sender, instance: Group, action: str, pk_set: set, **kwargs):
    """Invalidate cache when permissions for a Role (Group) change."""
    if action in ['post_add', 'post_remove', 'post_clear']:
        # Find all active memberships using this role (Group)
        memberships = OrganizationMembership.objects.filter(
            roles=instance, is_active=True
        ).values_list('user_id', 'organization_id')
        
        # Invalidate cache for each affected user/org combination
        # Optimization: Could use cache.delete_many if supported and keys are known/pattern matched
        for user_pk, org_pk in memberships:
            if user_pk and org_pk:
                _invalidate_user_org_perm_cache(user_pk, org_pk) 