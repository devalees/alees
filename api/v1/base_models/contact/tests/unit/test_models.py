import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from crum import impersonate
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
from api.v1.base_models.organization.tests.factories import OrganizationFactory, OrganizationTypeFactory

User = get_user_model()

# Define necessary fixtures if they don't exist globally for unit tests
@pytest.fixture
def test_user():
    return UserFactory()

@pytest.fixture
def test_org_type(test_user):
    # Assuming AuditableModel is not strictly enforced or handled by factory
    return OrganizationTypeFactory()

@pytest.fixture
def test_organization(test_user, test_org_type):
    # Assuming AuditableModel is not strictly enforced or handled by factory
    return OrganizationFactory(organization_type=test_org_type)

@pytest.mark.django_db
class TestContactModel:
    """Test cases for the Contact model."""

    def test_contact_creation(self, test_organization):
        """Test basic contact creation."""
        # Use the test_organization fixture
        contact = Contact.objects.create(
            first_name='John',
            last_name='Doe',
            contact_type=ContactType.PRIMARY,
            status=ContactStatus.ACTIVE,
            source=ContactSource.WEBSITE,
            organization=test_organization  # Pass the fixture result
        )
        assert contact.pk is not None
        assert contact.organization == test_organization
        assert contact.full_name == "John Doe"

    def test_contact_required_fields_organization(self, test_organization):
        """Test that IntegrityError is raised when organization is missing."""
        with pytest.raises(IntegrityError) as excinfo:
            # Attempt to create without organization
            Contact.objects.create(
                first_name="John", 
                last_name="Doe",
            )
        # Check that the error message mentions the organization_id constraint
        assert "organization_id" in str(excinfo.value)
        assert "violates not-null constraint" in str(excinfo.value)

    def test_contact_required_fields_django_validation(self, test_organization):
        """Test Django validation for other required fields (e.g., first_name)."""
        # Test missing first_name (Django validation)
        with pytest.raises(ValidationError) as ve:
             c = Contact(last_name="Smith", organization=test_organization)
             c.full_clean() # Django's full_clean checks non-db constraints
        assert 'first_name' in ve.value.message_dict

    def test_contact_tags(self, test_organization):
        """Test tag functionality."""
        contact = ContactFactory(organization=test_organization)
        contact.tags.add("customer", "important")
        assert contact.tags.count() == 2
        assert contact.tags.filter(name="customer").exists()

    def test_contact_custom_fields(self, test_organization):
        """Test custom fields functionality."""
        contact = ContactFactory(organization=test_organization)
        contact.custom_fields = {"lead_score": 95, "channel": "web"}
        contact.save()
        contact.refresh_from_db()
        assert contact.custom_fields == {"lead_score": 95, "channel": "web"}

    def test_contact_string_representation(self, test_organization):
        """Test the string representation."""
        contact = ContactFactory(first_name="Jane", last_name="Smith", organization=test_organization)
        assert str(contact) == "Jane Smith"

    def test_contact_clean_validation(self, test_organization):
        """Test model's clean method if applicable (e.g., custom validations)."""
        contact = ContactFactory.build(organization=test_organization) # Use build for pre-save validation
        # Add specific validation checks here if clean() has custom logic
        contact.full_clean() # Should not raise ValidationError for valid data

    def test_contact_properties(self, test_organization):
        """Test custom properties like full_name."""
        contact = ContactFactory(first_name="Alice", last_name="Wonder", organization=test_organization)
        assert contact.full_name == "Alice Wonder"

    def test_contact_meta(self):
        """Test model Meta options."""
        assert Contact._meta.verbose_name == "Contact"
        assert Contact._meta.verbose_name_plural == "Contacts"
        # Check ordering if defined
        assert Contact._meta.ordering == ['last_name', 'first_name']

