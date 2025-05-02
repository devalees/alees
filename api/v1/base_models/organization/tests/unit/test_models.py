import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from crum import impersonate
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase

from api.v1.base_models.organization.models import OrganizationType, Organization, OrganizationMembership
from api.v1.base_models.contact.models import Contact, ContactEmailAddress
from api.v1.base_models.common.address.models import Address
from api.v1.base_models.common.currency.models import Currency
from api.v1.base_models.organization.tests.factories import OrganizationFactory, OrganizationTypeFactory
from api.v1.base_models.user.tests.factories import UserFactory

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user(
        username='test_user',
        email='test@example.com',
        password='test_password'
    )

@pytest.fixture
def org_type(user):
    with impersonate(user):
        return OrganizationType.objects.create(
            name="Test Organization Type",
            description="Test Description"
        )

@pytest.fixture
def currency(user):
    with impersonate(user):
        return Currency.objects.create(
            code="USD",
            name="US Dollar",
            symbol="$"
        )

@pytest.fixture
def contact(user):
    with impersonate(user):
        contact = Contact.objects.create(
            first_name="John",
            last_name="Doe"
        )
        ContactEmailAddress.objects.create(
            contact=contact,
            email="john@example.com",
            is_primary=True
        )
        return contact

@pytest.fixture
def address(user):
    with impersonate(user):
        return Address.objects.create(
            street_address_1="123 Main St",
            city="Test City",
            country="US"
        )

@pytest.fixture
def parent_org(user, org_type):
    with impersonate(user):
        return Organization.objects.create(
            name="Parent Organization",
            code="PARENT",
            organization_type=org_type,
            status="active"
        )

@pytest.fixture
def organization(user, org_type, parent_org, contact, address, currency):
    with impersonate(user):
        return Organization.objects.create(
            name="Test Organization",
            code="TEST",
            organization_type=org_type,
            parent=parent_org,
            status="active",
            primary_contact=contact,
            primary_address=address,
            currency=currency,
            timezone="UTC",
            language="en"
        )

@pytest.fixture
def role(user):
    with impersonate(user):
        return Group.objects.create(name="Test Role")


@pytest.mark.django_db
class TestOrganizationType:
    def test_organization_type_creation(self, org_type, user):
        """Test that an OrganizationType can be created with all fields."""
        assert org_type.name == "Test Organization Type"
        assert org_type.description == "Test Description"
        assert org_type.created_by == user
        assert org_type.updated_by == user
        assert org_type.created_at is not None
        assert org_type.updated_at is not None

    def test_organization_type_str(self, org_type):
        """Test the string representation of an OrganizationType."""
        assert str(org_type) == "Test Organization Type"

    def test_organization_type_unique_name(self, user, org_type):
        """Test that OrganizationType names must be unique."""
        with pytest.raises(Exception):
            with impersonate(user):
                OrganizationType.objects.create(
                    name="Test Organization Type",
                    description="Another Description"
                )

    def test_organization_type_timestamps(self, org_type):
        """Test that timestamps are set correctly."""
        now = timezone.now()
        assert org_type.created_at <= now
        assert org_type.updated_at <= now

    def test_organization_type_update(self, user, org_type):
        """Test that updating an OrganizationType updates the updated_at timestamp."""
        old_updated_at = org_type.updated_at
        with impersonate(user):
            org_type.description = "Updated Description"
            org_type.save()
        org_type.refresh_from_db()
        assert org_type.updated_at > old_updated_at
        assert org_type.description == "Updated Description"


