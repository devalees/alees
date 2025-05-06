import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
import json
from datetime import date, timedelta

from api.v1.base_models.common.taxes.models import TaxJurisdiction, TaxCategory, TaxRate
from api.v1.base_models.common.taxes.tests.factories import (
    TaxJurisdictionFactory, TaxCategoryFactory, TaxRateFactory
)


@pytest.mark.django_db
class TestTaxJurisdictionEndpoint:
    """Test the TaxJurisdiction API endpoint."""
    
    def setup_method(self):
        self.client = APIClient()
        self.url = reverse('v1:base_models:common:taxjurisdiction-list')
        
    def test_unauthorized_access(self):
        """Test that unauthenticated users cannot access the endpoint."""
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_authenticated_read_access(self, django_user_model):
        """Test that authenticated users can read with DjangoModelPermissions."""
        # Create user without specific permissions (but authenticated)
        user = django_user_model.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=user)
        
        # GET is a safe method, so DjangoModelPermissions allows it by default
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        
    def test_authenticated_write_access_denied(self, django_user_model):
        """Test that authenticated users without permissions cannot write."""
        # Create user without specific permissions
        user = django_user_model.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=user)
        
        # POST is not a safe method, so it should be denied
        data = {'code': 'TEST', 'name': 'Test Jurisdiction', 'jurisdiction_type': 'COUNTRY'}
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_authenticated_write_access_with_permission(self, django_user_model):
        """Test that users with permissions can create."""
        # Create user with add permission
        user = django_user_model.objects.create_user(username='permissionuser', password='password')
        content_type = ContentType.objects.get_for_model(TaxJurisdiction)
        permission = Permission.objects.get(
            content_type=content_type,
            codename='add_taxjurisdiction'
        )
        user.user_permissions.add(permission)
        self.client.force_authenticate(user=user)
        
        # Should be able to create with the permission
        data = {'code': 'TEST', 'name': 'Test Jurisdiction', 'jurisdiction_type': 'COUNTRY'}
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_list_with_filtering(self, django_user_model):
        """Test that LIST endpoint supports filtering."""
        # Create test data
        TaxJurisdictionFactory(code='US', name='United States', jurisdiction_type='COUNTRY')
        TaxJurisdictionFactory(code='CA', name='Canada', jurisdiction_type='COUNTRY')
        TaxJurisdictionFactory(code='US-NY', name='New York', jurisdiction_type='STATE_PROVINCE', 
                              parent=TaxJurisdiction.objects.get(code='US'))
        
        # Authenticate user
        user = django_user_model.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=user)
        
        # Test filtering by jurisdiction_type
        response = self.client.get(f"{self.url}?jurisdiction_type=COUNTRY")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        
        # Test filtering by is_active
        response = self.client.get(f"{self.url}?is_active=true")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3
        
        # Test search functionality
        response = self.client.get(f"{self.url}?search=New")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'New York'
        
        # Test ordering
        response = self.client.get(f"{self.url}?ordering=-name")
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'][0]['name'] == 'United States'

    def test_create_with_invalid_data(self, django_user_model):
        """Test creating with invalid data returns appropriate errors."""
        # Create user with add permission
        user = django_user_model.objects.create_user(username='permissionuser', password='password')
        content_type = ContentType.objects.get_for_model(TaxJurisdiction)
        permission = Permission.objects.get(
            content_type=content_type,
            codename='add_taxjurisdiction'
        )
        user.user_permissions.add(permission)
        self.client.force_authenticate(user=user)
        
        # Missing required field
        data = {'name': 'Test Jurisdiction'}  # Missing code and jurisdiction_type
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'code' in response.data
        
        # Invalid jurisdiction_type
        data = {'code': 'TEST', 'name': 'Test Jurisdiction', 'jurisdiction_type': 'INVALID'}
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'jurisdiction_type' in response.data
        
        # Duplicate code (create one first)
        TaxJurisdictionFactory(code='DUPLICATE', name='Duplicate Jurisdiction')
        data = {'code': 'DUPLICATE', 'name': 'Another Jurisdiction', 'jurisdiction_type': 'COUNTRY'}
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'code' in response.data

    def test_retrieve_single_item(self, django_user_model):
        """Test retrieving a single jurisdiction."""
        # Create test data
        jurisdiction = TaxJurisdictionFactory(code='US', name='United States', jurisdiction_type='COUNTRY')
        
        # Authenticate user
        user = django_user_model.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=user)
        
        # Get detail URL
        detail_url = reverse('v1:base_models:common:taxjurisdiction-detail', kwargs={'pk': jurisdiction.code})
        
        # Test retrieval
        response = self.client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['code'] == 'US'
        assert response.data['name'] == 'United States'

    def test_update_item(self, django_user_model):
        """Test updating a jurisdiction."""
        # Create test data
        jurisdiction = TaxJurisdictionFactory(code='US', name='United States', jurisdiction_type='COUNTRY')
        
        # Create user with change permission
        user = django_user_model.objects.create_user(username='permissionuser', password='password')
        content_type = ContentType.objects.get_for_model(TaxJurisdiction)
        permission = Permission.objects.get(
            content_type=content_type,
            codename='change_taxjurisdiction'
        )
        user.user_permissions.add(permission)
        self.client.force_authenticate(user=user)
        
        # Get detail URL
        detail_url = reverse('v1:base_models:common:taxjurisdiction-detail', kwargs={'pk': jurisdiction.code})
        
        # Test PUT update
        data = {'code': 'US', 'name': 'United States of America', 'jurisdiction_type': 'COUNTRY'}
        response = self.client.put(detail_url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'United States of America'
        
        # Test PATCH update
        response = self.client.patch(detail_url, {'is_active': False})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_active'] is False

    def test_delete_item(self, django_user_model):
        """Test deleting a jurisdiction."""
        # Create test data
        jurisdiction = TaxJurisdictionFactory(code='TO-DELETE', name='To Delete', jurisdiction_type='COUNTRY')
        
        # Create user with delete permission
        user = django_user_model.objects.create_user(username='permissionuser', password='password')
        content_type = ContentType.objects.get_for_model(TaxJurisdiction)
        permission = Permission.objects.get(
            content_type=content_type,
            codename='delete_taxjurisdiction'
        )
        user.user_permissions.add(permission)
        self.client.force_authenticate(user=user)
        
        # Get detail URL
        detail_url = reverse('v1:base_models:common:taxjurisdiction-detail', kwargs={'pk': jurisdiction.code})
        
        # Test DELETE
        response = self.client.delete(detail_url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify it's gone
        response = self.client.get(detail_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestTaxCategoryEndpoint:
    """Test the TaxCategory API endpoint."""
    
    def setup_method(self):
        self.client = APIClient()
        self.url = reverse('v1:base_models:common:taxcategory-list')
        
    def test_unauthorized_access(self):
        """Test that unauthenticated users cannot access the endpoint."""
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_authenticated_read_access(self, django_user_model):
        """Test that authenticated users can read with DjangoModelPermissions."""
        # Create user without specific permissions (but authenticated)
        user = django_user_model.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=user)
        
        # GET is a safe method, so DjangoModelPermissions allows it by default
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        
    def test_authenticated_write_access_denied(self, django_user_model):
        """Test that authenticated users without permissions cannot write."""
        # Create user without specific permissions
        user = django_user_model.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=user)
        
        # POST is not a safe method, so it should be denied
        data = {'code': 'TEST', 'name': 'Test Category'}
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_authenticated_write_access_with_permission(self, django_user_model):
        """Test that users with permissions can create."""
        # Create user with add permission
        user = django_user_model.objects.create_user(username='permissionuser', password='password')
        content_type = ContentType.objects.get_for_model(TaxCategory)
        permission = Permission.objects.get(
            content_type=content_type,
            codename='add_taxcategory'
        )
        user.user_permissions.add(permission)
        self.client.force_authenticate(user=user)
        
        # Should be able to create with the permission
        data = {'code': 'TEST', 'name': 'Test Category'}
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_list_with_filtering(self, django_user_model):
        """Test that LIST endpoint supports filtering."""
        # Create test data
        TaxCategoryFactory(code='VAT', name='Value Added Tax', is_active=True)
        TaxCategoryFactory(code='GST', name='Goods and Services Tax', is_active=True)
        TaxCategoryFactory(code='SALES', name='Sales Tax', is_active=False)
        
        # Authenticate user
        user = django_user_model.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=user)
        
        # Test filtering by is_active
        response = self.client.get(f"{self.url}?is_active=true")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        
        # Test search functionality
        response = self.client.get(f"{self.url}?search=Sales")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'Sales Tax'
        
        # Test ordering
        response = self.client.get(f"{self.url}?ordering=code")
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'][0]['code'] == 'GST'

    def test_create_with_invalid_data(self, django_user_model):
        """Test creating with invalid data returns appropriate errors."""
        # Create user with add permission
        user = django_user_model.objects.create_user(username='permissionuser', password='password')
        content_type = ContentType.objects.get_for_model(TaxCategory)
        permission = Permission.objects.get(
            content_type=content_type,
            codename='add_taxcategory'
        )
        user.user_permissions.add(permission)
        self.client.force_authenticate(user=user)
        
        # Missing required field
        data = {'name': 'Test Category'}  # Missing code
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'code' in response.data
        
        # Duplicate code (create one first)
        TaxCategoryFactory(code='DUPLICATE', name='Duplicate Category')
        data = {'code': 'DUPLICATE', 'name': 'Another Category'}
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'code' in response.data

    def test_retrieve_single_item(self, django_user_model):
        """Test retrieving a single category."""
        # Create test data
        category = TaxCategoryFactory(code='VAT', name='Value Added Tax')
        
        # Authenticate user
        user = django_user_model.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=user)
        
        # Get detail URL
        detail_url = reverse('v1:base_models:common:taxcategory-detail', kwargs={'pk': category.id})
        
        # Test retrieval
        response = self.client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['code'] == 'VAT'
        assert response.data['name'] == 'Value Added Tax'

    def test_update_item(self, django_user_model):
        """Test updating a category."""
        # Create test data
        category = TaxCategoryFactory(code='VAT', name='Value Added Tax')
        
        # Create user with change permission
        user = django_user_model.objects.create_user(username='permissionuser', password='password')
        content_type = ContentType.objects.get_for_model(TaxCategory)
        permission = Permission.objects.get(
            content_type=content_type,
            codename='change_taxcategory'
        )
        user.user_permissions.add(permission)
        self.client.force_authenticate(user=user)
        
        # Get detail URL
        detail_url = reverse('v1:base_models:common:taxcategory-detail', kwargs={'pk': category.id})
        
        # Test PUT update
        data = {'code': 'VAT', 'name': 'Value-Added Tax'}
        response = self.client.put(detail_url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Value-Added Tax'
        
        # Test PATCH update
        response = self.client.patch(detail_url, {'description': 'A detailed description'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['description'] == 'A detailed description'

    def test_delete_item(self, django_user_model):
        """Test deleting a category."""
        # Create test data
        category = TaxCategoryFactory(code='TO-DELETE', name='To Delete')
        
        # Create user with delete permission
        user = django_user_model.objects.create_user(username='permissionuser', password='password')
        content_type = ContentType.objects.get_for_model(TaxCategory)
        permission = Permission.objects.get(
            content_type=content_type,
            codename='delete_taxcategory'
        )
        user.user_permissions.add(permission)
        self.client.force_authenticate(user=user)
        
        # Get detail URL
        detail_url = reverse('v1:base_models:common:taxcategory-detail', kwargs={'pk': category.id})
        
        # Test DELETE
        response = self.client.delete(detail_url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify it's gone
        response = self.client.get(detail_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestTaxRateEndpoint:
    """Test the TaxRate API endpoint."""
    
    def setup_method(self):
        self.client = APIClient()
        self.url = reverse('v1:base_models:common:taxrate-list')
        self.jurisdiction = TaxJurisdictionFactory()
        self.category = TaxCategoryFactory()
        
    def test_unauthorized_access(self):
        """Test that unauthenticated users cannot access the endpoint."""
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_authenticated_read_access(self, django_user_model):
        """Test that authenticated users can read with DjangoModelPermissions."""
        # Create user without specific permissions (but authenticated)
        user = django_user_model.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=user)
        
        # GET is a safe method, so DjangoModelPermissions allows it by default
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        
    def test_authenticated_write_access_denied(self, django_user_model):
        """Test that authenticated users without permissions cannot write."""
        # Create user without specific permissions
        user = django_user_model.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=user)
        
        # POST is not a safe method, so it should be denied
        data = {
            'name': 'Test Rate',
            'jurisdiction': self.jurisdiction.code,
            'tax_category': self.category.code,
            'rate': '10.00',
            'tax_type': 'VAT'
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_authenticated_write_access_with_permission(self, django_user_model):
        """Test that users with permissions can create."""
        # Create user with add permission
        user = django_user_model.objects.create_user(username='permissionuser', password='password')
        content_type = ContentType.objects.get_for_model(TaxRate)
        permission = Permission.objects.get(
            content_type=content_type,
            codename='add_taxrate'
        )
        user.user_permissions.add(permission)
        self.client.force_authenticate(user=user)
        
        # Should be able to create with the permission
        data = {
            'name': 'Test Rate',
            'jurisdiction': self.jurisdiction.code,
            'tax_category': self.category.code,
            'rate': '10.00',
            'tax_type': 'VAT'
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_list_with_filtering(self, django_user_model):
        """Test that LIST endpoint supports filtering."""
        # Create test data
        jurisdiction1 = TaxJurisdictionFactory(code='US', name='United States')
        jurisdiction2 = TaxJurisdictionFactory(code='CA', name='Canada')
        category1 = TaxCategoryFactory(code='VAT', name='Value Added Tax')
        category2 = TaxCategoryFactory(code='GST', name='Goods and Services Tax')
        
        TaxRateFactory(name='US VAT', jurisdiction=jurisdiction1, tax_category=category1, 
                      tax_type='VAT', rate=0.05, is_active=True)
        TaxRateFactory(name='CA GST', jurisdiction=jurisdiction2, tax_category=category2, 
                      tax_type='GST', rate=0.07, is_active=True)
        TaxRateFactory(name='US Sales', jurisdiction=jurisdiction1, tax_category=None, 
                      tax_type='SALES', rate=0.06, is_active=False)
        
        # Authenticate user
        user = django_user_model.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=user)
        
        # Test filtering by jurisdiction
        response = self.client.get(f"{self.url}?jurisdiction__code=US")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        
        # Test filtering by tax_category
        response = self.client.get(f"{self.url}?tax_category__code=GST")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'CA GST'
        
        # Test filtering by tax_type
        response = self.client.get(f"{self.url}?tax_type=VAT")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'US VAT'
        
        # Test filtering by is_active
        response = self.client.get(f"{self.url}?is_active=true")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
        
        # Test search functionality
        response = self.client.get(f"{self.url}?search=Sales")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'US Sales'
        
        # Test ordering
        response = self.client.get(f"{self.url}?ordering=-rate")
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'][0]['name'] == 'CA GST'  # Highest rate

    def test_create_with_invalid_data(self, django_user_model):
        """Test creating with invalid data returns appropriate errors."""
        # Create user with add permission
        user = django_user_model.objects.create_user(username='permissionuser', password='password')
        content_type = ContentType.objects.get_for_model(TaxRate)
        permission = Permission.objects.get(
            content_type=content_type,
            codename='add_taxrate'
        )
        user.user_permissions.add(permission)
        self.client.force_authenticate(user=user)
        
        # Missing required field
        data = {
            'name': 'Test Rate',
            'tax_type': 'VAT'
            # Missing jurisdiction and rate
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'jurisdiction' in response.data
        assert 'rate' in response.data
        
        # Invalid tax_type
        data = {
            'name': 'Test Rate',
            'jurisdiction': self.jurisdiction.code,
            'rate': '10.00',
            'tax_type': 'INVALID'
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'tax_type' in response.data
        
        # Negative rate
        data = {
            'name': 'Test Rate',
            'jurisdiction': self.jurisdiction.code,
            'rate': '-5.00',
            'tax_type': 'VAT'
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'rate' in response.data
        
        # Invalid date range (valid_from > valid_to)
        today = date.today()
        yesterday = today - timedelta(days=1)
        data = {
            'name': 'Test Rate',
            'jurisdiction': self.jurisdiction.code,
            'rate': '10.00',
            'tax_type': 'VAT',
            'valid_from': today.isoformat(),
            'valid_to': yesterday.isoformat()
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_single_item(self, django_user_model):
        """Test retrieving a single tax rate."""
        # Create test data
        tax_rate = TaxRateFactory(
            name='Test Rate',
            jurisdiction=self.jurisdiction,
            tax_category=self.category,
            rate=0.15,
            tax_type='VAT'
        )
        
        # Authenticate user
        user = django_user_model.objects.create_user(username='testuser', password='password')
        self.client.force_authenticate(user=user)
        
        # Get detail URL
        detail_url = reverse('v1:base_models:common:taxrate-detail', kwargs={'pk': tax_rate.id})
        
        # Test retrieval
        response = self.client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Test Rate'
        assert float(response.data['rate']) == 0.15
        assert response.data['tax_type'] == 'VAT'

    def test_update_item(self, django_user_model):
        """Test updating a tax rate."""
        # Create test data
        tax_rate = TaxRateFactory(
            name='Test Rate',
            jurisdiction=self.jurisdiction,
            tax_category=self.category,
            rate=0.15,
            tax_type='VAT'
        )
        
        # Create user with change permission
        user = django_user_model.objects.create_user(username='permissionuser', password='password')
        content_type = ContentType.objects.get_for_model(TaxRate)
        permission = Permission.objects.get(
            content_type=content_type,
            codename='change_taxrate'
        )
        user.user_permissions.add(permission)
        self.client.force_authenticate(user=user)
        
        # Get detail URL
        detail_url = reverse('v1:base_models:common:taxrate-detail', kwargs={'pk': tax_rate.id})
        
        # Test PUT update
        data = {
            'name': 'Updated Test Rate',
            'jurisdiction': self.jurisdiction.code,
            'tax_category': self.category.code,
            'rate': '20.00',
            'tax_type': 'VAT'
        }
        response = self.client.put(detail_url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Test Rate'
        assert float(response.data['rate']) == 20.0
        
        # Test PATCH update
        response = self.client.patch(detail_url, {'is_compound': True, 'priority': 5})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_compound'] is True
        assert response.data['priority'] == 5

    def test_custom_fields_update(self, django_user_model):
        """Test updating custom_fields."""
        # Create test data
        tax_rate = TaxRateFactory(
            name='Test Rate',
            jurisdiction=self.jurisdiction,
            tax_category=self.category,
            rate=0.15,
            tax_type='VAT',
            custom_fields={}
        )
        
        # Create user with change permission
        user = django_user_model.objects.create_user(username='permissionuser', password='password')
        content_type = ContentType.objects.get_for_model(TaxRate)
        permission = Permission.objects.get(
            content_type=content_type,
            codename='change_taxrate'
        )
        user.user_permissions.add(permission)
        self.client.force_authenticate(user=user)
        
        # Get detail URL
        detail_url = reverse('v1:base_models:common:taxrate-detail', kwargs={'pk': tax_rate.id})
        
        # Test PATCH update with custom_fields
        custom_fields = {
            'exemption_code': 'EX123',
            'reporting_category': 'STANDARD',
            'notes': 'Test note'
        }
        response = self.client.patch(detail_url, {'custom_fields': custom_fields}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['custom_fields'] == custom_fields

    def test_delete_item(self, django_user_model):
        """Test deleting a tax rate."""
        # Create test data
        tax_rate = TaxRateFactory(
            name='To Delete',
            jurisdiction=self.jurisdiction,
            tax_category=self.category,
            rate=0.15,
            tax_type='VAT'
        )
        
        # Create user with delete permission
        user = django_user_model.objects.create_user(username='permissionuser', password='password')
        content_type = ContentType.objects.get_for_model(TaxRate)
        permission = Permission.objects.get(
            content_type=content_type,
            codename='delete_taxrate'
        )
        user.user_permissions.add(permission)
        self.client.force_authenticate(user=user)
        
        # Get detail URL
        detail_url = reverse('v1:base_models:common:taxrate-detail', kwargs={'pk': tax_rate.id})
        
        # Test DELETE
        response = self.client.delete(detail_url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify it's gone
        response = self.client.get(detail_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND 