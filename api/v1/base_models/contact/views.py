from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from api.v1.base_models.contact.models import (
    Contact, ContactEmailAddress, ContactPhoneNumber, ContactAddress
)
from api.v1.base_models.contact.serializers import (
    ContactSerializer, ContactEmailAddressSerializer,
    ContactPhoneNumberSerializer, ContactAddressSerializer
)
from api.v1.base_models.contact.filters import ContactFilter


class ContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing contacts.
    
    Supports:
    - List/Create/Retrieve/Update/Delete operations
    - Filtering by status, contact_type, source
    - Search by first_name, last_name, organization_name
    - Ordering by multiple fields
    - Nested channel operations (email, phone, address)
    """
    permission_classes = [permissions.IsAuthenticated]
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

    def get_queryset(self):
        """Override to add custom filtering based on user permissions."""
        queryset = super().get_queryset()
        # Add any custom filtering based on user permissions here
        return queryset

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

    def perform_create(self, serializer):
        """Override to handle any post-create operations."""
        instance = serializer.save()
        # Add any post-create operations here
        return instance

    def perform_update(self, serializer):
        """Override to handle any post-update operations."""
        instance = serializer.save()
        # Add any post-update operations here
        return instance

    def perform_destroy(self, instance):
        """Override to handle any pre-delete operations."""
        # Add any pre-delete operations here
        super().perform_destroy(instance)


class ContactEmailAddressViewSet(viewsets.ModelViewSet):
    """ViewSet for ContactEmailAddress model."""
    permission_classes = [permissions.IsAuthenticated]
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
    permission_classes = [permissions.IsAuthenticated]
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
    permission_classes = [permissions.IsAuthenticated]
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
