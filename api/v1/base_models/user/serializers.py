from rest_framework import serializers
from django.core.exceptions import ValidationError
import json

from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model.
    Handles validation and representation of UserProfile instances.
    """
    class Meta:
        model = UserProfile
        fields = [
            'job_title',
            'employee_id',
            'phone_number',
            'manager',
            'date_of_birth',
            'employment_type',
            'profile_picture',
            'language',
            'timezone',
            'notification_preferences',
            'custom_fields'
        ]
        extra_kwargs = {
            'profile_picture': {'required': False, 'allow_null': True},
            'manager': {'required': False, 'allow_null': True},
            'custom_fields': {'required': False},
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