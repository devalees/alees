import pytest
import json
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from api.v1.base_models.user.tests.factories import UserFactory

User = get_user_model()

@pytest.mark.django_db
class TestMyProfileView:
    """Test cases for MyProfileView API endpoints."""

    @pytest.fixture
    def client(self):
        """Create an API client."""
        return APIClient()

    @pytest.fixture
    def user(self):
        """Create a test user."""
        return UserFactory()

    def test_get_my_profile_unauthenticated(self, client):
        """Test GET /api/v1/user/profiles/me/ without authentication."""
        response = client.get('/api/v1/user/profiles/me/')
        assert response.status_code == 401

    def test_get_my_profile_authenticated(self, client, user):
        """Test GET /api/v1/user/profiles/me/ with authentication."""
        client.force_authenticate(user=user)
        response = client.get('/api/v1/user/profiles/me/')
        assert response.status_code == 200
        assert response.data['username'] == user.username
        assert response.data['email'] == user.email
        assert response.data['first_name'] == user.first_name
        assert response.data['last_name'] == user.last_name

    def test_update_my_profile(self, client, user):
        """Test PUT /api/v1/user/profiles/me/ with authentication."""
        client.force_authenticate(user=user)
        data = {
            'job_title': 'Software Engineer',
            'phone_number': '+1234567890',
            'language': 'en',
            'timezone': 'UTC'
        }
        response = client.put('/api/v1/user/profiles/me/', data=data, format='json')
        assert response.status_code == 200
        assert response.data['job_title'] == data['job_title']
        assert response.data['phone_number'] == data['phone_number']
        assert response.data['language'] == data['language']
        assert response.data['timezone'] == data['timezone']

    def test_partial_update_my_profile(self, client, user):
        """Test PATCH /api/v1/user/profiles/me/ with authentication."""
        client.force_authenticate(user=user)
        data = {
            'job_title': 'Senior Software Engineer'
        }
        response = client.patch('/api/v1/user/profiles/me/', data=data, format='json')
        assert response.status_code == 200
        assert response.data['job_title'] == data['job_title']
        # Verify other fields remain unchanged
        assert response.data['username'] == user.username
        assert response.data['email'] == user.email

    def test_update_custom_fields(self, client, user):
        """Test updating custom_fields with various formats."""
        client.force_authenticate(user=user)
        
        # Test with valid JSON object as string
        data = {'custom_fields': json.dumps({'key': 'value'})}
        response = client.patch('/api/v1/user/profiles/me/', data=data, format='json')
        assert response.status_code == 200
        assert response.data['custom_fields'] == {'key': 'value'}

        # Test with valid JSON object as dict
        data = {'custom_fields': {'another_key': 'another_value'}}
        response = client.patch('/api/v1/user/profiles/me/', data=data, format='json')
        assert response.status_code == 200
        assert response.data['custom_fields'] == {'another_key': 'another_value'}

        # Test with None value
        data = {'custom_fields': None}
        response = client.patch('/api/v1/user/profiles/me/', data=data, format='json')
        assert response.status_code == 200
        assert response.data['custom_fields'] == {}

        # Test with invalid JSON string
        data = {'custom_fields': 'invalid json'}
        response = client.patch('/api/v1/user/profiles/me/', data=data, format='json')
        assert response.status_code == 400
        assert 'custom_fields' in response.data

        # Test with invalid type
        data = {'custom_fields': 123}
        response = client.patch('/api/v1/user/profiles/me/', data=data, format='json')
        assert response.status_code == 400
        assert 'custom_fields' in response.data

    def test_update_profile_picture(self, client, user):
        """Test updating profile_picture field."""
        client.force_authenticate(user=user)
        
        # Test setting profile_picture to None
        data = {'profile_picture': None}
        response = client.patch('/api/v1/user/profiles/me/', data=data, format='json')
        assert response.status_code == 200
        assert response.data['profile_picture'] is None 