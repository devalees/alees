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

fake = Faker()

class ContactFactory(DjangoModelFactory):
    """Factory for creating Contact instances."""
    class Meta:
        model = Contact

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    title = factory.Faker('job')
    organization_name = factory.Faker('company')
    organization_id = None  # Temporary solution until Organization model is implemented
    contact_type = factory.Faker('random_element', elements=[x[0] for x in ContactType.CHOICES])
    status = factory.Faker('random_element', elements=[x[0] for x in ContactStatus.CHOICES])
    source = factory.Faker('random_element', elements=[x[0] for x in ContactSource.CHOICES])
    notes = factory.Faker('text', max_nb_chars=200)
    custom_fields = factory.LazyFunction(lambda: {})


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
    phone_number = factory.Faker('phone_number')
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
