from rest_framework import viewsets, filters, permissions
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
    """
    permission_classes = [permissions.IsAuthenticated]
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
    filterset_fields = ['status', 'contact_type', 'source']
    search_fields = ['first_name', 'last_name', 'organization_name']
    ordering_fields = [
        'first_name', 'last_name', 'organization_name',
        'created_at', 'updated_at'
    ]
    ordering = ['-created_at']  # Default ordering


class ContactEmailAddressViewSet(viewsets.ModelViewSet):
    """ViewSet for ContactEmailAddress model."""
    queryset = ContactEmailAddress.objects.all()
    serializer_class = ContactEmailAddressSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['contact', 'email_type', 'is_primary']


class ContactPhoneNumberViewSet(viewsets.ModelViewSet):
    """ViewSet for ContactPhoneNumber model."""
    queryset = ContactPhoneNumber.objects.all()
    serializer_class = ContactPhoneNumberSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['contact', 'phone_type', 'is_primary']


class ContactAddressViewSet(viewsets.ModelViewSet):
    """ViewSet for ContactAddress model."""
    queryset = ContactAddress.objects.all()
    serializer_class = ContactAddressSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['contact', 'address_type', 'is_primary']
