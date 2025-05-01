import pytest
from api.v1.base_models.organization.tests.factories import OrganizationTypeFactory, OrganizationFactory

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

@pytest.mark.django_db
def test_organization_factory():
    # Test creating a single instance
    org = OrganizationFactory()
    assert org.name is not None
    assert org.code.startswith('ORG')
    assert org.organization_type is not None
    assert org.status in ['active', 'inactive', 'archived']
    assert org.parent is None
    assert org.effective_date is not None
    assert org.end_date is None
    assert org.primary_contact is not None
    assert org.primary_address is not None
    assert org.currency is not None
    assert org.timezone in ['UTC', 'America/New_York', 'Europe/London']
    assert org.language in ['en', 'fr', 'es']
    assert isinstance(org.metadata, dict)
    assert isinstance(org.custom_fields, dict)

    # Test django_get_or_create functionality
    same_code = OrganizationFactory(code=org.code)
    assert same_code.id == org.id  # Should get the same instance

    # Test creating multiple instances
    orgs = OrganizationFactory.create_batch(3)
    assert len(orgs) == 3
    assert len(set(o.code for o in orgs)) == 3  # All codes should be unique

@pytest.mark.django_db
def test_organization_factory_hierarchy():
    # Test creating a parent organization
    parent = OrganizationFactory()
    
    # Test creating a child organization
    child = OrganizationFactory(parent=parent)
    assert child.parent == parent
    assert child in parent.children.all()
    
    # Test creating a grandchild organization
    grandchild = OrganizationFactory(parent=child)
    assert grandchild.parent == child
    assert grandchild in child.children.all()
    assert grandchild in parent.get_descendants() 