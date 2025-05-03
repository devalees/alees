from django.contrib.auth import get_user_model
from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from api.v1.base_models.common.address.serializers import AddressSerializer
from api.v1.base_models.common.address.models import Address
from api.v1.base_models.organization.models import Organization
from api.v1.base_models.organization.serializers import OrganizationSimpleSerializer

from api.v1.base_models.contact.models import (
    Contact, ContactEmailAddress, ContactPhoneNumber, ContactAddress
)
from api.v1.base_models.contact.choices import (
    ContactType, ContactStatus, ContactSource,
    EmailType, PhoneType, AddressType
)

import logging

User = get_user_model()

logger = logging.getLogger(__name__)


class ContactEmailAddressSerializer(serializers.ModelSerializer):
    """Serializer for ContactEmailAddress model."""
    id = serializers.IntegerField(required=False)

    class Meta:
        model = ContactEmailAddress
        fields = ['id', 'email', 'is_primary', 'email_type']

    def validate_email(self, value):
        """Validate email format."""
        if not value or '@' not in value:
            raise serializers.ValidationError("Invalid email format")
        return value

    def validate(self, data):
        """Validate primary flag logic."""
        if data.get('is_primary'):
            contact = self.context.get('contact')
            if contact:
                existing_primary = ContactEmailAddress.objects.filter(
                    contact=contact,
                    is_primary=True
                )
                if self.instance:
                    existing_primary = existing_primary.exclude(id=self.instance.id)
                if existing_primary.exists():
                    raise serializers.ValidationError(
                        "A primary email already exists for this contact"
                    )
        return data

    def create(self, validated_data):
        """Create a new email address, ensuring contact is set from context."""
        contact = self.context.get('contact')
        if not contact:
            logger.error("ContactEmailAddressSerializer create failed: Contact context not provided.")
            raise serializers.ValidationError("Contact context is required")
        validated_data.pop('contact', None) # Ensure not duplicated
        instance = ContactEmailAddress.objects.create(contact=contact, **validated_data)
        logger.info(f"Created ContactEmailAddress {instance.id} for Contact {contact.id}")
        return instance


class ContactPhoneNumberSerializer(serializers.ModelSerializer):
    """Serializer for ContactPhoneNumber model."""
    id = serializers.IntegerField(required=False)

    class Meta:
        model = ContactPhoneNumber
        fields = ['id', 'phone_number', 'is_primary', 'phone_type']

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

    def validate(self, data):
        """Validate primary flag logic."""
        if data.get('is_primary'):
            contact = self.context.get('contact')
            if contact:
                existing_primary = ContactPhoneNumber.objects.filter(
                    contact=contact,
                    is_primary=True
                )
                if self.instance:
                    existing_primary = existing_primary.exclude(id=self.instance.id)
                if existing_primary.exists():
                    raise serializers.ValidationError(
                        "A primary phone number already exists for this contact"
                    )
        return data

    def create(self, validated_data):
        """Create a new phone number, ensuring contact is set from context."""
        contact = self.context.get('contact')
        if not contact:
            logger.error("ContactPhoneNumberSerializer create failed: Contact context not provided.")
            raise serializers.ValidationError("Contact context is required")
        validated_data.pop('contact', None) # Ensure not duplicated
        instance = ContactPhoneNumber.objects.create(contact=contact, **validated_data)
        logger.info(f"Created ContactPhoneNumber {instance.id} for Contact {contact.id}")
        return instance


