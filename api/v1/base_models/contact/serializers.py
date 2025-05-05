from django.contrib.auth import get_user_model
from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from api.v1.base_models.common.address.serializers import AddressSerializer
from api.v1.base_models.common.address.models import Address
from api.v1.base_models.organization.models import Organization
from api.v1.base_models.organization.serializers import OrganizationSimpleSerializer
from core.serializers.mixins import OrganizationScopedSerializerMixin

from api.v1.base_models.contact.models import (
    Contact, ContactEmailAddress, ContactPhoneNumber, ContactAddress
)
from api.v1.base_models.contact.choices import (
    ContactType, ContactStatus, ContactSource,
    EmailType, PhoneType, AddressType
)

import logging
from django.db import transaction
from core.rbac.utils import get_user_request_context

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


class ContactSerializer(OrganizationScopedSerializerMixin, TaggitSerializer, serializers.ModelSerializer):
    """Serializer for Contact model."""
    id = serializers.IntegerField(required=False)
    email_addresses = ContactEmailAddressSerializer(many=True, required=False)
    phone_numbers = ContactPhoneNumberSerializer(many=True, required=False)
    addresses = ContactAddressSerializer(many=True, required=False)
    organization_name = serializers.CharField(required=False, allow_blank=True)
    
    # Read-only field provided by the mixin
    organization = OrganizationSimpleSerializer(read_only=True)
    
    # Writable field for explicitly setting the org (required for tests)
    organization_id = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(), 
        source='organization', 
        required=False, 
        write_only=True
    )
    
    tags = TagListSerializerField(required=False)

    # Read-only fields for displaying created/updated by user info
    created_by_username = serializers.SerializerMethodField()
    updated_by_username = serializers.SerializerMethodField()

    def validate_organization_id(self, value):
        """Validate that organization_id is provided when required."""
        # If organization_id is None (not provided) and this is a create operation
        if value is None and not self.instance:
            # Only superusers or single-org users can create contacts without specifying an organization
            request = self.context.get('request')
            user = request.user if request and hasattr(request, 'user') else None
            
            # Check if superuser or single-org user
            if user and (user.is_superuser or self.is_single_org_user(user)):
                return value
                
            # Multi-org users must provide organization_id
            raise serializers.ValidationError('This field is required when creating a contact.')
        return value

    def is_single_org_user(self, user):
        """Check if user belongs to exactly one organization."""
        active_org_ids, is_single_org = get_user_request_context(user)
        return is_single_org

    def validate(self, attrs):
        """Validate the data as a whole."""
        # First check if this is a create operation and organization_id is missing for multi-org users
        if not self.instance:  # Create operation
            request = self.context.get('request')
            user = request.user if request and hasattr(request, 'user') else None
            
            # For multi-org non-superusers, organization_id is required
            if not (user and (user.is_superuser or self.is_single_org_user(user))) and 'organization' not in attrs:
                raise serializers.ValidationError({
                    'organization_id': 'This field is required when creating a contact.'
                })
                
        # Then call parent mixin to handle org validation (with superuser bypass)
        attrs = super().validate(attrs)
        
        # Additional validations specific to Contact data structure
        # Validate organization_name uniqueness within the same organization
        if 'organization_name' in attrs and attrs.get('organization_name'):
            # Determine the organization_id to use for uniqueness check
            organization_id = None
            if 'organization' in attrs and attrs.get('organization'):
                organization_id = attrs['organization'].pk
            elif self.instance:
                organization_id = self.instance.organization_id
            elif hasattr(self, '_validated_organization_id'):
                organization_id = self._validated_organization_id
            
            # Query for existing contacts with same org name in this organization
            if organization_id:
                existing = Contact.objects.filter(
                    organization_name=attrs['organization_name'],
                    organization_id=organization_id
                )
                if self.instance:
                    existing = existing.exclude(pk=self.instance.pk)
                    
                if existing.exists():
                    raise serializers.ValidationError({
                        'organization_name': f"Contact with this organization name already exists in this organization."
                    })
                    
        # Validate primary flags for nested related items
        self._validate_primary_flags(attrs.get('email_addresses', []), 'email_addresses')
        self._validate_primary_flags(attrs.get('phone_numbers', []), 'phone_numbers')
        self._validate_primary_flags(attrs.get('addresses', []), 'addresses')
        
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """Create a new contact with nested related objects."""
        logger.info(f"Creating new contact with data: {validated_data}")
        
        user = self.context.get('request').user if self.context.get('request') else None
        
        # Handle organization for superusers
        if user and user.is_superuser and 'organization' not in validated_data:
            # For superusers, ensure we have an organization_id
            # Get organization_id from the request data
            request = self.context.get('request')
            if request:
                organization_id = request.data.get('organization_id')
                if organization_id:
                    from api.v1.base_models.organization.models import Organization
                    try:
                        organization = Organization.objects.get(pk=organization_id)
                        validated_data['organization'] = organization
                    except Organization.DoesNotExist:
                        raise serializers.ValidationError({"organization_id": f"Organization with id {organization_id} does not exist."})
        
        # Extract nested related objects
        email_addresses_data = validated_data.pop('email_addresses', [])
        phone_numbers_data = validated_data.pop('phone_numbers', [])
        addresses_data = validated_data.pop('addresses', [])
        
        # Explicitly handle tags - get them before TaggitSerializer pops them
        tags_data = validated_data.pop('tags', [])

        # Create the main Contact instance
        contact = Contact.objects.create(**validated_data)

        # Process tags explicitly
        if tags_data:
            contact.tags.add(*tags_data)
            logger.info(f"Added tags to contact {contact.id}: {tags_data}")

        # Create nested related objects
        if email_addresses_data:
            self._process_nested_objects(contact, email_addresses_data, ContactEmailAddressSerializer)
        
        if phone_numbers_data:
            self._process_nested_objects(contact, phone_numbers_data, ContactPhoneNumberSerializer)
        
        if addresses_data:
            self._process_nested_objects(contact, addresses_data, ContactAddressSerializer)

        logger.info(f"Successfully created contact {contact.id}")
        return contact
        
    def _process_nested_objects(self, contact, nested_data_list, RelatedSerializer):
        """Helper to create nested objects during contact creation."""
        context = {'contact': contact, 'request': self.context.get('request')}
        for item_data in nested_data_list:
            serializer = RelatedSerializer(data=item_data, context=context)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
            else:
                logger.warning(f"Invalid data for nested object: {serializer.errors}")
                
    @transaction.atomic
    def update(self, instance, validated_data):
        """Update a contact and its nested related objects."""
        tags_data = validated_data.get('tags', None)
        logger.info(f"Updating contact with validated data: {validated_data}")
        
        # Handle nested objects
        emails_data = validated_data.pop('email_addresses', None)
        phones_data = validated_data.pop('phone_numbers', None)
        addresses_data = validated_data.pop('addresses', None)
        
        # Let the parent class handle the main instance update with any remaining fields
        instance = super().update(instance, validated_data)

        # Explicitly handle tags after super() call
        if tags_data is not None:
            logger.info(f"Updating tags for contact {instance.id} with: {tags_data}")
            # Clear existing tags and add new ones
            instance.tags.clear()
            for tag in tags_data:
                instance.tags.add(tag)
            # Ensure changes are saved
            instance.save()
            logger.info(f"Updated tags for contact {instance.id} to: {[t.name for t in instance.tags.all()]}")
        
        # Update nested objects using helper methods
        if emails_data is not None:
            self.update_email_addresses(instance, emails_data)
        
        if phones_data is not None:
            self.update_phone_numbers(instance, phones_data)
        
        if addresses_data is not None:
            self.update_addresses(instance, addresses_data)
        
        # Refresh instance after all updates
        instance.refresh_from_db()
        
        return instance

    def to_representation(self, instance):
        """Format the output according to the needs."""
        ret = super().to_representation(instance)
        
        # Ensure nested serializers are used for detailed output
        if hasattr(instance, 'email_addresses'):
            ret['email_addresses'] = ContactEmailAddressSerializer(
                instance.email_addresses.all(), many=True
            ).data
            
        if hasattr(instance, 'phone_numbers'):
            ret['phone_numbers'] = ContactPhoneNumberSerializer(
                instance.phone_numbers.all(), many=True
            ).data
            
        if hasattr(instance, 'addresses'):
            ret['addresses'] = ContactAddressSerializer(
                instance.addresses.all(), many=True
            ).data
            
        # Further customization can happen here
        return ret

    class Meta:
        model = Contact
        fields = [
            'id', 'first_name', 'last_name', 'title', 'organization_name',
            'organization',
            'organization_id',
            'contact_type', 'status', 'source', 'notes', 'tags', 
            'custom_fields',
            'email_addresses', 'phone_numbers', 'addresses',
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'created_by_username', 'updated_by_username'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at', 'created_by', 'updated_by',
                          'created_by_username', 'updated_by_username']

    def _validate_primary_flags(self, items, field_name):
        """Helper to ensure only one item is marked as primary."""
        primary_count = sum(1 for item in items if item.get('is_primary'))
        if primary_count > 1:
            raise serializers.ValidationError({
                field_name: f"Only one {field_name.replace('_', ' ')} can be marked as primary."
            })

    def get_created_by_username(self, obj):
        return obj.created_by.username if obj.created_by else None

    def get_updated_by_username(self, obj):
        return obj.updated_by.username if obj.updated_by else None

    def update_email_addresses(self, instance, emails_data):
        """Helper method to update email addresses for a contact."""
        logger.info(f"Updating email addresses for contact {instance.id} with data: {emails_data}")
        existing_ids = set(instance.email_addresses.values_list('id', flat=True))
        updated_ids = set()
        
        # Create a context with the contact instance
        context = {'contact': instance, 'request': self.context.get('request')}
        
        for email_data in emails_data:
            email_id = email_data.get('id')
            if email_id:
                if email_id in existing_ids:
                    # Update existing email
                    email = instance.email_addresses.get(id=email_id)
                    serializer = ContactEmailAddressSerializer(email, data=email_data, partial=True, context=context)
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
                        updated_ids.add(email_id)
                else:
                    # ID provided but doesn't belong to this contact or doesn't exist - skip
                    logger.warning(f"Attempted to update email with invalid ID {email_id} for contact {instance.id}")
            else:
                # Create new email
                serializer = ContactEmailAddressSerializer(data=email_data, context=context)
                if serializer.is_valid(raise_exception=True):
                    email = serializer.save()
                    if email and hasattr(email, 'id'):
                        updated_ids.add(email.id)
        
        # Delete any email addresses that weren't in the update data
        # This implements the "replace" behavior for nested objects
        to_delete_ids = existing_ids - updated_ids
        if to_delete_ids:
            instance.email_addresses.filter(id__in=to_delete_ids).delete()
            logger.info(f"Deleted {len(to_delete_ids)} email addresses for contact {instance.id}")
        
        return instance

    def update_phone_numbers(self, instance, phones_data):
        """Helper method to update phone numbers for a contact."""
        logger.info(f"Updating phone numbers for contact {instance.id} with data: {phones_data}")
        existing_ids = set(instance.phone_numbers.values_list('id', flat=True))
        updated_ids = set()
        
        # Create a context with the contact instance
        context = {'contact': instance, 'request': self.context.get('request')}
        
        for phone_data in phones_data:
            phone_id = phone_data.get('id')
            if phone_id:
                if phone_id in existing_ids:
                    # Update existing phone
                    phone = instance.phone_numbers.get(id=phone_id)
                    serializer = ContactPhoneNumberSerializer(phone, data=phone_data, partial=True, context=context)
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
                        updated_ids.add(phone_id)
                else:
                    # ID provided but doesn't belong to this contact or doesn't exist - skip
                    logger.warning(f"Attempted to update phone with invalid ID {phone_id} for contact {instance.id}")
            else:
                # Create new phone
                serializer = ContactPhoneNumberSerializer(data=phone_data, context=context)
                if serializer.is_valid(raise_exception=True):
                    phone = serializer.save()
                    if phone and hasattr(phone, 'id'):
                        updated_ids.add(phone.id)
        
        # Delete any phone numbers that weren't in the update data
        to_delete_ids = existing_ids - updated_ids
        if to_delete_ids:
            instance.phone_numbers.filter(id__in=to_delete_ids).delete()
            logger.info(f"Deleted {len(to_delete_ids)} phone numbers for contact {instance.id}")
        
        return instance

    def update_addresses(self, instance, addresses_data):
        """Helper method to update addresses for a contact."""
        logger.info(f"Updating addresses for contact {instance.id} with data: {addresses_data}")
        existing_ids = set(instance.addresses.values_list('id', flat=True))
        updated_ids = set()
        
        # Create a context with the contact instance
        context = {'contact': instance, 'request': self.context.get('request')}
        
        for address_data in addresses_data:
            address_id = address_data.get('id')
            if address_id:
                if address_id in existing_ids:
                    # Update existing address
                    address = instance.addresses.get(id=address_id)
                    serializer = ContactAddressSerializer(address, data=address_data, partial=True, context=context)
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
                        updated_ids.add(address_id)
                else:
                    # ID provided but doesn't belong to this contact or doesn't exist - skip
                    logger.warning(f"Attempted to update address with invalid ID {address_id} for contact {instance.id}")
            else:
                # Create new address
                serializer = ContactAddressSerializer(data=address_data, context=context)
                if serializer.is_valid(raise_exception=True):
                    address = serializer.save()
                    if address and hasattr(address, 'id'):
                        updated_ids.add(address.id)
        
        # Delete any addresses that weren't in the update data
        to_delete_ids = existing_ids - updated_ids
        if to_delete_ids:
            instance.addresses.filter(id__in=to_delete_ids).delete()
            logger.info(f"Deleted {len(to_delete_ids)} addresses for contact {instance.id}")
        
        return instance
