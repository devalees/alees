import factory
from factory.django import DjangoModelFactory
from api.v1.base_models.common.address.models import Address


class AddressFactory(DjangoModelFactory):
    """Factory for creating Address instances for testing."""

    class Meta:
        model = Address

    street_address_1 = factory.Faker("street_address")
    street_address_2 = factory.Faker("secondary_address")
    city = factory.Faker("city")
    state_province = factory.Faker("state_abbr")
    postal_code = factory.Faker("postcode")
    country = factory.Faker("country_code")
    latitude = factory.Faker("latitude")
    longitude = factory.Faker("longitude")
    status = "Active"
    custom_fields = {}
