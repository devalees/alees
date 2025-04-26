from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ..factories import OrganizationTypeFactory

class OrganizationTypeViewSetTests(APITestCase):
    def setUp(self):
        self.org_type = OrganizationTypeFactory()
        self.list_url = '/api/v1/organization/organization-types/'
        self.detail_url = f'/api/v1/organization/organization-types/{self.org_type.name}/'

    def test_unauthenticated_access(self):
        """Test that unauthenticated users can read organization types"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], self.org_type.name)
        self.assertEqual(response.data[0]['description'], self.org_type.description)

    def test_authenticated_access(self):
        """Test that authenticated users can read organization types"""
        # TODO: Add authentication once user model is implemented
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], self.org_type.name)
        self.assertEqual(response.data[0]['description'], self.org_type.description)

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