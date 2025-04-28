import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError

from api.v1.base_models.user.serializers import UserProfileSerializer
from api.v1.base_models.user.tests.factories import UserProfileFactory

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

    def test_serializer_validation_with_valid_data(self, profile_data):
        """Test serializer validation with valid data."""
        serializer = UserProfileSerializer(data=profile_data)
        assert serializer.is_valid()
        assert serializer.validated_data == profile_data

    def test_serializer_validation_with_null_profile_picture(self, profile_data):
        """Test serializer validation with null profile picture."""
        profile_data['profile_picture'] = None
        serializer = UserProfileSerializer(data=profile_data)
        assert serializer.is_valid()
        assert serializer.validated_data['profile_picture'] is None

    def test_serializer_validation_with_invalid_custom_fields(self, profile_data):
        """Test serializer validation with invalid custom fields."""
        profile_data['custom_fields'] = 'invalid_json'
        serializer = UserProfileSerializer(data=profile_data)
        assert not serializer.is_valid()
        assert 'custom_fields' in serializer.errors

    def test_serializer_representation(self, profile_data):
        """Test serializer representation."""
        profile = UserProfileFactory.build(**profile_data)
        serializer = UserProfileSerializer(profile)
        assert serializer.data['job_title'] == profile_data['job_title']
        assert serializer.data['employee_id'] == profile_data['employee_id']
        assert serializer.data['profile_picture'] == profile_data['profile_picture']
        assert serializer.data['custom_fields'] == profile_data['custom_fields'] 