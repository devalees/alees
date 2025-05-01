from django.contrib.auth import get_user_model
from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from api.v1.base_models.common.address.serializers import AddressSerializer
from api.v1.base_models.common.address.models import Address
from api.v1.base_models.organization.models import Organization

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
        """Create a new email address."""
        contact = validated_data.pop('contact', None) or self.context.get('contact')
        if not contact:
            raise serializers.ValidationError("Contact is required")
        return ContactEmailAddress.objects.create(contact=contact, **validated_data)


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
        """Create a new phone number."""
        contact = validated_data.pop('contact', None) or self.context.get('contact')
        if not contact:
            raise serializers.ValidationError("Contact is required")
        return ContactPhoneNumber.objects.create(contact=contact, **validated_data)


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
        """Create a new contact address."""
        logger.info(f"Creating ContactAddress with validated data: {validated_data}")
        
        try:
            address_data = validated_data.pop('address', None)
            if isinstance(address_data, dict):
                logger.info(f"Creating new address from data: {address_data}")
                address_serializer = AddressSerializer(data=address_data)
                address_serializer.is_valid(raise_exception=True)
                address = address_serializer.save()
                validated_data['address'] = address
            elif address_data:
                logger.info(f"Using existing address: {address_data}")
                validated_data['address'] = address_data
            else:
                logger.error("No valid address data found in validated_data")
                raise serializers.ValidationError({
                    'address_id': 'Either address or address_id must be provided'
                })
            
            result = super().create(validated_data)
            logger.info(f"Successfully created ContactAddress with ID: {result.id}")
            return result
        except Exception as e:
            logger.error(f"Error creating ContactAddress: {str(e)}")
            raise

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


