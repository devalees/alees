import pytest
from rest_framework.exceptions import ValidationError
from taggit.models import Tag

from api.v1.base_models.organization.models import Organization
from api.v1.base_models.organization.serializers import OrganizationSerializer
from api.v1.base_models.organization.tests.factories import (
    OrganizationFactory,
    OrganizationTypeFactory,
    ContactFactory,
    AddressFactory,
    CurrencyFactory
)

@pytest.fixture
@pytest.mark.django_db
def organization_type():
    return OrganizationTypeFactory()

@pytest.fixture
@pytest.mark.django_db
def contact():
    return ContactFactory()

@pytest.fixture
@pytest.mark.django_db
def address():
    return AddressFactory()

@pytest.fixture
@pytest.mark.django_db
def currency():
    return CurrencyFactory()

@pytest.fixture
@pytest.mark.django_db
def parent_org():
    return OrganizationFactory()

@pytest.fixture
def valid_org_data(organization_type, contact, address, currency, parent_org):
    return {
        'name': 'Test Organization',
        'code': 'TEST001',
        'organization_type': organization_type.id,
        'status': 'active',
        'primary_contact': contact.id,
        'primary_address': address.id,
        'currency': currency.code,
        'parent': parent_org.id,
        'timezone': 'UTC',
        'language': 'en',
        'tags': ['test', 'organization']
    }

@pytest.mark.django_db
def test_serializer_creates_valid_organization(valid_org_data, organization_type, contact, address, currency, parent_org):
    """Test that serializer can create a valid organization with all required fields."""
    serializer = OrganizationSerializer(data=valid_org_data)
    assert serializer.is_valid(), serializer.errors
    organization = serializer.save()

    assert organization.name == valid_org_data['name']
    assert organization.code == valid_org_data['code']
    assert organization.organization_type == organization_type
    assert organization.status == valid_org_data['status']
    assert organization.primary_contact == contact
    assert organization.primary_address == address
    assert organization.currency == currency
    assert organization.parent == parent_org
    assert organization.timezone == valid_org_data['timezone']
    assert organization.language == valid_org_data['language']
    assert set(tag.name for tag in organization.tags.all()) == set(valid_org_data['tags'])

@pytest.mark.django_db
def test_serializer_validates_unique_code(organization_type):
    """Test that serializer validates unique code constraint."""
    existing_org = OrganizationFactory(code='EXIST001')
    
    data = {
        'name': 'New Organization',
        'code': 'EXIST001',  # Same code as existing org
        'organization_type': organization_type.id,
        'status': 'active'
    }

    serializer = OrganizationSerializer(data=data)
    assert not serializer.is_valid()
    assert 'code' in serializer.errors
    assert 'already exists' in str(serializer.errors['code'])

@pytest.mark.django_db
def test_serializer_validates_custom_fields(organization_type):
    """Test that serializer validates custom fields format."""
    data = {
        'name': 'Test Organization',
        'code': 'TEST002',
        'organization_type': organization_type.id,
        'status': 'active',
        'custom_fields': 'invalid_json'  # Invalid JSON string
    }

    serializer = OrganizationSerializer(data=data)
    assert not serializer.is_valid()
    assert 'custom_fields' in serializer.errors

@pytest.mark.django_db
def test_serializer_validates_metadata(organization_type):
    """Test that serializer validates metadata format."""
    data = {
        'name': 'Test Organization',
        'code': 'TEST003',
        'organization_type': organization_type.id,
        'status': 'active',
        'metadata': 'invalid_json'  # Invalid JSON string
    }

    serializer = OrganizationSerializer(data=data)
    assert not serializer.is_valid()
    assert 'metadata' in serializer.errors

@pytest.mark.django_db
def test_serializer_handles_null_foreign_keys(organization_type):
    """Test that serializer handles null values for foreign keys."""
    data = {
        'name': 'Test Organization',
        'code': 'TEST004',
        'organization_type': organization_type.id,
        'status': 'active',
        'primary_contact': None,
        'primary_address': None,
        'currency': None,
        'parent': None
    }

    serializer = OrganizationSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    organization = serializer.save()

    assert organization.primary_contact is None
    assert organization.primary_address is None
    assert organization.currency is None
    assert organization.parent is None

@pytest.mark.django_db
def test_serializer_representation(organization_type, contact, address, currency, parent_org):
    """Test that serializer correctly represents organization data."""
    organization = OrganizationFactory(
        name='Test Org',
        code='TEST005',
        organization_type=organization_type,
        primary_contact=contact,
        primary_address=address,
        currency=currency,
        parent=parent_org,
        timezone='UTC',
        language='en'
    )
    organization.tags.add('test', 'org')

    serializer = OrganizationSerializer(organization)
    data = serializer.data

    assert data['name'] == organization.name
    assert data['code'] == organization.code
    assert data['organization_type'] == organization.organization_type.id
    assert data['status'] == organization.status
    assert data['primary_contact'] == organization.primary_contact.id
    assert data['primary_address'] == organization.primary_address.id
    assert data['currency'] == organization.currency.code
    assert data['parent'] == organization.parent.id
    assert data['timezone'] == organization.timezone
    assert data['language'] == organization.language
    assert set(data['tags']) == {'test', 'org'} 