import pytest
from django.db import IntegrityError
from django.utils.timezone import now
from mptt.models import MPTTModel
from decimal import Decimal
import datetime

from api.v1.base_models.common.taxes.models import TaxJurisdiction


@pytest.mark.django_db
class TestTaxJurisdiction:
    
    def test_create_tax_jurisdiction_with_required_fields(self):
        """Test creation of TaxJurisdiction with required fields."""
        jurisdiction = TaxJurisdiction.objects.create(
            code="US",
            name="United States",
            jurisdiction_type="COUNTRY"
        )
        
        assert jurisdiction.code == "US"
        assert jurisdiction.name == "United States"
        assert jurisdiction.jurisdiction_type == "COUNTRY"
        assert jurisdiction.is_active is True  # Default value check
        assert jurisdiction.custom_fields == {}  # Default empty dict
        assert jurisdiction.parent is None  # No parent by default
        
    def test_tax_jurisdiction_unique_code(self):
        """Test that TaxJurisdiction code must be unique."""
        TaxJurisdiction.objects.create(
            code="US",
            name="United States",
            jurisdiction_type="COUNTRY"
        )
        
        with pytest.raises(IntegrityError):
            TaxJurisdiction.objects.create(
                code="US",  # Duplicate code
                name="United States of America",
                jurisdiction_type="COUNTRY"
            )
            
    def test_tax_jurisdiction_hierarchy(self):
        """Test that TaxJurisdiction hierarchy works with MPTT."""
        country = TaxJurisdiction.objects.create(
            code="US",
            name="United States",
            jurisdiction_type="COUNTRY"
        )
        
        state = TaxJurisdiction.objects.create(
            code="US-CA",
            name="California",
            jurisdiction_type="STATE_PROVINCE",
            parent=country
        )
        
        county = TaxJurisdiction.objects.create(
            code="US-CA-SF",
            name="San Francisco",
            jurisdiction_type="COUNTY",
            parent=state
        )
        
        # Test parent-child relationships
        assert state.parent == country
        assert county.parent == state
        
        # Test MPTT specific fields
        assert county.level > state.level
        assert state.level > country.level
        assert county in state.get_descendants()
        assert state in country.get_descendants()
        assert county in country.get_descendants()
        
    def test_string_representation(self):
        """Test the string representation of TaxJurisdiction."""
        jurisdiction = TaxJurisdiction.objects.create(
            code="US",
            name="United States",
            jurisdiction_type="COUNTRY"
        )
        
        assert str(jurisdiction) == "United States"
        
    def test_inheritance(self):
        """Test that TaxJurisdiction inherits expected base classes."""
        from core.models import Timestamped, Auditable
        
        jurisdiction = TaxJurisdiction.objects.create(
            code="US",
            name="United States",
            jurisdiction_type="COUNTRY"
        )
        
        # Check model inheritance
        assert isinstance(jurisdiction, Timestamped)
        assert isinstance(jurisdiction, Auditable)
        assert isinstance(jurisdiction, MPTTModel)
        
        # Check timestamp fields exist and are properly set
        assert jurisdiction.created_at is not None
        assert jurisdiction.updated_at is not None
        assert jurisdiction.created_at <= now()
        assert jurisdiction.updated_at <= now()


