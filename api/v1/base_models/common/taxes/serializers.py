from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
import datetime
from rest_framework.validators import UniqueValidator

from .models import TaxJurisdiction, TaxCategory, TaxRate


class TaxJurisdictionSerializer(serializers.ModelSerializer):
    """Serializer for TaxJurisdiction model."""
    
    parent = serializers.PrimaryKeyRelatedField(
        queryset=TaxJurisdiction.objects.all(),
        allow_null=True,
        required=False
    )
    
    class Meta:
        model = TaxJurisdiction
        fields = [
            'code', 'name', 'jurisdiction_type', 'parent',
            'is_active', 'custom_fields', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_custom_fields(self, value):
        """Validate that custom_fields is a dictionary."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(_("Custom fields must be a dictionary."))
        return value


class TaxCategorySerializer(serializers.ModelSerializer):
    """Serializer for TaxCategory model."""
    
    name = serializers.CharField(
        max_length=255,
        validators=[UniqueValidator(queryset=TaxCategory.objects.all())]
    )
    
    class Meta:
        model = TaxCategory
        fields = [
            'code', 'name', 'description', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class TaxRateSerializer(serializers.ModelSerializer):
    """Serializer for TaxRate model."""
    
    jurisdiction = serializers.SlugRelatedField(
        slug_field='code',
        queryset=TaxJurisdiction.objects.all()
    )
    
    tax_category = serializers.SlugRelatedField(
        slug_field='code',
        queryset=TaxCategory.objects.all(),
        allow_null=True,
        required=False
    )
    
    # Optional nested representations for read operations
    jurisdiction_details = TaxJurisdictionSerializer(source='jurisdiction', read_only=True)
    tax_category_details = TaxCategorySerializer(source='tax_category', read_only=True)
    
    class Meta:
        model = TaxRate
        fields = [
            'id', 'jurisdiction', 'tax_category', 'name', 'rate',
            'tax_type', 'is_compound', 'priority', 'valid_from', 'valid_to',
            'is_active', 'custom_fields', 'created_at', 'updated_at',
            'jurisdiction_details', 'tax_category_details'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'jurisdiction_details', 'tax_category_details'
        ]
    
    def validate_rate(self, value):
        """Validate that rate is non-negative."""
        if value < 0:
            raise serializers.ValidationError(_("Tax rate cannot be negative."))
        return value
    
    def validate_custom_fields(self, value):
        """Validate that custom_fields is a dictionary."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(_("Custom fields must be a dictionary."))
        return value
    
    def validate(self, data):
        """Validate the entire TaxRate instance."""
        # Check that valid_to is after valid_from if both are provided
        valid_from = data.get('valid_from')
        valid_to = data.get('valid_to')
        
        if valid_from and valid_to and valid_from > valid_to:
            raise serializers.ValidationError({
                'valid_to': _("Valid to date must be after valid from date.")
            })
        
        return data 