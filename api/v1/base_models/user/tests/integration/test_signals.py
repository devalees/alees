import pytest
from django.contrib.auth import get_user_model
from api.v1.base_models.user.tests.factories import UserFactory
from api.v1.base_models.user.models import UserProfile

User = get_user_model()

@pytest.mark.django_db
class TestUserProfileAutoCreation:
    def test_profile_auto_creation_on_user_save(self):
        # Create a new user
        user = UserFactory()
        
        # Verify profile was automatically created
        assert hasattr(user, 'profile')
        assert isinstance(user.profile, UserProfile)
        
        # Verify profile has default values
        assert user.profile.language is not None
        assert user.profile.timezone is not None
        assert user.profile.profile_picture is None
        assert isinstance(user.profile.notification_preferences, dict)
        assert isinstance(user.profile.custom_fields, dict)

    def test_profile_not_created_for_existing_user(self):
        # Create a user with an existing profile
        user = UserFactory()
        existing_profile = user.profile
        
        # Modify the user
        user.first_name = "Test"
        user.save()
        
        # Verify the same profile instance is used
        assert user.profile == existing_profile
        assert user.profile.pk == existing_profile.pk 