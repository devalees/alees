import pytest
from django.contrib.auth import get_user_model
from api.v1.base_models.user.models import UserProfile

User = get_user_model()

@pytest.mark.django_db
class TestUserProfile:
    """Test cases for UserProfile model"""

    @pytest.fixture
    def user(self):
        """Create a test user"""
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_can_create_user_profile(self, user):
        """A UserProfile instance can be created and linked to a User instance"""
        profile = UserProfile.objects.create(user=user)
        assert profile.user == user
        assert profile.pk is not None

    def test_str_returns_username(self, user):
        """The __str__ method returns user.username"""
        profile = UserProfile.objects.create(user=user)
        assert str(profile) == user.username

    def test_has_timestamped_auditable_fields(self, user):
        """Inherited Timestamped/Auditable fields exist"""
        profile = UserProfile.objects.create(user=user)
        assert hasattr(profile, 'created_at')
        assert hasattr(profile, 'updated_at')
        assert hasattr(profile, 'created_by')
        assert hasattr(profile, 'updated_by')

    def test_profile_picture_is_nullable(self, user):
        """profile_picture field exists and is nullable"""
        profile = UserProfile.objects.create(user=user)
        assert hasattr(profile, 'profile_picture')
        assert profile.profile_picture is None

    def test_no_primary_organization(self, user):
        """No primary_organization field exists"""
        profile = UserProfile.objects.create(user=user)
        assert not hasattr(profile, 'primary_organization') 