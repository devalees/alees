from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ..factories import OrganizationTypeFactory
from ...models import OrganizationType

class OrganizationTypeViewSetTests(APITestCase):
    def setUp(self):
        self.org_type = OrganizationTypeFactory()
        self.list_url = '/api/v1/organization/organization-types/'
        self.detail_url = f'/api/v1/organization/organization-types/{self.org_type.name}/'

    def test_list_endpoint(self):
        """Test GET /api/v1/organization-types/ endpoint"""
        # Create multiple organization types
        types = [
            OrganizationTypeFactory(name='Company'),
            OrganizationTypeFactory(name='Department'),
            OrganizationTypeFactory(name='Customer')
        ]
        
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response structure
        self.assertIn('results', response.data)
        self.assertIsInstance(response.data['results'], list)
        
        # Verify all types are present
        returned_names = {item['name'] for item in response.data['results']}
        expected_names = {org_type.name for org_type in types} | {self.org_type.name}
        self.assertEqual(returned_names, expected_names)
        
        # Verify each item has required fields
        for item in response.data['results']:
            self.assertIn('name', item)
            self.assertIn('description', item)
            self.assertIsInstance(item['name'], str)
            self.assertIsInstance(item['description'], str)

    def test_retrieve_endpoint(self):
        """Test GET /api/v1/organization-types/{name}/ endpoint"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response structure
        self.assertEqual(response.data['name'], self.org_type.name)
        self.assertEqual(response.data['description'], self.org_type.description)
        
        # Verify all required fields are present
        self.assertIn('name', response.data)
        self.assertIn('description', response.data)
        self.assertIsInstance(response.data['name'], str)
        self.assertIsInstance(response.data['description'], str)

    def test_queryset_filtering(self):
        """Test that queryset filtering works correctly"""
        # Create a specific type
        specific_type = OrganizationTypeFactory(name='SpecificType')
        
        # Test filtering by name
        response = self.client.get(f"{self.list_url}?name={specific_type.name}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], specific_type.name)

    def test_ordering(self):
        """Test that ordering works correctly"""
        # Create multiple types with different names
        types = [
            OrganizationTypeFactory(name='Zeta'),
            OrganizationTypeFactory(name='Alpha'),
            OrganizationTypeFactory(name='Beta')
        ]
        
        # Test ascending order
        response = self.client.get(f"{self.list_url}?ordering=name")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item['name'] for item in response.data['results']]
        self.assertEqual(names, sorted(names))
        
        # Test descending order
        response = self.client.get(f"{self.list_url}?ordering=-name")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item['name'] for item in response.data['results']]
        self.assertEqual(names, sorted(names, reverse=True))

    def test_unauthenticated_access(self):
        """Test that unauthenticated users can read organization types"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], self.org_type.name)
        self.assertEqual(response.data['results'][0]['description'], self.org_type.description)

    def test_authenticated_access(self):
        """Test that authenticated users can read organization types"""
        # TODO: Add authentication once user model is implemented
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], self.org_type.name)
        self.assertEqual(response.data['results'][0]['description'], self.org_type.description)

    def test_read_only_permissions(self):
        """Test that write operations require authentication"""
        data = {'name': 'New Type', 'description': 'New Description'}
        
        # Test POST - should require authentication
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test PUT - should require authentication
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test PATCH - should require authentication
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test DELETE - should require authentication
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) 