@pytest.mark.django_db
class TestTaxCategory:
    """Tests for the TaxCategory model."""
    
    def test_create_tax_category(self):
        """Test creation of TaxCategory with required fields."""
        from api.v1.base_models.common.taxes.models import TaxCategory
        
        category = TaxCategory.objects.create(
            code="GST",
            name="Goods and Services Tax"
        )
        
        assert category.code == "GST"
        assert category.name == "Goods and Services Tax"
        assert category.description is None  # Default value check
        assert category.is_active is True  # Default value check
        
    def test_tax_category_unique_code(self):
        """Test that TaxCategory code must be unique."""
        from api.v1.base_models.common.taxes.models import TaxCategory
        
        TaxCategory.objects.create(
            code="GST",
            name="Goods and Services Tax"
        )
        
        with pytest.raises(IntegrityError):
            TaxCategory.objects.create(
                code="GST",  # Duplicate code
                name="General Sales Tax"
            )
    
    def test_string_representation(self):
        """Test the string representation of TaxCategory."""
        from api.v1.base_models.common.taxes.models import TaxCategory
        
        category = TaxCategory.objects.create(
            code="GST",
            name="Goods and Services Tax"
        )
        
        assert str(category) == "Goods and Services Tax"
        
    def test_inheritance(self):
        """Test that TaxCategory inherits expected base classes."""
        from core.models import Timestamped, Auditable
        from api.v1.base_models.common.taxes.models import TaxCategory
        
        category = TaxCategory.objects.create(
            code="GST",
            name="Goods and Services Tax"
        )
        
        # Check model inheritance
        assert isinstance(category, Timestamped)
        assert isinstance(category, Auditable)
        
        # Check timestamp fields exist and are properly set
        assert category.created_at is not None
        assert category.updated_at is not None
        assert category.created_at <= now()
        assert category.updated_at <= now() 


