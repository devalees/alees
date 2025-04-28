import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib import admin

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

    @pytest.mark.django_db
    def test_admin_registration(self):
        """Test that User model is registered with CustomUserAdmin."""
        # Unregister the User model if it's already registered
        if admin.site.is_registered(User):
            admin.site.unregister(User)
        
        # Register with our CustomUserAdmin
        admin.site.register(User, CustomUserAdmin)
        
        # Verify registration
        assert admin.site.is_registered(User)
        assert isinstance(admin.site._registry[User], CustomUserAdmin) 