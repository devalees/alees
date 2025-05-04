import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from ..factories import ContactFactory, ContactPhoneNumberFactory, ContactEmailAddressFactory, ContactAddressFactory
from ...models import Contact, ContactPhoneNumber, ContactEmailAddress, ContactAddress

pytestmark = pytest.mark.django_db

# ... existing tests for Contact, ContactPhoneNumber, etc. ...

# --- Taggit Integration Tests ---

def test_contact_can_be_tagged():
    """Verify tags can be added and retrieved for a Contact."""
    contact = ContactFactory()
    assert hasattr(contact, 'tags'), "Contact model should have a 'tags' attribute"

    # Check initial state (no tags)
    assert contact.tags.count() == 0

    # Add tags
    contact.tags.add("prospect", "vip", "needs_followup")
    contact.save() # Save is often required for M2M relations like tags

    # Refresh from DB to ensure tags are persisted
    contact.refresh_from_db()

    assert contact.tags.count() == 3
    tag_names = sorted([tag.name for tag in contact.tags.all()])
    assert tag_names == ["needs_followup", "prospect", "vip"]

    # Add an existing tag again (should not duplicate)
    contact.tags.add("vip")
    contact.save()
    contact.refresh_from_db()
    assert contact.tags.count() == 3

def test_filter_contact_by_tag():
    """Verify filtering Contacts by tag names works."""
    contact1 = ContactFactory()
    contact1.tags.add("prospect", "important")
    contact1.save()

    contact2 = ContactFactory()
    contact2.tags.add("vip", "important")
    contact2.save()

    contact3 = ContactFactory() # No tags
    contact3.save()

    # Filter by single tag 'prospect'
    prospects = Contact.objects.filter(tags__name__in=["prospect"])
    assert prospects.count() == 1
    assert prospects.first() == contact1

    # Filter by single tag 'vip'
    vips = Contact.objects.filter(tags__name__in=["vip"])
    assert vips.count() == 1
    assert vips.first() == contact2

    # Filter by common tag 'important'
    important_contacts = Contact.objects.filter(tags__name__in=["important"])
    assert important_contacts.count() == 2
    assert contact1 in important_contacts
    assert contact2 in important_contacts

    # Filter by multiple tags (OR condition)
    prospect_or_vip = Contact.objects.filter(tags__name__in=["prospect", "vip"])
    assert prospect_or_vip.count() == 2
    assert contact1 in prospect_or_vip
    assert contact2 in prospect_or_vip

    # Filter by non-existent tag
    no_match = Contact.objects.filter(tags__name__in=["nonexistent"])
    assert no_match.count() == 0 