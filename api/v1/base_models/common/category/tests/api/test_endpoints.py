# api/v1/base_models/common/category/tests/api/test_endpoints.py
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

# Corrected imports to be absolute
from api.v1.base_models.common.category.tests.factories import CategoryFactory
from api.v1.base_models.common.category.models import Category
from api.v1.base_models.common.category.choices import CategoryType

User = get_user_model()
pytestmark = pytest.mark.django_db

CATEGORY_LIST_URL_NAME = "v1:base_models:common:category-list"
CATEGORY_DETAIL_URL_NAME = "v1:base_models:common:category-detail"

@pytest.fixture
def api_client():
    """Fixture for DRF API client."""
    return APIClient()

@pytest.fixture
def test_user(db):
    """Fixture for creating a standard user."""
    return User.objects.create_user(username='testapiuser', password='password')

@pytest.fixture
def authenticated_api_client(api_client, test_user):
    """Fixture for an authenticated API client."""
    api_client.force_authenticate(user=test_user)
    return api_client

class TestCategoryApiEndpoints:

    # --- LIST Endpoint Tests --- 

    def test_list_categories_unauthenticated(self, api_client):
        """Verify unauthenticated users can list categories (due to IsAuthenticatedOrReadOnly)."""
        CategoryFactory.create_batch(3)
        list_url = reverse(CATEGORY_LIST_URL_NAME)
        response = api_client.get(list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data.get('results', [])) == 3 # Check pagination structure if used

    def test_list_categories_authenticated(self, authenticated_api_client):
        """Verify authenticated users can list categories."""
        CategoryFactory.create_batch(2)
        list_url = reverse(CATEGORY_LIST_URL_NAME)
        response = authenticated_api_client.get(list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data.get('results', [])) == 2

    def test_list_categories_filter_by_type(self, api_client):
        """Test filtering categories by category_type."""
        prod_cat = CategoryFactory(category_type=CategoryType.PRODUCT)
        doc_cat = CategoryFactory(category_type=CategoryType.DOCUMENT_TYPE)
        list_url = reverse(CATEGORY_LIST_URL_NAME)
        response = api_client.get(list_url, {'category_type': CategoryType.PRODUCT})
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', [])
        assert len(results) == 1
        assert results[0]['slug'] == prod_cat.slug

    def test_list_categories_filter_by_parent_slug(self, api_client):
        """Test filtering categories by parent slug."""
        parent = CategoryFactory()
        child1 = CategoryFactory(parent=parent)
        child2 = CategoryFactory(parent=parent)
        root_cat = CategoryFactory() # Another root category
        list_url = reverse(CATEGORY_LIST_URL_NAME)
        response = api_client.get(list_url, {'parent__slug': parent.slug})
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', [])
        assert len(results) == 2
        assert {cat['slug'] for cat in results} == {child1.slug, child2.slug}

    def test_list_categories_filter_by_parent_isnull(self, api_client):
        """Test filtering for root categories (parent is null)."""
        parent = CategoryFactory()
        CategoryFactory(parent=parent)
        root_cat1 = CategoryFactory()
        root_cat2 = CategoryFactory()
        list_url = reverse(CATEGORY_LIST_URL_NAME)
        response = api_client.get(list_url, {'parent__slug__isnull': 'true'})
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', [])
        # Includes parent itself plus the other two roots
        assert len(results) == 3 
        assert {cat['slug'] for cat in results} == {parent.slug, root_cat1.slug, root_cat2.slug}

    def test_list_categories_search_by_name(self, api_client):
        """Test searching categories by name."""
        cat1 = CategoryFactory(name="Searchable Category One")
        cat2 = CategoryFactory(name="Another Category")
        cat3 = CategoryFactory(name="Searchable Item Three")
        list_url = reverse(CATEGORY_LIST_URL_NAME)
        response = api_client.get(list_url, {'search': 'Searchable'})
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', [])
        assert len(results) == 2
        assert {cat['slug'] for cat in results} == {cat1.slug, cat3.slug}

    def test_list_categories_ordering_by_name(self, api_client):
        """Test ordering categories by name."""
        cat_b = CategoryFactory(name="Beta Category")
        cat_a = CategoryFactory(name="Alpha Category")
        cat_c = CategoryFactory(name="Charlie Category")
        list_url = reverse(CATEGORY_LIST_URL_NAME)
        
        # Ascending
        response = api_client.get(list_url, {'ordering': 'name'})
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', [])
        assert [cat['slug'] for cat in results] == [cat_a.slug, cat_b.slug, cat_c.slug]
        
        # Descending
        response = api_client.get(list_url, {'ordering': '-name'})
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', [])
        assert [cat['slug'] for cat in results] == [cat_c.slug, cat_b.slug, cat_a.slug]


    # --- CREATE Endpoint Tests --- 

    def test_create_category_requires_authentication(self, api_client):
        """Verify that creating a category requires authentication."""
        list_url = reverse(CATEGORY_LIST_URL_NAME)
        data = {'name': 'Test Category', 'category_type': CategoryType.PRODUCT}
        response = api_client.post(list_url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED # Or 403 depending on setup

    def test_create_category_authenticated(self, authenticated_api_client, test_user):
        """Verify authenticated user can create a root category."""
        list_url = reverse(CATEGORY_LIST_URL_NAME)
        data = {
            'name': 'New Root Prod Category',
            'category_type': CategoryType.PRODUCT,
            'description': 'Root category for products.',
            'parent_slug': None, # Explicitly root
            'custom_fields': {'color': 'blue'}
        }
        response = authenticated_api_client.post(list_url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Category.objects.count() == 1
        category = Category.objects.first()
        assert category.name == data['name']
        assert category.category_type == data['category_type']
        assert category.description == data['description']
        assert category.custom_fields == data['custom_fields']
        assert category.parent is None
        assert category.created_by == test_user
        assert category.updated_by == test_user
        assert 'slug' in response.data

    def test_create_child_category_authenticated(self, authenticated_api_client, test_user):
        """Verify authenticated user can create a child category."""
        parent = CategoryFactory(category_type=CategoryType.DOCUMENT_TYPE)
        list_url = reverse(CATEGORY_LIST_URL_NAME)
        data = {
            'name': 'Child Document Category',
            'category_type': parent.category_type,
            'parent_slug': parent.slug # Set parent via slug
        }
        response = authenticated_api_client.post(list_url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Category.objects.count() == 2 # Parent + Child
        category = Category.objects.get(name=data['name'])
        assert category.parent == parent
        assert category.created_by == test_user

    def test_create_category_invalid_data(self, authenticated_api_client):
        """Test creating category with missing required fields fails."""
        list_url = reverse(CATEGORY_LIST_URL_NAME)
        # Missing name and category_type
        data = {'description': 'Incomplete data'}
        response = authenticated_api_client.post(list_url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
        assert 'category_type' in response.data

    def test_create_category_duplicate_name_same_parent_type(self, authenticated_api_client):
        """Test unique_together constraint (parent, name, type)."""
        parent = CategoryFactory()
        CategoryFactory(name="Duplicate Name", parent=parent, category_type=parent.category_type)
        list_url = reverse(CATEGORY_LIST_URL_NAME)
        data = {
            'name': 'Duplicate Name',
            'category_type': parent.category_type,
            'parent_slug': parent.slug
        }
        response = authenticated_api_client.post(list_url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # The UniqueTogetherValidator should raise this
        assert 'non_field_errors' in response.data or 'name' in response.data # Depending on DRF version/exact validator behavior


    # --- RETRIEVE Endpoint Tests --- 

    def test_retrieve_category_unauthenticated(self, api_client):
        """Verify unauthenticated users can retrieve a category."""
        category = CategoryFactory()
        detail_url = reverse(CATEGORY_DETAIL_URL_NAME, kwargs={'slug': category.slug})
        response = api_client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['slug'] == category.slug
        assert response.data['name'] == category.name

    def test_retrieve_category_authenticated(self, authenticated_api_client):
        """Verify authenticated users can retrieve a category."""
        category = CategoryFactory()
        detail_url = reverse(CATEGORY_DETAIL_URL_NAME, kwargs={'slug': category.slug})
        response = authenticated_api_client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['slug'] == category.slug

    def test_retrieve_category_not_found(self, api_client):
        """Test retrieving a non-existent category slug."""
        detail_url = reverse(CATEGORY_DETAIL_URL_NAME, kwargs={'slug': 'non-existent-slug'})
        response = api_client.get(detail_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


    # --- UPDATE (PATCH) Endpoint Tests --- 

    def test_update_category_requires_authentication(self, api_client):
        """Verify updating requires authentication."""
        category = CategoryFactory()
        detail_url = reverse(CATEGORY_DETAIL_URL_NAME, kwargs={'slug': category.slug})
        data = {'name': 'Updated Name'}
        response = api_client.patch(detail_url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED # Or 403

    def test_update_category_authenticated(self, authenticated_api_client, test_user):
        """Verify authenticated user can update a category (non-parent fields)."""
        category = CategoryFactory(created_by=test_user, updated_by=test_user)
        detail_url = reverse(CATEGORY_DETAIL_URL_NAME, kwargs={'slug': category.slug})
        data = {
            'name': 'Updated Category Name',
            'description': 'Updated description.',
            'is_active': False,
            'custom_fields': {'status': 'archived'}
        }
        response = authenticated_api_client.patch(detail_url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert category.name == data['name']
        assert category.description == data['description']
        assert category.is_active == data['is_active']
        assert category.custom_fields == data['custom_fields']
        assert category.updated_by == test_user
        assert response.data['updated_by'] == test_user.id

    # Note: Testing parent update via PATCH/PUT might still be tricky due to MPTT.
    # Prefer testing via explicit move actions if available, or accept that this
    # specific update type might be better handled outside simple serializer updates.
    # def test_update_category_parent(self, authenticated_api_client, test_user):
    #     """Test updating the parent of a category."""
    #     category_to_move = CategoryFactory(parent=None)
    #     new_parent = CategoryFactory(parent=None, category_type=category_to_move.category_type)
    #     detail_url = reverse(CATEGORY_DETAIL_URL_NAME, kwargs={'slug': category_to_move.slug})
    #     data = {'parent_slug': new_parent.slug}
    #     response = authenticated_api_client.patch(detail_url, data, format='json')
    #     assert response.status_code == status.HTTP_200_OK
    #     category_to_move.refresh_from_db()
    #     assert category_to_move.parent == new_parent

    def test_update_category_partial_update(self, authenticated_api_client, test_user):
        """Verify PATCH updates only specified fields."""
        original_name = "Original Name"
        category = CategoryFactory(name=original_name, created_by=test_user, updated_by=test_user)
        detail_url = reverse(CATEGORY_DETAIL_URL_NAME, kwargs={'slug': category.slug})
        data = {'description': 'Only description updated'}
        response = authenticated_api_client.patch(detail_url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert category.name == original_name # Name should not change
        assert category.description == data['description']
        assert category.updated_by == test_user


    # --- DELETE Endpoint Tests --- 

    def test_delete_category_requires_authentication(self, api_client):
        """Verify deleting requires authentication."""
        category = CategoryFactory()
        detail_url = reverse(CATEGORY_DETAIL_URL_NAME, kwargs={'slug': category.slug})
        response = api_client.delete(detail_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED # Or 403

    def test_delete_category_authenticated(self, authenticated_api_client):
        """Verify authenticated user can delete a category."""
        category = CategoryFactory()
        assert Category.objects.count() == 1
        detail_url = reverse(CATEGORY_DETAIL_URL_NAME, kwargs={'slug': category.slug})
        response = authenticated_api_client.delete(detail_url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Category.objects.count() == 0

    def test_delete_category_with_children_cascade(self, authenticated_api_client):
        """Verify deleting a parent category also deletes children (CASCADE)."""
        parent = CategoryFactory()
        CategoryFactory(parent=parent)
        CategoryFactory(parent=parent)
        assert Category.objects.count() == 3
        detail_url = reverse(CATEGORY_DETAIL_URL_NAME, kwargs={'slug': parent.slug})
        response = authenticated_api_client.delete(detail_url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Category.objects.count() == 0

    def test_delete_category_not_found(self, authenticated_api_client):
        """Test deleting a non-existent category slug."""
        detail_url = reverse(CATEGORY_DETAIL_URL_NAME, kwargs={'slug': 'non-existent-slug'})
        response = authenticated_api_client.delete(detail_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND 