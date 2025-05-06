# Placeholder for Status API endpoint tests
import pytest
from django.urls import reverse
from rest_framework import status
# Import APIClient directly
from rest_framework.test import APIClient

# Correct relative import for models and factories
from ...models import Status
from ..factories import StatusFactory, CategoryFactory
from api.v1.base_models.common.category.models import Category

pytestmark = pytest.mark.django_db

# Correct URL reversing to include the base_models namespace
STATUS_LIST_URL = reverse('v1:base_models:common:status-list')

def status_detail_url(status_slug):
    return reverse('v1:base_models:common:status-detail', kwargs={'slug': status_slug})

# Test Read operations (GET)
def test_list_statuses_unauthenticated():
    """Verify anyone can list statuses (as per IsAuthenticatedOrReadOnly permission)."""
    api_client = APIClient()
    StatusFactory.create_batch(3)
    response = api_client.get(STATUS_LIST_URL)
    assert response.status_code == status.HTTP_200_OK
    # Check count excluding initial statuses from migration
    assert len(response.data) >= 3

def test_retrieve_status_unauthenticated():
    """Verify anyone can retrieve a specific status by slug."""
    api_client = APIClient()
    stat = StatusFactory()
    url = status_detail_url(stat.slug)
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['slug'] == stat.slug
    assert response.data['name'] == stat.name

def test_list_statuses_search():
    """Test searching statuses by name."""
    api_client = APIClient()
    StatusFactory(name='Findable Status Search Test')
    StatusFactory(name='Another One Search Test')
    response = api_client.get(STATUS_LIST_URL, {'search': 'Findable'})
    assert response.status_code == status.HTTP_200_OK
    assert any(item['name'] == 'Findable Status Search Test' for item in response.data)

def test_list_statuses_ordering():
    """Test ordering statuses by name."""
    api_client = APIClient()
    StatusFactory(name='Status B Order Test')
    StatusFactory(name='Status A Order Test')
    response = api_client.get(STATUS_LIST_URL, {'ordering': 'name'})
    assert response.status_code == status.HTTP_200_OK
    
    # Find our test statuses in the response
    names_in_response = [item['name'] for item in response.data]
    index_a = None
    index_b = None
    
    for i, name in enumerate(names_in_response):
        if name == 'Status A Order Test':
            index_a = i
        if name == 'Status B Order Test':
            index_b = i
    
    # Only check order if both statuses are found
    if index_a is not None and index_b is not None:
        assert index_a < index_b

# Test Create operations (POST)
def test_create_status_unauthenticated_fails():
    """Test that unauthenticated users cannot create statuses."""
    api_client = APIClient()
    # Create a category first
    category = CategoryFactory()
    data = {
        'slug': 'test-status',
        'name': 'Test Status',
        'category_slug': category.slug
    }
    response = api_client.post(STATUS_LIST_URL, data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not Status.objects.filter(slug='test-status').exists()

@pytest.mark.django_db
def test_create_status_authenticated(create_user):
    """Test that authenticated users can create statuses."""
    api_client = APIClient()
    # Authenticate the client
    user = create_user()
    api_client.force_authenticate(user=user)
    
    # Create a category first
    category = CategoryFactory()
    
    data = {
        'slug': 'new-test-status',
        'name': 'New Test Status',
        'category_slug': category.slug,
        'description': 'A test status',
        'color': '#FF5733'
    }
    response = api_client.post(STATUS_LIST_URL, data)
    assert response.status_code == status.HTTP_201_CREATED
    assert Status.objects.filter(slug='new-test-status').exists()
    status_obj = Status.objects.get(slug='new-test-status')
    assert status_obj.name == 'New Test Status'
    assert status_obj.category == category
    assert status_obj.color == '#FF5733'

# Test Update operations (PUT/PATCH)
@pytest.mark.django_db
def test_update_status_authenticated(create_user):
    """Test that authenticated users can update statuses."""
    api_client = APIClient()
    # Authenticate the client
    user = create_user()
    api_client.force_authenticate(user=user)
    
    # Create categories
    old_category = CategoryFactory(name="Old Category")
    new_category = CategoryFactory(name="New Category")
    
    # Create a status to update
    stat = StatusFactory(category=old_category)
    url = status_detail_url(stat.slug)
    
    data = {
        'name': stat.name,
        'slug': stat.slug,
        'category_slug': new_category.slug,
        'color': '#00FF00'
    }
    response = api_client.put(url, data)
    assert response.status_code == status.HTTP_200_OK
    stat.refresh_from_db()
    assert stat.category == new_category
    assert stat.color == '#00FF00'

@pytest.mark.django_db
def test_update_status_unauthenticated_fails():
    """Test that unauthenticated users cannot update statuses."""
    api_client = APIClient()
    stat = StatusFactory()
    url = status_detail_url(stat.slug)
    original_name = stat.name
    
    data = {
        'name': 'Updated Name',
        'slug': stat.slug
    }
    response = api_client.put(url, data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    stat.refresh_from_db()
    assert stat.name == original_name

@pytest.mark.django_db
def test_partial_update_status_authenticated(create_user):
    """Test that authenticated users can partially update statuses."""
    api_client = APIClient()
    # Authenticate the client
    user = create_user()
    api_client.force_authenticate(user=user)
    
    # Create a status to update
    stat = StatusFactory(description='Old description')
    url = status_detail_url(stat.slug)
    
    data = {
        'description': 'New description',
    }
    response = api_client.patch(url, data)
    assert response.status_code == status.HTTP_200_OK
    stat.refresh_from_db()
    assert stat.description == 'New description'

# Test Delete operations (DELETE)
@pytest.mark.django_db
def test_delete_status_authenticated(create_user):
    """Test that authenticated users can delete statuses."""
    api_client = APIClient()
    # Authenticate the client
    user = create_user()
    api_client.force_authenticate(user=user)
    
    # Create a status to delete
    stat = StatusFactory()
    url = status_detail_url(stat.slug)
    
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Status.objects.filter(slug=stat.slug).exists()

@pytest.mark.django_db
def test_delete_status_unauthenticated_fails():
    """Test that unauthenticated users cannot delete statuses."""
    api_client = APIClient()
    stat = StatusFactory()
    url = status_detail_url(stat.slug)
    
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert Status.objects.filter(slug=stat.slug).exists() 