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
    inlines = [
        ContactEmailAddressInline,
        ContactPhoneNumberInline,
        ContactAddressInline
    ]
    list_display = (
        'first_name', 'last_name', 'title', 'organization_name', 'organization',
        'contact_type', 'status', 'source', 'created_at'
    )
    list_filter = ('contact_type', 'status', 'source', 'created_at')
    search_fields = (
        'first_name', 'last_name', 'organization_name', 'email_addresses__email',
        'phone_numbers__phone_number', 'organization__name'
    )
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    fieldsets = (
        (None, {
            'fields': (
                'first_name', 'last_name', 'title', 'organization_name', 'organization'
            )
        }),
        (_('Details'), {
            'fields': ('contact_type', 'status', 'source', 'notes', 'tags'),
            'classes': ('collapse',)
        }),
        ('Custom Fields', {
            'fields': ('custom_fields',),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
