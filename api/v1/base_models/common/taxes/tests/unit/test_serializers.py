import pytest
from decimal import Decimal
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from api.v1.base_models.common.taxes.models import TaxJurisdiction, TaxCategory, TaxRate, TaxType, JurisdictionType
from api.v1.base_models.common.taxes.tests.factories import TaxJurisdictionFactory, TaxCategoryFactory, TaxRateFactory


class TestTaxJurisdictionSerializer:
    """Tests for the TaxJurisdictionSerializer."""

    @pytest.fixture
    def tax_jurisdiction_data(self):
        """Fixture providing valid data for creating a TaxJurisdiction."""
        return {
            'code': 'US-TX',
            'name': 'Texas',
            'jurisdiction_type': JurisdictionType.STATE_PROVINCE,
            'is_active': True,
            'custom_fields': {'region': 'South'}
        }

    @pytest.mark.django_db
    def test_serialization(self, tax_jurisdiction_data):
        """Test that a TaxJurisdiction is correctly serialized."""
        from api.v1.base_models.common.taxes.serializers import TaxJurisdictionSerializer
        
        jurisdiction = TaxJurisdictionFactory(**tax_jurisdiction_data)
        serializer = TaxJurisdictionSerializer(jurisdiction)
        data = serializer.data
        
        assert data['code'] == tax_jurisdiction_data['code']
        assert data['name'] == tax_jurisdiction_data['name']
        assert data['jurisdiction_type'] == tax_jurisdiction_data['jurisdiction_type']
        assert data['is_active'] == tax_jurisdiction_data['is_active']
        assert data['custom_fields'] == tax_jurisdiction_data['custom_fields']
        assert 'created_at' in data
        assert 'updated_at' in data

    @pytest.mark.django_db
    def test_deserialization(self, tax_jurisdiction_data):
        """Test that a TaxJurisdiction can be created from serialized data."""
        from api.v1.base_models.common.taxes.serializers import TaxJurisdictionSerializer
        
        serializer = TaxJurisdictionSerializer(data=tax_jurisdiction_data)
        assert serializer.is_valid()
        instance = serializer.save()
        
        assert instance.code == tax_jurisdiction_data['code']
        assert instance.name == tax_jurisdiction_data['name']
        assert instance.jurisdiction_type == tax_jurisdiction_data['jurisdiction_type']
        assert instance.is_active == tax_jurisdiction_data['is_active']
        assert instance.custom_fields == tax_jurisdiction_data['custom_fields']

    @pytest.mark.django_db
    def test_validation_duplicate_code(self, tax_jurisdiction_data):
        """Test that validation fails when using a duplicate code."""
        from api.v1.base_models.common.taxes.serializers import TaxJurisdictionSerializer
        
        # Create a jurisdiction with the same code
        TaxJurisdictionFactory(code=tax_jurisdiction_data['code'])
        
        serializer = TaxJurisdictionSerializer(data=tax_jurisdiction_data)
        assert not serializer.is_valid()
        assert 'code' in serializer.errors

    @pytest.mark.django_db
    def test_validation_invalid_jurisdiction_type(self, tax_jurisdiction_data):
        """Test that validation fails when using an invalid jurisdiction type."""
        from api.v1.base_models.common.taxes.serializers import TaxJurisdictionSerializer
        
        tax_jurisdiction_data['jurisdiction_type'] = 'INVALID'
        
        serializer = TaxJurisdictionSerializer(data=tax_jurisdiction_data)
        assert not serializer.is_valid()
        assert 'jurisdiction_type' in serializer.errors

    @pytest.mark.django_db
    def test_custom_fields_validation(self, tax_jurisdiction_data):
        """Test that custom_fields validates correctly."""
        from api.v1.base_models.common.taxes.serializers import TaxJurisdictionSerializer
        
        # Test with invalid JSON
        tax_jurisdiction_data['custom_fields'] = 'not a dict'
        serializer = TaxJurisdictionSerializer(data=tax_jurisdiction_data)
        assert not serializer.is_valid()
        assert 'custom_fields' in serializer.errors

        # Test with valid data
        tax_jurisdiction_data['custom_fields'] = {'region': 'South', 'population': 29_000_000}
        serializer = TaxJurisdictionSerializer(data=tax_jurisdiction_data)
        assert serializer.is_valid()


