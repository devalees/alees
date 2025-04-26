from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone
from crum import impersonate
from api.v1.base_models.organization.models import OrganizationType

User = get_user_model()

class TestOrganizationType(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.org_type_data = {
            'name': 'Test Organization Type',
            'description': 'Test Description'
        }

    def test_create_organization_type(self):
        """Test creating an organization type with valid data."""
        with impersonate(self.user):
            org_type = OrganizationType.objects.create(**self.org_type_data)

        self.assertEqual(org_type.name, self.org_type_data['name'])
        self.assertEqual(org_type.description, self.org_type_data['description'])
        self.assertEqual(org_type.created_by, self.user)
        self.assertEqual(org_type.updated_by, self.user)
        self.assertIsNotNone(org_type.created_at)
        self.assertIsNotNone(org_type.updated_at)

    def test_unique_name_constraint(self):
        """Test that organization type names must be unique."""
        with impersonate(self.user):
            OrganizationType.objects.create(**self.org_type_data)
            with self.assertRaises(IntegrityError):
                OrganizationType.objects.create(**self.org_type_data)

    def test_string_representation(self):
        """Test the string representation of the organization type."""
        with impersonate(self.user):
            org_type = OrganizationType.objects.create(**self.org_type_data)
        self.assertEqual(str(org_type), self.org_type_data['name'])

    def test_timestamps_auto_update(self):
        """Test that updated_at is automatically updated on save."""
        with impersonate(self.user):
            org_type = OrganizationType.objects.create(**self.org_type_data)
            initial_updated_at = org_type.updated_at
            
            # Wait a small amount of time to ensure the timestamp will be different
            timezone.now()
            
            org_type.description = 'Updated Description'
            org_type.save()
            
            self.assertNotEqual(org_type.updated_at, initial_updated_at)
            self.assertEqual(org_type.created_by, self.user)
            self.assertEqual(org_type.updated_by, self.user)

    def test_blank_description(self):
        """Test that description field can be blank."""
        data = self.org_type_data.copy()
        data['description'] = ''
        
        with impersonate(self.user):
            org_type = OrganizationType.objects.create(**data)
        
        self.assertEqual(org_type.description, '')
        self.assertTrue(isinstance(org_type, OrganizationType)) 