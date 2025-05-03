import pytest
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from taggit.models import Tag
from django.test import TestCase
from rest_framework import serializers
from taggit.serializers import TaggitSerializer, TagListSerializerField

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
from api.v1.base_models.organization.tests.factories import OrganizationFactory
from api.v1.base_models.organization.models import Organization

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
        data = {'email': 'test@example.com', 'is_primary': True, 'email_type': 'work'}
        serializer = ContactEmailAddressSerializer(data=data, context={'contact': contact})
        assert serializer.is_valid()
        email = serializer.save()
        assert email.email == data['email']
        assert email.contact == contact

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
        data = {'phone_number': '+1234567890', 'is_primary': True, 'phone_type': 'mobile'}
        serializer = ContactPhoneNumberSerializer(data=data, context={'contact': contact})
        assert serializer.is_valid()
        phone = serializer.save()
        assert phone.phone_number == data['phone_number']
        assert phone.contact == contact

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
        data = {'address_id': address.id, 'is_primary': True, 'address_type': 'work'}
        serializer = ContactAddressSerializer(data=data, context={'contact': contact})
        assert serializer.is_valid(), serializer.errors
        contact_address = serializer.save()
        assert contact_address.address == address
        assert contact_address.contact == contact

class TestContactSerializer(TestCase):
    """Test cases for ContactSerializer."""

    def test_serialization(self):
        organization = OrganizationFactory()
        contact_instance = ContactFactory(organization=organization)
        ContactEmailAddressFactory(contact=contact_instance)
        ContactPhoneNumberFactory(contact=contact_instance)
        ContactAddressFactory(contact=contact_instance)
        contact_instance.tags.add('test')

        serializer = ContactSerializer(instance=contact_instance)
        data = serializer.data
        self.assertEqual(data['first_name'], contact_instance.first_name)
        self.assertIsNotNone(data['organization'])
        self.assertEqual(data['organization']['id'], organization.pk)
        self.assertEqual(data['organization']['name'], organization.name)
        self.assertIn('test', data['tags'])

    def test_deserialization(self):
        organization = OrganizationFactory()
        valid_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'organization_id': organization.pk,
            'email_addresses': [{'email': 'john@example.com', 'email_type': 'personal', 'is_primary': True}],
            'phone_numbers': [{'phone_number': '+1234567890', 'phone_type': 'mobile', 'is_primary': True}],
            'tags': ['test']
        }
        serializer = ContactSerializer(data=valid_data)
        if not serializer.is_valid():
            print(f"Deserialization Errors: {serializer.errors}")
        self.assertTrue(serializer.is_valid())
        contact = serializer.save()
        self.assertEqual(contact.first_name, 'John')
        self.assertEqual(contact.organization, organization)

    def test_validation_with_invalid_organization(self):
        data = {
            'first_name': 'John', 
            'last_name': 'Doe',
            'organization_id': 999999 
        }
        serializer = ContactSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('organization_id', serializer.errors)

    def test_validation_with_organization_name_conflict(self):
        pass 

    def test_update_nested_objects(self):
        organization = OrganizationFactory()
        contact = ContactFactory(organization=organization)
        email = ContactEmailAddressFactory(contact=contact, email='old@example.com')
        phone = ContactPhoneNumberFactory(contact=contact, phone_number='+1111111111')
        address = ContactAddressFactory(contact=contact)
        address_obj = address.address # Get the related Address instance

        update_data = {
            'first_name': 'Jane',
            'organization_id': organization.pk, # Need to pass org ID for validation
            'email_addresses': [
                {'id': email.id, 'email': 'new@example.com', 'is_primary': True}
            ],
            'phone_numbers': [
                {'id': phone.id, 'phone_number': '+2222222222'}
            ],
            'addresses': [
                # Provide address_id for the nested update
                {'id': address.id, 'address_id': address_obj.pk, 'is_primary': False} 
            ],
            'tags': ['updated']
        }

        serializer = ContactSerializer(instance=contact, data=update_data, partial=True)
        if not serializer.is_valid():
            print(f"Update Nested Errors: {serializer.errors}")
        self.assertTrue(serializer.is_valid())
        updated_contact = serializer.save()

        self.assertEqual(updated_contact.first_name, 'Jane')
        updated_contact.email_addresses.get(id=email.id)
        self.assertEqual(updated_contact.email_addresses.first().email, 'new@example.com')
        self.assertEqual(updated_contact.phone_numbers.first().phone_number, '+2222222222')
        self.assertFalse(updated_contact.addresses.first().is_primary)
        self.assertIn('updated', updated_contact.tags.names())

    def test_organization_validation(self):
        """Test case where organization_id is missing."""
        valid_data_no_org = {
            'first_name': 'John',
            'last_name': 'Doe',
        }
        serializer = ContactSerializer(data=valid_data_no_org)
        self.assertFalse(serializer.is_valid())
        self.assertIn('organization_id', serializer.errors) 