class ContactSerializer(TaggitSerializer, serializers.ModelSerializer):
    """Serializer for Contact model."""
    id = serializers.IntegerField(required=False)
    email_addresses = ContactEmailAddressSerializer(many=True, required=False)
    phone_numbers = ContactPhoneNumberSerializer(many=True, required=False)
    addresses = ContactAddressSerializer(many=True, required=False)
    organization_name = serializers.CharField(required=False)
    linked_organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        allow_null=True,
        required=False
    )
    linked_organization_name = serializers.CharField(
        source='linked_organization.name',
        read_only=True,
        allow_null=True
    )
    tags = TagListSerializerField(required=False)

    def validate(self, attrs):
        """Validate the contact data."""
        logger.info("Starting contact validation with data: %s", attrs)

        # Check for organization name and ID conflict
        org_name = attrs.get('organization_name')
        linked_org = attrs.get('linked_organization')
        if org_name and linked_org:
            logger.error("Cannot provide both organization name and organization ID")
            raise serializers.ValidationError({'organization_name': 'Cannot provide both organization name and organization ID'})

        # Validate nested objects
        if 'email_addresses' in attrs:
            logger.info("Validating %d email addresses", len(attrs['email_addresses']))
            for email in attrs['email_addresses']:
                if not email.get('email'):
                    raise serializers.ValidationError({
                        'email_addresses': 'Email is required for each email address.'
                    })

        if 'phone_numbers' in attrs:
            logger.info("Validating %d phone numbers", len(attrs['phone_numbers']))
            for phone in attrs['phone_numbers']:
                if not phone.get('phone_number'):
                    raise serializers.ValidationError({
                        'phone_numbers': 'Phone number is required for each phone number.'
                    })

        if 'addresses' in attrs:
            logger.info("Validating %d addresses", len(attrs['addresses']))
            for address in attrs['addresses']:
                if not address.get('address') and not address.get('address_id'):
                    raise serializers.ValidationError({
                        'addresses': 'Either address or address_id must be provided for each address.'
                    })

        # Validate primary flags
        email_addresses = attrs.get('email_addresses', [])
        phone_numbers = attrs.get('phone_numbers', [])
        addresses = attrs.get('addresses', [])

        logger.info("Validating primary flags for %d email addresses, %d phone numbers, and %d addresses",
                    len(email_addresses), len(phone_numbers), len(addresses))

        self._validate_primary_flags(email_addresses, 'email_addresses')
        self._validate_primary_flags(phone_numbers, 'phone_numbers')
        self._validate_primary_flags(addresses, 'addresses')

        # Validate required fields for new contacts
        if not self.instance:
            required_fields = ['first_name', 'last_name']
            missing_fields = [field for field in required_fields if not attrs.get(field)]
            if missing_fields:
                logger.error("Missing required fields: %s", missing_fields)
                raise serializers.ValidationError({
                    field: 'This field is required.'
                    for field in missing_fields
                })

        logger.info("Contact validation completed successfully")
        return attrs

    def create(self, validated_data):
        """Create a new contact with nested objects."""
        logger.info(f"Creating new contact with data: {validated_data}")
        
        email_addresses = validated_data.pop('email_addresses', [])
        phone_numbers = validated_data.pop('phone_numbers', [])
        addresses = validated_data.pop('addresses', [])
        tags = validated_data.pop('tags', [])

        # Create the contact first
        contact = Contact.objects.create(**validated_data)
        logger.info(f"Created contact with ID: {contact.id}")
        
        # Set tags if provided
        if tags:
            logger.info(f"Setting tags: {tags}")
            contact.tags.set(tags)

        # Create nested objects with proper context
        for email_data in email_addresses:
            logger.info(f"Creating email address: {email_data}")
            serializer = ContactEmailAddressSerializer(data=email_data, context={'contact': contact})
            serializer.is_valid(raise_exception=True)
            serializer.save(contact=contact)

        for phone_data in phone_numbers:
            logger.info(f"Creating phone number: {phone_data}")
            serializer = ContactPhoneNumberSerializer(data=phone_data, context={'contact': contact})
            serializer.is_valid(raise_exception=True)
            serializer.save(contact=contact)

        for address_data in addresses:
            logger.info(f"Creating address: {address_data}")
            serializer = ContactAddressSerializer(data=address_data, context={'contact': contact})
            serializer.is_valid(raise_exception=True)
            serializer.save(contact=contact)

        return contact

    def update(self, instance, validated_data):
        """Update a contact and its nested objects."""
        logger.info(f"Updating contact {instance.id} with data: {validated_data}")
        
        email_addresses = validated_data.pop('email_addresses', None)
        phone_numbers = validated_data.pop('phone_numbers', None)
        addresses = validated_data.pop('addresses', None)
        tags = validated_data.pop('tags', None)

        # Update base fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        logger.info(f"Updated contact base fields for ID: {instance.id}")

        # Update tags if provided
        if tags is not None:
            logger.info(f"Updating tags to: {tags}")
            instance.tags.set(tags)

        # Update nested objects if provided
        if email_addresses is not None:
            logger.info(f"Updating {len(email_addresses)} email addresses")
            self._update_nested_objects(
                instance, 'email_addresses', email_addresses,
                ContactEmailAddressSerializer
            )

        if phone_numbers is not None:
            logger.info(f"Updating {len(phone_numbers)} phone numbers")
            self._update_nested_objects(
                instance, 'phone_numbers', phone_numbers,
                ContactPhoneNumberSerializer
            )

        if addresses is not None:
            logger.info(f"Updating {len(addresses)} addresses")
            self._update_nested_objects(
                instance, 'addresses', addresses,
                ContactAddressSerializer
            )

        return instance

    def _update_nested_objects(self, instance, field_name, objects_data, serializer_class):
        """Helper method to update nested objects."""
        # Get existing objects
        existing_objects = {obj.id: obj for obj in getattr(instance, field_name).all()}
        
        # Update or create objects
        for obj_data in objects_data:
            obj_id = obj_data.get('id')
            if obj_id and obj_id in existing_objects:
                # Update existing object
                obj = existing_objects.pop(obj_id)
                serializer = serializer_class(
                    obj, data=obj_data,
                    context={'contact': instance}
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
            else:
                # Create new object
                serializer = serializer_class(
                    data=obj_data,
                    context={'contact': instance}
                )
                serializer.is_valid(raise_exception=True)
                serializer.save(contact=instance)
        
        # Delete remaining objects
        for obj in existing_objects.values():
            obj.delete()

    def to_representation(self, instance):
        """Convert instance to representation."""
        data = super().to_representation(instance)
        # Sort tags to ensure consistent order
        if 'tags' in data:
            data['tags'] = sorted(data['tags'])
        return data

    class Meta:
        model = Contact
        fields = [
            'id', 'first_name', 'last_name', 'title', 'organization_name',
            'linked_organization', 'linked_organization_name',
            'contact_type', 'status', 'source', 'notes', 'tags', 'custom_fields',
            'email_addresses', 'phone_numbers', 'addresses',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def _validate_primary_flags(self, items, field_name):
        # Implementation of _validate_primary_flags method
        pass
