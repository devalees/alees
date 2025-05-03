from rest_framework.viewsets import ViewSetMixin
from django.db.models import Q
from core.organization_model import get_organization_model
from rest_framework.exceptions import PermissionDenied, ValidationError # Import exceptions
from django.conf import settings # For permission string construction
from api.v1.base_models.organization.models import Organization, OrganizationMembership # Import Organization and OrganizationMembership
from rest_framework.permissions import IsAuthenticated # Import IsAuthenticated permission
from rest_framework import status # Import status for Response
from rest_framework.response import Response # Import Response
from rest_framework.settings import api_settings # Import api_settings
from core.rbac.permissions import has_perm_in_org # Import the REAL function
import logging # Import logging

logger = logging.getLogger(__name__) # Get logger instance

class OrganizationScopedViewSetMixin(ViewSetMixin):
    """
    A mixin for ViewSets that automatically filters querysets
    to objects belonging to the organizations the user is a member of.
    Injects organization-specific permission checks into create operations.

    Assumes:
    - The related model has an 'organization' ForeignKey.
    - The serializer has a writeable 'organization' field (e.g., PrimaryKeyRelatedField).
    - Uses HasModelPermissionInOrg for view/list/object permissions.
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

        # Handle OrganizationMembership model specifically
        if qs.model == OrganizationMembership:
            # If listing memberships, filter by the organizations the user is in.
            # We only show memberships the user is part of, OR if they have broader perms (handled by HasModelPermissionInOrg)
            # The base filtering here ensures we don't leak existence of other orgs.
            # NOTE: The get_queryset override in the test ViewSet might be more specific for *listing*.
            return qs.filter(organization_id__in=user_org_ids)
        elif hasattr(qs.model, 'organization'):
            # For other models, filter by their 'organization' field.
            return qs.filter(organization_id__in=user_org_ids)
        else:
            # Model doesn't seem to be organization-scoped, return original queryset
            # Consider logging a warning here
            logger.warning(f"Model {qs.model.__name__} in {self.__class__.__name__} does not appear to be organization-scoped for get_queryset.")
            return qs

    # Override the main CREATE method to inject permission check
    def create(self, request, *args, **kwargs):
        """
        Handles create requests, validating data and checking organization permissions.
        """
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            logger.warning(f"Serialization validation failed: {e.detail}")
            raise e

        # --- Organization Permission Check --- 
        user = request.user
        validated_data = serializer.validated_data
        target_organization = validated_data.get('organization') # Get the Org instance from validated data

        if not target_organization:
             # Should have been caught by serializer required=True if properly configured
             logger.error(f"Target organization missing in validated_data after validation passed: {validated_data}")
             raise ValidationError({'organization': ['Organization is required.']})

        # Construct the standard Django permission codename
        model_meta = self.get_queryset().model._meta # Use queryset's model
        perm_codename = f'{model_meta.app_label}.add_{model_meta.model_name}'
        
        # <<< Add more detailed logging before the check >>>
        logger.info(f"[CREATE CHECK] User: '{user}', Target Org: {target_organization.pk} ({target_organization.name}), Required Perm: '{perm_codename}'")
        user_roles = user.organization_memberships.filter(organization=target_organization).values_list('role__name', flat=True)
        logger.info(f"[CREATE CHECK] User Roles in Target Org: {list(user_roles)}")
        # <<< End Logging >>>

        permission_granted = True # Assume true initially
        if not settings.DISABLE_PERMISSIONS_CHECK:
            if not user.is_superuser:
                permission_granted = has_perm_in_org(user, perm_codename, target_organization)
                # <<< Add logging for the result >>>
                logger.info(f"[CREATE CHECK] has_perm_in_org result: {permission_granted}")
                # <<< End Logging >>>
                if not permission_granted:
                    logger.warning(f"Permission Denied: User {user} lacks perm '{perm_codename}' in org {target_organization}")
                    # Use standard DRF permission denied exception
                    self.permission_denied(
                        request, message=f"User does not have permission '{perm_codename}' in organization '{target_organization}'."
                    )
        # --- End Permission Check ---

        # If check passes, proceed with perform_create (which just saves by default)
        try:
            self.perform_create(serializer)
        except Exception as e:
            logger.error(f"Error during perform_create: {e}", exc_info=True)
            raise # Re-raise the exception after logging
            
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    # Keep perform_create simple - just adds audit fields if needed
    def perform_create(self, serializer):
        """
        Save the instance, adding audit fields if necessary.
        Permission checks are done in the overridden create method.
        """
        save_kwargs = {}
        if hasattr(serializer.Meta.model, 'created_by'):
             user = self.request.user if self.request and hasattr(self.request, 'user') else None
             if user and user.is_authenticated:
                 save_kwargs['created_by'] = user
                 save_kwargs['updated_by'] = user
             else: # Handle anonymous or non-request context if applicable
                 logger.warning(f"Cannot set audit fields for {serializer.Meta.model.__name__} - no authenticated user found.")
        
        # Log validated data state *before* attempting save
        logger.info(f"[perform_create] Validated data before save: {serializer.validated_data}")
        logger.info(f"[perform_create] About to call serializer.save() for {serializer.Meta.model.__name__} with kwargs: {save_kwargs}")
        # Add audit fields before saving
        try:
            instance = serializer.save(**save_kwargs)
            logger.debug(f"Successfully saved instance via perform_create: {instance}")
        except Exception as e:
            logger.error(f"Error during serializer.save in perform_create: {e}", exc_info=True)
            raise

    # Copied from CreateModelMixin for header generation
    def get_success_headers(self, data):
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {} 