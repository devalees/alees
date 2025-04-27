import pytest
from decimal import Decimal
from ..factories import AddressFactory


@pytest.mark.django_db
class TestAddressFactory:
    """Test cases for the AddressFactory."""

    def test_create_address_with_factory(self):
        """Test that AddressFactory creates valid Address instances."""
        address = AddressFactory()
        assert address.street_address_1 is not None
        assert address.city is not None
        assert address.country is not None
        assert address.pk is not None

    def test_factory_optional_fields(self):
        """Test that factory sets optional fields correctly."""
        address = AddressFactory()
        assert isinstance(address.latitude, (Decimal, type(None)))
        assert isinstance(address.longitude, (Decimal, type(None)))
        assert address.custom_fields == {}
        assert address.status == "Active"

    def test_factory_with_overrides(self):
        """Test that factory accepts field overrides."""
        custom_fields = {"floor": "4", "building": "A"}
        address = AddressFactory(
            street_address_1="123 Main St",
            custom_fields=custom_fields,
            status="Inactive",
        )
        assert address.street_address_1 == "123 Main St"
        assert address.custom_fields == custom_fields
        assert address.status == "Inactive"

    def test_factory_batch_creation(self):
        """Test that factory can create multiple instances."""
        addresses = AddressFactory.create_batch(5)
        assert len(addresses) == 5
        assert all(addr.pk is not None for addr in addresses)
        assert (
            len(set(addr.street_address_1 for addr in addresses)) == 5
        )  # All addresses should be unique
