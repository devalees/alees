from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth.models import Organization

class TestModels(TestCase):
    def test_get_organizations(self):
        """Test that get_organizations returns all organizations for a user"""
        # Create a user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create some organizations
        org1 = Organization.objects.create(name='Org 1')
        org2 = Organization.objects.create(name='Org 2')
        
        # Add user to organizations
        org1.members.add(user)
        org2.members.add(user)
        
        # Get organizations for user
        organizations = user.get_organizations()
        
        # Check that both organizations are returned
        self.assertEqual(organizations.count(), 2)
        self.assertIn(org1, organizations)
        self.assertIn(org2, organizations) 