from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer

from api.v1.base_models.organization.models import Organization, OrganizationType, OrganizationMembership
from api.v1.base_models.contact.models import Contact
from api.v1.base_models.common.address.models import Address
from api.v1.base_models.common.currency.models import Currency
from django.contrib.auth.models import User, Group
from api.v1.base_models.user.serializers import UserSimpleSerializer

class OrganizationSimpleSerializer(serializers.ModelSerializer):
    """A simple serializer for Organization, showing only essential fields."""
    class Meta:
        model = Organization
        fields = ('id', 'name', 'code') # Add/remove fields as needed for context
        read_only_fields = fields # Typically read-only in this context

class OrganizationSerializer(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField(required=False)
    custom_fields = serializers.JSONField(required=False, allow_null=True)
    metadata = serializers.JSONField(required=False, allow_null=True)
    primary_contact = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all(),
        required=False,
        allow_null=True
    )
    primary_address = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(),
        required=False,
        allow_null=True
    )
    currency = serializers.SlugRelatedField(
        slug_field='code',
        queryset=Currency.objects.all(),
        required=False,
        allow_null=True
    )
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        required=False,
        allow_null=True
    )

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
            'created_at',
            'updated_at',
            'created_by',
            'updated_by'
        ]
        read_only_fields = ['name', 'description', 'created_at', 'updated_at', 'created_by', 'updated_by']

class OrganizationMembershipSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationMembership model"""
    
    user_detail = serializers.SerializerMethodField(read_only=True)
    organization_detail = serializers.SerializerMethodField(read_only=True)
    roles_detail = serializers.SerializerMethodField(read_only=True)

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all())
    roles = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), many=True)

    class Meta:
        model = OrganizationMembership
        fields = [
            'id',
            'user',
            'user_detail',
            'organization',
            'organization_detail',
            'roles',
            'roles_detail',
            'is_active',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by'
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by'
        ]

    def get_user_detail(self, obj):
        """Return nested user data"""
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email
        }

    def get_organization_detail(self, obj):
        """Return nested organization data"""
        return {
            'id': obj.organization.id,
            'name': obj.organization.name,
            'code': obj.organization.code
        }

    def get_roles_detail(self, obj):
        """Return nested roles data as a list"""
        return [
            {
                'id': role.id,
                'name': role.name
            }
            for role in obj.roles.all()
        ]

    def validate(self, attrs):
        """Validate the membership data"""
        # The unique constraint on user+organization will handle duplicate memberships
        return attrs 