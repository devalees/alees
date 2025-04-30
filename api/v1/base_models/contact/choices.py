from django.utils.translation import gettext_lazy as _

class ContactType:
    """Contact type choices for the Contact model."""
    
    PRIMARY = 'primary'
    BILLING = 'billing'
    SUPPORT = 'support'
    TECHNICAL = 'technical'
    OTHER = 'other'

    CHOICES = [
        (PRIMARY, _('Primary')),
        (BILLING, _('Billing')),
        (SUPPORT, _('Support')),
        (TECHNICAL, _('Technical')),
        (OTHER, _('Other')),
    ]

class ContactStatus:
    """Contact status choices for the Contact model."""
    
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    DO_NOT_CONTACT = 'do_not_contact'

    CHOICES = [
        (ACTIVE, _('Active')),
        (INACTIVE, _('Inactive')),
        (DO_NOT_CONTACT, _('Do Not Contact')),
    ]

class ContactSource:
    """Contact source choices for the Contact model."""
    
    WEBSITE = 'website'
    REFERRAL = 'referral'
    CONFERENCE = 'conference'
    OTHER = 'other'

    CHOICES = [
        (WEBSITE, _('Website')),
        (REFERRAL, _('Referral')),
        (CONFERENCE, _('Conference')),
        (OTHER, _('Other')),
    ]

class EmailType:
    """Email type choices for the ContactEmailAddress model."""
    
    PRIMARY = 'primary'
    WORK = 'work'
    PERSONAL = 'personal'
    OTHER = 'other'

    CHOICES = [
        (PRIMARY, _('Primary')),
        (WORK, _('Work')),
        (PERSONAL, _('Personal')),
        (OTHER, _('Other')),
    ]

class PhoneType:
    """Phone type choices for the ContactPhoneNumber model."""
    
    MOBILE = 'mobile'
    WORK = 'work'
    HOME = 'home'
    FAX = 'fax'
    OTHER = 'other'

    CHOICES = [
        (MOBILE, _('Mobile')),
        (WORK, _('Work')),
        (HOME, _('Home')),
        (FAX, _('Fax')),
        (OTHER, _('Other')),
    ]

class AddressType:
    """Address type choices for the ContactAddress model."""
    
    HOME = 'home'
    WORK = 'work'
    BILLING = 'billing'
    SHIPPING = 'shipping'
    OTHER = 'other'

    CHOICES = [
        (HOME, _('Home')),
        (WORK, _('Work')),
        (BILLING, _('Billing')),
        (SHIPPING, _('Shipping')),
        (OTHER, _('Other')),
    ]
