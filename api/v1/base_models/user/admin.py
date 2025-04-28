from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

from .models import UserProfile

User = get_user_model()


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile model."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    raw_id_fields = ('profile_picture',)


class CustomUserAdmin(BaseUserAdmin):
    """Custom User admin that includes UserProfileInline."""
    inlines = (UserProfileInline,)


# Only register if not in test mode
if not admin.site.is_registered(User):
    admin.site.register(User, CustomUserAdmin) 