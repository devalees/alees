from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from api.v1.base_models.common.address.serializers import AddressSerializer
from api.v1.base_models.common.address.models import Address

from api.v1.base_models.contact.models import (
    Contact, ContactEmailAddress, ContactPhoneNumber, ContactAddress
)
from api.v1.base_models.contact.choices import (
    ContactType, ContactStatus, ContactSource,
    EmailType, PhoneType, AddressType
)


class ContactEmailAddressSerializer(serializers.ModelSerializer):
    """Serializer for ContactEmailAddress model."""
    class Meta:
        model = ContactEmailAddress
        fields = ('id', 'email', 'email_type', 'is_primary')
        read_only_fields = ('id',)

    def validate_email(self, value):
        """Validate email format."""
        if not value or '@' not in value:
            raise serializers.ValidationError("Invalid email format")
        return value


class ContactPhoneNumberSerializer(serializers.ModelSerializer):
    """Serializer for ContactPhoneNumber model."""

    class Meta:
        model = ContactPhoneNumber
        fields = ('id', 'phone_number', 'phone_type', 'is_primary')
        read_only_fields = ('id',)

    def validate_phone_number(self, value):
        """Validate phone number format."""
        if not value:
            raise serializers.ValidationError("Phone number is required")
        if not value.startswith('+'):
            raise serializers.ValidationError("Phone number must start with +")
        if not value[1:].isdigit():
            raise serializers.ValidationError("Phone number must contain only digits after +")
        if len(value) < 8:
            raise serializers.ValidationError("Phone number is too short")
        if len(value) > 15:
            raise serializers.ValidationError("Phone number is too long")
        return value


class ContactAddressSerializer(serializers.ModelSerializer):
    """Serializer for ContactAddress model."""
    address = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all())

    class Meta:
        model = ContactAddress
        fields = ('id', 'address', 'address_type', 'is_primary')
        read_only_fields = ('id',)


class ContactSerializer(TaggitSerializer, serializers.ModelSerializer):
    """Serializer for Contact model with nested serializers."""
    email_addresses = ContactEmailAddressSerializer(many=True, required=False)
    phone_numbers = ContactPhoneNumberSerializer(many=True, required=False)
    addresses = ContactAddressSerializer(many=True, required=False)
    tags = TagListSerializerField(required=False)

    # Temporary workaround for Organization link
    linked_organization_id = serializers.IntegerField(
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
        fields = (
            'id', 'first_name', 'last_name', 'title', 'organization_name',
            'organization_id', 'contact_type', 'status', 'source', 'notes',
            'tags', 'custom_fields', 'email_addresses', 'phone_numbers',
            'addresses', 'created_at', 'updated_at',
            'linked_organization_id', 'linked_organization_name'
        )
        read_only_fields = ('id', 'linked_organization_name', 'created_at', 'updated_at')

    def validate_organization_id(self, value):
        """Validate organization_id."""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Invalid organization ID")
        return value

    def validate_linked_organization_id(self, value):
        """Manual validation until Organization model is implemented."""
        if value is not None:
            if not isinstance(value, int) or value <= 0:
                raise serializers.ValidationError("Invalid Organization ID provided.")
        return value

    def create(self, validated_data):
        """Create a new contact with nested objects."""
        # Extract nested data
        email_addresses_data = validated_data.pop('email_addresses', [])
        phone_numbers_data = validated_data.pop('phone_numbers', [])
        addresses_data = validated_data.pop('addresses', [])
        tags_data = validated_data.pop('tags', [])
        linked_organization_id = validated_data.pop('linked_organization_id', None)

        # Create contact
        contact = Contact.objects.create(**validated_data)

        # Add tags
        if tags_data:
            contact.tags.add(*tags_data)

        # Create nested objects
        for email_data in email_addresses_data:
            ContactEmailAddress.objects.create(contact=contact, **email_data)

        for phone_data in phone_numbers_data:
            ContactPhoneNumber.objects.create(contact=contact, **phone_data)

        for address_data in addresses_data:
            ContactAddress.objects.create(contact=contact, **address_data)

        # Set linked organization
        if linked_organization_id:
            contact.linked_organization_id = linked_organization_id
            contact.save()

        return contact

    def update(self, instance, validated_data):
        """Update a contact and its nested objects."""
        # Extract nested data
        email_addresses_data = validated_data.pop('email_addresses', None)
        phone_numbers_data = validated_data.pop('phone_numbers', None)
        addresses_data = validated_data.pop('addresses', None)
        tags_data = validated_data.pop('tags', None)
        linked_organization_id = validated_data.pop('linked_organization_id', None)

        # Update contact fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update tags
        if tags_data is not None:
            instance.tags.set(tags_data)

        # Update nested objects
        if email_addresses_data is not None:
            self._update_nested_objects(instance, 'email_addresses', email_addresses_data)
        if phone_numbers_data is not None:
            self._update_nested_objects(instance, 'phone_numbers', phone_numbers_data)
        if addresses_data is not None:
            self._update_nested_objects(instance, 'addresses', addresses_data)

        # Set linked organization
        if linked_organization_id:
            instance.linked_organization_id = linked_organization_id
            instance.save()

        return instance

    def _update_nested_objects(self, contact, related_name, objects_data):
        """Update nested objects for a contact."""
        # Get the related manager
        related_manager = getattr(contact, related_name)
        
        # Delete existing objects not in the new data
        existing_ids = {obj['id'] for obj in objects_data if 'id' in obj}
        related_manager.exclude(id__in=existing_ids).delete()

        # Update or create objects
        for obj_data in objects_data:
            obj_id = obj_data.pop('id', None)
            if obj_id:
                # Update existing object
                obj = related_manager.get(id=obj_id)
                for attr, value in obj_data.items():
                    setattr(obj, attr, value)
                obj.save()
            else:
                # Create new object
                related_manager.create(**obj_data)

    def to_representation(self, instance):
        """Convert instance to representation."""
        data = super().to_representation(instance)
        # Sort tags to ensure consistent order
        if 'tags' in data:
            data['tags'] = sorted(data['tags'])
        return data
