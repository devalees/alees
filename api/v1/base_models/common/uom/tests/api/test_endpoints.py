import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from django.utils.http import urlencode
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from api.v1.base_models.common.uom.models import UomType, UnitOfMeasure
# Use absolute import for factories
from api.v1.base_models.common.uom.tests.factories import UomTypeFactory, UnitOfMeasureFactory

pytestmark = pytest.mark.django_db

# Define the correct full namespace
UOM_NAMESPACE = "v1:base_models:common"

User = get_user_model()

@pytest.fixture
def test_user():
    """Create a test user with the necessary permissions."""
    user = User.objects.create_user(
        username='test_user',
        email='test@example.com',
        password='password123'
    )
    # Add view permissions for UomType and UnitOfMeasure
    view_uomtype_perm = Permission.objects.get(codename='view_uomtype')
    view_uom_perm = Permission.objects.get(codename='view_unitofmeasure')
    user.user_permissions.add(view_uomtype_perm, view_uom_perm)
    return user

@pytest.fixture
def api_client(test_user):
    """Return an authenticated API client."""
    client = APIClient()
    client.force_authenticate(user=test_user)
    return client


# --- UomType API Tests ---

def test_list_uom_types(api_client):
    """Test retrieving a list of UomTypes (includes migrated data)."""
    # Create a couple *extra* unique types for testing listing > initial data
    UomTypeFactory.create(code="EXTRA_TYPE_1", name="Extra Type 1")
    UomTypeFactory.create(code="EXTRA_TYPE_2", name="Extra Type 2")

    initial_types_count = UomType.objects.count() # Should be >= 2 + initial migrated types

    url = reverse(f'{UOM_NAMESPACE}:uomtype-list')
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == initial_types_count # Check total count
    # Check that results list is not empty and contains expected fields
    assert len(response.data['results']) > 0
    assert 'code' in response.data['results'][0]
    assert 'name' in response.data['results'][0]
    # Check for a known migrated type in the results (might not be first page)
    # For more robust check, would need pagination handling or filter
    # assert any(item['code'] == 'LENGTH' for item in response.data['results'])


def test_retrieve_uom_type(api_client):
    """Test retrieving a single migrated UomType by its code."""
    uom_type_code = "MASS" # Use a code known to exist from migration
    uom_type = UomType.objects.get(code=uom_type_code)
    url = reverse(f'{UOM_NAMESPACE}:uomtype-detail', kwargs={'code': uom_type_code})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['code'] == uom_type_code
    assert response.data['name'] == uom_type.name # Check against DB object name

def test_retrieve_nonexistent_uom_type(api_client):
    """Test retrieving a non-existent UomType returns 404."""
    url = reverse(f'{UOM_NAMESPACE}:uomtype-detail', kwargs={'code': 'NONEXISTENT'})
    response = api_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

# --- UnitOfMeasure API Tests ---

def test_list_uoms(api_client):
    """Test retrieving a list of UnitOfMeasures (includes migrated data)."""
    # Create a couple *extra* unique units
    UnitOfMeasureFactory.create(code="EXTRA_UOM_1", name="Extra UOM 1")
    UnitOfMeasureFactory.create(code="EXTRA_UOM_2", name="Extra UOM 2")
    initial_uoms_count = UnitOfMeasure.objects.count()

    url = reverse(f'{UOM_NAMESPACE}:unitofmeasure-list')
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == initial_uoms_count # Check total count via pagination
    # Check that results list is not empty and contains expected fields
    assert len(response.data['results']) > 0
    assert 'code' in response.data['results'][0]
    assert 'name' in response.data['results'][0]
    assert 'uom_type' in response.data['results'][0]
    assert isinstance(response.data['results'][0]['uom_type'], dict)


def test_retrieve_uom(api_client):
    """Test retrieving a single migrated UnitOfMeasure by its code."""
    uom_code = "M" # Use Meter code from migration
    uom = UnitOfMeasure.objects.get(code=uom_code)
    url = reverse(f'{UOM_NAMESPACE}:unitofmeasure-detail', kwargs={'code': uom_code})
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['code'] == uom_code
    assert response.data['name'] == uom.name
    # Check the nested uom_type code
    assert response.data['uom_type']['code'] == uom.uom_type.code

def test_retrieve_nonexistent_uom(api_client):
    """Test retrieving non-existent UnitOfMeasure returns 404."""
    url = reverse(f'{UOM_NAMESPACE}:unitofmeasure-detail', kwargs={'code': 'NONEXISTENT'})
    response = api_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_filter_uoms_by_type(api_client):
    """Test filtering UnitOfMeasures by uom_type code (using migrated data)."""
    # Assumes migration created units for LENGTH and MASS
    length_count = UnitOfMeasure.objects.filter(uom_type__code="LENGTH").count()
    mass_count = UnitOfMeasure.objects.filter(uom_type__code="MASS").count()
    assert length_count > 0
    assert mass_count > 0

    base_url = reverse(f'{UOM_NAMESPACE}:unitofmeasure-list')
    query_params_length = urlencode({'uom_type__code': 'LENGTH'})
    url_length = f'{base_url}?{query_params_length}'
    response_length = api_client.get(url_length)

    assert response_length.status_code == status.HTTP_200_OK
    assert response_length.data['count'] == length_count # Check total count
    # Check that *all* results have the correct nested type code
    for item in response_length.data['results']:
        assert item['uom_type']['code'] == 'LENGTH'

    query_params_mass = urlencode({'uom_type__code': 'MASS'})
    url_mass = f'{base_url}?{query_params_mass}'
    response_mass = api_client.get(url_mass)
    assert response_mass.status_code == status.HTTP_200_OK
    assert response_mass.data['count'] == mass_count # Check total count
    for item in response_mass.data['results']:
        assert item['uom_type']['code'] == 'MASS'


def test_search_uom_types(api_client):
    """Test searching UomTypes."""
    # Assumes 'Length' and 'Mass' exist
    url = reverse(f'{UOM_NAMESPACE}:uomtype-list')
    response = api_client.get(url, {'search': 'Length'})
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] >= 1
    # Check if any result name matches
    assert any(t['name'] == 'Length' for t in response.data['results'])

    response = api_client.get(url, {'search': 'MASS'}) # Search by code
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] >= 1
    # Check if any result code matches
    assert any(t['code'] == 'MASS' for t in response.data['results'])

def test_search_uoms(api_client):
    """Test searching UnitOfMeasures."""
    # Assumes 'Meter' (m) and 'Kilogram' (kg) exist
    url = reverse(f'{UOM_NAMESPACE}:unitofmeasure-list')
    response = api_client.get(url, {'search': 'Meter'}) # Search by name
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] >= 1
    # Check if *any* result name matches 'Meter'
    assert any(u['name'] == 'Meter' for u in response.data['results'])

    response = api_client.get(url, {'search': 'KG'}) # Search by code
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] >= 1
    # Check if *any* result code matches 'KG'
    assert any(u['code'] == 'KG' for u in response.data['results'])

    response = api_client.get(url, {'search': 'kg'}) # Search by symbol
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] >= 1
    # Check if *any* result symbol matches 'kg'
    assert any(u['symbol'] == 'kg' for u in response.data['results'])

    response = api_client.get(url, {'search': 'Mass'}) # Search by type name
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] >= 1
    # Check if *any* result type name matches 'Mass'
    assert any(u['uom_type']['name'] == 'Mass' for u in response.data['results'])

# Add ordering tests if needed 