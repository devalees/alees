import pytest
from django.urls import reverse, resolve
from rest_framework.test import APIClient

from api.v1.base_models.contact.views import ContactViewSet

@pytest.mark.django_db
class TestContactURLs:
    """Test cases for Contact API URL routing."""

    def test_contact_list_url(self):
        """Test that the contact list URL resolves to the correct view."""
        url = reverse('v1:contact:contact-list')
        assert resolve(url).func.cls == ContactViewSet
        assert resolve(url).func.actions == {'get': 'list', 'post': 'create', 'head': 'list'}

    def test_contact_detail_url(self):
        """Test that the contact detail URL resolves to the correct view."""
        url = reverse('v1:contact:contact-detail', args=[1])
        assert resolve(url).func.cls == ContactViewSet
        assert resolve(url).func.actions == {
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy',
            'head': 'retrieve'
        }

    def test_url_patterns(self):
        """Test that all expected URL patterns are present."""
        url_patterns = [
            reverse('v1:contact:contact-list'),
            reverse('v1:contact:contact-detail', args=[1]),
        ]
        
        for url in url_patterns:
            response = APIClient().get(url)
            assert response.status_code in [200, 401]  # 401 is acceptable for unauthenticated requests 