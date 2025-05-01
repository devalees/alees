from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
import pytest

from api.v1.base_models.organization.models import Organization, OrganizationType
from api.v1.base_models.organization.tests.factories import (
    OrganizationFactory,
    OrganizationTypeFactory,
    ContactFactory,
    AddressFactory,
    CurrencyFactory,
)
from api.v1.base_models.user.tests.factories import UserFactory

def get_permission(model, codename):
    content_type = ContentType.objects.get_for_model(model)
    return Permission.objects.get(content_type=content_type, codename=codename)

class OrganizationTypeViewSetTests(APITestCase):
    def setUp(self):
        self.org_type = OrganizationTypeFactory()
        self.list_url = reverse('v1:base_models:organization:organizationtype-list')
        self.detail_url = reverse('v1:base_models:organization:organizationtype-detail', kwargs={'name': self.org_type.name})

    def test_list_endpoint(self):
        """Test GET /api/v1/organization/types/ endpoint"""
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
        """Test GET /api/v1/organization/types/{name}/ endpoint"""
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

class OrganizationViewSetTests(APITestCase):
    def setUp(self):
        self.org_type = OrganizationTypeFactory()
        self.contact = ContactFactory()
        self.address = AddressFactory()
        self.currency = CurrencyFactory()
        self.parent_org = OrganizationFactory()
        self.organization = OrganizationFactory(
            organization_type=self.org_type,
            primary_contact=self.contact,
            primary_address=self.address,
            currency=self.currency,
            parent=self.parent_org
        )
        self.list_url = reverse('v1:base_models:organization:organization-list')
        self.detail_url = reverse('v1:base_models:organization:organization-detail', kwargs={'pk': self.organization.id})
        
        # Create and authenticate user
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_list_with_filters(self):
        """Test LIST endpoint with various filters"""
        # Add view permission
        self.user.user_permissions.add(get_permission(Organization, 'view_organization'))

        # Create test data
        active_org = OrganizationFactory(status='active')
        inactive_org = OrganizationFactory(status='inactive')
        tagged_org = OrganizationFactory()
        tagged_org.tags.add('test-tag')

        # Test filter by type
        response = self.client.get(f"{self.list_url}?organization_type={self.org_type.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.organization.id)

        # Test filter by status
        response = self.client.get(f"{self.list_url}?status=active")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(org['id'] == active_org.id for org in response.data['results']))

        # Test filter by parent
        response = self.client.get(f"{self.list_url}?parent={self.parent_org.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.organization.id)

        # Test filter by tags
        response = self.client.get(f"{self.list_url}?tags=test-tag")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(org['id'] == tagged_org.id for org in response.data['results']))

    def test_create_organization(self):
        """Test CREATE endpoint with valid and invalid data"""
        # Add create permission
        self.user.user_permissions.add(get_permission(Organization, 'add_organization'))

        # Get initial count
        initial_count = Organization.objects.count()

        data = {
            'name': 'New Organization',
            'code': 'NEW001',
            'organization_type': self.org_type.id,
            'status': 'active',
            'primary_contact': self.contact.id,
            'primary_address': self.address.id,
            'currency': self.currency.code,
            'parent': self.parent_org.id,
            'timezone': 'UTC',
            'language': 'en'
        }

        # Test valid creation
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Organization.objects.count(), initial_count + 1)

        # Test invalid data
        invalid_data = data.copy()
        invalid_data['code'] = ''  # Required field
        response = self.client.post(self.list_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_with_nullable_fields(self):
        """Test creating organization with nullable fields"""
        # Add create permission
        self.user.user_permissions.add(get_permission(Organization, 'add_organization'))

        data = {
            'name': 'Null Fields Org',
            'code': 'NULL001',
            'organization_type': self.org_type.id,
            'status': 'active',
            'primary_contact': None,
            'primary_address': None,
            'currency': None,
            'parent': None,
            'timezone': 'UTC',
            'language': 'en'
        }

        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        org = Organization.objects.get(code='NULL001')
        self.assertIsNone(org.primary_contact)
        self.assertIsNone(org.primary_address)
        self.assertIsNone(org.currency)
        self.assertIsNone(org.parent)

    def test_retrieve_organization(self):
        """Test RETRIEVE endpoint"""
        # Add view permission
        self.user.user_permissions.add(get_permission(Organization, 'view_organization'))

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.organization.id)
        self.assertEqual(response.data['name'], self.organization.name)

    def test_update_organization(self):
        """Test UPDATE endpoint"""
        # Add change permission
        self.user.user_permissions.add(get_permission(Organization, 'change_organization'))

        data = {
            'name': 'Updated Organization',
            'code': self.organization.code,
            'organization_type': self.org_type.id,
            'status': 'inactive',
            'primary_contact': self.contact.id,
            'primary_address': self.address.id,
            'currency': self.currency.code,
            'parent': self.parent_org.id,
            'timezone': 'UTC',
            'language': 'en'
        }

        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, 'Updated Organization')
        self.assertEqual(self.organization.status, 'inactive')

    def test_patch_organization(self):
        """Test PATCH endpoint"""
        # Add change permission
        self.user.user_permissions.add(get_permission(Organization, 'change_organization'))

        data = {
            'name': 'Patched Organization',
            'status': 'inactive'
        }

        response = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.name, 'Patched Organization')
        self.assertEqual(self.organization.status, 'inactive')

    def test_delete_organization(self):
        """Test DELETE endpoint"""
        # Add delete permission
        self.user.user_permissions.add(get_permission(Organization, 'delete_organization'))

        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Organization.objects.filter(id=self.organization.id).exists())

    def test_hierarchy_actions(self):
        """Test hierarchy-related actions"""
        # Add view permission
        self.user.user_permissions.add(get_permission(Organization, 'view_organization'))

        # Create a hierarchy of organizations
        child_org = OrganizationFactory(parent=self.organization)
        grandchild_org = OrganizationFactory(parent=child_org)

        # Test descendants endpoint
        response = self.client.get(f"{self.detail_url}descendants/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # child and grandchild
        descendant_ids = {org['id'] for org in response.data}
        self.assertEqual(descendant_ids, {child_org.id, grandchild_org.id})

        # Test ancestors endpoint
        response = self.client.get(f"{self.detail_url}ancestors/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # parent only
        self.assertEqual(response.data[0]['id'], self.parent_org.id)

    def test_metadata_and_custom_fields(self):
        """Test metadata and custom fields handling"""
        # Add create permission
        self.user.user_permissions.add(get_permission(Organization, 'add_organization'))

        data = {
            'name': 'Metadata Org',
            'code': 'META001',
            'organization_type': self.org_type.id,
            'status': 'active',
            'metadata': {
                'key1': 'value1',
                'key2': 'value2'
            },
            'custom_fields': {
                'field1': 'value1',
                'field2': 'value2'
            }
        }

        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        org = Organization.objects.get(code='META001')
        self.assertEqual(org.metadata, data['metadata'])
        self.assertEqual(org.custom_fields, data['custom_fields'])

    def test_tag_operations(self):
        """Test tag-related operations"""
        # Add create and change permissions
        self.user.user_permissions.add(get_permission(Organization, 'add_organization'))
        self.user.user_permissions.add(get_permission(Organization, 'change_organization'))

        # Create organization with tags
        data = {
            'name': 'Tagged Org',
            'code': 'TAG001',
            'organization_type': self.org_type.id,
            'status': 'active',
            'tags': ['tag1', 'tag2']
        }

        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        org = Organization.objects.get(code='TAG001')
        self.assertEqual(set(org.tags.names()), {'tag1', 'tag2'})

        # Update tags
        data = {'tags': ['tag3', 'tag4']}
        response = self.client.patch(
            reverse('v1:base_models:organization:organization-detail', kwargs={'pk': org.id}),
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        org.refresh_from_db()
        self.assertEqual(set(org.tags.names()), {'tag3', 'tag4'})

@pytest.mark.django_db
class TestOrganizationViewSet:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def user(self):
        return UserFactory()

    @pytest.fixture
    def org_type(self):
        return OrganizationTypeFactory()

    @pytest.fixture
    def contact(self):
        return ContactFactory()

    @pytest.fixture
    def address(self):
        return AddressFactory()

    @pytest.fixture
    def currency(self):
        return CurrencyFactory()

    @pytest.fixture
    def parent_org(self):
        return OrganizationFactory()

    @pytest.fixture
    def organization(self, org_type, contact, address, currency, parent_org):
        return OrganizationFactory(
            organization_type=org_type,
            primary_contact=contact,
            primary_address=address,
            currency=currency,
            parent=parent_org
        )

    @pytest.fixture
    def list_url(self):
        return reverse('v1:base_models:organization:organization-list')

    @pytest.fixture
    def detail_url(self, organization):
        return reverse('v1:base_models:organization:organization-detail', kwargs={'pk': organization.id})

    def test_list_with_filters(self, api_client, list_url, organization, org_type, parent_org, user):
        """Test LIST endpoint with various filters"""
        # Add view permission and authenticate
        user.user_permissions.add(get_permission(Organization, 'view_organization'))
        api_client.force_authenticate(user=user)

        # Create test data
        active_org = OrganizationFactory(status='active')
        inactive_org = OrganizationFactory(status='inactive')
        tagged_org = OrganizationFactory()
        tagged_org.tags.add('test-tag')

        # Test filter by type
        response = api_client.get(f"{list_url}?organization_type={org_type.id}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == organization.id

        # Test filter by status
        response = api_client.get(f"{list_url}?status=active")
        assert response.status_code == status.HTTP_200_OK
        assert any(org['id'] == active_org.id for org in response.data['results'])

        # Test filter by parent
        response = api_client.get(f"{list_url}?parent={parent_org.id}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == organization.id

        # Test filter by tags
        response = api_client.get(f"{list_url}?tags=test-tag")
        assert response.status_code == status.HTTP_200_OK
        assert any(org['id'] == tagged_org.id for org in response.data['results'])

    def test_create_organization(self, api_client, list_url, org_type, contact, address, currency, parent_org, user):
        """Test CREATE endpoint with valid and invalid data"""
        # Add create permission and authenticate
        user.user_permissions.add(get_permission(Organization, 'add_organization'))
        api_client.force_authenticate(user=user)

        # Get initial count
        initial_count = Organization.objects.count()

        data = {
            'name': 'New Organization',
            'code': 'NEW001',
            'organization_type': org_type.id,
            'status': 'active',
            'primary_contact': contact.id,
            'primary_address': address.id,
            'currency': currency.code,
            'parent': parent_org.id,
            'timezone': 'UTC',
            'language': 'en'
        }

        # Test valid creation
        response = api_client.post(list_url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Organization.objects.count() == initial_count + 1

        # Test invalid data
        invalid_data = data.copy()
        invalid_data['code'] = ''  # Required field
        response = api_client.post(list_url, invalid_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_with_nullable_fields(self, api_client, list_url, org_type, user):
        """Test creating organization with nullable fields"""
        # Add create permission and authenticate
        user.user_permissions.add(get_permission(Organization, 'add_organization'))
        api_client.force_authenticate(user=user)

        data = {
            'name': 'Null Fields Org',
            'code': 'NULL001',
            'organization_type': org_type.id,
            'status': 'active',
            'primary_contact': None,
            'primary_address': None,
            'currency': None,
            'parent': None,
            'timezone': 'UTC',
            'language': 'en'
        }

        response = api_client.post(list_url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        org = Organization.objects.get(code='NULL001')
        assert org.primary_contact is None
        assert org.primary_address is None
        assert org.currency is None
        assert org.parent is None

    def test_retrieve_organization(self, api_client, detail_url, organization, user):
        """Test RETRIEVE endpoint"""
        # Add view permission and authenticate
        user.user_permissions.add(get_permission(Organization, 'view_organization'))
        api_client.force_authenticate(user=user)

        response = api_client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == organization.id
        assert response.data['name'] == organization.name

    def test_update_organization(self, api_client, detail_url, organization, org_type, contact, address, currency, parent_org, user):
        """Test UPDATE endpoint"""
        # Add change permission and authenticate
        user.user_permissions.add(get_permission(Organization, 'change_organization'))
        api_client.force_authenticate(user=user)

        data = {
            'name': 'Updated Organization',
            'code': organization.code,
            'organization_type': org_type.id,
            'status': 'inactive',
            'primary_contact': contact.id,
            'primary_address': address.id,
            'currency': currency.code,
            'parent': parent_org.id,
            'timezone': 'UTC',
            'language': 'en'
        }

        response = api_client.put(detail_url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        organization.refresh_from_db()
        assert organization.name == 'Updated Organization'
        assert organization.status == 'inactive'

    def test_patch_organization(self, api_client, detail_url, organization, user):
        """Test PATCH endpoint"""
        # Add change permission and authenticate
        user.user_permissions.add(get_permission(Organization, 'change_organization'))
        api_client.force_authenticate(user=user)

        data = {
            'name': 'Patched Organization',
            'status': 'inactive'
        }

        response = api_client.patch(detail_url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        organization.refresh_from_db()
        assert organization.name == 'Patched Organization'
        assert organization.status == 'inactive'

    def test_delete_organization(self, api_client, detail_url, organization, user):
        """Test DELETE endpoint"""
        # Add delete permission and authenticate
        user.user_permissions.add(get_permission(Organization, 'delete_organization'))
        api_client.force_authenticate(user=user)

        response = api_client.delete(detail_url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Organization.objects.filter(id=organization.id).exists()

    def test_hierarchy_actions(self, api_client, detail_url, organization, user):
        """Test hierarchy-related actions"""
        # Add view permission and authenticate
        user.user_permissions.add(get_permission(Organization, 'view_organization'))
        api_client.force_authenticate(user=user)

        # Create a hierarchy of organizations
        child_org = OrganizationFactory(parent=organization)
        grandchild_org = OrganizationFactory(parent=child_org)

        # Test descendants endpoint
        response = api_client.get(f"{detail_url}descendants/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2  # child and grandchild
        descendant_ids = {org['id'] for org in response.data}
        assert descendant_ids == {child_org.id, grandchild_org.id}

        # Test ancestors endpoint
        response = api_client.get(f"{detail_url}ancestors/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1  # parent only
        assert response.data[0]['id'] == organization.parent.id

    def test_metadata_and_custom_fields(self, api_client, list_url, org_type, user):
        """Test metadata and custom fields handling"""
        # Add create permission and authenticate
        user.user_permissions.add(get_permission(Organization, 'add_organization'))
        api_client.force_authenticate(user=user)

        data = {
            'name': 'Metadata Org',
            'code': 'META001',
            'organization_type': org_type.id,
            'status': 'active',
            'metadata': {
                'key1': 'value1',
                'key2': 'value2'
            },
            'custom_fields': {
                'field1': 'value1',
                'field2': 'value2'
            }
        }

        response = api_client.post(list_url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        org = Organization.objects.get(code='META001')
        assert org.metadata == data['metadata']
        assert org.custom_fields == data['custom_fields']

    def test_tag_operations(self, api_client, list_url, org_type, user):
        """Test tag-related operations"""
        # Add create and change permissions and authenticate
        user.user_permissions.add(get_permission(Organization, 'add_organization'))
        user.user_permissions.add(get_permission(Organization, 'change_organization'))
        api_client.force_authenticate(user=user)

        # Create organization with tags
        data = {
            'name': 'Tagged Org',
            'code': 'TAG001',
            'organization_type': org_type.id,
            'status': 'active',
            'tags': ['tag1', 'tag2']
        }

        response = api_client.post(list_url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        org = Organization.objects.get(code='TAG001')
        assert set(org.tags.names()) == {'tag1', 'tag2'}

        # Update tags
        data = {'tags': ['tag3', 'tag4']}
        response = api_client.patch(
            reverse('v1:base_models:organization:organization-detail', kwargs={'pk': org.id}),
            data,
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        org.refresh_from_db()
        assert set(org.tags.names()) == {'tag3', 'tag4'} 