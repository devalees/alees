from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import Timestamped, Auditable
from mptt.models import MPTTModel, TreeForeignKey
from taggit.managers import TaggableManager
from django.contrib.auth.models import Group
from django.conf import settings
from django.core.exceptions import ValidationError

class OrganizationType(Timestamped, Auditable):
    """
    Model representing different types of organizations in the system.
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text=_("The unique name of the organization type")
    )
    description = models.TextField(
        blank=True,
        help_text=_("Optional description of the organization type")
    )

    class Meta:
        app_label = 'api_v1_organization'
        verbose_name = _("Organization Type")
        verbose_name_plural = _("Organization Types")
        ordering = ['name']

    def __str__(self):
        return self.name


class Organization(Timestamped, Auditable, MPTTModel):
    """
    Model representing an organization unit in the system.
    Supports hierarchical structure and flexible categorization.
    """
    name = models.CharField(
        max_length=255,
        help_text=_("The display name of the organization")
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text=_("Unique identifier/code for the organization")
    )
    organization_type = models.ForeignKey(
        'OrganizationType',
        on_delete=models.PROTECT,
        help_text=_("The type of organization")
    )
    status = models.CharField(
        max_length=20,
        default='active',
        choices=[
            ('active', _('Active')),
            ('inactive', _('Inactive')),
            ('archived', _('Archived'))
        ],
        help_text=_("Current status of the organization")
    )
    parent = TreeForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='children',
        help_text=_("Parent organization in the hierarchy")
    )
    effective_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Date the organization becomes active")
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Date the organization ceases to be active")
    )
    primary_contact = models.ForeignKey(
        'contact.Contact',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_for_organizations',
        help_text=_("Primary contact person for the organization")
    )
    primary_address = models.ForeignKey(
        'address.Address',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_for_organizations',
        help_text=_("Primary address for the organization")
    )
    currency = models.ForeignKey(
        'api_v1_currency.Currency',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text=_("Default operating currency")
    )
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        null=True,
        blank=True,
        help_text=_("Default timezone for the organization")
    )
    language = models.CharField(
        max_length=10,
        default='en',
        null=True,
        blank=True,
        help_text=_("Default language preference")
    )
    tags = TaggableManager(blank=True)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Additional metadata for the organization")
    )
    custom_fields = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Custom fields for the organization")
    )

    class Meta:
        app_label = 'api_v1_organization'
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['status']),
            models.Index(fields=['code']),
            models.Index(fields=['organization_type']),
        ]

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name


class OrganizationMembership(Timestamped, Auditable):
    """
    Model representing a user's membership in an organization with a specific role.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organization_memberships',
        verbose_name=_("User")
    )
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name=_("Organization")
    )
    role = models.ForeignKey(
        Group,
        on_delete=models.PROTECT,
        related_name='organization_memberships',
        verbose_name=_("Role (Group)"),
        null=True,
        blank=True
    )
    is_active = models.BooleanField(
        _("Is Active Member"),
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = _("Organization Membership")
        verbose_name_plural = _("Organization Memberships")
        unique_together = ('user', 'organization')
        ordering = ['organization__name', 'user__username']
        indexes = [
            models.Index(fields=['user', 'organization']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        """Return a string representation of the membership."""
        role_name = self.role.name if self.role else 'N/A'
        user_name = self.user.username if self.user else 'N/A'
        org_name = self.organization.name if self.organization else 'N/A'
        return f"{user_name} in {org_name} as {role_name}"

    def clean(self):
        """Validate the membership."""
        if not self.user or not self.organization:
            raise ValidationError(_("User and organization are required."))
        
        # Check for existing membership
        existing = OrganizationMembership.objects.filter(
            user=self.user,
            organization=self.organization
        ).exclude(pk=self.pk).exists()
        
        if existing:
            raise ValidationError(_("User already has a membership in this organization.")) 