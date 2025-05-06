import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

@pytest.fixture
def api_client():
    """Return an API client for testing."""
    return APIClient()

@pytest.fixture
def create_user():
    """Create and return a user for testing."""
    def _create_user(username='testuser', email='test@example.com', password='password123', is_staff=False, is_superuser=False):
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=is_staff,
            is_superuser=is_superuser
        )
    return _create_user 