""" Core ViewSet mixins. """

import logging
from django.core.exceptions import ImproperlyConfigured

# Import the RBAC helper
from core.rbac.utils import get_user_request_context

logger = logging.getLogger(__name__)


class OrganizationScopedViewSetMixin:
    """
    Mixin for ViewSets to automatically filter querysets based on user's organization.

    Assumes the model managed by the ViewSet has an 'organization' foreign key.
    Filters the queryset to only include objects belonging to the organizations
    the requesting user is an active member of.
    Superusers bypass this filter and see all objects.
    Requires the request object to be available on the view via `self.request`.
    """

    # Specify the lookup field on the model that points to the Organization.
    # Defaults to 'organization'. Subclasses can override this.
    organization_field_lookup = 'organization'

    def get_queryset(self):
        """
        Overrides the default queryset to filter by the user's accessible organizations.
        """
        # Get the original queryset from the parent class (e.g., ModelViewSet)
        queryset = super().get_queryset()

        # Check if the request and user are available
        if not hasattr(self, 'request') or not hasattr(self.request, 'user'):
            # This shouldn't happen in a standard DRF view lifecycle, but safeguard anyway.
            logger.warning("Request or user not found on view. Cannot apply organization scope.")
            # Return empty queryset or raise error, depending on desired strictness.
            # Returning empty is safer for list views.
            return queryset.none()

        user = self.request.user

        # Superusers see everything
        if user.is_authenticated and user.is_superuser:
            logger.debug("Superuser access: returning unfiltered queryset.")
            return queryset

        # Anonymous users or users without specific org context might see nothing,
        # depending on how get_user_request_context handles them.
        if not user.is_authenticated:
             logger.debug("Anonymous user: returning empty queryset based on auth.")
             # Generally, permissions handle this, but filtering adds a layer.
             return queryset.none()

        # Get the organization IDs the user has access to
        try:
            active_org_ids, _ = get_user_request_context(user)
        except Exception as e:
            # Handle potential errors from the helper (e.g., DB issues)
            logger.error(f"Error getting user org context for {user}: {e}", exc_info=True)
            return queryset.none() # Return empty on error

        if not active_org_ids:
            logger.debug(f"User {user} has no active organization memberships. Returning empty queryset.")
            return queryset.none()

        # Check if the model actually has the specified organization field
        model = queryset.model
        if not hasattr(model, self.organization_field_lookup):
             raise ImproperlyConfigured(
                 f"{self.__class__.__name__} is configured with organization_field_lookup='{self.organization_field_lookup}', "
                 f"but the model {model.__name__} does not have this field."
             )

        # Filter the queryset
        filter_kwargs = {f"{self.organization_field_lookup}_id__in": active_org_ids}
        logger.debug(f"Applying organization filter for user {user}: {filter_kwargs}")
        return queryset.filter(**filter_kwargs)

# Placeholder for OrganizationScopedViewSetMixin 