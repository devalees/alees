from rest_framework import serializers
from .models import Currency

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = [
            'code',
            'name',
            'symbol',
            'numeric_code',
            'decimal_places',
            'is_active',
            'custom_fields',
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def validate_code(self, value):
        """Validate the currency code."""
        if not value or len(value) != 3:
            raise serializers.ValidationError("Currency code must be exactly 3 characters long.")
        return value.upper()

    def validate_custom_fields(self, value):
        """Validate the custom fields."""
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError("Custom fields must be a dictionary.")
        return value

    def validate(self, data):
        """Validate unique constraints."""
        instance = getattr(self, 'instance', None)
        
        # Check code uniqueness for new instances
        if not instance and 'code' in data:
            code_exists = Currency.objects.filter(code=data['code']).exists()
            if code_exists:
                raise serializers.ValidationError({'code': 'Currency with this code already exists.'})
        
        # Check name uniqueness
        if 'name' in data:
            name_query = Currency.objects.filter(name=data['name'])
            if instance:
                name_query = name_query.exclude(pk=instance.pk)
            if name_query.exists():
                raise serializers.ValidationError({'name': 'Currency with this name already exists.'})
        
        # Check numeric_code uniqueness if provided
        if 'numeric_code' in data and data['numeric_code']:
            numeric_code_query = Currency.objects.filter(numeric_code=data['numeric_code'])
            if instance:
                numeric_code_query = numeric_code_query.exclude(pk=instance.pk)
            if numeric_code_query.exists():
                raise serializers.ValidationError({'numeric_code': 'Currency with this numeric code already exists.'})
        
        return data

    def create(self, validated_data):
        """Create a new Currency instance."""
        return Currency.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update a Currency instance."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
