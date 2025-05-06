"""
Unit tests for the Product model.
"""
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from api.v1.features.products.models import Product
from api.v1.base_models.organization.tests.factories import OrganizationFactory
from api.v1.base_models.common.category.tests.factories import CategoryFactory
from api.v1.base_models.common.uom.tests.factories import UnitOfMeasureFactory
from taggit.models import Tag

class TestProductModel:
    """Test cases for the Product model."""

    @pytest.mark.django_db
    def test_product_creation_with_required_fields(self):
        """Test Product creation with all required fields."""
        organization = OrganizationFactory()
        category = CategoryFactory(category_type="PRODUCT")
        base_uom = UnitOfMeasureFactory()
        
        product = Product.objects.create(
            name="Test Product",
            sku="TEST001",
            organization=organization,
            product_type="PHYSICAL",
            category=category,
            base_uom=base_uom,
            status="ACTIVE"
        )
        
        assert product.id is not None
        assert product.name == "Test Product"
        assert product.sku == "TEST001"
        assert product.organization == organization
        assert product.product_type == "PHYSICAL"
        assert product.category == category
        assert product.base_uom == base_uom
        assert product.status == "ACTIVE"
        assert product.is_inventory_tracked is False  # Default
        assert product.is_purchasable is False  # Default
        assert product.is_sellable is False  # Default
        assert hasattr(product, 'created_at')  # Timestamped
        assert hasattr(product, 'updated_at')  # Timestamped
    
    @pytest.mark.django_db
    def test_unique_together_organization_sku(self):
        """Test that organization+sku combination must be unique."""
        organization = OrganizationFactory()
        category = CategoryFactory(category_type="PRODUCT")
        base_uom = UnitOfMeasureFactory()
        
        # Create first product
        Product.objects.create(
            name="Test Product 1",
            sku="TEST001",
            organization=organization,
            product_type="PHYSICAL",
            category=category,
            base_uom=base_uom,
            status="ACTIVE"
        )
        
        # Attempt to create second product with same SKU in same organization
        with pytest.raises(IntegrityError):
            Product.objects.create(
                name="Test Product 2",
                sku="TEST001",  # Same SKU
                organization=organization,  # Same organization
                product_type="PHYSICAL",
                category=category,
                base_uom=base_uom,
                status="ACTIVE"
            )
    
    @pytest.mark.django_db
    def test_sku_can_be_reused_across_organizations(self):
        """Test that same SKU can be used in different organizations."""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        category = CategoryFactory(category_type="PRODUCT")
        base_uom = UnitOfMeasureFactory()
        
        # Create product in first organization
        product1 = Product.objects.create(
            name="Test Product Org1",
            sku="TEST001",
            organization=org1,
            product_type="PHYSICAL",
            category=category,
            base_uom=base_uom,
            status="ACTIVE"
        )
        
        # Create product with same SKU in second organization
        product2 = Product.objects.create(
            name="Test Product Org2",
            sku="TEST001",  # Same SKU
            organization=org2,  # Different organization
            product_type="PHYSICAL",
            category=category,
            base_uom=base_uom,
            status="ACTIVE"
        )
        
        assert product1.id != product2.id
        assert product1.sku == product2.sku
        assert product1.organization != product2.organization
    
    @pytest.mark.django_db
    def test_product_string_representation(self):
        """Test the string representation of a Product."""
        organization = OrganizationFactory()
        category = CategoryFactory(category_type="PRODUCT")
        base_uom = UnitOfMeasureFactory()
        
        product = Product.objects.create(
            name="Test Product",
            sku="TEST001",
            organization=organization,
            product_type="PHYSICAL",
            category=category,
            base_uom=base_uom,
            status="ACTIVE"
        )
        
        assert str(product) == "TEST001 - Test Product"
    
    @pytest.mark.django_db
    def test_product_tags(self):
        """Test that tags can be added to a Product."""
        organization = OrganizationFactory()
        category = CategoryFactory(category_type="PRODUCT")
        base_uom = UnitOfMeasureFactory()
        
        product = Product.objects.create(
            name="Test Product",
            sku="TEST001",
            organization=organization,
            product_type="PHYSICAL",
            category=category,
            base_uom=base_uom,
            status="ACTIVE"
        )
        
        # Add tags
        product.tags.add("electronics", "sale", "featured")
        
        # Refresh from DB
        product.refresh_from_db()
        
        assert product.tags.count() == 3
        assert "electronics" in [tag.name for tag in product.tags.all()]
        assert "sale" in [tag.name for tag in product.tags.all()]
        assert "featured" in [tag.name for tag in product.tags.all()]
    
    @pytest.mark.django_db
    def test_organization_scoped_inheritance(self):
        """Test that Product inherits from OrganizationScoped."""
        from core.models import OrganizationScoped
        assert issubclass(Product, OrganizationScoped) 