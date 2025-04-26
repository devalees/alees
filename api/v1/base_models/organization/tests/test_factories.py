import pytest
from api.v1.base_models.organization.tests.factories import OrganizationTypeFactory

@pytest.mark.django_db
def test_organization_type_factory():
    # Test creating a single instance
    org_type = OrganizationTypeFactory()
    assert org_type.name in ['Company', 'Department', 'Customer', 'Supplier', 'Branch']
    assert org_type.description is not None

    # Test django_get_or_create functionality
    same_name = OrganizationTypeFactory(name=org_type.name)
    assert same_name.id == org_type.id  # Should get the same instance

    # Test creating multiple instances
    org_types = OrganizationTypeFactory.create_batch(3)
    assert len(org_types) == 3
    assert len(set(org.name for org in org_types)) == 3  # All names should be unique 