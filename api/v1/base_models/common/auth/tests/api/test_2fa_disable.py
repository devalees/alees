import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django_otp.plugins.otp_totp.models import TOTPDevice

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user_with_2fa():
    user = User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com'
    )
    device = TOTPDevice.objects.create(
        user=user,
        name='default',
        confirmed=True
    )
    return user

@pytest.mark.django_db
def test_disable_2fa_unauthenticated(api_client):
    """Test that unauthenticated users cannot disable 2FA."""
    url = reverse('v1:base_models:auth:2fa-totp-disable')
    response = api_client.post(url, {'password': 'testpass123'})
    assert response.status_code == 401

@pytest.mark.django_db
def test_disable_2fa_authenticated_no_2fa(api_client, user_with_2fa):
    """Test that users without 2FA cannot disable it."""
    api_client.force_authenticate(user=user_with_2fa)
    # Delete the 2FA device
    TOTPDevice.objects.filter(user=user_with_2fa).delete()
    
    url = reverse('v1:base_models:auth:2fa-totp-disable')
    response = api_client.post(url, {'password': 'testpass123'})
    assert response.status_code == 400
    assert '2FA is not enabled' in str(response.data)

@pytest.mark.django_db
def test_disable_2fa_wrong_password(api_client, user_with_2fa):
    """Test that wrong password prevents 2FA disable."""
    api_client.force_authenticate(user=user_with_2fa)
    
    url = reverse('v1:base_models:auth:2fa-totp-disable')
    response = api_client.post(url, {'password': 'wrongpass'})
    assert response.status_code == 400
    assert 'Invalid password' in str(response.data)

@pytest.mark.django_db
def test_disable_2fa_success(api_client, user_with_2fa):
    """Test successful 2FA disable."""
    api_client.force_authenticate(user=user_with_2fa)
    
    url = reverse('v1:base_models:auth:2fa-totp-disable')
    response = api_client.post(url, {'password': 'testpass123'})
    assert response.status_code == 200
    assert '2FA disabled successfully' in str(response.data)
    
    # Verify device is deleted
    assert not TOTPDevice.objects.filter(user=user_with_2fa).exists() 