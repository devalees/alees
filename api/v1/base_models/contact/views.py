from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
import logging

# Import Mixin and RBAC Permission
from core.viewsets.mixins import OrganizationScopedViewSetMixin 
from core.rbac.drf_permissions import HasModelPermissionInOrg

from api.v1.base_models.contact.models import (
    Contact, ContactEmailAddress, ContactPhoneNumber, ContactAddress
)
from api.v1.base_models.contact.serializers import (
    ContactSerializer, ContactEmailAddressSerializer,
    ContactPhoneNumberSerializer, ContactAddressSerializer
)
from api.v1.base_models.contact.filters import ContactFilter

logger = logging.getLogger(__name__)

# Add OrganizationScopedViewSetMixin inheritance
class ContactViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing contacts.
    Automatically scoped by Organization.
    
    Supports:
    - List/Create/Retrieve/Update/Delete operations
    - Filtering by status, contact_type, source
    - Search by first_name, last_name, organization_name
    - Ordering by multiple fields
    - Nested channel operations (email, phone, address)
    
    Permission handling:
    - Superusers bypass all permission checks (handled by HasModelPermissionInOrg)
    - Regular users need appropriate permissions in the target organization
    """
    # Apply Org Scoping and RBAC permissions
    permission_classes = [HasModelPermissionInOrg]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head']
    queryset = Contact.objects.prefetch_related(
        'email_addresses',
        'phone_numbers',
        'addresses',
        'tags'
    ).all()
    serializer_class = ContactSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_class = ContactFilter
    search_fields = ['first_name', 'last_name', 'organization_name']
    ordering_fields = [
        'first_name', 'last_name', 'organization_name',
        'created_at', 'updated_at'
    ]
    ordering = ['-created_at']  # Default ordering

    def perform_create(self, serializer):
        """
        Ensure user and organization context are correctly set when creating.
        Additional permission checks for creating contacts in organizations.
        Also ensure organization_id is correctly processed for all users.
        """
        user = self.request.user
        logger.info(f"Creating contact by user: {user.username}, superuser: {user.is_superuser}")
        
        # Get organization_id from request data
        organization_id = self.request.data.get('organization_id')
        
        # If superuser, use the specified organization_id directly
        if user.is_superuser:
            if organization_id:
                from api.v1.base_models.organization.models import Organization
                try:
                    organization = Organization.objects.get(pk=organization_id)
                    # Set the organization in the serializer data
                    serializer.save(created_by=user, updated_by=user, organization=organization)
                    return
                except Organization.DoesNotExist:
                    from rest_framework.exceptions import ValidationError
                    raise ValidationError({"organization_id": f"Organization with id {organization_id} does not exist."})
        
        # For regular users, check permissions for the specified organization
        if not user.is_superuser and organization_id:
            # Check if organization ID is valid and if user has permission
            from core.rbac.utils import get_user_request_context
            from core.rbac.permissions import has_perm_in_org
            from rest_framework.exceptions import PermissionDenied
            
            # Get user's active organizations
            active_org_ids, _ = get_user_request_context(user)
            
            # Convert organization_id to integer if it's a string
            try:
                org_id = int(organization_id)
            except (ValueError, TypeError):
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"organization_id": "Invalid organization ID format"})
            
            # Check if targeted organization is in user's active orgs
            if org_id not in active_org_ids:
                # Trying to create in an org the user is not a member of
                raise PermissionDenied(
                    f"You cannot create contacts in organization {org_id} as you are not a member."
                )
            
            # Check if user has the appropriate permission in the organization
            if not has_perm_in_org(user, "add_contact", org_id):
                raise PermissionDenied(
                    f"You don't have permission to create contacts in organization {org_id}."
                )
            
            # Get the organization object
            from api.v1.base_models.organization.models import Organization
            try:
                organization = Organization.objects.get(pk=org_id)
                # Set the organization in the serializer data
                serializer.save(created_by=user, updated_by=user, organization=organization)
                return
            except Organization.DoesNotExist:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"organization_id": f"Organization with id {org_id} does not exist."})
        
        # If we get here, use the default logic
        serializer.save(created_by=user, updated_by=user)

    def perform_update(self, serializer):
        """
        Ensure user context is correctly set when updating.
        Permission checks should be handled by HasModelPermissionInOrg.
        """
        user = self.request.user
        logger.info(f"Updating contact by user: {user.username}, superuser: {user.is_superuser}")
        
        # Update the user who last modified the contact
        serializer.save(updated_by=user)

    def get_serializer_context(self):
        """
        Add additional context for serializers.
        Ensures the serializer has access to the request and user.
        """
        context = super().get_serializer_context()
        return context

    @action(detail=True, methods=['get'])
    def channels(self, request, pk=None):
        """Get all communication channels for a contact."""
        contact = self.get_object()
        data = {
            'email_addresses': ContactEmailAddressSerializer(
                contact.email_addresses.all(), many=True
            ).data,
            'phone_numbers': ContactPhoneNumberSerializer(
                contact.phone_numbers.all(), many=True
            ).data,
            'addresses': ContactAddressSerializer(
                contact.addresses.all(), many=True
            ).data
        }
        return Response(data)

    # Explicitly define partial_update to ensure the base DRF logic is called
    # This seemed necessary to make ContactSerializer.update get called correctly.
    def partial_update(self, request, *args, **kwargs):
        # logger.info(f"[ContactViewSet.partial_update ENTRY] Request data: {request.data}")
        response = super().partial_update(request, *args, **kwargs)
        # logger.info(f"[ContactViewSet.partial_update EXIT] Response status: {response.status_code}, Response data: {response.data}")
        return response

    def perform_destroy(self, instance):
        """Override to handle any pre-delete operations."""
        # Add any pre-delete operations here
        super().perform_destroy(instance)


class ContactEmailAddressViewSet(viewsets.ModelViewSet):
    """ViewSet for ContactEmailAddress model."""
    permission_classes = [HasModelPermissionInOrg]
    queryset = ContactEmailAddress.objects.all()
    serializer_class = ContactEmailAddressSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['contact', 'email_type', 'is_primary']

    def perform_create(self, serializer):
        """Handle primary flag logic on create."""
        instance = serializer.save()
        if instance.is_primary:
            ContactEmailAddress.objects.filter(
                contact=instance.contact
            ).exclude(id=instance.id).update(is_primary=False)


class ContactPhoneNumberViewSet(viewsets.ModelViewSet):
    """ViewSet for ContactPhoneNumber model."""
    permission_classes = [HasModelPermissionInOrg]
    queryset = ContactPhoneNumber.objects.all()
    serializer_class = ContactPhoneNumberSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['contact', 'phone_type', 'is_primary']

    def perform_create(self, serializer):
        """Handle primary flag logic on create."""
        instance = serializer.save()
        if instance.is_primary:
            ContactPhoneNumber.objects.filter(
                contact=instance.contact
            ).exclude(id=instance.id).update(is_primary=False)


class ContactAddressViewSet(viewsets.ModelViewSet):
    """ViewSet for ContactAddress model."""
    permission_classes = [HasModelPermissionInOrg]
    queryset = ContactAddress.objects.all()
    serializer_class = ContactAddressSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['contact', 'address_type', 'is_primary']

    def perform_create(self, serializer):
        """Handle primary flag logic on create."""
        instance = serializer.save()
        if instance.is_primary:
            ContactAddress.objects.filter(
                contact=instance.contact
            ).exclude(id=instance.id).update(is_primary=False)
