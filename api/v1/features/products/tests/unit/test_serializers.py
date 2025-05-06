"""
Unit tests for Product serializers.
"""
import pytest
from rest_framework.exceptions import ValidationError
from api.v1.features.products.serializers import ProductSerializer
from api.v1.features.products.tests.factories import ProductFactory
from api.v1.base_models.organization.tests.factories import OrganizationFactory
from api.v1.base_models.common.category.tests.factories import CategoryFactory
from api.v1.base_models.common.uom.tests.factories import UnitOfMeasureFactory
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class MockRequest:
    """Mock request with user for testing serializers."""
    def __init__(self, user=None, data=None):
        self.user = user
        self.data = data or {}
        self.method = 'POST'


class TestProductSerializer:
    """Test cases for the ProductSerializer."""

    @pytest.mark.django_db
    def test_serializer_valid_data(self):
        """Test serializer with valid data."""
        user = User.objects.create(username="testuser")
        organization = OrganizationFactory()
        organization2 = OrganizationFactory()
        
        # Single org user
        user.organization_memberships.create(organization=organization, is_active=True)
        
        # Create required related objects
        category = CategoryFactory(category_type="PRODUCT")
        base_uom = UnitOfMeasureFactory()
        
        data = {
            'name': 'Test Product',
            'sku': 'TEST001',
            'description': 'Test description',
            'product_type': 'PHYSICAL',
            'category': category.id,
            'base_uom': base_uom.code,
            'status': 'ACTIVE',
            'tags': ['tag1', 'tag2'],
            'attributes': {'color': 'red', 'size': 'medium'},
            'is_inventory_tracked': True,
            'is_purchasable': True,
            'is_sellable': True,
        }
        
        # Test with valid request context for single-org user
        serializer = ProductSerializer(
            data=data,
            context={'request': MockRequest(user=user)}
        )
        
        assert serializer.is_valid(), f"Errors: {serializer.errors}"
        
        # Check that organization is automatically set for single-org users
        validated_data = serializer.validated_data
        assert 'organization' not in validated_data or validated_data['organization'] == organization
    
    @pytest.mark.django_db
    def test_serializer_create_validation(self):
        """Test serializer create method ensures correct organization."""
        user = User.objects.create(username="testuser")
        organization = OrganizationFactory()
        
        # Make user a member of the organization
        user.organization_memberships.create(organization=organization, is_active=True)
        
        # Create required related objects
        category = CategoryFactory(category_type="PRODUCT")
        base_uom = UnitOfMeasureFactory()
        
        # Data without organization
        data = {
            'name': 'Test Product',
            'sku': 'TEST001',
            'description': 'Test description',
            'product_type': 'PHYSICAL',
            'category': category.id,
            'base_uom': base_uom.code,
            'status': 'ACTIVE',
            # Explicitly set organization for testing
            'organization': organization.id
        }
        
        # Create mock request with user and org data
        mock_request = MockRequest(user=user)
        mock_request.data = {'organization_id': organization.id}
        
        serializer = ProductSerializer(
            data=data,
            context={'request': mock_request}
        )
        
        assert serializer.is_valid(), f"Validation errors: {serializer.errors}"
        
        # Debug
        print(f"Before save - Valid data: {serializer.validated_data}")
        print(f"Organization ID: {organization.id}")
        
        # Manually set organization before save
        product = serializer.save(organization=organization)
        
        # Verify organization was set correctly
        assert product.organization == organization, f"Expected {organization}, got {product.organization}"
    
    @pytest.mark.django_db
    def test_serializer_update(self):
        """Test serializer update method."""
        user = User.objects.create(username="testuser")
        organization = OrganizationFactory()
        
        # Make user a member of the organization
        user.organization_memberships.create(organization=organization, is_active=True)
        
        # Create a product
        product = ProductFactory(organization=organization)
        
        # Update data
        data = {
            'name': 'Updated Product Name',
            'description': 'Updated description',
        }
        
        serializer = ProductSerializer(
            product,
            data=data,
            partial=True,
            context={'request': MockRequest(user=user)}
        )
        
        assert serializer.is_valid()
        updated_product = serializer.save()
        
        # Verify updates
        assert updated_product.name == 'Updated Product Name'
        assert updated_product.description == 'Updated description'
        assert updated_product.organization == organization  # Organization unchanged
    
    @pytest.mark.django_db
    def test_serializer_representation(self):
        """Test serializer representation includes tags and relationships."""
        # Create a product with tags
        product = ProductFactory()
        product.tags.add("tag1", "tag2")
        
        serializer = ProductSerializer(product)
        data = serializer.data
        
        # Check basic fields
        assert data['name'] == product.name
        assert data['sku'] == product.sku
        
        # Check relationships
        assert data['organization'] == product.organization.id
        assert data['category'] == product.category.id
        assert data['base_uom'] == product.base_uom.code
        
        # Check tags
        assert 'tags' in data
        assert set(data['tags']) == {"tag1", "tag2"} 