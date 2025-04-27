from rest_framework import serializers
from django_countries.serializer_fields import CountryField
from api.v1.base_models.common.address.models import Address

# Define allowed custom field types and their validators
CUSTOM_FIELD_SCHEMA = {
    'floor': {
        'type': str,
        'max_length': 10,
        'required': False
    },
    'building': {
        'type': str,
        'max_length': 50,
        'required': False
    },
    'unit': {
        'type': str,
        'max_length': 20,
        'required': False
    },
    'access_code': {
        'type': str,
        'max_length': 20,
        'required': False
    },
    'delivery_instructions': {
        'type': str,
        'max_length': 255,
        'required': False
    }
}

class AddressSerializer(serializers.ModelSerializer):
    """Serializer for the Address model."""
    country = CountryField(country_dict=True)

    class Meta:
        model = Address
        fields = [
            'id',
            'street_address_1',
            'street_address_2',
            'city',
            'state_province',
            'postal_code',
            'country',
            'latitude',
            'longitude',
            'status',
            'custom_fields',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_custom_fields(self, value):
        """
        Validate custom_fields against the defined schema.
        
        Args:
            value: The custom_fields dictionary to validate
            
        Returns:
            dict: The validated custom_fields dictionary
            
        Raises:
            ValidationError: If the custom_fields don't match the schema
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("Custom fields must be a dictionary.")

        # Validate each field against the schema
        for field_name, field_value in value.items():
            # Check if the field is allowed
            if field_name not in CUSTOM_FIELD_SCHEMA:
                raise serializers.ValidationError(
                    f"'{field_name}' is not an allowed custom field. "
                    f"Allowed fields are: {', '.join(CUSTOM_FIELD_SCHEMA.keys())}"
                )

            # Get field schema
            field_schema = CUSTOM_FIELD_SCHEMA[field_name]

            # Validate type
            if not isinstance(field_value, field_schema['type']):
                raise serializers.ValidationError(
                    f"'{field_name}' must be of type {field_schema['type'].__name__}"
                )

            # Validate max_length for string fields
            if field_schema['type'] == str and len(field_value) > field_schema['max_length']:
                raise serializers.ValidationError(
                    f"'{field_name}' cannot exceed {field_schema['max_length']} characters"
                )

        # Check for required fields
        required_fields = [
            field_name for field_name, schema in CUSTOM_FIELD_SCHEMA.items()
            if schema.get('required', False)
        ]
        for field_name in required_fields:
            if field_name not in value:
                raise serializers.ValidationError(
                    f"'{field_name}' is required in custom_fields"
                )

        return value 