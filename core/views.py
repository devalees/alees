from rest_framework.viewsets import ViewSetMixin
from django.db.models import Q
from core.organization_model import get_organization_model
from rest_framework.exceptions import PermissionDenied, ValidationError # Import exceptions
from django.conf import settings # For permission string construction
from api.v1.base_models.organization.models import Organization, OrganizationMembership # Import Organization and OrganizationMembership
from rest_framework.permissions import IsAuthenticated # Import IsAuthenticated permission
from core.rbac.permissions import has_perm_in_org # Import the REAL function

class OrganizationScopedViewSetMixin(ViewSetMixin):
    """
    A mixin for ViewSets that automatically filters querysets
    to objects belonging to the organizations the user is a member of.
    Also ensures that new objects are created within an organization
    the user has permission to add to.
    """
    permission_classes = [IsAuthenticated] # Base permission

    def get_queryset(self):
        """
        Filter the queryset to only include objects belonging to the user's organizations.
        Handles the special case where the ViewSet's model is OrganizationMembership itself.
        """
        user = self.request.user
        qs = super().get_queryset()

        if not user or not user.is_authenticated:
            return qs.none()

        if user.is_superuser:
            return qs

        # Get IDs of organizations the user is an active member of
        user_org_ids = OrganizationMembership.objects.filter(
            user=user, is_active=True
        ).values_list('organization_id', flat=True)

        if not user_org_ids:
            return qs.none()

        # *** RBAC Integration: Handle OrganizationMembership model specifically ***
        if qs.model == OrganizationMembership:
            # If listing memberships, filter by the organizations the user is in.
            return qs.filter(organization_id__in=user_org_ids)
        elif hasattr(qs.model, 'organization'):
            # For other models, filter by their 'organization' field.
            return qs.filter(organization_id__in=user_org_ids)
        else:
            # Model doesn't seem to be organization-scoped, return original queryset
            # Or potentially raise an error, depending on desired strictness
            # warnings.warn(f"Model {qs.model.__name__} in {self.__class__.__name__} does not have 'organization' field for scoping.")
            return qs # Or qs.none() for stricter scoping

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
        # Ensure the user is also passed if your model uses AuditableModel
        save_kwargs = {'organization': target_organization}
        if hasattr(serializer.Meta.model, 'created_by'): # Simple check for AuditableModel
             save_kwargs['created_by'] = user
             save_kwargs['updated_by'] = user # Usually same on create
        serializer.save(**save_kwargs) 