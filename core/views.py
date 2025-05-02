from rest_framework.viewsets import ViewSetMixin
from django.db.models import Q
from core.organization_model import get_organization_model
from rest_framework.exceptions import PermissionDenied, ValidationError # Import exceptions
from django.conf import settings # For permission string construction
from api.v1.base_models.organization.models import Organization # Import Organization

class OrganizationScopedViewSetMixin(ViewSetMixin):
    """
    Mixin for ViewSets to automatically filter querysets by the user's organizations.
    Superusers see all records, regular users only see records from their organizations.
    """
    def get_queryset(self):
        """
        Filter the queryset based on the user's organization memberships.
        - Superusers see all records
        - Regular users only see records from organizations they are members of
        - Users with no organization memberships see no records
        """
        queryset = super().get_queryset()
        user = self.request.user

        # Superusers see everything
        if user.is_superuser:
            return queryset

        # Get the user's organizations using the method on the User model
        user_organizations = user.get_organizations()

        # If user has no organizations, return empty queryset
        if not user_organizations.exists():
            return queryset.none()

        # Filter queryset to only include records from user's organizations
        return queryset.filter(organization__in=user_organizations)

    def perform_create(self, serializer):
        """
        Handles creation, ensuring the user has permission in the target organization.
        The 'organization' must be provided in serializer.validated_data.
        """
        user = self.request.user
        validated_data = serializer.validated_data

        # 1. Get target organization from validated data
        target_organization = validated_data.get('organization')
        if not target_organization:
            # This case should ideally be caught by serializer validation if 'organization' is required
            raise ValidationError({'organization': ['This field is required for organization-scoped creation.']})

        # Handle case where validated_data gives PK, need instance (shouldn't happen with PrimaryKeyRelatedField default)
        if isinstance(target_organization, int):
             try:
                 target_organization = Organization.objects.get(pk=target_organization)
             except Organization.DoesNotExist:
                 raise ValidationError({'organization': [f'Invalid organization PK: {target_organization}.']})

        # 2. Check permission (using placeholder RBAC function)
        # Construct the standard Django permission codename
        model_meta = serializer.Meta.model._meta
        perm_codename = f'{model_meta.app_label}.add_{model_meta.model_name}'
        
        if not settings.DISABLE_PERMISSIONS_CHECK: # Optional: Add a setting to disable checks easily
            if not user.is_superuser and not has_perm_in_org(user, perm_codename, target_organization):
                raise PermissionDenied(f"User does not have permission '{perm_codename}' in organization '{target_organization}'.")

        # 3. Save with the validated organization
        # Important: Pass organization explicitly to save()
        serializer.save(organization=target_organization)

# Placeholder RBAC function (to be mocked in tests)
def has_perm_in_org(user, perm_codename, organization):
    """Placeholder: Checks if a user has a specific permission in an organization."""
    # In real implementation, this would check actual roles/permissions.
    # For now, it's just a target for mocking.
    print(f"[Placeholder RBAC] Checking if {user} has '{perm_codename}' in {organization}")
    return False # Default to False for safety until implemented/mocked 