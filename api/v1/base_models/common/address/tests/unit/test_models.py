import pytest
from decimal import Decimal
from django_countries.fields import CountryField
from django.core.exceptions import ValidationError
from api.v1.base_models.common.address.models import Address


@pytest.mark.django_db
class TestAddressModel:
    """Test cases for the Address model."""

    def test_create_address_with_required_fields(self):
        """Test that an Address instance can be created with required fields."""
        address = Address.objects.create(
            street_address_1="123 Main St", city="New York", country="US"
        )
        assert address.street_address_1 == "123 Main St"
        assert address.city == "New York"
        assert address.country == "US"
        assert address.pk is not None

    def test_create_address_with_optional_fields(self):
        """Test that optional fields can be set."""
        address = Address.objects.create(
            street_address_1="123 Main St",
            street_address_2="Apt 4B",
            city="New York",
            state_province="NY",
            postal_code="10001",
            country="US",
            latitude=Decimal("40.7128"),
            longitude=Decimal("-74.0060"),
            status="Active",
            custom_fields={"floor": "4", "building": "A"},
        )
        assert address.street_address_2 == "Apt 4B"
        assert address.state_province == "NY"
        assert address.postal_code == "10001"
        assert address.latitude == Decimal("40.7128")
        assert address.longitude == Decimal("-74.0060")
        assert address.status == "Active"
        assert address.custom_fields == {"floor": "4", "building": "A"}

    def test_custom_fields_default(self):
        """Test that custom_fields defaults to an empty dict."""
        address = Address.objects.create(
            street_address_1="123 Main St", city="New York", country="US"
        )
        assert address.custom_fields == {}

    def test_latitude_longitude_decimal_values(self):
        """Test that latitude/longitude accept Decimal values."""
        address = Address.objects.create(
            street_address_1="123 Main St",
            city="New York",
            country="US",
            latitude=Decimal("40.7128"),
            longitude=Decimal("-74.0060"),
        )
        assert isinstance(address.latitude, Decimal)
        assert isinstance(address.longitude, Decimal)
        assert address.latitude == Decimal("40.7128")
        assert address.longitude == Decimal("-74.0060")

    def test_country_field_validation(self):
        """Test that country field validates country codes."""
        # Valid country code
        address = Address.objects.create(
            street_address_1="123 Main St", city="New York", country="US"
        )
        assert address.country == "US"

        # Invalid country code should raise ValidationError
        address = Address(
            street_address_1="123 Main St",
            city="New York",
            country="XX",  # Invalid country code
        )
        with pytest.raises(ValidationError):
            address.full_clean()

    def test_string_representation(self):
        """Test the __str__ method returns a reasonable string."""
        address = Address.objects.create(
            street_address_1="123 Main St", city="New York", country="US"
        )
        assert str(address) == "123 Main St, New York, US"

        # Test with missing fields
        address = Address.objects.create(street_address_1="123 Main St", country="US")
        assert str(address) == "123 Main St, US"

    def test_inherited_fields(self):
        """Test that inherited Timestamped and Auditable fields exist."""
        address = Address.objects.create(
            street_address_1="123 Main St", city="New York", country="US"
        )
        assert hasattr(address, "created_at")
        assert hasattr(address, "updated_at")
        assert hasattr(address, "created_by")
        assert hasattr(address, "updated_by")
        assert address.created_at is not None
        assert address.updated_at is not None
