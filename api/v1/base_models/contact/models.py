from django.db import models
from django.core.validators import MinLengthValidator
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase

from core.models import Timestamped, Auditable
from api.v1.base_models.common.address.models import Address
from api.v1.base_models.contact.choices import (
    ContactType, ContactStatus, ContactSource,
    EmailType, PhoneType, AddressType
)


class TaggedContact(TaggedItemBase):
    """Custom tag model for Contact."""
    content_object = models.ForeignKey('Contact', on_delete=models.CASCADE)

    class Meta:
        app_label = 'contact'


class Contact(Timestamped, Auditable):
    """Model representing a contact in the system."""

    first_name = models.CharField(
        _('First Name'),
        max_length=100,
        validators=[MinLengthValidator(2)]
    )
    last_name = models.CharField(
        _('Last Name'),
        max_length=100,
        validators=[MinLengthValidator(2)]
    )
    title = models.CharField(
        _('Title'),
        max_length=100,
        blank=True
    )
    organization_name = models.CharField(
        _('Organization Name'),
        max_length=200,
        blank=True
    )
    # Temporary solution: Store organization ID until Organization model is implemented
    organization_id = models.IntegerField(
        _('Organization ID'),
        null=True,
        blank=True,
        help_text=_('Temporary field to store organization ID until Organization model is implemented')
    )
    contact_type = models.CharField(
        _('Contact Type'),
        max_length=20,
        choices=ContactType.CHOICES,
        default=ContactType.PRIMARY
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=ContactStatus.CHOICES,
        default=ContactStatus.ACTIVE
    )
    source = models.CharField(
        _('Source'),
        max_length=20,
        choices=ContactSource.CHOICES,
        default=ContactSource.WEBSITE
    )
    notes = models.TextField(
        _('Notes'),
        blank=True
    )
    tags = TaggableManager(
        through=TaggedContact,
        blank=True
    )
    custom_fields = models.JSONField(
        _('Custom Fields'),
        default=dict,
        blank=True
    )

    class Meta:
        app_label = 'contact'
        verbose_name = _('Contact')
        verbose_name_plural = _('Contacts')
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['organization_name']),
            models.Index(fields=['contact_type']),
            models.Index(fields=['status'])
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def clean(self):
        """Custom validation logic."""
        super().clean()


class ContactEmailAddress(Timestamped, Auditable):
    """Model representing a contact's email address."""

    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='email_addresses',
        verbose_name=_('Contact')
    )
    email = models.EmailField(
        _('Email Address'),
        max_length=254
    )
    email_type = models.CharField(
        _('Email Type'),
        max_length=20,
        choices=EmailType.CHOICES,
        default=EmailType.PRIMARY
    )
    is_primary = models.BooleanField(
        _('Is Primary'),
        default=False
    )

    class Meta:
        app_label = 'contact'
        verbose_name = _('Contact Email Address')
        verbose_name_plural = _('Contact Email Addresses')
        unique_together = ['contact', 'email']
        ordering = ['-is_primary', 'email_type', 'email']

    def __str__(self):
        return f"{self.email} ({self.get_email_type_display()})"

    def clean(self):
        """Custom validation logic."""
        super().clean()
        if self.is_primary:
            # Ensure only one primary email per contact
            ContactEmailAddress.objects.filter(
                contact=self.contact,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)


class ContactPhoneNumber(Timestamped, Auditable):
    """Model representing a contact's phone number."""

    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='phone_numbers',
        verbose_name=_('Contact')
    )
    phone_number = models.CharField(
        _('Phone Number'),
        max_length=20
    )
    phone_type = models.CharField(
        _('Phone Type'),
        max_length=20,
        choices=PhoneType.CHOICES,
        default=PhoneType.MOBILE
    )
    is_primary = models.BooleanField(
        _('Is Primary'),
        default=False
    )

    class Meta:
        app_label = 'contact'
        verbose_name = _('Contact Phone Number')
        verbose_name_plural = _('Contact Phone Numbers')
        unique_together = ['contact', 'phone_number']
        ordering = ['-is_primary', 'phone_type', 'phone_number']

    def __str__(self):
        return f"{self.phone_number} ({self.get_phone_type_display()})"

    def clean(self):
        """Custom validation logic."""
        super().clean()
        if self.is_primary:
            # Ensure only one primary phone number per contact
            ContactPhoneNumber.objects.filter(
                contact=self.contact,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)


class ContactAddress(Timestamped, Auditable):
    """Model representing a contact's address."""

    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name=_('Contact')
    )
    address = models.ForeignKey(
        Address,
        on_delete=models.CASCADE,
        related_name='contact_addresses',
        verbose_name=_('Address')
    )
    address_type = models.CharField(
        _('Address Type'),
        max_length=20,
        choices=AddressType.CHOICES,
        default=AddressType.HOME
    )
    is_primary = models.BooleanField(
        _('Is Primary'),
        default=False
    )

    class Meta:
        app_label = 'contact'
        verbose_name = _('Contact Address')
        verbose_name_plural = _('Contact Addresses')
        ordering = ['-is_primary', 'address_type']

    def __str__(self):
        return f"{self.address} ({self.get_address_type_display()})"

    def clean(self):
        """Custom validation logic."""
        super().clean()
        if self.is_primary:
            # Ensure only one primary address per contact
            ContactAddress.objects.filter(
                contact=self.contact,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
