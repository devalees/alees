import pytest
from django.contrib.auth import get_user_model
from api.v1.base_models.user.models import UserProfile
from api.v1.base_models.user.tests.factories import UserFactory, UserProfileFactory
from api.v1.base_models.organization.tests.factories import OrganizationFactory
from api.v1.base_models.organization.models import OrganizationMembership

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

    @pytest.fixture
    def organization(self):
        """Create a test organization"""
        return OrganizationFactory()

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

    def test_str_representation(self):
        """Test the string representation of UserProfile."""
        user = UserFactory(username='testuser')
        profile = user.profile  # Profile is auto-created by signal
        assert str(profile) == 'testuser'

    def test_get_organizations_no_memberships(self, user):
        """Test get_organizations() returns empty queryset when user has no memberships"""
        organizations = user.get_organizations()
        assert organizations.count() == 0

    def test_get_organizations_one_active_membership(self, user, organization):
        """Test get_organizations() returns organization when user has one active membership"""
        OrganizationMembership.objects.create(
            user=user,
            organization=organization,
            role=None,  # Role is optional
            is_active=True
        )
        organizations = user.get_organizations()
        assert organizations.count() == 1
        assert organization in organizations

    def test_get_organizations_multiple_active_memberships(self, user):
        """Test get_organizations() returns all organizations when user has multiple active memberships"""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        OrganizationMembership.objects.create(user=user, organization=org1, is_active=True)
        OrganizationMembership.objects.create(user=user, organization=org2, is_active=True)
        
        organizations = user.get_organizations()
        assert organizations.count() == 2
        assert org1 in organizations
        assert org2 in organizations

    def test_get_organizations_only_active_memberships(self, user, organization):
        """Test get_organizations() only returns organizations with active memberships"""
        # Create an active membership
        OrganizationMembership.objects.create(
            user=user,
            organization=organization,
            is_active=True
        )
        
        # Create an inactive membership
        org2 = OrganizationFactory()
        OrganizationMembership.objects.create(
            user=user,
            organization=org2,
            is_active=False
        )
        
        organizations = user.get_organizations()
        assert organizations.count() == 1
        assert organization in organizations
        assert org2 not in organizations 