import factory
from factory.django import DjangoModelFactory
from api.v1.base_models.organization.models import OrganizationType

class OrganizationTypeFactory(DjangoModelFactory):
    class Meta:
        model = OrganizationType
        django_get_or_create = ('name',)

    name = factory.Iterator(['Company', 'Department', 'Customer', 'Supplier', 'Branch'])
    description = factory.Faker('sentence') 