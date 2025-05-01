import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from taggit.models import Tag
from django.contrib.auth import get_user_model

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
from api.v1.base_models.user.tests.factories import UserFactory

User = get_user_model()

@pytest.mark.django_db
class TestContactModel:
    """Test cases for the Contact model."""

    def test_contact_creation(self):
        """Test creating a contact with all fields."""
        contact = ContactFactory()
        assert contact.pk is not None
        assert contact.first_name
        assert contact.last_name
        assert contact.contact_type in [x[0] for x in ContactType.CHOICES]
        assert contact.status in [x[0] for x in ContactStatus.CHOICES]
        assert contact.source in [x[0] for x in ContactSource.CHOICES]

    def test_contact_required_fields(self):
        """Test that required fields are enforced."""
        contact = Contact.objects.create(
            first_name='John',
            last_name='Doe',
            contact_type=ContactType.PRIMARY,
            status=ContactStatus.ACTIVE,
            source=ContactSource.WEBSITE
        )
        assert contact.pk is not None

    def test_contact_tags(self):
        """Test adding tags to a contact."""
        contact = ContactFactory()
        contact.tags.add('important', 'customer')
        assert contact.tags.count() == 2
        assert 'important' in contact.tags.names()
        assert 'customer' in contact.tags.names()

    def test_contact_custom_fields(self):
        """Test custom fields functionality."""
        custom_data = {'preferred_language': 'English', 'interests': ['technology', 'sports']}
        contact = ContactFactory(custom_fields=custom_data)
        assert contact.custom_fields == custom_data

    def test_contact_string_representation(self):
        """Test the string representation of a contact."""
        contact = ContactFactory(first_name='John', last_name='Doe')
        assert str(contact) == 'John Doe'

    def test_contact_clean_validation(self):
        """Test contact validation."""
        # Test with no names
        contact = ContactFactory.build(first_name='', last_name='')
        with pytest.raises(ValidationError):
            contact.clean()

        # Test with invalid custom fields
        contact = ContactFactory.build(custom_fields='invalid')
        with pytest.raises(ValidationError):
            contact.clean()

    def test_contact_properties(self):
        """Test contact properties."""
        contact = ContactFactory()
        email = ContactEmailAddressFactory(contact=contact, is_primary=True)
        phone = ContactPhoneNumberFactory(contact=contact, is_primary=True)
        address = ContactAddressFactory(contact=contact, is_primary=True)

        assert contact.primary_email == email
        assert contact.primary_phone == phone
        assert contact.primary_address == address
        assert contact.full_name == f"{contact.first_name} {contact.last_name}".strip()

    def test_contact_meta(self):
        """Test contact Meta options."""
        assert Contact._meta.verbose_name == 'Contact'
        assert Contact._meta.verbose_name_plural == 'Contacts'
        assert Contact._meta.ordering == ['last_name', 'first_name']
        assert len(Contact._meta.indexes) == 6

@pytest.mark.django_db
class TestContactEmailAddressModel:
    """Test cases for the ContactEmailAddress model."""

    def test_email_creation(self):
        """Test creating an email address for a contact."""
        email = ContactEmailAddressFactory()
        assert email.pk is not None
        assert email.email
        assert email.email_type in [x[0] for x in EmailType.CHOICES]

    def test_email_validation(self):
        """Test email validation."""
        with pytest.raises(ValidationError):
            email = ContactEmailAddressFactory.build(email="invalid-email")
            email.full_clean()

    def test_primary_email_uniqueness(self):
        """Test that only one email can be primary per contact."""
        contact = ContactFactory()
        email1 = ContactEmailAddressFactory(contact=contact, is_primary=True)
        email2 = ContactEmailAddressFactory(contact=contact, is_primary=True)
        email1.refresh_from_db()
        assert not email1.is_primary
        assert email2.is_primary

    def test_email_clean_validation(self):
        """Test email validation."""
        contact = ContactFactory()
        email = ContactEmailAddressFactory.build(contact=contact, email='invalid')
        with pytest.raises(ValidationError):
            email.clean()

    def test_primary_email_handling(self):
        """Test primary email handling."""
        contact = ContactFactory()
        email1 = ContactEmailAddressFactory(contact=contact, is_primary=True)
        email2 = ContactEmailAddressFactory(contact=contact, is_primary=True)
        
        email1.refresh_from_db()
        email2.refresh_from_db()
        
        assert not email1.is_primary
        assert email2.is_primary

@pytest.mark.django_db
class TestContactPhoneNumberModel:
    """Test cases for the ContactPhoneNumber model."""

    def test_phone_creation(self):
        """Test creating a phone number for a contact."""
        phone = ContactPhoneNumberFactory()
        assert phone.pk is not None
        assert phone.phone_number
        assert phone.phone_type in [x[0] for x in PhoneType.CHOICES]

    def test_phone_validation(self):
        """Test phone number validation."""
        phone = ContactPhoneNumberFactory(phone_number="1234567890")
        assert phone.pk is not None

    def test_primary_phone_uniqueness(self):
        """Test that only one phone number can be primary per contact."""
        contact = ContactFactory()
        phone1 = ContactPhoneNumberFactory(contact=contact, is_primary=True)
        phone2 = ContactPhoneNumberFactory(contact=contact, is_primary=True)
        phone1.refresh_from_db()
        assert not phone1.is_primary
        assert phone2.is_primary

    def test_phone_clean_validation(self):
        """Test phone number validation."""
        contact = ContactFactory()
        
        # Test invalid phone number formats
        invalid_numbers = [
            '1234567',  # No +
            '+abc123',  # Non-digit characters
            '+123',     # Too short
            '+1234567890123456'  # Too long
        ]
        
        for number in invalid_numbers:
            phone = ContactPhoneNumberFactory.build(contact=contact, phone_number=number)
            with pytest.raises(ValidationError):
                phone.clean()

    def test_primary_phone_handling(self):
        """Test primary phone handling."""
        contact = ContactFactory()
        phone1 = ContactPhoneNumberFactory(contact=contact, is_primary=True)
        phone2 = ContactPhoneNumberFactory(contact=contact, is_primary=True)
        
        phone1.refresh_from_db()
        phone2.refresh_from_db()
        
        assert not phone1.is_primary
        assert phone2.is_primary

@pytest.mark.django_db
class TestContactAddressModel:
    """Test cases for the ContactAddress model."""

    def test_address_creation(self):
        """Test creating an address for a contact."""
        address = ContactAddressFactory()
        assert address.pk is not None
        assert address.address
        assert address.address_type in [x[0] for x in AddressType.CHOICES]

    def test_primary_address_uniqueness(self):
        """Test that only one address can be primary per contact."""
        contact = ContactFactory()
        address1 = ContactAddressFactory(contact=contact, is_primary=True)
        address2 = ContactAddressFactory(contact=contact, is_primary=True)
        address1.refresh_from_db()
        assert not address1.is_primary
        assert address2.is_primary

    def test_primary_address_handling(self):
        """Test primary address handling."""
        contact = ContactFactory()
        address1 = AddressFactory()
        address2 = AddressFactory()
        addr1 = ContactAddressFactory(contact=contact, address=address1, is_primary=True)
        addr2 = ContactAddressFactory(contact=contact, address=address2, is_primary=True)
        
        addr1.refresh_from_db()
        addr2.refresh_from_db()
        
        assert not addr1.is_primary
        assert addr2.is_primary 