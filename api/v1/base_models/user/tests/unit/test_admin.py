import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model

from api.v1.base_models.user.admin import CustomUserAdmin, UserProfileInline
from api.v1.base_models.user.models import UserProfile

User = get_user_model()


class TestUserAdmin:
    """Test cases for User admin implementation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        self.site = AdminSite()
        self.admin = CustomUserAdmin(User, self.site)
        self.inline = UserProfileInline(UserProfile, self.site)

    def test_user_admin_has_profile_inline(self):
        """Test that User admin includes UserProfileInline."""
        assert UserProfileInline in self.admin.inlines

    def test_profile_inline_configuration(self):
        """Test UserProfileInline configuration."""
        assert self.inline.model == UserProfile
        assert not self.inline.can_delete
        assert self.inline.verbose_name_plural == 'Profile'
        assert 'profile_picture' in self.inline.raw_id_fields 