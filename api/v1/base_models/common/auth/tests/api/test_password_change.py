import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from api.v1.base_models.user.tests.factories import UserFactory

User = get_user_model()

@pytest.mark.django_db
class TestPasswordChangeView:
    def test_password_change_unauthenticated(self):
        """Test that unauthenticated users cannot change password."""
        client = APIClient()
        url = reverse('v1:auth:password-change')
        response = client.post(url, {
            'old_password': 'oldpass123',
            'new_password': 'newpass123'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_password_change_missing_fields(self):
        """Test that missing required fields return 400."""
        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)
        url = reverse('v1:auth:password-change')
        
        # Test missing old_password
        response = client.post(url, {'new_password': 'newpass123'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'old_password' in response.data
        
        # Test missing new_password
        response = client.post(url, {'old_password': 'oldpass123'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'new_password' in response.data

    def test_password_change_wrong_old_password(self):
        """Test that wrong old password prevents password change."""
        client = APIClient()
        user = UserFactory()
        client.force_authenticate(user=user)
        url = reverse('v1:auth:password-change')
        
        response = client.post(url, {
            'old_password': 'wrongpass',
            'new_password': 'newpass123'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Invalid old password' in str(response.data)

    def test_password_change_success(self):
        """Test successful password change."""
        client = APIClient()
        user = UserFactory()
        old_password = 'oldpass123'
        user.set_password(old_password)
        user.save()
        client.force_authenticate(user=user)
        url = reverse('v1:auth:password-change')
        
        new_password = 'newpass123'
        response = client.post(url, {
            'old_password': old_password,
            'new_password': new_password
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'Password changed successfully' in str(response.data)
        
        # Verify new password works
        assert user.check_password(new_password) 