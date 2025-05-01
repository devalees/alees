import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from api.v1.base_models.contact.models import Contact
from api.v1.base_models.contact.tests.factories import (
    ContactFactory, ContactEmailAddressFactory,
    ContactPhoneNumberFactory, ContactAddressFactory
)
from api.v1.base_models.contact.choices import ContactType, ContactStatus, ContactSource, EmailType, PhoneType, AddressType
from api.v1.base_models.common.address.tests.factories import AddressFactory

User = get_user_model()

@pytest.mark.django_db
class TestContactViewSet:
    """Test cases for the Contact API ViewSet."""

    @pytest.fixture
    def user(self):
        """Create a test user."""
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def setup_method(self, method):
        """Set up test client and base URL."""
        self.client = APIClient()
        self.url = reverse('v1:contact:contact-list')
        # Create and authenticate a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_list_contacts(self):
        """Test listing contacts."""
        # Create test contacts with related data
        contact = ContactFactory()
        email = ContactEmailAddressFactory(contact=contact, is_primary=True)
        phone = ContactPhoneNumberFactory(contact=contact, is_primary=True)
        address = ContactAddressFactory(contact=contact, is_primary=True)
        contact.tags.add('important')

        # Create additional contacts without related data
        ContactFactory.create_batch(2)

        # Make request
        response = self.client.get(self.url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3
        
        # Find the contact with related data in the response
        contact_data = next(
            c for c in response.data['results']
            if c['id'] == contact.id
        )
        
        # Check related data
        assert len(contact_data['email_addresses']) == 1
        assert contact_data['email_addresses'][0]['id'] == email.id
        assert len(contact_data['phone_numbers']) == 1
        assert contact_data['phone_numbers'][0]['id'] == phone.id
        assert len(contact_data['addresses']) == 1
        assert contact_data['addresses'][0]['id'] == address.id
        assert len(contact_data['tags']) == 1
        assert 'important' in contact_data['tags']

    def test_create_contact(self):
        """Test creating a new contact."""
        # Create an address first
        address = AddressFactory()
        
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'title': 'Manager',
            'organization_name': 'Test Corp',
            'contact_type': ContactType.PRIMARY,
            'status': ContactStatus.ACTIVE,
            'source': ContactSource.WEBSITE,
            'tags': ['important', 'customer'],
            'email_addresses': [{
                'email': 'john@example.com',
                'email_type': EmailType.WORK,
                'is_primary': True
            }],
            'phone_numbers': [{
                'phone_number': '+1234567890',
                'phone_type': PhoneType.MOBILE,
                'is_primary': True
            }],
            'addresses': [{
                'address': address.id,
                'address_type': AddressType.WORK,
                'is_primary': True
            }],
            'custom_fields': {},
            'notes': 'Test contact'
        }

        response = self.client.post(self.url, data, format='json')
        
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response data: {response.data}")
        
        assert response.status_code == status.HTTP_201_CREATED
        
        contact = Contact.objects.get(id=response.data['id'])
        assert contact.first_name == data['first_name']
        assert contact.last_name == data['last_name']
        assert contact.email_addresses.count() == 1
        assert contact.phone_numbers.count() == 1
        assert contact.addresses.count() == 1
        assert set(contact.tags.names()) == set(data['tags'])

    def test_retrieve_contact(self):
        """Test retrieving a single contact."""
        contact = ContactFactory()
        ContactEmailAddressFactory(contact=contact)
        ContactPhoneNumberFactory(contact=contact)
        ContactAddressFactory(contact=contact)
        contact.tags.add('important')

        url = reverse('v1:contact:contact-detail', args=[contact.id])
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == contact.id
        assert response.data['first_name'] == contact.first_name
        assert len(response.data['email_addresses']) == 1
        assert len(response.data['phone_numbers']) == 1
        assert len(response.data['addresses']) == 1
        assert len(response.data['tags']) == 1

    def test_update_contact(self):
        """Test updating a contact."""
        contact = ContactFactory()
        url = reverse('v1:contact:contact-detail', args=[contact.id])
        
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'title': 'New Title',
            'tags': ['updated']
        }

        response = self.client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        contact.refresh_from_db()
        assert contact.first_name == data['first_name']
        assert contact.last_name == data['last_name']
        assert contact.title == data['title']
        assert list(contact.tags.names()) == data['tags']

    def test_delete_contact(self):
        """Test deleting a contact."""
        contact = ContactFactory()
        url = reverse('v1:contact:contact-detail', args=[contact.id])

        response = self.client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Contact.objects.filter(id=contact.id).exists()

    def test_filter_contacts(self):
        """Test filtering contacts."""
        ContactFactory(first_name='John', last_name='Doe')
        ContactFactory(first_name='Jane', last_name='Smith')
        
        # Test name filter
        response = self.client.get(f"{self.url}?search=John")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['first_name'] == 'John'

        # Test status filter
        response = self.client.get(f"{self.url}?status={ContactStatus.ACTIVE}")
        assert response.status_code == status.HTTP_200_OK
        assert all(c['status'] == ContactStatus.ACTIVE for c in response.data['results'])

    def test_ordering_contacts(self):
        """Test ordering contacts."""
        ContactFactory(first_name='Alice')
        ContactFactory(first_name='Bob')
        ContactFactory(first_name='Charlie')

        # Test ordering by first_name
        response = self.client.get(f"{self.url}?ordering=first_name")
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert results[0]['first_name'] == 'Alice'
        assert results[1]['first_name'] == 'Bob'
        assert results[2]['first_name'] == 'Charlie'

        # Test reverse ordering
        response = self.client.get(f"{self.url}?ordering=-first_name")
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert results[0]['first_name'] == 'Charlie'
        assert results[1]['first_name'] == 'Bob'
        assert results[2]['first_name'] == 'Alice' 