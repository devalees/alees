import pytest
from decimal import Decimal

from api.v1.base_models.common.taxes.models import TaxJurisdiction, TaxCategory, TaxRate
from api.v1.base_models.common.taxes.tests.factories import (
    TaxJurisdictionFactory,
    TaxCategoryFactory,
    TaxRateFactory
)


@pytest.mark.django_db
class TestTaxFactories:
    """Tests to ensure tax-related factories create valid model instances."""
    
    def test_tax_jurisdiction_factory(self):
        """Test TaxJurisdictionFactory creates valid instances."""
        jurisdiction = TaxJurisdictionFactory()
        
        # Check instance type
        assert isinstance(jurisdiction, TaxJurisdiction)
        
        # Check required fields are set
        assert jurisdiction.code, "Code should be set"
        assert jurisdiction.name, "Name should be set"
        assert jurisdiction.jurisdiction_type, "Jurisdiction type should be set"
        
        # Check default values are set
        assert jurisdiction.is_active is True
        assert jurisdiction.custom_fields == {}
        
        # Verify the instance can be retrieved from the database
        db_jurisdiction = TaxJurisdiction.objects.get(code=jurisdiction.code)
        assert db_jurisdiction == jurisdiction
    
    def test_tax_category_factory(self):
        """Test TaxCategoryFactory creates valid instances."""
        category = TaxCategoryFactory()
        
        # Check instance type
        assert isinstance(category, TaxCategory)
        
        # Check required fields are set
        assert category.code, "Code should be set"
        assert category.name, "Name should be set"
        
        # Check default values are set
        assert category.is_active is True
        
        # Verify description is set (even though it's optional in the model)
        assert category.description, "Description should be set by the factory"
        
        # Verify the instance can be retrieved from the database
        db_category = TaxCategory.objects.get(code=category.code)
        assert db_category == category

    def test_tax_rate_factory(self):
        """Test TaxRateFactory creates valid instances."""
        tax_rate = TaxRateFactory()
        
        # Check instance type
        assert isinstance(tax_rate, TaxRate)
        
        # Check required fields are set
        assert tax_rate.jurisdiction, "Jurisdiction should be set"
        assert tax_rate.name, "Name should be set"
        assert tax_rate.rate is not None, "Rate should be set"
        assert tax_rate.tax_type, "Tax type should be set"
        
        # Check relationships are set correctly
        assert isinstance(tax_rate.jurisdiction, TaxJurisdiction)
        assert isinstance(tax_rate.tax_category, TaxCategory)
        
        # Check default values
        assert tax_rate.is_compound is False
        assert tax_rate.priority == 0
        assert tax_rate.is_active is True
        assert tax_rate.custom_fields == {}
        
        # Verify dates are set
        assert tax_rate.valid_from, "Valid from date should be set"
        assert tax_rate.valid_to, "Valid to date should be set"
        assert tax_rate.valid_from < tax_rate.valid_to, "Valid from should be before valid to"
        
        # Verify the instance can be retrieved from the database
        db_tax_rate = TaxRate.objects.get(pk=tax_rate.pk)
        assert db_tax_rate == tax_rate
        
    def test_create_multiple_instances(self):
        """Test creating multiple instances with the factories."""
        # Create multiple instances
        jurisdictions = [TaxJurisdictionFactory() for _ in range(3)]
        categories = [TaxCategoryFactory() for _ in range(3)]
        tax_rates = [TaxRateFactory() for _ in range(3)]
        
        # Verify all were created with unique attributes
        assert len(set(j.code for j in jurisdictions)) == 3, "Jurisdiction codes should be unique"
        assert len(set(c.code for c in categories)) == 3, "Category codes should be unique"
        assert len(set(tr.name for tr in tax_rates)) == 3, "Tax rate names should be unique"
        
        # Verify all instances exist in the database
        assert TaxJurisdiction.objects.filter(code__in=[j.code for j in jurisdictions]).count() == 3
        assert TaxCategory.objects.filter(code__in=[c.code for c in categories]).count() == 3
        assert TaxRate.objects.filter(pk__in=[tr.pk for tr in tax_rates]).count() == 3
    
    def test_custom_factory_attributes(self):
        """Test creating factory instances with custom attributes."""
        # Custom jurisdiction
        custom_jurisdiction = TaxJurisdictionFactory(
            code="US-CA",
            name="California",
            jurisdiction_type="STATE_PROVINCE",
            is_active=False,
            custom_fields={"population": "39.5M"}
        )
        
        assert custom_jurisdiction.code == "US-CA"
        assert custom_jurisdiction.name == "California"
        assert custom_jurisdiction.jurisdiction_type == "STATE_PROVINCE"
        assert custom_jurisdiction.is_active is False
        assert custom_jurisdiction.custom_fields == {"population": "39.5M"}
        
        # Custom category
        custom_category = TaxCategoryFactory(
            code="FOOD",
            name="Food Tax",
            description="Tax on food items",
            is_active=False
        )
        
        assert custom_category.code == "FOOD"
        assert custom_category.name == "Food Tax"
        assert custom_category.description == "Tax on food items"
        assert custom_category.is_active is False
        
        # Custom tax rate
        custom_tax_rate = TaxRateFactory(
            jurisdiction=custom_jurisdiction,
            tax_category=custom_category,
            name="CA Food Tax",
            rate=Decimal("0.0875"),
            tax_type="SALES",
            is_compound=True,
            priority=2,
            is_active=False,
            custom_fields={"exempt_items": ["milk", "bread"]}
        )
        
        assert custom_tax_rate.jurisdiction == custom_jurisdiction
        assert custom_tax_rate.tax_category == custom_category
        assert custom_tax_rate.name == "CA Food Tax"
        assert custom_tax_rate.rate == Decimal("0.0875")
        assert custom_tax_rate.tax_type == "SALES"
        assert custom_tax_rate.is_compound is True
        assert custom_tax_rate.priority == 2
        assert custom_tax_rate.is_active is False
        assert custom_tax_rate.custom_fields == {"exempt_items": ["milk", "bread"]} 