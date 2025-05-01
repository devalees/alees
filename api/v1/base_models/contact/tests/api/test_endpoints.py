import pytest
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from api.v1.base_models.contact.models import Contact, ContactEmailAddress, ContactPhoneNumber, ContactAddress
from api.v1.base_models.contact.tests.factories import (
    ContactFactory,
    ContactEmailAddressFactory,
    ContactPhoneNumberFactory,
    ContactAddressFactory
)

User = get_user_model()

@pytest.mark.django_db
class TestContactAPI:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse('v1:base_models:contact:contact-list')

    def test_create_contact_with_channels(self):
        """Test creating a contact with nested channel data"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email_addresses': [
                {
                    'email': 'john@example.com',
                    'is_primary': True,
                    'email_type': 'work'
                }
            ],
            'phone_numbers': [
                {
                    'phone_number': '+1234567890',
                    'is_primary': True,
                    'phone_type': 'mobile'
                }
            ],
            'addresses': [
                {
                    'address': {
                        'street_address_1': '123 Main St',
                        'city': 'New York',
                        'state_province': 'NY',
                        'postal_code': '10001',
                        'country': {'code': 'US', 'name': 'United States'}
                    },
                    'is_primary': True,
                    'address_type': 'work'
                }
            ]
        }

        response = self.client.post(self.url, data, format='json')
        if response.status_code != status.HTTP_201_CREATED:
            print("Response data:", response.data)  # Print response data on failure
        assert response.status_code == status.HTTP_201_CREATED
        assert Contact.objects.count() == 1
        assert ContactEmailAddress.objects.count() == 1
        assert ContactPhoneNumber.objects.count() == 1
        assert ContactAddress.objects.count() == 1

    def test_update_contact_primary_flags(self):
        """Test updating primary flags for contact channels"""
        contact = ContactFactory()
        email1 = ContactEmailAddressFactory(contact=contact, is_primary=True)
        email2 = ContactEmailAddressFactory(contact=contact, is_primary=False)

        data = {
            'email_addresses': [
                {
                    'id': email1.id,
                    'email': email1.email,
                    'is_primary': False,
                    'email_type': email1.email_type
                },
                {
                    'id': email2.id,
                    'email': email2.email,
                    'is_primary': True,
                    'email_type': email2.email_type
                }
            ]
        }

        response = self.client.patch(
            reverse('v1:base_models:contact:contact-detail', kwargs={'pk': contact.id}),
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        email1.refresh_from_db()
        email2.refresh_from_db()
        assert not email1.is_primary
        assert email2.is_primary

    def test_list_contacts_with_filtering(self):
        """Test listing contacts with various filters"""
        ContactFactory(first_name='John', last_name='Doe')
        ContactFactory(first_name='Jane', last_name='Smith')

        # Test name filter
        response = self.client.get(f'{self.url}?first_name=John')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['first_name'] == 'John'

    def test_contact_organization_link(self):
        """Test setting and unsetting organization link"""
        contact = ContactFactory()
        data = {
            'linked_organization_id': 1  # This will be validated in the serializer
        }

        response = self.client.patch(
            reverse('v1:base_models:contact:contact-detail', kwargs={'pk': contact.id}),
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK

        # Test unsetting
        data = {'linked_organization_id': None}
        response = self.client.patch(
            reverse('v1:base_models:contact:contact-detail', kwargs={'pk': contact.id}),
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK

    def test_contact_validation_errors(self):
        """Test various validation errors"""
        # Test invalid email
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email_addresses': [
                {
                    'email': 'invalid-email',
                    'is_primary': True,
                    'email_type': 'work'
                }
            ]
        }
        response = self.client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data['email_addresses'][0]

    def test_contact_permissions(self):
        """Test API permissions"""
        # Test unauthenticated access
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_contact_custom_fields_and_tags(self):
        """Test custom fields and tags functionality"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'tags': ['important', 'client'],
            'custom_fields': {
                'department': 'Sales',
                'position': 'Manager'
            }
        }

        response = self.client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        contact = Contact.objects.get(id=response.data['id'])
        assert set(contact.tags.names()) == {'important', 'client'}
        assert contact.custom_fields == {'department': 'Sales', 'position': 'Manager'} 