import pytest
from decimal import Decimal
from django_countries.fields import CountryField
from rest_framework.exceptions import ValidationError
from api.v1.base_models.common.address.serializers import AddressSerializer
from api.v1.base_models.common.address.models import Address

@pytest.mark.django_db
class TestAddressSerializerIntegration:
    """Integration test cases for the AddressSerializer."""

    def test_serializer_create(self):
        """Test serializer create operation."""
        data = {
            'street_address_1': '123 Main St',
            'city': 'New York',
            'country': 'US',
            'state_province': 'NY',
            'postal_code': '10001'
        }
        serializer = AddressSerializer(data=data)
        assert serializer.is_valid()
        address = serializer.save()
        
        assert isinstance(address, Address)
        assert address.street_address_1 == '123 Main St'
        assert address.city == 'New York'
        assert address.country == 'US'
        assert address.state_province == 'NY'
        assert address.postal_code == '10001'

    def test_serializer_update(self):
        """Test serializer update operation."""
        # Create initial address
        address = Address.objects.create(
            street_address_1='123 Main St',
            city='New York',
            country='US'
        )
        
        # Update address
        data = {
            'street_address_1': '456 Park Ave',
            'city': 'New York',
            'country': 'US',
            'state_province': 'NY'
        }
        serializer = AddressSerializer(address, data=data, partial=True)
        assert serializer.is_valid()
        updated_address = serializer.save()
        
        assert updated_address.street_address_1 == '456 Park Ave'
        assert updated_address.state_province == 'NY'
        assert updated_address.pk == address.pk

    def test_serializer_custom_fields_validation(self):
        """Test custom fields validation."""
        # Valid custom fields
        data = {
            'street_address_1': '123 Main St',
            'city': 'New York',
            'country': 'US',
            'custom_fields': {'floor': '4', 'building': 'A'}
        }
        serializer = AddressSerializer(data=data)
        assert serializer.is_valid()
        
        # Invalid custom fields (not a dict)
        data['custom_fields'] = 'not-a-dict'
        serializer = AddressSerializer(data=data)
        assert not serializer.is_valid()
        assert 'custom_fields' in serializer.errors

    def test_serializer_read_only_fields(self):
        """Test that read-only fields are handled correctly."""
        address = Address.objects.create(
            street_address_1='123 Main St',
            city='New York',
            country='US'
        )
        
        # Try to update read-only fields
        data = {
            'street_address_1': '123 Main St',
            'city': 'New York',
            'country': 'US',
            'created_at': '2023-01-01T00:00:00Z',  # Read-only field
            'updated_at': '2023-01-01T00:00:00Z'   # Read-only field
        }
        serializer = AddressSerializer(address, data=data)
        assert serializer.is_valid()
        updated_address = serializer.save()
        
        # Read-only fields should not be updated
        assert updated_address.created_at != '2023-01-01T00:00:00Z'
        assert updated_address.updated_at != '2023-01-01T00:00:00Z' 