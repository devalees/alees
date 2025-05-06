from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import json

from .models import UserProfile

User = get_user_model()

class UserSimpleSerializer(serializers.ModelSerializer):
    """A simple serializer for User, showing only essential fields."""
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email')
        read_only_fields = fields

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model.
    Handles validation and representation of UserProfile instances.
    """
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    profile_picture = serializers.PrimaryKeyRelatedField(
        read_only=True,
        allow_null=True,
        required=False
    )
    manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        allow_null=True,
        required=False
    )

    class Meta:
        model = UserProfile
        fields = [
            'user',
            'username', 'email', 'first_name', 'last_name',
            'job_title', 'employee_id', 'phone_number',
            'date_of_birth', 'employment_type',
            'profile_picture',
            'manager',
            'language', 'timezone', 'notification_preferences',
            'custom_fields',
            'created_at', 'updated_at',
        ]
        read_only_fields = ('user', 'created_at', 'updated_at')
        extra_kwargs = {
            'profile_picture': {'required': False, 'allow_null': True},
            'manager': {'required': False, 'allow_null': True},
            'custom_fields': {'required': False, 'allow_null': True},
            'notification_preferences': {'required': False}
        }

    def validate_custom_fields(self, value):
        """
        Validate that custom_fields is a valid JSON object.
        """
        if value is None:
            return {}
        
        if isinstance(value, dict):
            return value
            
        try:
            if isinstance(value, str):
                return json.loads(value)
        except json.JSONDecodeError:
            raise ValidationError('custom_fields must be a valid JSON object')
        
        raise ValidationError('custom_fields must be a valid JSON object')

    def to_internal_value(self, data):
        """
        Override to handle profile_picture field properly.
        """
        internal_value = super().to_internal_value(data)
        if 'profile_picture' in data and data['profile_picture'] is None:
            internal_value['profile_picture'] = None
        # Explicitly handle None for profile_picture
        if internal_value.get('profile_picture') == "":
            internal_value['profile_picture'] = None
        return internal_value

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model, including nested profile."""
    profile = UserProfileSerializer(required=False)
    organization_id = serializers.IntegerField(write_only=True, required=False)
    role_id = serializers.IntegerField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 
            'password', 'is_active', 'is_staff', 'is_superuser', 
            'date_joined', 'last_login',
            'profile', 'organization_id', 'role_id'
        )
        read_only_fields = ('id', 'is_staff', 'is_superuser', 'date_joined', 'last_login')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }
    
    def validate_email(self, value):
        """Ensure email is unique."""
        user = self.instance
        
        # If this is an update, don't validate if email hasn't changed
        if user and user.email == value:
            return value
            
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value
    
    def validate_username(self, value):
        """Ensure username is unique."""
        user = self.instance
        
        # If this is an update, don't validate if username hasn't changed
        if user and user.username == value:
            return value
            
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already in use.")
        return value
    
    def validate(self, data):
        """Additional validation"""
        # For creation, require organization_id
        if not self.instance and 'organization_id' not in data:
            request = self.context.get('request')
            if request and not request.user.is_superuser:
                active_org_ids, is_single_org = self.context.get('request').user.get_organizations().values_list('id', flat=True), False
                if len(active_org_ids) > 1:
                    raise serializers.ValidationError({'organization_id': 'This field is required for user creation.'})
        
        return data

    def create(self, validated_data):
        """Create a new User with nested profile."""
        profile_data = validated_data.pop('profile', {})
        organization_id = validated_data.pop('organization_id', None)
        role_id = validated_data.pop('role_id', None)
        password = validated_data.pop('password')
        
        # Create the user
        user = User.objects.create_user(
            **validated_data,
            password=password
        )
        
        # Create profile
        UserProfile.objects.create(
            user=user,
            **profile_data
        )
        
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        password = validated_data.pop('password', None)

        # Update User fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Handle password separately
        if password:
            instance.set_password(password)
        
        instance.save()

        # Update nested profile if data exists
        if profile_data:
            profile_serializer = UserProfileSerializer(
                instance.profile, data=profile_data, partial=True, context=self.context
            )
            if profile_serializer.is_valid(raise_exception=True):
                profile_serializer.save()
            
        return instance 