import pytest
from django.contrib.auth import get_user_model
from ..factories import UserFactory, UserProfileFactory

User = get_user_model()

@pytest.mark.django_db
class TestUserFactory:
    def test_user_creation(self):
        user = UserFactory()
        assert user.username is not None
        assert user.email is not None
        assert user.is_active is True
        assert user.check_password('password123') is True
        # Verify profile was auto-created
        assert hasattr(user, 'profile')

@pytest.mark.django_db
class TestUserProfileFactory:
    def test_profile_creation(self):
        """Test that UserProfileFactory creates valid instances"""
        # Create a user without auto-creating a profile
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Delete the auto-created profile
        user.profile.delete()
        
        # Now create a profile using the factory
        profile = UserProfileFactory(user=user)
        assert profile.user == user
        assert profile.job_title is not None
        assert profile.employee_id is not None
        assert profile.phone_number is not None
        assert profile.profile_picture is None  # As specified
        assert profile.language is not None
        assert profile.timezone is not None
        assert isinstance(profile.notification_preferences, dict)
        assert isinstance(profile.custom_fields, dict)

    def test_profile_with_manager(self):
        """Test profile creation with a manager"""
        manager = UserFactory()
        # Create a user without auto-creating a profile
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Delete the auto-created profile
        user.profile.delete()
        
        profile = UserProfileFactory(user=user, manager=manager)
        assert profile.manager == manager

    def test_unique_employee_id(self):
        """Test that employee_ids are unique"""
        # Create users without auto-creating profiles
        user1 = User.objects.create_user(username='user1', password='pass')
        user2 = User.objects.create_user(username='user2', password='pass')
        # Delete the auto-created profiles
        user1.profile.delete()
        user2.profile.delete()
        
        profile1 = UserProfileFactory(user=user1)
        profile2 = UserProfileFactory(user=user2)
        assert profile1.employee_id != profile2.employee_id

    def test_circular_dependency_prevention(self):
        """Test that profile=None in SubFactory prevents circular dependency"""
        # Create a user without auto-creating a profile
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Delete the auto-created profile
        user.profile.delete()
        
        profile = UserProfileFactory(user=user)
        assert profile.user.profile == profile 