class ContactAddressSerializer(serializers.ModelSerializer):
    """Serializer for contact addresses."""
    id = serializers.IntegerField(required=False)
    address = AddressSerializer(required=False)
    address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(),
        source='address',
        required=False,
        write_only=True
    )
    is_primary = serializers.BooleanField(required=False)
    address_type = serializers.ChoiceField(choices=AddressType.CHOICES, required=False)

    class Meta:
        model = ContactAddress
        fields = ['id', 'address', 'address_id', 'is_primary', 'address_type']

    def validate(self, data):
        """Validate that either address or address_id is provided."""
        logger.info(f"Validating ContactAddress data: {data}")
        
        # Check if we have address data
        has_address = 'address' in data and data['address'] is not None
        has_address_id = 'address_id' in data and data['address_id'] is not None
        
        logger.info(f"Has address data: {has_address}, Has address_id: {has_address_id}")
        
        if not has_address and not has_address_id:
            logger.error("Validation failed: Neither address nor address_id provided")
            raise serializers.ValidationError({
                'address_id': 'Either address or address_id must be provided'
            })
            
        logger.info("ContactAddress validation successful")
        return data

    def to_internal_value(self, data):
        """Convert primitive values to native values."""
        logger.info(f"Converting ContactAddress to internal value. Input data: {data}")
        
        # Log the type and value of address if present
        if 'address' in data:
            addr_type = type(data['address']).__name__
            addr_value = data['address']
            logger.info(f"Address in data - Type: {addr_type}, Value: {addr_value}")
            
            if isinstance(data['address'], (int, str)):
                logger.info(f"Converting address ID from {addr_type}: {addr_value}")
                data['address_id'] = data.pop('address')
            elif isinstance(data['address'], Address):
                logger.info(f"Converting Address object to ID: {data['address'].id}")
                data['address_id'] = data.pop('address').id
            elif isinstance(data['address'], dict):
                logger.info(f"Address is a dictionary with keys: {data['address'].keys()}")
        
        try:
            result = super().to_internal_value(data)
            logger.info(f"Internal value conversion successful. Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in to_internal_value: {str(e)}")
            raise

    def to_representation(self, instance):
        """Convert instance to primitive types."""
        ret = super().to_representation(instance)
        # Convert the full address object to just its ID
        if 'address' in ret and ret['address']:
            ret['address'] = instance.address.id
        return ret

    def create(self, validated_data):
        """Create a new contact address, ensuring contact is set from context."""
        logger.info(f"Creating ContactAddress with validated data: {validated_data}")
        contact = self.context.get('contact')
        if not contact:
            logger.error("ContactAddressSerializer create failed: Contact context not provided.")
            raise serializers.ValidationError("Contact context is required")

        address_instance = None
        try:
            address_data = validated_data.pop('address', None)
            if isinstance(address_data, Address):
                 logger.info(f"Using existing address instance: {address_data.id}")
                 address_instance = address_data
            elif isinstance(address_data, dict):
                logger.info(f"Creating new address from data: {address_data}")
                address_serializer = AddressSerializer(data=address_data)
                address_serializer.is_valid(raise_exception=True)
                address_instance = address_serializer.save()
                logger.info(f"Created new address instance: {address_instance.id}")

            if not address_instance:
                 logger.error("No valid address instance or data found in validated_data")
                 raise serializers.ValidationError({'address': 'Valid address object or new address data must be provided.'})

            validated_data.pop('contact', None)
            validated_data.pop('address', None)
            
            instance = ContactAddress.objects.create(
                contact=contact, 
                address=address_instance, 
                **validated_data
            )
            logger.info(f"Created ContactAddress {instance.id} for Contact {contact.id} with Address {address_instance.id}")
            return instance
        except serializers.ValidationError as e:
            logger.error(f"Validation error creating ContactAddress: {e.detail}")
            raise
        except Exception as e:
            logger.error(f"Error creating ContactAddress: {e}", exc_info=True)
            raise serializers.ValidationError(f"An unexpected error occurred creating the contact address: {e}")

    def update(self, instance, validated_data):
        """Update an existing contact address."""
        logger.info(f"Updating ContactAddress {instance.id} with data: {validated_data}")
        address_data = validated_data.pop('address', None)
        if isinstance(address_data, dict):
            logger.info("Updating address from data")
            address_serializer = AddressSerializer(instance.address, data=address_data, partial=True)
            address_serializer.is_valid(raise_exception=True)
            address = address_serializer.save()
            validated_data['address'] = address
        elif 'address_id' in validated_data:
            logger.info(f"Updating to use address with ID: {validated_data['address_id']}")
            validated_data['address'] = validated_data.pop('address_id')
        return super().update(instance, validated_data)


