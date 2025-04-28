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

    def test_profile_auto_created(self, user):
        """A UserProfile instance is automatically created when a User is created"""
        assert hasattr(user, 'profile')
        assert isinstance(user.profile, UserProfile)
        assert user.profile.pk is not None

    def test_str_returns_username(self, user):
        """The __str__ method returns user.username"""
        assert str(user.profile) == user.username

    def test_has_timestamped_auditable_fields(self, user):
        """Inherited Timestamped/Auditable fields exist"""
        profile = user.profile
        assert hasattr(profile, 'created_at')
        assert hasattr(profile, 'updated_at')
        assert hasattr(profile, 'created_by')
        assert hasattr(profile, 'updated_by')

    def test_profile_picture_is_nullable(self, user):
        """profile_picture field exists and is nullable"""
        profile = user.profile
        assert hasattr(profile, 'profile_picture')
        assert profile.profile_picture is None

    def test_no_primary_organization(self, user):
        """No primary_organization field exists"""
        profile = user.profile
        assert not hasattr(profile, 'primary_organization') 