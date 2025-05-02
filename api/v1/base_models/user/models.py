from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import Timestamped, Auditable
from api.v1.base_models.organization.models import Organization
from django.contrib.auth import get_user_model

# Forward reference string for FileStorage model
FILESTORAGE_MODEL = 'common.FileStorage'  # Adjust app_label if FileStorage is elsewhere

class OrganizationMixin:
    """Mixin to add organization-related methods to User model."""
    
    def get_organizations(self):
        """Returns a QuerySet of active Organizations the user is a member of."""
        return Organization.objects.filter(
            memberships__user=self,
            memberships__is_active=True  # Only consider active memberships
        ).distinct()

# Add mixin to User model
User = get_user_model()
if not hasattr(User, 'get_organizations'):
    User.add_to_class('get_organizations', OrganizationMixin.get_organizations)

class UserProfile(Timestamped, Auditable):
    """UserProfile model extending Django User with additional fields"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        primary_key=True,
    )

    # Basic Attributes
    job_title = models.CharField(_("Job Title"), max_length=100, blank=True, null=True)
    employee_id = models.CharField(_("Employee ID"), max_length=50, unique=True, blank=True, null=True)
    phone_number = models.CharField(_("Phone Number"), max_length=30, blank=True, null=True)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Manager"),
        on_delete=models.SET_NULL,
        related_name='direct_reports',
        null=True,
        blank=True
    )
    date_of_birth = models.DateField(_("Date of Birth"), null=True, blank=True)
    employment_type = models.CharField(_("Employment Type"), max_length=50, blank=True, null=True)

    # Profile Picture (Temporarily Nullable - Will be updated when FileStorage is implemented)
    profile_picture = models.CharField(_("Profile Picture"), max_length=255, null=True, blank=True)

    # Preferences
    language = models.CharField(_("Language"), max_length=10, default=settings.LANGUAGE_CODE)
    timezone = models.CharField(_("Timezone"), max_length=60, default=settings.TIME_ZONE)
    notification_preferences = models.JSONField(_("Notification Preferences"), default=dict, blank=True)

    # Custom Fields
    custom_fields = models.JSONField(_("Custom Fields"), default=dict, blank=True)

    def __str__(self):
        return str(self.user.username)

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

class UserProxy(get_user_model()):
    """Proxy model for User that adds organization-related methods."""
    
    class Meta:
        proxy = True
        verbose_name = _("User")
        verbose_name_plural = _("Users") 