# Restore TaggitSerializer
class ContactSerializer(TaggitSerializer, serializers.ModelSerializer):
    """Serializer for Contact model."""
    id = serializers.IntegerField(required=False)
    email_addresses = ContactEmailAddressSerializer(many=True, required=False)
    phone_numbers = ContactPhoneNumberSerializer(many=True, required=False)
    addresses = ContactAddressSerializer(many=True, required=False)
    organization_name = serializers.CharField(required=False, allow_blank=True)
    
    organization = OrganizationSimpleSerializer(read_only=True)
    organization_id = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(), 
        source='organization', 
        required=True, 
        allow_null=False
    )

    tags = TagListSerializerField(required=False) # Restore tags field

    def validate(self, attrs):
        """Validate the contact data."""
        logger.info("Starting contact validation with data: %s", attrs)
        emails_data = attrs.get('email_addresses', [])
        phones_data = attrs.get('phone_numbers', [])
        addresses_data = attrs.get('addresses', [])

        self._validate_primary_flags(emails_data, 'email_addresses')
        self._validate_primary_flags(phones_data, 'phone_numbers')
        self._validate_primary_flags(addresses_data, 'addresses')

        organization_name = attrs.get('organization_name')
        organization_instance = attrs.get('organization') 
        organization_id = organization_instance.pk if organization_instance else None
        
        if organization_name and not self.instance and organization_id: 
            if Contact.objects.filter(organization_id=organization_id, organization_name__iexact=organization_name).exists():
                raise serializers.ValidationError({
                    'organization_name': 'A contact with this organization name already exists within the organization.'
                })
        
        logger.info("Contact validation completed successfully.")
        return attrs

    def create(self, validated_data):
        """Create a new contact and handle nested objects."""
        emails_data = validated_data.pop('email_addresses', [])
        phones_data = validated_data.pop('phone_numbers', [])
        addresses_data = validated_data.pop('addresses', [])
        tags_data = validated_data.pop('tags', [])

        contact = Contact.objects.create(**validated_data)
        
        if tags_data:
            contact.tags.set(tags_data)

        self._update_nested_objects(contact, 'email_addresses', emails_data, ContactEmailAddressSerializer)
        self._update_nested_objects(contact, 'phone_numbers', phones_data, ContactPhoneNumberSerializer)
        self._update_nested_objects(contact, 'addresses', addresses_data, ContactAddressSerializer)

        return contact

    def update(self, instance, validated_data):
        """Update a contact instance and handle nested objects."""
        emails_data = validated_data.pop('email_addresses', None)
        phones_data = validated_data.pop('phone_numbers', None)
        addresses_data = validated_data.pop('addresses', None)
        tags_data = validated_data.pop('tags', None)

        instance = super().update(instance, validated_data)

        if tags_data is not None: 
            instance.tags.set(tags_data)

        if emails_data: 
            self._update_nested_objects(instance, 'email_addresses', emails_data, ContactEmailAddressSerializer)
        
        if phones_data:
            self._update_nested_objects(instance, 'phone_numbers', phones_data, ContactPhoneNumberSerializer)

        if addresses_data:
            self._update_nested_objects(instance, 'addresses', addresses_data, ContactAddressSerializer)

        return instance

    # --- HELPER METHOD FOR NESTED WRITES ---
    def _update_nested_objects(self, instance, field_name, objects_data, serializer_class):
        """
        Handles create/update/delete for nested objects.
        Assumes the parent instance (`instance`) is already saved.
        """
        logger.info(f"[_update_nested] START: Contact {instance.id}, Field: {field_name}, Data Count: {len(objects_data)}")
        manager = getattr(instance, field_name) # e.g., instance.email_addresses
        existing_ids = set(manager.values_list('id', flat=True))
        updated_ids = set()

        for item_data in objects_data:
            item_id = item_data.get('id')
            logger.info(f"[_update_nested] Processing item: {item_data}")
            if item_id:
                logger.info(f"[_update_nested] Updating {field_name} item ID {item_id}")
                item_instance = manager.get(id=item_id)
                serializer = serializer_class(item_instance, data=item_data, partial=True, context={'contact': instance})
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    updated_ids.add(item_id)
                    logger.info(f"[_update_nested] Update successful for ID {item_id}")
                else:
                    logger.error(f"[_update_nested] Validation failed for new {field_name} item: {serializer.errors}")
            else:
                logger.info(f"[_update_nested] Creating new {field_name} item")
                serializer = serializer_class(data=item_data, context={'contact': instance})
                if serializer.is_valid(raise_exception=True):
                    try:
                        # Rely *only* on context for create, do not pass contact kwarg
                        nested_instance = serializer.save()
                        if hasattr(nested_instance, 'id'):
                            updated_ids.add(nested_instance.id)
                            logger.info(f"[_update_nested] Creation successful, new ID: {nested_instance.id}")
                        else:
                            logger.error(f"[_update_nested] Failed to get ID for newly created {field_name} item.")
                    except Exception as e:
                        logger.error(f"[_update_nested] Error saving nested {field_name}: {e}", exc_info=True)
                        raise
                else:
                    logger.error(f"[_update_nested] Validation failed for new {field_name} item: {serializer.errors}")

        # Delete items not included in the update (optional, depends on desired PATCH behavior)
        ids_to_delete = existing_ids - updated_ids
        if ids_to_delete:
            logger.info(f"[_update_nested] Deleting {field_name} items: {ids_to_delete}")
            manager.filter(id__in=ids_to_delete).delete()
        logger.info(f"[_update_nested] END: Contact {instance.id}, Field: {field_name}")

    # --- END HELPER ---

    def to_representation(self, instance):
        """Ensure nested fields are represented correctly."""
        representation = super().to_representation(instance)
        # Ensure nested serializers are used for output
        representation['email_addresses'] = ContactEmailAddressSerializer(instance.email_addresses.all(), many=True).data
        representation['phone_numbers'] = ContactPhoneNumberSerializer(instance.phone_numbers.all(), many=True).data
        representation['addresses'] = ContactAddressSerializer(instance.addresses.all(), many=True).data
        # TaggitSerializer handles tags automatically
        return representation

    class Meta:
        model = Contact
        fields = [
            'id', 'first_name', 'last_name', 'title', 'organization_name',
            'organization',
            'organization_id',
            'contact_type', 'status', 'source', 'notes', 'tags', 
            'custom_fields',
            'email_addresses', 'phone_numbers', 'addresses',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at'] 

    def _validate_primary_flags(self, items, field_name):
        """Helper to ensure only one item is marked as primary."""
        primary_count = sum(1 for item in items if item.get('is_primary'))
        if primary_count > 1:
            raise serializers.ValidationError({
                field_name: f"Only one {field_name.replace('_', ' ')} can be marked as primary."
            })
