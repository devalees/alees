import pytest
from django.core.exceptions import ValidationError
from ..factories import UserFactory, UserProfileFactory

@pytest.mark.django_db
class TestUserFactory:
    def test_user_creation(self):
        user = UserFactory()
        assert user.username is not None
        assert user.email is not None
        assert user.is_active is True
        assert user.check_password('password123') is True

@pytest.mark.django_db
class TestUserProfileFactory:
    def test_profile_creation(self):
        profile = UserProfileFactory()
        assert profile.user is not None
        assert profile.job_title is not None
        assert profile.employee_id is not None
        assert profile.phone_number is not None
        assert profile.profile_picture is None  # As specified
        assert profile.language is not None
        assert profile.timezone is not None
        assert isinstance(profile.notification_preferences, dict)
        assert isinstance(profile.custom_fields, dict)

    def test_profile_with_manager(self):
        manager = UserFactory()
        profile = UserProfileFactory(manager=manager)
        assert profile.manager == manager

    def test_unique_employee_id(self):
        profile1 = UserProfileFactory()
        profile2 = UserProfileFactory()
        assert profile1.employee_id != profile2.employee_id

    def test_circular_dependency_prevention(self):
        # This should not raise an error due to profile=None in SubFactory
        profile = UserProfileFactory()
        assert profile.user.profile == profile 