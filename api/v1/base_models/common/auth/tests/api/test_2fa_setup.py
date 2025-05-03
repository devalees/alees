import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django_otp.plugins.otp_totp.models import TOTPDevice
from api.v1.base_models.user.tests.factories import UserFactory

# Define the correct full namespace
AUTH_NAMESPACE = "v1:base_models:common"

@pytest.mark.django_db
class TestTOTPSetupView:
    def test_setup_totp_unauthenticated(self):
        client = APIClient()
        url = reverse(f'{AUTH_NAMESPACE}:2fa-totp-setup')
        response = client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_setup_totp_authenticated(self):
        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)
        url = reverse(f'{AUTH_NAMESPACE}:2fa-totp-setup')
        response = client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'secret' in response.data
        assert 'qr_url' in response.data
        assert 'provisioning_uri' in response.data
        
        # Verify device was created but not confirmed
        device = TOTPDevice.objects.get(user=user)
        assert not device.confirmed

@pytest.mark.django_db
class TestTOTPVerifyView:
    def test_verify_totp_unauthenticated(self):
        client = APIClient()
        url = reverse(f'{AUTH_NAMESPACE}:2fa-totp-verify')
        response = client.post(url, {'token': '123456'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_totp_no_device(self):
        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)
        url = reverse(f'{AUTH_NAMESPACE}:2fa-totp-verify')
        response = client.post(url, {'token': '123456'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_totp_invalid_token(self):
        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)
        
        # Setup TOTP first
        setup_url = reverse(f'{AUTH_NAMESPACE}:2fa-totp-setup')
        client.post(setup_url)
        
        # Try to verify with invalid token
        url = reverse(f'{AUTH_NAMESPACE}:2fa-totp-verify')
        response = client.post(url, {'token': '123456'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Verify device still not confirmed
        device = TOTPDevice.objects.get(user=user)
        assert not device.confirmed

    def test_verify_totp_success(self, mocker):
        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)
        
        # Setup TOTP first
        setup_url = reverse(f'{AUTH_NAMESPACE}:2fa-totp-setup')
        setup_response = client.post(setup_url)
        device = TOTPDevice.objects.get(user=user)
        
        # Mock the token verification
        mocker.patch.object(TOTPDevice, 'verify_token', return_value=True)
        
        # Verify with (mocked) valid token
        url = reverse(f'{AUTH_NAMESPACE}:2fa-totp-verify')
        response = client.post(url, {'token': '123456'})
        assert response.status_code == status.HTTP_200_OK
        
        # Verify device is now confirmed
        device.refresh_from_db()
        assert device.confirmed 