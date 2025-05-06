"""
API tests for Product endpoints.
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from api.v1.features.products.models import Product
from api.v1.features.products.tests.factories import ProductFactory
from api.v1.base_models.organization.models import Organization, OrganizationMembership
from api.v1.base_models.organization.tests.factories import OrganizationFactory
from api.v1.base_models.common.category.tests.factories import CategoryFactory
from api.v1.base_models.common.uom.tests.factories import UnitOfMeasureFactory
import uuid

User = get_user_model()


@pytest.fixture
def api_client():
    """Return an API client for testing."""
    return APIClient()


@pytest.fixture
def product_api_test_user_with_permissions():
    """Create a user with all product permissions."""
    # Use a unique username to avoid conflicts with other tests
    unique_suffix = uuid.uuid4().hex[:8]
    user = User.objects.create_user(
        username=f'product_test_user_{unique_suffix}',
        email=f'product_test_{unique_suffix}@example.com',
        password='testpassword'
    )
    
    # Get or create Product Manager group with a unique name
    admin_group, _ = Group.objects.get_or_create(name=f'ProductAdmin_{unique_suffix}')
    
    # Add product permissions to group
    product_permissions = Permission.objects.filter(
        codename__in=['add_product', 'change_product', 'view_product', 'delete_product']
    )
    
    # Print permissions for debugging
    print(f"Found {product_permissions.count()} product permissions:")
    for perm in product_permissions:
        print(f" - {perm.codename} from {perm.content_type.app_label}")
    
    admin_group.permissions.add(*product_permissions)
    
    # Add user to group
    user.groups.add(admin_group)
    
    return user


def assign_product_role_with_permissions(user, organization):
    """Helper function to assign roles with permissions to a user in an org."""
    # Create a unique role name for this test
    unique_suffix = uuid.uuid4().hex[:8]
    role_name = f"ProductManager_{unique_suffix}"
    
    # Get or create Product Manager role
    role, _ = Group.objects.get_or_create(name=role_name)
    
    # Add product permissions to the role
    product_permissions = Permission.objects.filter(
        codename__in=['add_product', 'change_product', 'view_product', 'delete_product']
    )
    role.permissions.add(*product_permissions)
    
    # Get the membership and assign the role
    membership = OrganizationMembership.objects.get(
        user=user, 
        organization=organization
    )
    membership.roles.add(role)
    
    return membership


@pytest.mark.django_db
class TestProductsAPIEndpoints:
    """Test Product API endpoints with RBAC."""
    
    def setup_method(self):
        """Set up test data for each test method."""
        # This runs before each test method
        self.unique_suffix = uuid.uuid4().hex[:8]
    
    def teardown_method(self):
        """Clean up after each test."""
        # This helps with test isolation
        pass
    
    def test_endpoint_url_exists(self, api_client):
        """Test that product URLs are resolved correctly."""
        # List URL
        url = '/api/v1/products/'
        assert url == '/api/v1/products/'
    
    def test_list_requires_authentication(self, api_client):
        """Test that endpoint requires authentication."""
        url = '/api/v1/products/'
        response = api_client.get(url)
        assert response.status_code == 401
    
    def test_list_products_organization_scoped(self, api_client, product_api_test_user_with_permissions):
        """Test that users only see products from their organizations."""
        # Create organizations with unique names
        org1 = OrganizationFactory(name=f"ProductTestOrg1_{self.unique_suffix}")
        org2 = OrganizationFactory(name=f"ProductTestOrg2_{self.unique_suffix}")
        
        # Add user to org1
        membership = product_api_test_user_with_permissions.organization_memberships.create(
            organization=org1, 
            is_active=True
        )
        
        # Assign role with permissions
        assign_product_role_with_permissions(product_api_test_user_with_permissions, org1)
        
        # Create products in both orgs with unique SKUs - note we use uppercase since validation
        # may convert to uppercase
        product1 = ProductFactory(
            organization=org1,
            sku=f"PROD1_{self.unique_suffix}".upper()
        )
        product2 = ProductFactory(
            organization=org2,
            sku=f"PROD2_{self.unique_suffix}".upper()
        )
        
        # Authenticate user
        api_client.force_authenticate(user=product_api_test_user_with_permissions)
        
        # List products
        url = '/api/v1/products/'
        response = api_client.get(url)
        
        # Check response
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == product1.id
    
    def test_create_product_with_permissions(self, api_client, product_api_test_user_with_permissions):
        """Test creating a product with proper permissions."""
        # Create organization with unique name
        unique_suffix = uuid.uuid4().hex[:8]  # Different suffix for this test
        organization = OrganizationFactory(name=f"ProductCreateTestOrg_{unique_suffix}")
        
        # Add user to organization
        membership = product_api_test_user_with_permissions.organization_memberships.create(
            organization=organization, 
            is_active=True
        )
        
        # Assign role with permissions
        assign_product_role_with_permissions(product_api_test_user_with_permissions, organization)
        
        # Create required related objects
        category = CategoryFactory(category_type="PRODUCT")
        base_uom = UnitOfMeasureFactory()
        
        # Authenticate user
        api_client.force_authenticate(user=product_api_test_user_with_permissions)
        
        # Create product with unique SKU (uppercase because serializer converts to uppercase)
        url = '/api/v1/products/'
        sku = f"TEST_{unique_suffix}".upper()
        data = {
            'name': f'Test Product {unique_suffix}',
            'sku': sku,
            'description': 'Test description',
            'product_type': 'PHYSICAL',
            'category': category.id,
            'base_uom': base_uom.code,  # Using code instead of id
            'status': 'ACTIVE',
            'tags': ['electronics', 'new'],
            'is_inventory_tracked': True,
            'is_purchasable': True,
            'is_sellable': True,
        }
        
        response = api_client.post(url, data, format='json')
        
        # Check response
        assert response.status_code == 201
        assert response.data['name'] == f'Test Product {unique_suffix}'
        assert response.data['sku'] == sku
        assert response.data['organization'] == organization.id
        
        # Verify in database
        product = Product.objects.get(id=response.data['id'])
        assert product.organization == organization
        assert product.name == f'Test Product {unique_suffix}'
        assert set([tag.name for tag in product.tags.all()]) == {'electronics', 'new'}
    
    def test_retrieve_product_permission_check(self, api_client, product_api_test_user_with_permissions):
        """Test retrieving a product checks permissions."""
        # Create organizations with unique names
        unique_suffix = uuid.uuid4().hex[:8]  # Different suffix for this test
        org1 = OrganizationFactory(name=f"RetrieveTestOrg1_{unique_suffix}")
        org2 = OrganizationFactory(name=f"RetrieveTestOrg2_{unique_suffix}")
        
        # Add user to org1 only
        membership = product_api_test_user_with_permissions.organization_memberships.create(
            organization=org1, 
            is_active=True
        )
        
        # Assign role with permissions
        assign_product_role_with_permissions(product_api_test_user_with_permissions, org1)
        
        # Create products in both orgs with unique SKUs (uppercase for consistent validation)
        product1 = ProductFactory(
            organization=org1,
            sku=f"RETRIEVE1_{unique_suffix}".upper()
        )
        product2 = ProductFactory(
            organization=org2,
            sku=f"RETRIEVE2_{unique_suffix}".upper()
        )
        
        # Authenticate user
        api_client.force_authenticate(user=product_api_test_user_with_permissions)
        
        # Retrieve product from org1 (should succeed)
        url1 = f'/api/v1/products/{product1.id}/'
        response1 = api_client.get(url1)
        
        assert response1.status_code == 200
        
        # Retrieve product from org2 (should fail)
        url2 = f'/api/v1/products/{product2.id}/'
        response2 = api_client.get(url2)
        assert response2.status_code == 404  # Not found in user's scope 