@pytest.mark.django_db
class TestContactEmailAddressModel:
    """Test cases for the ContactEmailAddress model."""

    def test_email_creation(self, test_organization):
        contact = ContactFactory(organization=test_organization)
        email = ContactEmailAddress.objects.create(
            contact=contact,
            email="test@example.com",
            email_type=EmailType.WORK,
            is_primary=True
        )
        assert email.pk is not None
        assert email.contact == contact
        assert email.email == "test@example.com"

    def test_email_validation(self, test_organization):
        contact = ContactFactory(organization=test_organization)
        with pytest.raises(ValidationError):
            email = ContactEmailAddress(contact=contact, email="invalid-email", email_type=EmailType.WORK)
            email.full_clean()

    def test_primary_email_uniqueness(self, test_organization):
        contact = ContactFactory(organization=test_organization)
        ContactEmailAddressFactory(contact=contact, is_primary=True)
        with pytest.raises(ValidationError) as excinfo:
            email2 = ContactEmailAddress(contact=contact, email="another@example.com", is_primary=True)
            email2.full_clean()
        assert "Only one primary email address is allowed per contact" in str(excinfo.value)

    def test_email_clean_validation(self, test_organization):
        contact = ContactFactory(organization=test_organization)
        email = ContactEmailAddressFactory.build(contact=contact, is_primary=False)
        email.full_clean() # Should pass

        # Test primary constraint during clean
        ContactEmailAddressFactory(contact=contact, is_primary=True)
        email_primary_again = ContactEmailAddressFactory.build(contact=contact, is_primary=True)
        with pytest.raises(ValidationError):
            email_primary_again.full_clean()

    def test_primary_email_handling(self, test_organization):
        contact = ContactFactory(organization=test_organization)
        email1 = ContactEmailAddressFactory(contact=contact, is_primary=True)
        email2 = ContactEmailAddressFactory(contact=contact, is_primary=False)
        email3 = ContactEmailAddressFactory(contact=contact, is_primary=False)

        # Setting email2 as primary should unset email1
        email2.is_primary = True
        email2.save()
        email1.refresh_from_db()
        assert not email1.is_primary
        assert email2.is_primary

        # Setting email3 as primary should unset email2
        email3.is_primary = True
        email3.save()
        email1.refresh_from_db()
        email2.refresh_from_db()
        assert not email1.is_primary
        assert not email2.is_primary
        assert email3.is_primary

@pytest.mark.django_db
class TestContactPhoneNumberModel:
    """Test cases for the ContactPhoneNumber model."""

    def test_phone_creation(self, test_organization):
        contact = ContactFactory(organization=test_organization)
        phone = ContactPhoneNumber.objects.create(
            contact=contact,
            phone_number="+15551234567",
            phone_type=PhoneType.MOBILE,
            is_primary=True
        )
        assert phone.pk is not None
        assert str(phone.phone_number) == "+15551234567"

    def test_phone_validation(self, test_organization):
        contact = ContactFactory(organization=test_organization)
        with pytest.raises(ValidationError):
            # Example of invalid phone number format for phonenumber_field
            phone = ContactPhoneNumber(contact=contact, phone_number="123", phone_type=PhoneType.WORK)
            phone.full_clean()

    def test_primary_phone_uniqueness(self, test_organization):
        contact = ContactFactory(organization=test_organization)
        ContactPhoneNumberFactory(contact=contact, is_primary=True)
        with pytest.raises(ValidationError) as excinfo:
            phone2 = ContactPhoneNumber(contact=contact, phone_number="+15559876543", is_primary=True)
            phone2.full_clean()
        assert "Only one primary phone number is allowed per contact" in str(excinfo.value)

    def test_phone_clean_validation(self, test_organization):
        contact = ContactFactory(organization=test_organization)
        phone = ContactPhoneNumberFactory.build(contact=contact, is_primary=False)
        phone.full_clean() # Should pass

        ContactPhoneNumberFactory(contact=contact, is_primary=True)
        phone_primary_again = ContactPhoneNumberFactory.build(contact=contact, is_primary=True)
        with pytest.raises(ValidationError):
            phone_primary_again.full_clean()

    def test_primary_phone_handling(self, test_organization):
        contact = ContactFactory(organization=test_organization)
        phone1 = ContactPhoneNumberFactory(contact=contact, is_primary=True)
        phone2 = ContactPhoneNumberFactory(contact=contact, is_primary=False)

        phone2.is_primary = True
        phone2.save()
        phone1.refresh_from_db()
        assert not phone1.is_primary
        assert phone2.is_primary

@pytest.mark.django_db
class TestContactAddressModel:
    """Test cases for the ContactAddress model."""

    def test_address_creation(self, test_organization):
        contact = ContactFactory(organization=test_organization)
        address = AddressFactory() # Create a shared address instance
        contact_address = ContactAddress.objects.create(
            contact=contact,
            address=address,
            address_type=AddressType.BILLING,
            is_primary=True
        )
        assert contact_address.pk is not None
        assert contact_address.address.street_address_1 == address.street_address_1

    def test_primary_address_uniqueness(self, test_organization):
        contact = ContactFactory(organization=test_organization)
        ContactAddressFactory(contact=contact, is_primary=True)
        with pytest.raises(ValidationError) as excinfo:
            address2 = AddressFactory()
            contact_address2 = ContactAddress(contact=contact, address=address2, is_primary=True)
            contact_address2.full_clean()
        assert "Only one primary address is allowed per contact" in str(excinfo.value)

    def test_primary_address_handling(self, test_organization):
        contact = ContactFactory(organization=test_organization)
        ca1 = ContactAddressFactory(contact=contact, is_primary=True)
        ca2 = ContactAddressFactory(contact=contact, is_primary=False)

        ca2.is_primary = True
        ca2.save()
        ca1.refresh_from_db()
        assert not ca1.is_primary
        assert ca2.is_primary 