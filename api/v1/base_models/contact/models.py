from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.auth import get_user_model
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

from core.models import Timestamped, Auditable
from api.v1.base_models.common.address.models import Address
from api.v1.base_models.organization.models import Organization
from api.v1.base_models.contact.choices import (
    ContactType, ContactStatus, ContactSource,
    EmailType, PhoneType, AddressType
)

User = get_user_model()


class TaggedContact(TaggedItemBase):
    """Custom tag model for Contact."""
    content_object = models.ForeignKey('Contact', on_delete=models.CASCADE)

    class Meta:
        app_label = 'contact'


class Contact(Timestamped, Auditable):
    """Model for storing contact information."""
    
    first_name = models.CharField(
        _('First Name'),
        max_length=100,
        help_text=_('First name of the contact')
    )
    last_name = models.CharField(
        _('Last Name'),
        max_length=100,
        help_text=_('Last name of the contact')
    )
    title = models.CharField(
        _('Title'),
        max_length=100,
        blank=True,
        help_text=_('Professional title or position')
    )
    organization_name = models.CharField(
        _('Organization Name'),
        max_length=200,
        blank=True,
        help_text=_('Name of the organization if not linked to an existing one')
    )
    linked_organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts',
        verbose_name=_('Linked Organization'),
        help_text=_('The organization this contact is linked to')
    )
    contact_type = models.CharField(
        _('Contact Type'),
        max_length=20,
        choices=ContactType.CHOICES,
        default=ContactType.PRIMARY,
        help_text=_('Type of contact (e.g., individual, business)')
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=ContactStatus.CHOICES,
        default=ContactStatus.ACTIVE,
        help_text=_('Current status of the contact')
    )
    source = models.CharField(
        _('Source'),
        max_length=20,
        choices=ContactSource.CHOICES,
        default=ContactSource.WEBSITE,
        help_text=_('How the contact was acquired')
    )
    notes = models.TextField(
        _('Notes'),
        blank=True,
        help_text=_('Additional notes about the contact')
    )
    tags = TaggableManager(
        _('Tags'),
        blank=True,
        help_text=_('Tags associated with this contact')
    )
    custom_fields = models.JSONField(
        _('Custom Fields'),
        default=dict,
        blank=True,
        help_text=_('Additional custom fields for the contact')
    )

    class Meta:
        verbose_name = _('Contact')
        verbose_name_plural = _('Contacts')
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['organization_name']),
            models.Index(fields=['contact_type']),
            models.Index(fields=['status']),
            models.Index(fields=['source']),
            models.Index(fields=['linked_organization'])
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def clean(self):
        """Validate contact data."""
        if not self.first_name and not self.last_name:
            raise ValidationError(_('At least one name field (first or last) must be provided'))
        if self.custom_fields and not isinstance(self.custom_fields, dict):
            raise ValidationError(_('Custom fields must be a dictionary'))
        if self.organization_name and self.linked_organization:
            raise ValidationError(_('Cannot provide both organization name and linked organization'))

    @property
    def full_name(self):
        """Return the contact's full name."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def primary_email(self):
        """Return the primary email address."""
        return self.email_addresses.filter(is_primary=True).first()

    @property
    def primary_phone(self):
        """Return the primary phone number."""
        return self.phone_numbers.filter(is_primary=True).first()

    @property
    def primary_address(self):
        """Return the primary address."""
        return self.addresses.filter(is_primary=True).first()


class ContactEmailAddress(Timestamped, Auditable):
    """Model for storing a contact's email address."""
    
    contact = models.ForeignKey(
        'Contact',
        on_delete=models.CASCADE,
        related_name='email_addresses',
        verbose_name=_('Contact')
    )
    email = models.EmailField(
        _('Email Address'),
        max_length=254,
        help_text=_('The email address')
    )
    email_type = models.CharField(
        _('Email Type'),
        max_length=20,
        choices=EmailType.CHOICES,
        default=EmailType.PERSONAL,
        help_text=_('The type of email address (e.g., personal, work)')
    )
    is_primary = models.BooleanField(
        _('Is Primary'),
        default=False,
        help_text=_('Whether this is the primary email address for the contact')
    )
    notes = models.TextField(
        _('Notes'),
        blank=True,
        help_text=_('Additional notes about this email address')
    )

    class Meta:
        verbose_name = _('Contact Email Address')
        verbose_name_plural = _('Contact Email Addresses')
        ordering = ['-is_primary', 'created_at']
        unique_together = ['contact', 'email']

    def __str__(self):
        return f"{self.contact}: {self.email} ({self.get_email_type_display()})"

    def save(self, *args, **kwargs):
        """Override save to handle primary flag."""
        if self.is_primary:
            # Set all other email addresses for this contact as non-primary
            ContactEmailAddress.objects.filter(
                contact=self.contact,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    def clean(self):
        """Validate email format."""
        if not self.email or '@' not in self.email:
            raise ValidationError("Invalid email format")


class ContactPhoneNumber(Timestamped, Auditable):
    """Model for storing a contact's phone number."""
    
    contact = models.ForeignKey(
        'Contact',
        on_delete=models.CASCADE,
        related_name='phone_numbers',
        verbose_name=_('Contact')
    )
    phone_number = models.CharField(
        _('Phone Number'),
        max_length=50,
        blank=False,
        help_text=_('The phone number in E.164 format (e.g., +12125551234)')
    )
    phone_type = models.CharField(
        _('Phone Type'),
        max_length=20,
        choices=PhoneType.CHOICES,
        default=PhoneType.MOBILE,
        help_text=_('The type of phone number (e.g., mobile, work, home)')
    )
    is_primary = models.BooleanField(
        _('Is Primary'),
        default=False,
        help_text=_('Whether this is the primary phone number for the contact')
    )
    notes = models.TextField(
        _('Notes'),
        blank=True,
        help_text=_('Additional notes about this phone number')
    )

    class Meta:
        verbose_name = _('Contact Phone Number')
        verbose_name_plural = _('Contact Phone Numbers')
        ordering = ['-is_primary', 'created_at']
        unique_together = ['contact', 'phone_number']

    def __str__(self):
        return f"{self.contact}: {self.phone_number} ({self.get_phone_type_display()})"

    def clean(self):
        """Validate the phone number format."""
        if self.phone_number:
            # Basic validation - ensure it starts with + and has digits
            if not self.phone_number.startswith('+'):
                raise ValidationError(_('Phone number should start with +'))
            if not self.phone_number[1:].isdigit():
                raise ValidationError(_('Phone number should contain only digits after +'))
            if len(self.phone_number) < 8:  # Minimum length for a valid phone number
                raise ValidationError(_('Phone number is too short'))
            if len(self.phone_number) > 15:  # Maximum length for a valid phone number
                raise ValidationError(_('Phone number is too long'))

    def save(self, *args, **kwargs):
        """Override save to handle primary flag."""
        if self.is_primary:
            # Set all other phone numbers for this contact as non-primary
            ContactPhoneNumber.objects.filter(
                contact=self.contact,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class ContactAddress(Timestamped, Auditable):
    """Model for storing a contact's address."""
    
    contact = models.ForeignKey(
        'Contact',
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name=_('Contact')
    )
    address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        related_name='contact_addresses',
        verbose_name=_('Address')
    )
    address_type = models.CharField(
        _('Address Type'),
        max_length=20,
        choices=AddressType.CHOICES,
        default=AddressType.HOME,
        help_text=_('The type of address (e.g., home, work)')
    )
    is_primary = models.BooleanField(
        _('Is Primary'),
        default=False,
        help_text=_('Whether this is the primary address for the contact')
    )
    notes = models.TextField(
        _('Notes'),
        blank=True,
        help_text=_('Additional notes about this address')
    )

    class Meta:
        verbose_name = _('Contact Address')
        verbose_name_plural = _('Contact Addresses')
        ordering = ['-is_primary', 'created_at']
        unique_together = ['contact', 'address']

    def __str__(self):
        return f"{self.contact}: {self.address} ({self.get_address_type_display()})"

    def save(self, *args, **kwargs):
        """Override save to handle primary flag."""
        if self.is_primary:
            # Set all other addresses for this contact as non-primary
            ContactAddress.objects.filter(
                contact=self.contact,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
