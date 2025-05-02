import pytest
from rest_framework.exceptions import ValidationError
from taggit.models import Tag

from api.v1.base_models.organization.models import Organization
from api.v1.base_models.organization.serializers import OrganizationSerializer
from api.v1.base_models.organization.tests.factories import (
    OrganizationFactory,
    OrganizationTypeFactory,
    AddressFactory,
    CurrencyFactory,
)
from api.v1.base_models.contact.tests.factories import ContactFactory
from api.v1.base_models.organization.tests.factories import (
    OrganizationMembershipFactory,
    GroupFactory,
    UserFactory,
)
from api.v1.base_models.organization.serializers import OrganizationMembershipSerializer

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

@pytest.mark.django_db
class TestOrganizationMembershipSerializer:
    """Test cases for OrganizationMembershipSerializer"""

    @pytest.fixture
    def user(self):
        """Create a test user"""
        return UserFactory()

    @pytest.fixture
    def organization(self):
        """Create a test organization"""
        return OrganizationFactory()

    @pytest.fixture
    def role(self):
        """Create a test role (Django Group)"""
        return GroupFactory()

    @pytest.fixture
    def membership(self, user, organization, role):
        """Create a test membership"""
        return OrganizationMembershipFactory(
            user=user,
            organization=organization,
            role=role,
            is_active=True
        )

    def test_serializer_representation(self, membership):
        """Test the serializer representation includes all required fields"""
        serializer = OrganizationMembershipSerializer(membership)
        data = serializer.data

        assert 'id' in data
        assert 'user' in data
        assert 'organization' in data
        assert 'role' in data
        assert 'is_active' in data
        assert 'created_at' in data
        assert 'updated_at' in data
        assert 'created_by' in data
        assert 'updated_by' in data

    def test_serializer_validation_unique_together(self, user, organization, role):
        """Test that unique_together constraint is enforced"""
        # Create first membership
        OrganizationMembershipFactory(
            user=user,
            organization=organization,
            role=role
        )

        # Try to create duplicate membership
        data = {
            'user': user.id,
            'organization': organization.id,
            'role': role.id,
            'is_active': True
        }
        serializer = OrganizationMembershipSerializer(data=data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors

    def test_serializer_read_only_fields(self, membership):
        """Test that read-only fields cannot be modified"""
        data = {
            'id': 999,  # Try to modify read-only field
            'created_at': '2024-01-01T00:00:00Z',  # Try to modify read-only field
            'updated_at': '2024-01-01T00:00:00Z',  # Try to modify read-only field
            'created_by': 999,  # Try to modify read-only field
            'updated_by': 999,  # Try to modify read-only field
            'is_active': False  # This should be modifiable
        }
        serializer = OrganizationMembershipSerializer(membership, data=data, partial=True)
        assert serializer.is_valid()
        assert serializer.validated_data == {'is_active': False}

    def test_serializer_nested_representation(self, membership):
        """Test that nested user, organization, and role data is included"""
        serializer = OrganizationMembershipSerializer(membership)
        data = serializer.data

        assert isinstance(data['user_detail'], dict)
        assert 'id' in data['user_detail']
        assert 'username' in data['user_detail']

        assert isinstance(data['organization_detail'], dict)
        assert 'id' in data['organization_detail']
        assert 'name' in data['organization_detail']

        assert isinstance(data['role_detail'], dict)
        assert 'id' in data['role_detail']
        assert 'name' in data['role_detail']

    def test_serializer_create(self, user, organization, role):
        """Test creating a new membership via serializer"""
        data = {
            'user': user.id,
            'organization': organization.id,
            'role': role.id,
            'is_active': True
        }
        serializer = OrganizationMembershipSerializer(data=data)
        assert serializer.is_valid()
        membership = serializer.save()
        assert membership.user == user
        assert membership.organization == organization
        assert membership.role == role
        assert membership.is_active is True

    def test_serializer_update(self, membership):
        """Test updating a membership via serializer"""
        data = {
            'is_active': False
        }
        serializer = OrganizationMembershipSerializer(membership, data=data, partial=True)
        assert serializer.is_valid()
        updated_membership = serializer.save()
        assert updated_membership.is_active is False 