class TestTaxCategorySerializer:
    """Tests for the TaxCategorySerializer."""

    @pytest.fixture
    def tax_category_data(self):
        """Fixture providing valid data for creating a TaxCategory."""
        return {
            'code': 'FOOD',
            'name': 'Food and Beverages',
            'description': 'Edible items including prepared foods',
            'is_active': True
        }

    @pytest.mark.django_db
    def test_serialization(self, tax_category_data):
        """Test that a TaxCategory is correctly serialized."""
        from api.v1.base_models.common.taxes.serializers import TaxCategorySerializer
        
        category = TaxCategoryFactory(**tax_category_data)
        serializer = TaxCategorySerializer(category)
        data = serializer.data
        
        assert data['code'] == tax_category_data['code']
        assert data['name'] == tax_category_data['name']
        assert data['description'] == tax_category_data['description']
        assert data['is_active'] == tax_category_data['is_active']
        assert 'created_at' in data
        assert 'updated_at' in data

    @pytest.mark.django_db
    def test_deserialization(self, tax_category_data):
        """Test that a TaxCategory can be created from serialized data."""
        from api.v1.base_models.common.taxes.serializers import TaxCategorySerializer
        
        serializer = TaxCategorySerializer(data=tax_category_data)
        assert serializer.is_valid()
        instance = serializer.save()
        
        assert instance.code == tax_category_data['code']
        assert instance.name == tax_category_data['name']
        assert instance.description == tax_category_data['description']
        assert instance.is_active == tax_category_data['is_active']

    @pytest.mark.django_db
    def test_validation_duplicate_code(self, tax_category_data):
        """Test that validation fails when using a duplicate code."""
        from api.v1.base_models.common.taxes.serializers import TaxCategorySerializer
        
        # Create a category with the same code
        TaxCategoryFactory(code=tax_category_data['code'])
        
        serializer = TaxCategorySerializer(data=tax_category_data)
        assert not serializer.is_valid()
        assert 'code' in serializer.errors

    @pytest.mark.django_db
    def test_validation_duplicate_name(self, tax_category_data):
        """Test that validation fails when using a duplicate name."""
        from api.v1.base_models.common.taxes.serializers import TaxCategorySerializer
        
        # Create a category with the same name
        TaxCategoryFactory(name=tax_category_data['name'])
        
        serializer = TaxCategorySerializer(data=tax_category_data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors


class TestTaxRateSerializer:
    """Tests for the TaxRateSerializer."""

    @pytest.fixture
    @pytest.mark.django_db
    def tax_rate_data(self):
        """Fixture providing valid data for creating a TaxRate."""
        jurisdiction = TaxJurisdictionFactory()
        category = TaxCategoryFactory()
        
        return {
            'jurisdiction': jurisdiction.code,
            'tax_category': category.code,
            'name': 'Texas Sales Tax',
            'rate': '0.0825',
            'tax_type': TaxType.SALES,
            'is_compound': False,
            'priority': 1,
            'valid_from': timezone.now().date().isoformat(),
            'valid_to': None,
            'is_active': True,
            'custom_fields': {'exempt_items': ['food', 'medicine']}
        }

    @pytest.mark.django_db
    def test_serialization(self, tax_rate_data):
        """Test that a TaxRate is correctly serialized."""
        from api.v1.base_models.common.taxes.serializers import TaxRateSerializer
        
        jurisdiction = TaxJurisdiction.objects.get(code=tax_rate_data['jurisdiction'])
        category = TaxCategory.objects.get(code=tax_rate_data['tax_category'])
        
        rate = TaxRateFactory(
            jurisdiction=jurisdiction,
            tax_category=category,
            name=tax_rate_data['name'],
            rate=Decimal(tax_rate_data['rate']),
            tax_type=tax_rate_data['tax_type'],
            is_compound=tax_rate_data['is_compound'],
            priority=tax_rate_data['priority'],
            valid_from=tax_rate_data['valid_from'],
            valid_to=tax_rate_data['valid_to'],
            is_active=tax_rate_data['is_active'],
            custom_fields=tax_rate_data['custom_fields']
        )
        
        serializer = TaxRateSerializer(rate)
        data = serializer.data
        
        assert data['jurisdiction'] == tax_rate_data['jurisdiction']
        assert data['tax_category'] == tax_rate_data['tax_category']
        assert data['name'] == tax_rate_data['name']
        assert float(data['rate']) == float(tax_rate_data['rate'])
        assert data['tax_type'] == tax_rate_data['tax_type']
        assert data['is_compound'] == tax_rate_data['is_compound']
        assert data['priority'] == tax_rate_data['priority']
        assert data['is_active'] == tax_rate_data['is_active']
        assert data['custom_fields'] == tax_rate_data['custom_fields']
        assert 'created_at' in data
        assert 'updated_at' in data

    @pytest.mark.django_db
    def test_deserialization(self, tax_rate_data):
        """Test that a TaxRate can be created from serialized data."""
        from api.v1.base_models.common.taxes.serializers import TaxRateSerializer
        
        serializer = TaxRateSerializer(data=tax_rate_data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        
        assert instance.jurisdiction.code == tax_rate_data['jurisdiction']
        assert instance.tax_category.code == tax_rate_data['tax_category']
        assert instance.name == tax_rate_data['name']
        assert float(instance.rate) == float(tax_rate_data['rate'])
        assert instance.tax_type == tax_rate_data['tax_type']
        assert instance.is_compound == tax_rate_data['is_compound']
        assert instance.priority == tax_rate_data['priority']
        assert instance.is_active == tax_rate_data['is_active']
        assert instance.custom_fields == tax_rate_data['custom_fields']

    @pytest.mark.django_db
    def test_validation_rate_negative(self, tax_rate_data):
        """Test that validation fails when using a negative rate."""
        from api.v1.base_models.common.taxes.serializers import TaxRateSerializer
        
        tax_rate_data['rate'] = '-0.05'
        
        serializer = TaxRateSerializer(data=tax_rate_data)
        assert not serializer.is_valid()
        assert 'rate' in serializer.errors

    @pytest.mark.django_db
    def test_validation_date_ranges(self, tax_rate_data):
        """Test validation for date ranges."""
        from api.v1.base_models.common.taxes.serializers import TaxRateSerializer
        import datetime
        
        # Set valid_from later than valid_to
        today = datetime.date.today()
        tax_rate_data['valid_from'] = (today + datetime.timedelta(days=10)).isoformat()
        tax_rate_data['valid_to'] = today.isoformat()
        
        serializer = TaxRateSerializer(data=tax_rate_data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors or 'valid_to' in serializer.errors

    @pytest.mark.django_db
    def test_validation_missing_jurisdiction(self, tax_rate_data):
        """Test that validation fails when jurisdiction is missing."""
        from api.v1.base_models.common.taxes.serializers import TaxRateSerializer
        
        del tax_rate_data['jurisdiction']
        
        serializer = TaxRateSerializer(data=tax_rate_data)
        assert not serializer.is_valid()
        assert 'jurisdiction' in serializer.errors

    @pytest.mark.django_db
    def test_validation_invalid_tax_type(self, tax_rate_data):
        """Test that validation fails when using an invalid tax type."""
        from api.v1.base_models.common.taxes.serializers import TaxRateSerializer
        
        tax_rate_data['tax_type'] = 'INVALID'
        
        serializer = TaxRateSerializer(data=tax_rate_data)
        assert not serializer.is_valid()
        assert 'tax_type' in serializer.errors 