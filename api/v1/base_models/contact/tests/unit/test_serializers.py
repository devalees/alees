import pytest
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from taggit.models import Tag

from api.v1.base_models.contact.serializers import (
    ContactEmailAddressSerializer,
    ContactPhoneNumberSerializer,
    ContactAddressSerializer,
    ContactSerializer
)
from api.v1.base_models.contact.models import (
    Contact, ContactEmailAddress, ContactPhoneNumber, ContactAddress
)
from api.v1.base_models.contact.choices import (
    ContactType, ContactStatus, ContactSource,
    EmailType, PhoneType, AddressType
)
from api.v1.base_models.contact.tests.factories import (
    ContactFactory, ContactEmailAddressFactory,
    ContactPhoneNumberFactory, ContactAddressFactory
)
from api.v1.base_models.common.address.tests.factories import AddressFactory

User = get_user_model()

@pytest.mark.django_db
class TestContactEmailAddressSerializer:
    """Test cases for ContactEmailAddressSerializer."""

    def test_serialization(self):
        """Test serialization of email address."""
        email = ContactEmailAddressFactory()
        serializer = ContactEmailAddressSerializer(email)
        data = serializer.data
        
        assert data['id'] == email.id
        assert data['email'] == email.email
        assert data['email_type'] == email.email_type
        assert data['is_primary'] == email.is_primary

    def test_deserialization(self):
        """Test deserializing email address data."""
        contact = ContactFactory()
        data = {
            'email': 'test@example.com',
            'email_type': EmailType.WORK,
            'is_primary': True
        }
        serializer = ContactEmailAddressSerializer(data=data)
        assert serializer.is_valid()
        email = serializer.save(contact=contact)
        assert email.email == data['email']
        assert email.email_type == data['email_type']
        assert email.is_primary == data['is_primary']

    def test_validation(self):
        """Test email validation."""
        serializer = ContactEmailAddressSerializer(data={'email': 'invalid'})
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

@pytest.mark.django_db
class TestContactPhoneNumberSerializer:
    """Test cases for ContactPhoneNumberSerializer."""

    def test_serialization(self):
        """Test serialization of phone number."""
        phone = ContactPhoneNumberFactory()
        serializer = ContactPhoneNumberSerializer(phone)
        data = serializer.data
        
        assert data['id'] == phone.id
        assert data['phone_number'] == phone.phone_number
        assert data['phone_type'] == phone.phone_type
        assert data['is_primary'] == phone.is_primary

    def test_deserialization(self):
        """Test deserializing phone number data."""
        contact = ContactFactory()
        data = {
            'phone_number': '+1234567890',
            'phone_type': PhoneType.MOBILE,
            'is_primary': True
        }
        serializer = ContactPhoneNumberSerializer(data=data)
        assert serializer.is_valid()
        phone = serializer.save(contact=contact)
        assert phone.phone_number == data['phone_number']
        assert phone.phone_type == data['phone_type']
        assert phone.is_primary == data['is_primary']

    def test_validation(self):
        """Test phone number validation."""
        invalid_numbers = [
            '1234567',  # No +
            '+abc123',  # Non-digit characters
            '+123',     # Too short
            '+1234567890123456'  # Too long
        ]
        
        for number in invalid_numbers:
            serializer = ContactPhoneNumberSerializer(data={'phone_number': number})
            assert not serializer.is_valid()
            assert 'phone_number' in serializer.errors

@pytest.mark.django_db
class TestContactAddressSerializer:
    """Test cases for ContactAddressSerializer."""

    def test_serialization(self):
        """Test serialization of address."""
        address = ContactAddressFactory()
        serializer = ContactAddressSerializer(address)
        data = serializer.data
        
        assert data['id'] == address.id
        assert data['address'] == address.address.id
        assert data['address_type'] == address.address_type
        assert data['is_primary'] == address.is_primary

    def test_deserialization(self):
        """Test deserializing address data."""
        contact = ContactFactory()
        address = AddressFactory()
        data = {
            'address': address.id,
            'address_type': AddressType.WORK,
            'is_primary': True
        }
        serializer = ContactAddressSerializer(data=data)
        assert serializer.is_valid()
        contact_address = serializer.save(contact=contact)
        assert contact_address.address == address
        assert contact_address.address_type == data['address_type']
        assert contact_address.is_primary == data['is_primary']