@pytest.mark.django_db
class TestTaxRate:
    """Tests for the TaxRate model."""
    
    def test_create_tax_rate_with_required_fields(self):
        """Test creation of TaxRate with required fields."""
        from api.v1.base_models.common.taxes.models import TaxRate, TaxJurisdiction, TaxType
        
        jurisdiction = TaxJurisdiction.objects.create(
            code="US-CA",
            name="California",
            jurisdiction_type="STATE_PROVINCE"
        )
        
        tax_rate = TaxRate.objects.create(
            jurisdiction=jurisdiction,
            name="California Sales Tax",
            rate=Decimal("0.0725"),
            tax_type=TaxType.SALES
        )
        
        assert tax_rate.jurisdiction == jurisdiction
        assert tax_rate.name == "California Sales Tax"
        assert tax_rate.rate == Decimal("0.0725")
        assert tax_rate.tax_type == TaxType.SALES
        assert tax_rate.tax_category is None  # Optional field
        assert tax_rate.is_compound is False  # Default value
        assert tax_rate.priority == 0  # Default value
        assert tax_rate.valid_from is None  # Optional field
        assert tax_rate.valid_to is None  # Optional field
        assert tax_rate.is_active is True  # Default value
        assert tax_rate.custom_fields == {}  # Default empty dict
    
    def test_tax_rate_with_all_fields(self):
        """Test creation of TaxRate with all fields."""
        from api.v1.base_models.common.taxes.models import TaxRate, TaxJurisdiction, TaxCategory, TaxType
        
        jurisdiction = TaxJurisdiction.objects.create(
            code="US-CA",
            name="California",
            jurisdiction_type="STATE_PROVINCE"
        )
        
        category = TaxCategory.objects.create(
            code="SALES",
            name="Sales Tax"
        )
        
        today = datetime.date.today()
        next_year = today.replace(year=today.year + 1)
        
        tax_rate = TaxRate.objects.create(
            jurisdiction=jurisdiction,
            tax_category=category,
            name="California Sales Tax",
            rate=Decimal("0.0725"),
            tax_type=TaxType.SALES,
            is_compound=True,
            priority=1,
            valid_from=today,
            valid_to=next_year,
            is_active=True,
            custom_fields={"exempt_items": ["food", "medicine"]}
        )
        
        assert tax_rate.jurisdiction == jurisdiction
        assert tax_rate.tax_category == category
        assert tax_rate.name == "California Sales Tax"
        assert tax_rate.rate == Decimal("0.0725")
        assert tax_rate.tax_type == TaxType.SALES
        assert tax_rate.is_compound is True
        assert tax_rate.priority == 1
        assert tax_rate.valid_from == today
        assert tax_rate.valid_to == next_year
        assert tax_rate.is_active is True
        assert tax_rate.custom_fields == {"exempt_items": ["food", "medicine"]}
    
    def test_tax_rate_with_category_relationship(self):
        """Test TaxRate relationship with TaxCategory."""
        from api.v1.base_models.common.taxes.models import TaxRate, TaxJurisdiction, TaxCategory, TaxType
        
        jurisdiction = TaxJurisdiction.objects.create(
            code="US-CA",
            name="California",
            jurisdiction_type="STATE_PROVINCE"
        )
        
        category = TaxCategory.objects.create(
            code="SALES",
            name="Sales Tax"
        )
        
        tax_rate = TaxRate.objects.create(
            jurisdiction=jurisdiction,
            tax_category=category,
            name="California Sales Tax",
            rate=Decimal("0.0725"),
            tax_type=TaxType.SALES
        )
        
        # Test the relationship
        assert tax_rate.tax_category.code == "SALES"
        assert tax_rate.tax_category.name == "Sales Tax"
    
    def test_string_representation(self):
        """Test the string representation of TaxRate."""
        from api.v1.base_models.common.taxes.models import TaxRate, TaxJurisdiction, TaxType
        
        jurisdiction = TaxJurisdiction.objects.create(
            code="US-CA",
            name="California",
            jurisdiction_type="STATE_PROVINCE"
        )
        
        # With name
        tax_rate1 = TaxRate.objects.create(
            jurisdiction=jurisdiction,
            name="California Sales Tax",
            rate=Decimal("0.0725"),
            tax_type=TaxType.SALES
        )
        assert str(tax_rate1) == "California Sales Tax"
        
        # Without name (fallback to jurisdiction.code and rate)
        tax_rate2 = TaxRate.objects.create(
            jurisdiction=jurisdiction,
            name="",
            rate=Decimal("0.0500"),
            tax_type=TaxType.SALES
        )
        assert str(tax_rate2) == "US-CA 5.0%"
    
    def test_inheritance(self):
        """Test that TaxRate inherits expected base classes."""
        from core.models import Timestamped, Auditable
        from api.v1.base_models.common.taxes.models import TaxRate, TaxJurisdiction, TaxType
        
        jurisdiction = TaxJurisdiction.objects.create(
            code="US-CA",
            name="California",
            jurisdiction_type="STATE_PROVINCE"
        )
        
        tax_rate = TaxRate.objects.create(
            jurisdiction=jurisdiction,
            name="California Sales Tax",
            rate=Decimal("0.0725"),
            tax_type=TaxType.SALES
        )
        
        # Check model inheritance
        assert isinstance(tax_rate, Timestamped)
        assert isinstance(tax_rate, Auditable)
        
        # Check timestamp fields exist and are properly set
        assert tax_rate.created_at is not None
        assert tax_rate.updated_at is not None
        assert tax_rate.created_at <= now()
        assert tax_rate.updated_at <= now()
    
    def test_decimal_field_precision(self):
        """Test that rate field stores decimal values with proper precision."""
        from api.v1.base_models.common.taxes.models import TaxRate, TaxJurisdiction, TaxType
        
        jurisdiction = TaxJurisdiction.objects.create(
            code="US-CA",
            name="California",
            jurisdiction_type="STATE_PROVINCE"
        )
        
        # Test with various decimal values
        test_rates = [
            ("0.0725", "0.0725"),  # Standard rate
            ("0.10", "0.1"),       # Single decimal
            ("0.12345", "0.12345") # Multiple decimals
        ]
        
        for input_rate, expected_rate in test_rates:
            tax_rate = TaxRate.objects.create(
                jurisdiction=jurisdiction,
                name=f"Test Rate {input_rate}",
                rate=Decimal(input_rate),
                tax_type=TaxType.SALES
            )
            
            # Retrieve from DB to verify storage
            refreshed_rate = TaxRate.objects.get(pk=tax_rate.pk)
            assert refreshed_rate.rate == Decimal(expected_rate) 