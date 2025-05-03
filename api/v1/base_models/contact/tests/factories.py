import factory
from factory.django import DjangoModelFactory
from faker import Faker

from api.v1.base_models.contact.models import (
    Contact, ContactEmailAddress, ContactPhoneNumber, ContactAddress
)
from api.v1.base_models.contact.choices import (
    ContactType, ContactStatus, ContactSource,
    EmailType, PhoneType, AddressType
)
from api.v1.base_models.common.address.tests.factories import AddressFactory
from api.v1.base_models.organization.tests.factories import OrganizationFactory

fake = Faker()

class ContactFactory(DjangoModelFactory):
    """Factory for Contact model."""
    class Meta:
        model = Contact

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    title = factory.Faker('job')
    organization = factory.SubFactory(OrganizationFactory)
    contact_type = factory.Iterator(ContactType.CHOICES, getter=lambda c: c[0])
    status = factory.Iterator(ContactStatus.CHOICES, getter=lambda c: c[0])
    source = factory.Iterator(ContactSource.CHOICES, getter=lambda c: c[0])
    notes = factory.Faker('text')


class ContactEmailAddressFactory(DjangoModelFactory):
    """Factory for creating ContactEmailAddress instances."""
    class Meta:
        model = ContactEmailAddress

    contact = factory.SubFactory(ContactFactory)
    email = factory.Faker('email')
    email_type = factory.Faker('random_element', elements=[x[0] for x in EmailType.CHOICES])
    is_primary = False


class ContactPhoneNumberFactory(DjangoModelFactory):
    """Factory for creating ContactPhoneNumber instances."""
    class Meta:
        model = ContactPhoneNumber

    contact = factory.SubFactory(ContactFactory)
    phone_number = factory.LazyFunction(lambda: '+' + ''.join([str(fake.random_digit()) for _ in range(10)]))
    phone_type = factory.Faker('random_element', elements=[x[0] for x in PhoneType.CHOICES])
    is_primary = False


class ContactAddressFactory(DjangoModelFactory):
    """Factory for creating ContactAddress instances."""
    class Meta:
        model = ContactAddress

    contact = factory.SubFactory(ContactFactory)
    address = factory.SubFactory(AddressFactory)
    address_type = factory.Faker('random_element', elements=[x[0] for x in AddressType.CHOICES])
    is_primary = False
