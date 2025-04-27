import factory
from factory.django import DjangoModelFactory
from ..models import Address

class AddressFactory(DjangoModelFactory):
    """Factory for creating Address instances."""
    class Meta:
        model = Address

    street_address_1 = factory.Faker('street_address')
    city = factory.Faker('city')
    state_province = factory.Faker('state_abbr')
    postal_code = factory.Faker('postcode')
    country = factory.Faker('country_code')
    latitude = factory.Faker('latitude')
    longitude = factory.Faker('longitude')
    custom_fields = {}
    status = 'Active' 