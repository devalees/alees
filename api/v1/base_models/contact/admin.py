from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from api.v1.base_models.contact.models import (
    Contact, ContactEmailAddress, ContactPhoneNumber, ContactAddress
)


class ContactEmailAddressInline(admin.TabularInline):
    """Inline admin for ContactEmailAddress."""
    model = ContactEmailAddress
    extra = 1
    fields = ('email', 'email_type', 'is_primary')


class ContactPhoneNumberInline(admin.TabularInline):
    """Inline admin for ContactPhoneNumber."""
    model = ContactPhoneNumber
    extra = 1
    fields = ('phone_number', 'phone_type', 'is_primary')


class ContactAddressInline(admin.TabularInline):
    """Inline admin for ContactAddress."""
    model = ContactAddress
    extra = 1
    fields = ('address', 'address_type', 'is_primary')
    raw_id_fields = ('address',)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Admin configuration for Contact model."""
    list_display = (
        'first_name', 'last_name', 'title', 'organization_name',
        'linked_organization', 'contact_type', 'status', 'source'
    )
    list_filter = ('contact_type', 'status', 'source')
    search_fields = ('first_name', 'last_name', 'organization_name')
    inlines = [
        ContactEmailAddressInline,
        ContactPhoneNumberInline,
        ContactAddressInline
    ]
    fieldsets = (
        (None, {
            'fields': (
                'first_name', 'last_name', 'title', 'organization_name',
                'linked_organization', 'contact_type', 'status', 'source'
            )
        }),
        (_('Additional Information'), {
            'fields': ('notes', 'tags', 'custom_fields'),
            'classes': ('collapse',)
        })
    )
