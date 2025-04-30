from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer

from api.v1.base_models.contact.models import (
    Contact, ContactEmailAddress, ContactPhoneNumber, ContactAddress
)
from api.v1.base_models.contact.choices import (
    EmailType, PhoneType, AddressType
)
from api.v1.base_models.common.serializers import AddressSerializer


class ContactEmailAddressSerializer(serializers.ModelSerializer):
    """Serializer for ContactEmailAddress model."""
    class Meta:
        model = ContactEmailAddress
        fields = ('id', 'email', 'email_type', 'is_primary')
        read_only_fields = ('id',)


class ContactPhoneNumberSerializer(serializers.ModelSerializer):
    """Serializer for ContactPhoneNumber model."""
    class Meta:
        model = ContactPhoneNumber
        fields = ('id', 'phone_number', 'phone_type', 'is_primary')
        read_only_fields = ('id',)


class ContactAddressSerializer(serializers.ModelSerializer):
    """Serializer for ContactAddress model."""
    address = AddressSerializer()

    class Meta:
        model = ContactAddress
        fields = ('id', 'address', 'address_type', 'is_primary')
        read_only_fields = ('id',)


class ContactSerializer(TaggitSerializer, serializers.ModelSerializer):
    """Serializer for Contact model."""
    tags = TagListSerializerField(required=False)
    email_addresses = ContactEmailAddressSerializer(many=True, required=False)
    phone_numbers = ContactPhoneNumberSerializer(many=True, required=False)
    addresses = ContactAddressSerializer(many=True, required=False)

    # Temporary workaround for Organization link
    linked_organization_id = serializers.IntegerField(
        source='linked_organization_id',
        allow_null=True,
        required=False,
        write_only=True
    )
    linked_organization_name = serializers.CharField(
        source='linked_organization.name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = Contact
        fields = [
            'id', 'first_name', 'last_name', 'title', 'organization_name',
            'linked_organization_id', 'linked_organization_name',
            'contact_type', 'status', 'source', 'notes', 'tags', 'custom_fields',
            'email_addresses', 'phone_numbers', 'addresses',
            'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'linked_organization_name', 'created_at', 'updated_at')

    def validate_linked_organization_id(self, value):
        """Manual validation until Organization model is implemented."""
        if value is not None:
            if not isinstance(value, int) or value <= 0:
                raise serializers.ValidationError("Invalid Organization ID provided.")
        return value

    def create(self, validated_data):
        """Create a new Contact with nested objects."""
        emails_data = validated_data.pop('email_addresses', [])
        phones_data = validated_data.pop('phone_numbers', [])
        addresses_data = validated_data.pop('addresses', [])

        contact = Contact.objects.create(**validated_data)

        # Create nested objects
        self._create_nested_channels(contact, emails_data, phones_data, addresses_data)

        return contact

    def update(self, instance, validated_data):
        """Update a Contact and its nested objects."""
        emails_data = validated_data.pop('email_addresses', None)
        phones_data = validated_data.pop('phone_numbers', None)
        addresses_data = validated_data.pop('addresses', None)

        # Update instance fields
        instance = super().update(instance, validated_data)

        # Update nested objects
        if emails_data is not None:
            self._update_nested_emails(instance, emails_data)
        if phones_data is not None:
            self._update_nested_phones(instance, phones_data)
        if addresses_data is not None:
            self._update_nested_addresses(instance, addresses_data)

        return instance

    def _create_nested_channels(self, contact, emails_data, phones_data, addresses_data):
        """Create nested channel objects."""
        for email_data in emails_data:
            ContactEmailAddress.objects.create(contact=contact, **email_data)
        for phone_data in phones_data:
            ContactPhoneNumber.objects.create(contact=contact, **phone_data)
        for address_data in addresses_data:
            address_data = address_data.pop('address')
            address = Address.objects.create(**address_data)
            ContactAddress.objects.create(contact=contact, address=address, **address_data)

    def _update_nested_emails(self, contact, emails_data):
        """Update email addresses."""
        existing_emails = {email.id: email for email in contact.email_addresses.all()}
        for email_data in emails_data:
            email_id = email_data.get('id')
            if email_id and email_id in existing_emails:
                email = existing_emails[email_id]
                for attr, value in email_data.items():
                    setattr(email, attr, value)
                email.save()
            else:
                ContactEmailAddress.objects.create(contact=contact, **email_data)

        # Delete emails not in the update
        current_ids = {email.get('id') for email in emails_data if email.get('id')}
        for email_id, email in existing_emails.items():
            if email_id not in current_ids:
                email.delete()

    def _update_nested_phones(self, contact, phones_data):
        """Update phone numbers."""
        existing_phones = {phone.id: phone for phone in contact.phone_numbers.all()}
        for phone_data in phones_data:
            phone_id = phone_data.get('id')
            if phone_id and phone_id in existing_phones:
                phone = existing_phones[phone_id]
                for attr, value in phone_data.items():
                    setattr(phone, attr, value)
                phone.save()
            else:
                ContactPhoneNumber.objects.create(contact=contact, **phone_data)

        # Delete phones not in the update
        current_ids = {phone.get('id') for phone in phones_data if phone.get('id')}
        for phone_id, phone in existing_phones.items():
            if phone_id not in current_ids:
                phone.delete()

    def _update_nested_addresses(self, contact, addresses_data):
        """Update addresses."""
        existing_addresses = {address.id: address for address in contact.addresses.all()}
        for address_data in addresses_data:
            address_id = address_data.get('id')
            if address_id and address_id in existing_addresses:
                address = existing_addresses[address_id]
                address_data = address_data.pop('address')
                for attr, value in address_data.items():
                    setattr(address.address, attr, value)
                address.address.save()
                for attr, value in address_data.items():
                    setattr(address, attr, value)
                address.save()
            else:
                address_data = address_data.pop('address')
                address = Address.objects.create(**address_data)
                ContactAddress.objects.create(contact=contact, address=address, **address_data)

        # Delete addresses not in the update
        current_ids = {address.get('id') for address in addresses_data if address.get('id')}
        for address_id, address in existing_addresses.items():
            if address_id not in current_ids:
                address.delete()
