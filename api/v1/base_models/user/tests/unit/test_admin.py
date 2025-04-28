import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite

from api.v1.base_models.user.admin import CustomUserAdmin, UserProfileInline
from api.v1.base_models.user import admin as user_admin  # Import to trigger registration
from api.v1.base_models.user.models import UserProfile

User = get_user_model()


@pytest.mark.django_db
class TestUserAdmin:
    """Test cases for User admin configuration."""

    def test_user_profile_inline_configuration(self):
        """Test that UserProfileInline is properly configured."""
        inline = UserProfileInline
        assert not inline.can_delete
        assert inline.verbose_name_plural == 'Profile'
        assert inline.raw_id_fields == ('profile_picture',)

    def test_custom_user_admin_configuration(self):
        """Test that CustomUserAdmin is properly configured."""
        admin_class = CustomUserAdmin
        assert UserProfileInline in admin_class.inlines
        assert len(admin_class.inlines) == 1

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