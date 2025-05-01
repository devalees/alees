import factory
from factory.django import DjangoModelFactory
from api.v1.base_models.organization.models import OrganizationType, Organization
from api.v1.base_models.contact.tests.factories import ContactFactory
from api.v1.base_models.common.address.tests.factories import AddressFactory
from api.v1.base_models.common.currency.tests.factories import CurrencyFactory

class OrganizationTypeFactory(DjangoModelFactory):
    class Meta:
        model = OrganizationType
        django_get_or_create = ('name',)

    name = factory.Iterator(['Company', 'Department', 'Customer', 'Supplier', 'Branch'])
    description = factory.Faker('sentence')

class OrganizationFactory(DjangoModelFactory):
    class Meta:
        model = Organization
        django_get_or_create = ('code',)

    name = factory.Faker('company')
    code = factory.Sequence(lambda n: f'ORG{n:03d}')
    organization_type = factory.SubFactory(OrganizationTypeFactory)
    status = factory.Iterator(['active', 'inactive', 'archived'])
    parent = None  # Will be set in tests if needed
    effective_date = factory.Faker('date_this_decade')
    end_date = None
    primary_contact = factory.SubFactory(ContactFactory)
    primary_address = factory.SubFactory(AddressFactory)
    currency = factory.SubFactory(CurrencyFactory)
    timezone = factory.Iterator(['UTC', 'America/New_York', 'Europe/London'])
    language = factory.Iterator(['en', 'fr', 'es'])
    metadata = factory.LazyFunction(lambda: {})
    custom_fields = factory.LazyFunction(lambda: {}) 