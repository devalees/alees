from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework import serializers
from django_otp.plugins.otp_totp.models import TOTPDevice
from django.core.cache import cache, caches # Import cache
from django.conf import settings # Import settings
from django.apps import apps # Import apps
import logging # Import logging

logger = logging.getLogger(__name__)
permission_cache = caches['rbac']
CACHE_TIMEOUT = settings.RBAC_CACHE_TIMEOUT if hasattr(settings, 'RBAC_CACHE_TIMEOUT') else 3600

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer for obtaining JWT token pair.
    Extends the default to populate RBAC cache on successful login.
    """

    # Override validate or get_token. get_token is called after validation.
    def validate(self, attrs):
        # First, call the parent's validate method to perform standard auth checks
        data = super().validate(attrs)

        # If authentication was successful, self.user will be set.
        # Now, populate the RBAC cache.
        user = self.user
        if user and user.is_authenticated:
            logger.info(f"Populating RBAC cache for user {user.pk} on login.")
            try:
                # 1. Cache Active Organization IDs
                if not hasattr(user, 'get_organizations'):
                    logger.error(f"User model missing 'get_organizations' method. Cannot populate RBAC cache.")
                else:
                    active_orgs = user.get_organizations() # Assumes this filters for active
                    active_org_ids = list(active_orgs.values_list('pk', flat=True))
                    org_ids_cache_key = f'user:{user.pk}:active_org_ids'
                    cache.set(org_ids_cache_key, active_org_ids, timeout=CACHE_TIMEOUT)
                    logger.info(f"Cached active_org_ids for user {user.pk}: {active_org_ids}")

                    # 2. Pre-warm Permission Cache per Active Organization
                    OrganizationMembership = apps.get_model('api_v1_organization', 'OrganizationMembership')
                    memberships = OrganizationMembership.objects.filter(
                        user=user,
                        organization_id__in=active_org_ids, # Only fetch for active orgs
                        is_active=True # Explicitly ensure membership is active
                    ).prefetch_related('roles', 'roles__permissions')

                    for membership in memberships:
                        org_id = membership.organization_id
                        perms_set = set()
                        # Get permissions from all roles assigned to this membership
                        for role in membership.roles.all():
                            perms_set.update(role.permissions.values_list('codename', flat=True))
                            
                        perm_cache_key = f'rbac:perms:user:{user.pk}:org:{org_id}'
                        permission_cache.set(perm_cache_key, perms_set, timeout=CACHE_TIMEOUT)
                        logger.info(f"Cached permissions for user {user.pk}, org {org_id}: {perms_set}")

            except Exception as e:
                # Log error but don't prevent login if caching fails
                logger.error(f"Failed to populate RBAC cache for user {user.pk} during login: {e}", exc_info=True)

        return data # Return the original token data

class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Custom serializer for refreshing JWT token.
    Extends the default TokenRefreshSerializer to allow for future customization.
    """
    pass

class TOTPVerifySerializer(serializers.Serializer):
    token = serializers.CharField(min_length=6, max_length=6)

    def validate(self, attrs):
        request = self.context['request']
        try:
            device = TOTPDevice.objects.get(user=request.user, confirmed=False)
        except TOTPDevice.DoesNotExist:
            raise serializers.ValidationError("No unconfirmed TOTP device found.")
        
        if not device.verify_token(attrs['token']):
            raise serializers.ValidationError("Invalid token.")
        
        attrs['device'] = device
        return attrs

class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change endpoint."""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Invalid old password')
        return value

    def validate_new_password(self, value):
        # Add any password validation rules here if needed
        if len(value) < 8:
            raise serializers.ValidationError('Password must be at least 8 characters long')
        return value
