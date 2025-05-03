from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.cache import caches
from django.conf import settings
from django.contrib.auth.models import Group

from api.v1.base_models.organization.models import OrganizationMembership

# Use the consistent 'rbac' cache alias
permission_cache = caches['rbac']

def _invalidate_user_org_perm_cache(user_pk, org_pk):
    """Helper function to invalidate the cache for a specific user/org."""
    cache_key = f'rbac:perms:user:{user_pk}:org:{org_pk}'
    permission_cache.delete(cache_key)
    # print(f"DEBUG: Invalidated RBAC cache for user {user_pk}, org {org_pk}") # For debugging

@receiver(post_save, sender=OrganizationMembership)
def invalidate_on_membership_save(sender, instance: OrganizationMembership, **kwargs):
    """Invalidate cache when an OrganizationMembership is saved (role or active status changes)."""
    if instance.user_id and instance.organization_id:
        _invalidate_user_org_perm_cache(instance.user_id, instance.organization_id)

@receiver(post_delete, sender=OrganizationMembership)
def invalidate_on_membership_delete(sender, instance: OrganizationMembership, **kwargs):
    """Invalidate cache when an OrganizationMembership is deleted."""
    if instance.user_id and instance.organization_id:
        _invalidate_user_org_perm_cache(instance.user_id, instance.organization_id)

@receiver(m2m_changed, sender=Group.permissions.through)
def invalidate_on_role_permission_change(sender, instance: Group, action: str, pk_set: set, **kwargs):
    """Invalidate cache when permissions for a Role (Group) change."""
    if action in ['post_add', 'post_remove', 'post_clear']:
        # Find all active memberships using this role (Group)
        memberships = OrganizationMembership.objects.filter(
            role=instance, is_active=True
        ).values_list('user_id', 'organization_id')
        
        # Invalidate cache for each affected user/org combination
        # Optimization: Could use cache.delete_many if supported and keys are known/pattern matched
        for user_pk, org_pk in memberships:
            if user_pk and org_pk:
                _invalidate_user_org_perm_cache(user_pk, org_pk) 