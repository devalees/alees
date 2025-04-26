from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from crum import impersonate

from api.v1.base_models.organization.models import OrganizationType

User = get_user_model()


class TestOrganizationType(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='test_password'
        )
        with impersonate(self.user):
            self.org_type = OrganizationType.objects.create(
                name="Test Organization Type",
                description="Test Description"
            )

    def test_organization_type_creation(self):
        """Test that an OrganizationType can be created with all fields."""
        self.assertEqual(self.org_type.name, "Test Organization Type")
        self.assertEqual(self.org_type.description, "Test Description")
        self.assertEqual(self.org_type.created_by, self.user)
        self.assertEqual(self.org_type.updated_by, self.user)
        self.assertIsNotNone(self.org_type.created_at)
        self.assertIsNotNone(self.org_type.updated_at)

    def test_organization_type_str(self):
        """Test the string representation of an OrganizationType."""
        self.assertEqual(str(self.org_type), "Test Organization Type")

    def test_organization_type_unique_name(self):
        """Test that OrganizationType names must be unique."""
        with self.assertRaises(Exception):
            with impersonate(self.user):
                OrganizationType.objects.create(
                    name="Test Organization Type",
                    description="Another Description"
                )

    def test_organization_type_timestamps(self):
        """Test that timestamps are set correctly."""
        now = timezone.now()
        self.assertLessEqual(self.org_type.created_at, now)
        self.assertLessEqual(self.org_type.updated_at, now)

    def test_organization_type_update(self):
        """Test that updating an OrganizationType updates the updated_at timestamp."""
        old_updated_at = self.org_type.updated_at
        with impersonate(self.user):
            self.org_type.description = "Updated Description"
            self.org_type.save()
        self.org_type.refresh_from_db()
        self.assertGreater(self.org_type.updated_at, old_updated_at)
        self.assertEqual(self.org_type.description, "Updated Description") 