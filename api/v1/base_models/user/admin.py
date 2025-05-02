from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

from .models import UserProfile, UserProxy

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

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'job_title', 'employee_id', 'phone_number', 'manager')
    search_fields = ('user__username', 'user__email', 'job_title', 'employee_id')
    raw_id_fields = ('user', 'manager')
    readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')

@admin.register(UserProxy)
class UserProxyAdmin(BaseUserAdmin):
    """Admin configuration for the User proxy model."""
    pass 