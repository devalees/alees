""" Core serializer mixins. """

import logging
from rest_framework import serializers
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.translation import gettext_lazy as _

# Import the RBAC helper
from core.rbac.utils import get_user_request_context

logger = logging.getLogger(__name__)

class OrganizationScopedSerializerMixin(serializers.Serializer):
    """
    Mixin for serializers handling models scoped to an Organization.

    Handles automatic validation and setting of the 'organization' field
    based on the user's context (single vs. multi-organization).

    Assumes the user context is available via `self.context['request'].user`.
    Assumes the underlying model has an 'organization' foreign key.
    Adds an 'organization' field to the serializer if not already present.
    
    Note: Superusers bypass organization validation checks.
    """

    # Define the organization field - can be overridden by subclasses if needed
    # Making it read_only=True simplifies things as validation/create handles logic.
    organization = serializers.PrimaryKeyRelatedField(
        # queryset=None, # Not needed if read_only=True
        read_only=True,
        # required=False, # Not relevant for read_only
        # allow_null=True, # Not relevant for read_only
        help_text=_("The organization this resource belongs to.")
    )

    def validate(self, attrs):
        """
        Validates user context and sets internal org ID for single-org users on create.
        Does NOT validate organization input (field is read-only in mixin).
        Inheriting serializers MUST handle input validation if they make the field writable.
        
        Superusers bypass organization validation checks.
        """
        attrs = super().validate(attrs)
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            raise PermissionDenied(_("User context not found in serializer."))

        user = request.user
        
        # Superusers bypass organization validation
        if user.is_superuser:
            logger.debug("Superuser bypassing organization validation in serializer")
            # Still remove the read-only field from attrs if present
            attrs.pop('organization', None)
            return attrs
            
        is_update = self.instance is not None

        active_org_ids, is_single_org = get_user_request_context(user)

        if not active_org_ids:
            raise PermissionDenied(_("You do not belong to any active organizations."))

        if not is_update:
            # --- Handle Create: Determine target org ID for single-org only --- #
            if is_single_org:
                 # Store the automatically determined org_id for create method
                 self._validated_organization_id = active_org_ids[0]
            # else: # Multi-org user: Mixin does nothing, subclass must handle.
            #     pass

        # else: # is_update: No validation needed for read_only field
        #     pass

        # Remove the read-only field from attrs if present (it shouldn't be)
        attrs.pop('organization', None)
        return attrs

    def create(self, validated_data):
        """
        Sets the organization automatically for single-org users before saving.
        Ensures organization_id is present in validated_data.
        Actual object creation is deferred to the inheriting class or super().create().
        
        Superusers can create resources in any organization.
        """
        request = self.context.get('request')
        user = request.user if request and hasattr(request, 'user') else None
        
        # Special handling for superusers
        if user and user.is_superuser:
            # Superusers can explicitly set organization_id if provided in validated_data
            # or it will be handled by the model's default behavior
            logger.debug("Superuser creating resource: %s", validated_data)
            # Remove the potentially passed 'organization' attribute if it exists
            validated_data.pop('organization', None)
            return None  # Let inheriting serializer handle actual creation
        
        # Retrieve the validated/determined org ID from the validate method
        org_id = getattr(self, '_validated_organization_id', None)

        if org_id:
            validated_data['organization_id'] = org_id
        elif not self.instance: # Check if it's a create operation explicitly
             # This case should ideally be prevented by the validate method, but raise error defensively.
             logger.error("Organization ID missing in create method for OrganizationScopedSerializerMixin.")
             raise ValidationError(_("Cannot create resource without a valid organization context."))

        # Remove the potentially passed 'organization' attribute if it exists,
        # as we are using organization_id directly
        validated_data.pop('organization', None)

        # The actual object creation should happen in the inheriting serializer's create
        # or by calling super().create() if this mixin inherits from ModelSerializer
        logger.debug("OrganizationScopedSerializerMixin processed validated_data: %s", validated_data)
        # We don't call super().create() or create an object here.
        # We just ensure validated_data is ready for the inheriting class.
        # Remove the dummy return
        # return MockOrganizationScopedModel(**validated_data)

    # Add get_fields to dynamically set queryset if needed (e.g., for browsable API)
    # Or adjust the 'organization' field definition based on specific needs. 