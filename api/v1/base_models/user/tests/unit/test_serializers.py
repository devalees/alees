import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model

from api.v1.base_models.user.serializers import UserProfileSerializer
from api.v1.base_models.user.tests.factories import UserProfileFactory, UserFactory

User = get_user_model()

@pytest.mark.django_db
class TestUserProfileSerializer:
    """Test cases for UserProfileSerializer."""

    @pytest.fixture
    def profile_data(self):
        """Create test profile data."""
        profile = UserProfileFactory.build()
        return {
            'job_title': profile.job_title,
            'employee_id': profile.employee_id,
            'phone_number': profile.phone_number,
            'date_of_birth': profile.date_of_birth,
            'employment_type': profile.employment_type,
            'profile_picture': profile.profile_picture,
            'language': profile.language,
            'timezone': profile.timezone,
            'notification_preferences': profile.notification_preferences,
            'custom_fields': profile.custom_fields,
        }

    def test_serializer_validation_with_valid_data(self):
        data = {
            'job_title': 'Barista',
            'employee_id': 'EMP0001',
            'phone_number': '8825297631',
            'date_of_birth': '1915-01-30',
            'employment_type': 'PART_TIME',
            'profile_picture': None,
            'language': 'en-us',
            'timezone': 'UTC',
            'notification_preferences': {},
            'custom_fields': None
        }
        serializer = UserProfileSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['profile_picture'] is None

    def test_serializer_validation_with_null_profile_picture(self):
        data = {
            'job_title': 'Barista',
            'employee_id': 'EMP0001',
            'phone_number': '8825297631',
            'date_of_birth': '1915-01-30',
            'employment_type': 'PART_TIME',
            'profile_picture': None,
            'language': 'en-us',
            'timezone': 'UTC',
            'notification_preferences': {},
            'custom_fields': None
        }
        serializer = UserProfileSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['profile_picture'] is None

    def test_serializer_validation_with_invalid_custom_fields(self):
        data = {
            'job_title': 'Barista',
            'employee_id': 'EMP0001',
            'phone_number': '8825297631',
            'date_of_birth': '1915-01-30',
            'employment_type': 'PART_TIME',
            'profile_picture': None,
            'language': 'en-us',
            'timezone': 'UTC',
            'notification_preferences': {},
            'custom_fields': 'invalid json'
        }
        serializer = UserProfileSerializer(data=data)
        assert not serializer.is_valid()
        assert 'custom_fields' in serializer.errors

    def test_serializer_validation_with_valid_json_custom_fields(self):
        data = {
            'job_title': 'Barista',
            'employee_id': 'EMP0001',
            'phone_number': '8825297631',
            'date_of_birth': '1915-01-30',
            'employment_type': 'PART_TIME',
            'profile_picture': None,
            'language': 'en-us',
            'timezone': 'UTC',
            'notification_preferences': {},
            'custom_fields': '{"key": "value"}'
        }
        serializer = UserProfileSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['custom_fields'] == {"key": "value"}

    def test_serializer_validation_with_valid_dict_custom_fields(self):
        data = {
            'job_title': 'Barista',
            'employee_id': 'EMP0001',
            'phone_number': '8825297631',
            'date_of_birth': '1915-01-30',
            'employment_type': 'PART_TIME',
            'profile_picture': None,
            'language': 'en-us',
            'timezone': 'UTC',
            'notification_preferences': {},
            'custom_fields': {"key": "value"}
        }
        serializer = UserProfileSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['custom_fields'] == {"key": "value"}

    def test_serializer_validation_with_invalid_type_custom_fields(self):
        data = {
            'job_title': 'Barista',
            'employee_id': 'EMP0001',
            'phone_number': '8825297631',
            'date_of_birth': '1915-01-30',
            'employment_type': 'PART_TIME',
            'profile_picture': None,
            'language': 'en-us',
            'timezone': 'UTC',
            'notification_preferences': {},
            'custom_fields': 123  # Invalid type (not dict or str)
        }
        serializer = UserProfileSerializer(data=data)
        assert not serializer.is_valid()
        assert 'custom_fields' in serializer.errors

    def test_serializer_representation(self):
        """Test serializer representation"""
        user = UserFactory()
        serializer = UserProfileSerializer(user.profile)
        data = serializer.data

        assert data['user'] == user.id
        assert data['first_name'] == user.first_name
        assert data['last_name'] == user.last_name
        assert data['email'] == user.email
        assert data['phone_number'] == user.profile.phone_number
        assert data['profile_picture'] == user.profile.profile_picture
        assert data['custom_fields'] == user.profile.custom_fields

    def test_serializer_read_only_fields(self):
        """Test serializer read-only fields"""
        user = UserFactory()
        serializer = UserProfileSerializer(user.profile)
        data = serializer.data

        # Check read-only fields that are actually defined in the serializer
        assert 'created_at' in data
        assert 'updated_at' in data
        assert 'user' in data
        assert 'username' in data
        assert 'email' in data
        assert 'first_name' in data
        assert 'last_name' in data

    def test_serializer_manager_field(self):
        manager = UserFactory()
        data = {
            'job_title': 'Barista',
            'employee_id': 'EMP0001',
            'phone_number': '8825297631',
            'date_of_birth': '1915-01-30',
            'employment_type': 'PART_TIME',
            'profile_picture': None,
            'manager': manager.id,
            'language': 'en-us',
            'timezone': 'UTC',
            'notification_preferences': {},
            'custom_fields': None
        }
        serializer = UserProfileSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['manager'] == manager

    def test_serializer_custom_fields_validation(self):
        data = {
            'job_title': 'Barista',
            'employee_id': 'EMP0001',
            'phone_number': '8825297631',
            'date_of_birth': '1915-01-30',
            'employment_type': 'PART_TIME',
            'profile_picture': None,
            'language': 'en-us',
            'timezone': 'UTC',
            'notification_preferences': {},
            'custom_fields': None
        }
        serializer = UserProfileSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['custom_fields'] == {}

    def test_serializer_to_internal_value(self):
        """Test to_internal_value method for profile_picture handling"""
        data = {
            'job_title': 'Barista',
            'employee_id': 'EMP0001',
            'phone_number': '8825297631',
            'date_of_birth': '1915-01-30',
            'employment_type': 'PART_TIME',
            'profile_picture': None,
            'language': 'en-us',
            'timezone': 'UTC',
            'notification_preferences': {},
            'custom_fields': None
        }
        serializer = UserProfileSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['profile_picture'] is None 