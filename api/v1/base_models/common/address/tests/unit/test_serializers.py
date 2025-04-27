import pytest
from decimal import Decimal
from django_countries.fields import CountryField
from rest_framework.exceptions import ValidationError
from api.v1.base_models.common.address.serializers import (
    AddressSerializer,
    CUSTOM_FIELD_SCHEMA,
)


@pytest.mark.django_db
class TestAddressSerializer:
    """Test cases for the AddressSerializer."""

    def test_serializer_validation(self):
        """Test serializer validation with valid data."""
        data = {"street_address_1": "123 Main St", "city": "New York", "country": "US"}
        serializer = AddressSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["street_address_1"] == "123 Main St"
        assert serializer.validated_data["city"] == "New York"
        assert serializer.validated_data["country"] == "US"

    def test_serializer_optional_fields(self):
        """Test serializer with optional fields."""
        data = {
            "street_address_1": "123 Main St",
            "city": "New York",
            "country": "US",
            "street_address_2": "Apt 4B",
            "state_province": "NY",
            "postal_code": "10001",
            "latitude": "40.7128",
            "longitude": "-74.0060",
            "status": "Active",
            "custom_fields": {
                "floor": "4",
                "building": "A",
                "unit": "4B",
                "access_code": "1234",
                "delivery_instructions": "Leave at front desk",
            },
        }
        serializer = AddressSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["street_address_2"] == "Apt 4B"
        assert serializer.validated_data["state_province"] == "NY"
        assert serializer.validated_data["postal_code"] == "10001"
        assert serializer.validated_data["latitude"] == Decimal("40.7128")
        assert serializer.validated_data["longitude"] == Decimal("-74.0060")
        assert serializer.validated_data["status"] == "Active"
        assert serializer.validated_data["custom_fields"] == {
            "floor": "4",
            "building": "A",
            "unit": "4B",
            "access_code": "1234",
            "delivery_instructions": "Leave at front desk",
        }

    def test_serializer_invalid_country(self):
        """Test serializer with invalid country code."""
        data = {
            "street_address_1": "123 Main St",
            "city": "New York",
            "country": "XX",  # Invalid country code
        }
        serializer = AddressSerializer(data=data)
        assert not serializer.is_valid()
        assert "country" in serializer.errors

    def test_serializer_field_lengths(self):
        """Test serializer field length validation."""
        data = {
            "street_address_1": "a" * 256,  # Exceeds max_length of 255
            "city": "New York",
            "country": "US",
        }
        serializer = AddressSerializer(data=data)
        assert not serializer.is_valid()
        assert "street_address_1" in serializer.errors

    def test_serializer_representation(self):
        """Test serializer representation of an instance."""
        address_data = {
            "street_address_1": "123 Main St",
            "city": "New York",
            "country": "US",
            "state_province": "NY",
            "postal_code": "10001",
        }
        serializer = AddressSerializer(data=address_data)
        assert serializer.is_valid()
        address = serializer.save()

        representation = AddressSerializer(address).data
        assert representation["street_address_1"] == "123 Main St"
        assert representation["city"] == "New York"
        assert representation["country"] == {
            "code": "US",
            "name": "United States of America",
        }
        assert representation["state_province"] == "NY"
        assert representation["postal_code"] == "10001"
        assert "id" in representation
        assert "created_at" in representation
        assert "updated_at" in representation

    def test_custom_fields_validation_invalid_field(self):
        """Test custom_fields validation with invalid field name."""
        data = {
            "street_address_1": "123 Main St",
            "city": "New York",
            "country": "US",
            "custom_fields": {"invalid_field": "value"},  # Not in schema
        }
        serializer = AddressSerializer(data=data)
        assert not serializer.is_valid()
        assert "custom_fields" in serializer.errors
        assert "invalid_field" in str(serializer.errors["custom_fields"][0])

    def test_custom_fields_validation_max_length(self):
        """Test custom_fields validation with field exceeding max_length."""
        data = {
            "street_address_1": "123 Main St",
            "city": "New York",
            "country": "US",
            "custom_fields": {"floor": "a" * 11},  # Exceeds max_length of 10
        }
        serializer = AddressSerializer(data=data)
        assert not serializer.is_valid()
        assert "custom_fields" in serializer.errors
        assert "floor" in str(serializer.errors["custom_fields"][0])
        assert "cannot exceed 10 characters" in str(
            serializer.errors["custom_fields"][0]
        )

    def test_custom_fields_validation_invalid_type(self):
        """Test custom_fields validation with invalid type."""
        data = {
            "street_address_1": "123 Main St",
            "city": "New York",
            "country": "US",
            "custom_fields": {"floor": 123},  # Should be string
        }
        serializer = AddressSerializer(data=data)
        assert not serializer.is_valid()
        assert "custom_fields" in serializer.errors
        assert "must be of type str" in str(serializer.errors["custom_fields"][0])
