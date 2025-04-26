import pytest
from django.db import IntegrityError
from api.v1.base_models.organization.models import OrganizationType
from django.contrib.auth import get_user_model
from crum import impersonate

User = get_user_model()

@pytest.mark.django_db
class TestOrganizationTypePytest:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def org_type_data(self):
        return {
            'name': 'Test Organization Type',
            'description': 'Test Description'
        }

    def test_create_organization_type(self, user, org_type_data):
        """Test creating an organization type with valid data."""
        with impersonate(user):
            org_type = OrganizationType.objects.create(**org_type_data)
        assert org_type.name == org_type_data['name']
        assert org_type.description == org_type_data['description']
        assert org_type.created_by == user
        assert org_type.updated_by == user
        assert org_type.created_at is not None
        assert org_type.updated_at is not None

    def test_unique_name_constraint(self, user, org_type_data):
        """Test that organization type names must be unique."""
        with impersonate(user):
            OrganizationType.objects.create(**org_type_data)
            with pytest.raises(IntegrityError):
                OrganizationType.objects.create(**org_type_data)

    def test_string_representation(self, user, org_type_data):
        """Test the string representation of the organization type."""
        with impersonate(user):
            org_type = OrganizationType.objects.create(**org_type_data)
        assert str(org_type) == org_type_data['name']

    def test_blank_description(self, user, org_type_data):
        """Test that description field can be blank."""
        data = org_type_data.copy()
        data['description'] = ''
        with impersonate(user):
            org_type = OrganizationType.objects.create(**data)
        assert org_type.description == ''
        assert isinstance(org_type, OrganizationType) 