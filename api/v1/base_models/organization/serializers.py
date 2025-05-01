from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer

from api.v1.base_models.organization.models import Organization, OrganizationType
from api.v1.base_models.contact.models import Contact
from api.v1.base_models.common.address.models import Address
from api.v1.base_models.common.currency.models import Currency

class OrganizationSerializer(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField(required=False)
    custom_fields = serializers.JSONField(required=False, allow_null=True)
    metadata = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = Organization
        fields = [
            'id',
            'name',
            'code',
            'organization_type',
            'status',
            'effective_date',
            'primary_contact',
            'primary_address',
            'currency',
            'parent',
            'timezone',
            'language',
            'tags',
            'custom_fields',
            'metadata',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_code(self, value):
        """Validate that the code is unique."""
        if self.instance and self.instance.code == value:
            return value
            
        if Organization.objects.filter(code=value).exists():
            raise serializers.ValidationError(
                f"An organization with code '{value}' already exists."
            )
        return value

    def validate_custom_fields(self, value):
        """Validate that custom_fields is a valid JSON object."""
        if value is None:
            return value
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "Custom fields must be a valid JSON object."
            )
        return value

    def validate_metadata(self, value):
        """Validate that metadata is a valid JSON object."""
        if value is None:
            return value
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "Metadata must be a valid JSON object."
            )
        return value

    def validate_organization_type(self, value):
        """Validate that the organization type exists."""
        if not OrganizationType.objects.filter(id=value.id).exists():
            raise serializers.ValidationError(
                f"Organization type with id {value.id} does not exist."
            )
        return value

    def validate_primary_contact(self, value):
        """Validate that the primary contact exists if provided."""
        if value and not Contact.objects.filter(id=value.id).exists():
            raise serializers.ValidationError(
                f"Contact with id {value.id} does not exist."
            )
        return value

    def validate_primary_address(self, value):
        """Validate that the primary address exists if provided."""
        if value and not Address.objects.filter(id=value.id).exists():
            raise serializers.ValidationError(
                f"Address with id {value.id} does not exist."
            )
        return value

    def validate_currency(self, value):
        """Validate that the currency exists if provided."""
        if value and not Currency.objects.filter(code=value.code).exists():
            raise serializers.ValidationError("Invalid currency.")
        return value

    def validate_parent(self, value):
        """Validate that the parent organization exists if provided."""
        if value and not Organization.objects.filter(id=value.id).exists():
            raise serializers.ValidationError(
                f"Parent organization with id {value.id} does not exist."
            )
        return value

class OrganizationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationType
        fields = [
            'name',
            'description',
        ]
        read_only_fields = ['name', 'description'] 