@pytest.mark.django_db
class TestContactSerializer:
    """Test cases for ContactSerializer."""

    def test_serialization(self):
        """Test serialization of contact with nested objects."""
        contact = ContactFactory()
        email = ContactEmailAddressFactory(contact=contact)
        phone = ContactPhoneNumberFactory(contact=contact)
        address = ContactAddressFactory(contact=contact)
        contact.tags.add('test')
        
        serializer = ContactSerializer(contact)
        data = serializer.data
        
        assert data['id'] == contact.id
        assert data['first_name'] == contact.first_name
        assert data['last_name'] == contact.last_name
        assert len(data['email_addresses']) == 1
        assert len(data['phone_numbers']) == 1
        assert len(data['addresses']) == 1
        assert 'test' in data['tags']

    def test_deserialization(self):
        """Test deserialization of contact data."""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'contact_type': 'primary',
            'status': 'active',
            'source': 'website',
            'email_addresses': [
                {
                    'email': 'john@example.com',
                    'email_type': 'personal',
                    'is_primary': True
                }
            ],
            'phone_numbers': [
                {
                    'phone_number': '+1234567890',
                    'phone_type': 'mobile',
                    'is_primary': True
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
                    'address_type': 'home',
                    'is_primary': True
                }
            ],
            'tags': ['test']
        }
        serializer = ContactSerializer(data=data)
        assert serializer.is_valid()
        contact = serializer.save()
        assert contact.first_name == 'John'
        assert contact.last_name == 'Doe'
        assert contact.email_addresses.count() == 1
        assert contact.phone_numbers.count() == 1
        assert contact.addresses.count() == 1
        assert contact.tags.count() == 1

    def test_update_nested_objects(self):
        """Test updating nested objects."""
        contact = ContactFactory()
        email = ContactEmailAddressFactory(contact=contact)
        phone = ContactPhoneNumberFactory(contact=contact)
        address = ContactAddressFactory(contact=contact)

        data = {
            'email_addresses': [
                {
                    'id': email.id,
                    'email': 'new@example.com',
                    'email_type': 'work',
                    'is_primary': True
                }
            ],
            'phone_numbers': [
                {
                    'id': phone.id,
                    'phone_number': '+1987654321',
                    'phone_type': 'home',
                    'is_primary': True
                }
            ],
            'addresses': [
                {
                    'id': address.id,
                    'address': {
                        'street_address_1': '456 New St',
                        'city': 'Boston',
                        'state_province': 'MA',
                        'postal_code': '02108',
                        'country': {'code': 'US', 'name': 'United States'}
                    },
                    'address_type': 'work',
                    'is_primary': True
                }
            ]
        }

        serializer = ContactSerializer(contact, data=data, partial=True)
        if not serializer.is_valid():
            pytest.fail(f"Serializer validation failed: {serializer.errors}")
        updated_contact = serializer.save()

        # Verify updates
        email.refresh_from_db()
        phone.refresh_from_db()
        address.refresh_from_db()

        assert email.email == 'new@example.com'
        assert email.email_type == 'work'
        assert email.is_primary

        assert phone.phone_number == '+1987654321'
        assert phone.phone_type == 'home'
        assert phone.is_primary

        assert address.address.street_address_1 == '456 New St'
        assert address.address.city == 'Boston'
        assert address.address_type == 'work'
        assert address.is_primary

    def test_organization_validation(self):
        """Test organization ID validation."""
        serializer = ContactSerializer(data={'organization_id': -1})
        assert not serializer.is_valid()
        assert 'organization_id' in serializer.errors

        serializer = ContactSerializer(data={'linked_organization_id': -1})
        assert not serializer.is_valid()
        assert 'linked_organization_id' in serializer.errors

    def test_to_representation(self):
        """Test to_representation method."""
        contact = ContactFactory()
        contact.tags.add('tag2', 'tag1')
        
        serializer = ContactSerializer(contact)
        data = serializer.data
        
        assert data['tags'] == ['tag1', 'tag2'] 