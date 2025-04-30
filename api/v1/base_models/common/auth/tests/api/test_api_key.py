import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_api_key.models import APIKey
from django.utils import timezone
from datetime import timedelta

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def valid_api_key():
    """Create a valid API key for testing."""
    _, key = APIKey.objects.create_key(name="Test API Key")
    return key

@pytest.fixture
def expired_api_key():
    """Create an expired API key for testing."""
    _, key = APIKey.objects.create_key(
        name="Expired API Key",
        expiry_date=timezone.now() - timedelta(days=1)
    )
    return key

@pytest.fixture
def revoked_api_key():
    """Create a revoked API key for testing."""
    _, key = APIKey.objects.create_key(name="Revoked API Key")
    api_key = APIKey.objects.get_from_key(key)
    api_key.revoked = True
    api_key.save()
    return key

@pytest.mark.django_db
def test_api_key_required(api_client):
    """Test that API key is required for access."""
    url = reverse('v1:user:my-profile')
    response = api_client.get(url)
    assert response.status_code == 401  # Unauthorized without API key

@pytest.mark.django_db
def test_invalid_api_key(api_client):
    """Test that invalid API key is rejected."""
    url = reverse('v1:user:my-profile')
    response = api_client.get(url, HTTP_X_API_KEY='invalid-key')
    assert response.status_code == 401  # Unauthorized with invalid key

@pytest.mark.django_db
def test_valid_api_key(api_client, valid_api_key):
    """Test that valid API key is accepted."""
    url = reverse('v1:user:my-profile')
    headers = {'X-Api-Key': valid_api_key}
    response = api_client.get(url, **headers)
    assert response.status_code == 200  # Success with valid key
    assert response.data is not None  # Ensure we got a response

@pytest.mark.django_db
def test_expired_api_key(api_client, expired_api_key):
    """Test that expired API key is rejected."""
    url = reverse('v1:user:my-profile')
    headers = {'X-Api-Key': expired_api_key}
    response = api_client.get(url, **headers)
    assert response.status_code == 401  # Unauthorized with expired key

@pytest.mark.django_db
def test_revoked_api_key(api_client, revoked_api_key):
    """Test that revoked API key is rejected."""
    url = reverse('v1:user:my-profile')
    headers = {'X-Api-Key': revoked_api_key}
    response = api_client.get(url, **headers)
    assert response.status_code == 401  # Unauthorized with revoked key 