@pytest.mark.django_db
class TestOrganization:
    def test_organization_creation(self, organization, org_type, parent_org, contact, address, currency, user):
        """Test that an Organization can be created with all fields."""
        assert organization.name == "Test Organization"
        assert organization.code == "TEST"
        assert organization.organization_type == org_type
        assert organization.parent == parent_org
        assert organization.status == "active"
        assert organization.primary_contact == contact
        assert organization.primary_address == address
        assert organization.currency == currency
        assert organization.timezone == "UTC"
        assert organization.language == "en"
        assert organization.created_by == user
        assert organization.updated_by == user
        assert organization.created_at is not None
        assert organization.updated_at is not None

    def test_organization_str(self, organization):
        """Test the string representation of an Organization."""
        assert str(organization) == "Test Organization"

    def test_organization_unique_code(self, user, org_type, organization):
        """Test that Organization codes must be unique."""
        with pytest.raises(Exception):
            with impersonate(user):
                Organization.objects.create(
                    name="Another Organization",
                    code="TEST",  # Same code as existing org
                    organization_type=org_type,
                    status="active"
                )

    def test_organization_required_fields(self, user):
        """Test that required fields are enforced."""
        with pytest.raises(Exception):
            with impersonate(user):
                Organization.objects.create(
                    name="Test Org",  # Missing required fields
                )

    def test_organization_hierarchy(self, organization, parent_org):
        """Test MPTT hierarchy functionality."""
        assert organization.get_ancestors().count() == 1
        assert organization.get_ancestors().first() == parent_org
        assert parent_org.get_descendants().count() == 1
        assert parent_org.get_descendants().first() == organization

    def test_organization_tags(self, organization):
        """Test tag functionality."""
        organization.tags.add("test", "organization")
        assert organization.tags.count() == 2
        assert organization.tags.filter(name="test").exists()
        assert organization.tags.filter(name="organization").exists()

    def test_organization_custom_fields(self, organization):
        """Test custom fields functionality."""
        organization.custom_fields = {"key": "value"}
        organization.save()
        organization.refresh_from_db()
        assert organization.custom_fields == {"key": "value"}

    def test_organization_metadata(self, organization):
        """Test metadata functionality."""
        organization.metadata = {"key": "value"}
        organization.save()
        organization.refresh_from_db()
        assert organization.metadata == {"key": "value"}


@pytest.mark.django_db
class TestOrganizationMembership:
    """Test cases for the OrganizationMembership model."""
    def test_membership_creation(self, user, organization, role):
        """Test that an OrganizationMembership can be created with required fields."""
        with impersonate(user):
            membership = OrganizationMembership.objects.create(
                user=user,
                organization=organization,
                role=role
            )
            assert membership.user == user
            assert membership.organization == organization
            assert membership.role == role
            assert membership.is_active is True

    def test_unique_together_constraint(self, user, organization, role):
        """Test that a user can only have one membership per organization."""
        with impersonate(user):
            # Create first membership
            membership = OrganizationMembership(
                user=user,
                organization=organization,
                role=role
            )
            membership.full_clean()
            membership.save()

            # Attempt to create duplicate membership
            duplicate = OrganizationMembership(
                user=user,
                organization=organization,
                role=role
            )
            with pytest.raises(ValidationError):
                duplicate.full_clean()

    def test_default_values(self, user, organization, role):
        """Test default values are set correctly."""
        with impersonate(user):
            membership = OrganizationMembership.objects.create(
                user=user,
                organization=organization,
                role=role
            )
            assert membership.is_active is True

    def test_foreign_key_constraints(self, user, organization, role):
        """Test that foreign key constraints work correctly."""
        with impersonate(user):
            membership = OrganizationMembership.objects.create(
                user=user,
                organization=organization,
                role=role
            )
            assert membership.user.id == user.id
            assert membership.organization.id == organization.id
            assert membership.role.id == role.id

    def test_string_representation(self, user, organization, role):
        """Test the string representation of an OrganizationMembership."""
        with impersonate(user):
            membership = OrganizationMembership.objects.create(
                user=user,
                organization=organization,
                role=role
            )
            expected = f"{user.username} in {organization.name} as {role.name}"
            assert str(membership) == expected

    def test_inherited_fields(self, user, organization, role):
        """Test that inherited fields from Timestamped and Auditable exist."""
        with impersonate(user):
            membership = OrganizationMembership.objects.create(
                user=user,
                organization=organization,
                role=role
            )
            assert membership.created_at is not None
            assert membership.updated_at is not None
            assert membership.created_by == user
            assert membership.updated_by == user 