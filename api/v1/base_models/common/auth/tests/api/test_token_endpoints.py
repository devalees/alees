import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_user():
    return User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com'
    )

@pytest.mark.django_db
class TestTokenEndpoints:
    def test_obtain_token_success(self, api_client, test_user):
        """Test successful token obtain endpoint"""
        response = api_client.post(
            '/api/v1/auth/token/',
            {'username': 'testuser', 'password': 'testpass123'},
            format='json'
        )
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_obtain_token_invalid_credentials(self, api_client):
        """Test token obtain with invalid credentials"""
        response = api_client.post(
            '/api/v1/auth/token/',
            {'username': 'wronguser', 'password': 'wrongpass'},
            format='json'
        )
        assert response.status_code == 401

    def test_obtain_token_missing_credentials(self, api_client):
        """Test token obtain with missing credentials"""
        response = api_client.post(
            '/api/v1/auth/token/',
            {},
            format='json'
        )
        assert response.status_code == 400

    def test_refresh_token_success(self, api_client, test_user):
        """Test successful token refresh"""
        # First get a refresh token
        refresh = RefreshToken.for_user(test_user)
        response = api_client.post(
            '/api/v1/auth/token/refresh/',
            {'refresh': str(refresh)},
            format='json'
        )
        assert response.status_code == 200
        assert 'access' in response.data

    def test_refresh_token_invalid(self, api_client):
        """Test token refresh with invalid token"""
        response = api_client.post(
            '/api/v1/auth/token/refresh/',
            {'refresh': 'invalid_token'},
            format='json'
        )
        assert response.status_code == 401

    def test_refresh_token_missing(self, api_client):
        """Test token refresh with missing token"""
        response = api_client.post(
            '/api/v1/auth/token/refresh/',
            {},
            format='json'
        )
        assert response.status_code == 400 