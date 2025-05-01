import pytest
from rest_framework.exceptions import ValidationError
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

@pytest.mark.django_db
class TestContactEmailAddressSerializer:
    """Test cases for ContactEmailAddressSerializer."""

    def test_serialization(self):
        """Test serializing an email address."""
        email = ContactEmailAddressFactory()
        serializer = ContactEmailAddressSerializer(email)
        data = serializer.data
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
        data = {
            'email': 'invalid-email',
            'email_type': EmailType.WORK,
            'is_primary': True
        }
        serializer = ContactEmailAddressSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

@pytest.mark.django_db
class TestContactPhoneNumberSerializer:
    """Test cases for ContactPhoneNumberSerializer."""

    def test_serialization(self):
        """Test serializing a phone number."""
        phone = ContactPhoneNumberFactory()
        serializer = ContactPhoneNumberSerializer(phone)
        data = serializer.data
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

@pytest.mark.django_db
class TestContactAddressSerializer:
    """Test cases for ContactAddressSerializer."""

    def test_serialization(self):
        """Test serializing an address."""
        address = ContactAddressFactory()
        serializer = ContactAddressSerializer(address)
        data = serializer.data
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
        """Test serializing a contact with nested data."""
        contact = ContactFactory()
        email = ContactEmailAddressFactory(contact=contact, is_primary=True)
        phone = ContactPhoneNumberFactory(contact=contact, is_primary=True)
        address = ContactAddressFactory(contact=contact, is_primary=True)
        contact.tags.add('important', 'customer')

        serializer = ContactSerializer(contact)
        data = serializer.data

        assert data['first_name'] == contact.first_name
        assert data['last_name'] == contact.last_name
        assert data['organization_id'] == contact.organization_id
        assert data['tags'] == ['customer', 'important']
        assert len(data['email_addresses']) == 1
        assert len(data['phone_numbers']) == 1
        assert len(data['addresses']) == 1

    def test_deserialization(self):
        """Test deserializing contact data with nested objects."""
        address = AddressFactory()
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'organization_id': 1,
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
            }]
        }

        serializer = ContactSerializer(data=data)
        assert serializer.is_valid()
        contact = serializer.save()
        
        assert contact.first_name == data['first_name']
        assert contact.last_name == data['last_name']
        assert contact.organization_id == data['organization_id']
        assert set(contact.tags.names()) == set(data['tags'])
        assert contact.email_addresses.count() == 1
        assert contact.phone_numbers.count() == 1
        assert contact.addresses.count() == 1

    def test_organization_id_validation(self):
        """Test organization_id validation."""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'organization_id': -1,  # Invalid ID
            'contact_type': ContactType.PRIMARY,
            'status': ContactStatus.ACTIVE,
            'source': ContactSource.WEBSITE
        }
        serializer = ContactSerializer(data=data)
        assert not serializer.is_valid()
        assert 'organization_id' in serializer.errors

    def test_null_organization_id(self):
        """Test that organization_id can be null."""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'organization_id': None,
            'contact_type': ContactType.PRIMARY,
            'status': ContactStatus.ACTIVE,
            'source': ContactSource.WEBSITE
        }
        serializer = ContactSerializer(data=data)
        assert serializer.is_valid()
        contact = serializer.save()
        assert contact.organization_id is None 