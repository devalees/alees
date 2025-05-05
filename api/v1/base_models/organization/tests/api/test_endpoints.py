from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
import pytest
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType

from api.v1.base_models.organization.models import Organization, OrganizationType, OrganizationMembership
from api.v1.base_models.organization.tests.factories import (
    OrganizationFactory,
    OrganizationTypeFactory,
    AddressFactory,
    CurrencyFactory,
    OrganizationMembershipFactory,
    GroupFactory,
)
from api.v1.base_models.contact.tests.factories import ContactFactory
from api.v1.base_models.user.tests.factories import UserFactory

def get_permission(model, codename):
    content_type = ContentType.objects.get_for_model(model)
    return Permission.objects.get(content_type=content_type, codename=codename)

# Function to set up RBAC role with permissions
def setup_role_with_permissions(role_name, model, permissions):
    role, _ = Group.objects.get_or_create(name=role_name)
    content_type = ContentType.objects.get_for_model(model)
    perms = Permission.objects.filter(content_type=content_type, codename__in=permissions)
    role.permissions.set(perms)
    return role

@pytest.mark.django_db
class TestOrganizationTypeViewSet:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def org_type(self):
        return OrganizationTypeFactory()

    @pytest.fixture
    def list_url(self):
        return reverse('v1:base_models:organization:organizationtype-list')

    @pytest.fixture
    def detail_url(self, org_type):
        return reverse('v1:base_models:organization:organizationtype-detail', kwargs={'name': org_type.name})

    def test_list_endpoint(self, api_client, list_url, org_type):
        """Test GET /api/v1/organization/types/ endpoint"""
        # Create multiple organization types
        types = [
            OrganizationTypeFactory(name='Company'),
            OrganizationTypeFactory(name='Department'),
            OrganizationTypeFactory(name='Customer')
        ]
        
        response = api_client.get(list_url)
        assert response.status_code == status.HTTP_200_OK
        
        # Verify response structure
        assert 'results' in response.data
        assert isinstance(response.data['results'], list)
        
        # Verify all types are present
        returned_names = {item['name'] for item in response.data['results']}
        expected_names = {org_type.name for org_type in types} | {org_type.name}
        assert returned_names == expected_names
        
        # Verify each item has required fields
        for item in response.data['results']:
            assert 'name' in item
            assert 'description' in item
            assert isinstance(item['name'], str)
            assert isinstance(item['description'], str)

    def test_retrieve_endpoint(self, api_client, detail_url, org_type):
        """Test GET /api/v1/organization/types/{name}/ endpoint"""
        response = api_client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK
        
        # Verify response structure
        assert response.data['name'] == org_type.name
        assert response.data['description'] == org_type.description
        
        # Verify all required fields are present
        assert 'name' in response.data
        assert 'description' in response.data
        assert isinstance(response.data['name'], str)
        assert isinstance(response.data['description'], str)

    def test_queryset_filtering(self, api_client, list_url):
        """Test that queryset filtering works correctly"""
        # Create a specific type
        specific_type = OrganizationTypeFactory(name='SpecificType')
        
        # Test filtering by name
        response = api_client.get(f"{list_url}?name={specific_type.name}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == specific_type.name

    def test_ordering(self, api_client, list_url):
        """Test that ordering works correctly"""
        # Create multiple types with different names
        types = [
            OrganizationTypeFactory(name='Zeta'),
            OrganizationTypeFactory(name='Alpha'),
            OrganizationTypeFactory(name='Beta')
        ]
        
        # Test ascending order
        response = api_client.get(f"{list_url}?ordering=name")
        assert response.status_code == status.HTTP_200_OK
        names = [item['name'] for item in response.data['results']]
        assert names == sorted(names)
        
        # Test descending order
        response = api_client.get(f"{list_url}?ordering=-name")
        assert response.status_code == status.HTTP_200_OK
        names = [item['name'] for item in response.data['results']]
        assert names == sorted(names, reverse=True)

    def test_unauthenticated_access(self, api_client, list_url, org_type):
        """Test that unauthenticated users can read organization types"""
        response = api_client.get(list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == org_type.name
        assert response.data['results'][0]['description'] == org_type.description

    def test_authenticated_access(self, api_client, list_url, org_type):
        """Test that authenticated users can read organization types"""
        # TODO: Add authentication once user model is implemented
        response = api_client.get(list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == org_type.name
        assert response.data['results'][0]['description'] == org_type.description

    def test_read_only_permissions(self, api_client, list_url, detail_url):
        """Test that write operations require authentication"""
        data = {'name': 'New Type', 'description': 'New Description'}
        
        # Test POST - should require authentication
        response = api_client.post(list_url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test PUT - should require authentication
        response = api_client.put(detail_url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test PATCH - should require authentication
        response = api_client.patch(detail_url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test DELETE - should require authentication
        response = api_client.delete(detail_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
class TestOrganizationViewSet:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def superuser(self):
        return UserFactory(is_superuser=True, is_staff=True)

    @pytest.fixture
    def user(self):
        u = UserFactory()
        # Give basic view permission for most tests
        u.user_permissions.add(get_permission(Organization, 'view_organization'))
        return u

    @pytest.fixture
    def org_type(self):
        return OrganizationTypeFactory()

    @pytest.fixture
    def contact(self):
        return ContactFactory()

    @pytest.fixture
    def address(self):
        return AddressFactory()

    @pytest.fixture
    def currency(self):
        return CurrencyFactory()

    @pytest.fixture
    def parent_org(self):
        return OrganizationFactory()

    @pytest.fixture
    def organization(self, org_type, contact, address, currency, parent_org):
        return OrganizationFactory(
            organization_type=org_type,
            primary_contact=contact,
            primary_address=address,
            currency=currency,
            parent=parent_org
        )

    @pytest.fixture
    def other_organization(self):
        # An org the default user is NOT a member of
        return OrganizationFactory()

    # Add membership fixture for the default user
    @pytest.fixture
    def user_membership(self, user, organization):
        return OrganizationMembershipFactory(user=user, organization=organization)

    @pytest.fixture
    def list_url(self):
        return reverse('v1:base_models:organization:organization-list')

    @pytest.fixture
    def detail_url(self, organization):
        return reverse('v1:base_models:organization:organization-detail', kwargs={'pk': organization.id})

    def test_list_organizations_as_member(self, api_client, list_url, user, organization, other_organization, user_membership):
        """Test regular user can only list orgs they are members of."""
        api_client.force_authenticate(user=user)
        response = api_client.get(list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1 # Should only see 'organization'
        assert response.data['results'][0]['id'] == organization.id
        found_ids = {org['id'] for org in response.data['results']}
        assert organization.id in found_ids
        assert other_organization.id not in found_ids

    def test_list_organizations_as_superuser(self, api_client, list_url, superuser, organization, other_organization):
        """Test superuser can list all orgs."""
        api_client.force_authenticate(user=superuser)
        response = api_client.get(list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 2 # Should see at least both orgs
        found_ids = {org['id'] for org in response.data['results']}
        assert organization.id in found_ids
        assert other_organization.id in found_ids

    def test_retrieve_organization_member(self, api_client, detail_url, user, organization, user_membership):
        """Test member can retrieve their org."""
        api_client.force_authenticate(user=user)
        response = api_client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == organization.id

    def test_retrieve_organization_non_member(self, api_client, user, other_organization):
        """Test non-member cannot retrieve an org (404 due to queryset filtering)."""
        api_client.force_authenticate(user=user)
        non_member_url = reverse('v1:base_models:organization:organization-detail', kwargs={'pk': other_organization.id})
        response = api_client.get(non_member_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_organization_superuser(self, api_client, detail_url, superuser, organization):
        """Test superuser can retrieve any org."""
        api_client.force_authenticate(user=superuser)
        response = api_client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == organization.id

    def test_update_organization(self, api_client, detail_url, organization, org_type, contact, address, currency, parent_org, user):
        user.user_permissions.add(get_permission(Organization, 'change_organization')) # Grant perm
        # Ensure user is member to pass get_object check due to get_queryset filtering
        OrganizationMembershipFactory(user=user, organization=organization)
        api_client.force_authenticate(user=user)
        data = {
            'name': 'Updated Org Name',
            'code': 'UPDATEDCODE',
            'organization_type': org_type.id,
            'status': 'inactive',
            'effective_date': '2024-01-01',
            'primary_contact': contact.id,
            'primary_address': address.id,
            'currency': currency.code,
            'parent': parent_org.id,
            'timezone': 'PST',
            'language': 'fr',
            'tags': ['updated', 'test']
        }
        response = api_client.put(detail_url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        organization.refresh_from_db()
        assert organization.name == 'Updated Org Name'
        assert organization.status == 'inactive'

    def test_delete_organization(self, api_client, detail_url, organization, user):
        user.user_permissions.add(get_permission(Organization, 'delete_organization')) # Grant perm
        # Ensure user is member to pass get_object check
        OrganizationMembershipFactory(user=user, organization=organization)
        api_client.force_authenticate(user=user)
        response = api_client.delete(detail_url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Organization.objects.filter(pk=organization.id).exists()

    def test_list_filter_by_type_and_parent(self, api_client, list_url, organization, other_organization, org_type, parent_org, user):
        """Test LIST endpoint filtering by organization_type and parent, considering membership."""
        # Make user member of the target org 
        OrganizationMembershipFactory(user=user, organization=organization)
        # Make user member of another org with different parent/type to test filtering
        other_org_type = OrganizationTypeFactory()
        other_parent = OrganizationFactory()
        other_org_different = OrganizationFactory(organization_type=other_org_type, parent=other_parent)
        OrganizationMembershipFactory(user=user, organization=other_org_different) 
        
        api_client.force_authenticate(user=user)

        # Test filter by type (org_type.id)
        response = api_client.get(f"{list_url}?organization_type={org_type.id}")
        assert response.status_code == status.HTTP_200_OK
        results_ids = {org['id'] for org in response.data['results']}
        assert organization.id in results_ids
        assert other_org_different.id not in results_ids # Belongs to user, but wrong type

        # Test filter by parent (parent_org.id)
        response = api_client.get(f"{list_url}?parent={parent_org.id}")
        assert response.status_code == status.HTTP_200_OK
        results_ids = {org['id'] for org in response.data['results']}
        assert organization.id in results_ids
        assert other_org_different.id not in results_ids # Belongs to user, but wrong parent

    def test_list_filter_by_status(self, api_client, list_url, user):
        """Test LIST endpoint filtering by status, considering membership."""
        api_client.force_authenticate(user=user)

        active_org = OrganizationFactory(status='active')
        inactive_org = OrganizationFactory(status='inactive')
        # Make user member of both orgs to test filtering
        OrganizationMembershipFactory(user=user, organization=active_org)
        OrganizationMembershipFactory(user=user, organization=inactive_org)
        # Create another org user is not member of
        other_active = OrganizationFactory(status='active')

        # Test filter by status=active
        response = api_client.get(f"{list_url}?status=active")
        assert response.status_code == status.HTTP_200_OK
        results_ids = {org['id'] for org in response.data['results']}
        assert active_org.id in results_ids
        assert inactive_org.id not in results_ids
        assert other_active.id not in results_ids # Not a member

        # Test filter by status=inactive
        response = api_client.get(f"{list_url}?status=inactive")
        assert response.status_code == status.HTTP_200_OK
        results_ids = {org['id'] for org in response.data['results']}
        assert inactive_org.id in results_ids
        assert active_org.id not in results_ids

    def test_list_filter_by_tags(self, api_client, list_url, user):
        """Test LIST endpoint filtering by tags, considering membership."""
        api_client.force_authenticate(user=user)

        tagged_org = OrganizationFactory()
        tagged_org.tags.add("test-tag")
        untagged_org = OrganizationFactory()
        # Make user member of both
        OrganizationMembershipFactory(user=user, organization=tagged_org)
        OrganizationMembershipFactory(user=user, organization=untagged_org)
        # Another tagged org user is not member of
        other_tagged_org = OrganizationFactory()
        other_tagged_org.tags.add("test-tag")

        response = api_client.get(f"{list_url}?tags=test-tag")
        assert response.status_code == status.HTTP_200_OK
        results_ids = {org['id'] for org in response.data['results']}
        assert tagged_org.id in results_ids
        assert untagged_org.id not in results_ids
        assert other_tagged_org.id not in results_ids # Not a member

    def test_hierarchy_actions(self, api_client, detail_url, organization, user):
        """Test hierarchy actions (descendants, ancestors). User must be member."""
        # Grant view permission and membership
        user.user_permissions.add(get_permission(Organization, 'view_organization'))
        OrganizationMembershipFactory(user=user, organization=organization)
        # Create hierarchy
        child_org = OrganizationFactory(parent=organization)
        grandchild_org = OrganizationFactory(parent=child_org)

        api_client.force_authenticate(user=user)

        # Test descendants
        descendants_url = f"{detail_url}descendants/"
        response = api_client.get(descendants_url)
        assert response.status_code == status.HTTP_200_OK # Ensure user can access base org
        descendant_ids = {org['id'] for org in response.data}
        assert child_org.id in descendant_ids
        assert grandchild_org.id in descendant_ids
        assert len(descendant_ids) == 2

        # Test ancestors (testing on grandchild)
        grandchild_detail_url = reverse('v1:base_models:organization:organization-detail', kwargs={'pk': grandchild_org.id})
        # User must also be member of grandchild org to retrieve it first for the action url
        OrganizationMembershipFactory(user=user, organization=grandchild_org)
        ancestors_url = f"{grandchild_detail_url}ancestors/"
        response = api_client.get(ancestors_url)
        assert response.status_code == status.HTTP_200_OK # Ensure user can access grandchild org
        ancestor_ids = {org['id'] for org in response.data}
        assert organization.id in ancestor_ids
        assert child_org.id in ancestor_ids
        # Check length carefully - depends if the root org 'organization' has a parent itself
        expected_ancestors = 2 # organization and child_org
        if organization.parent:
            # If the main test org has a parent, MPTT should include it
            expected_ancestors += 1
        assert len(ancestor_ids) == expected_ancestors

    def test_metadata_and_custom_fields(self, api_client, list_url, org_type, user):
        """Test operations involving metadata and custom_fields. User needs membership and perms."""
        user.user_permissions.add(get_permission(Organization, 'add_organization'))
        user.user_permissions.add(get_permission(Organization, 'change_organization'))
        user.user_permissions.add(get_permission(Organization, 'view_organization')) # Needed for detail view access
        api_client.force_authenticate(user=user)

        # Test create with meta/custom fields
        create_data = {
            'name': 'Meta Org', 'code': 'META01', 'organization_type': org_type.id,
            'metadata': {'project': 'alpha', 'priority': 1},
            'custom_fields': {'legacy_id': 'LGCY001'}
        }
        response = api_client.post(list_url, create_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        org_id = response.data['id']
        org = Organization.objects.get(pk=org_id)
        # User must be made member to access it later
        OrganizationMembershipFactory(user=user, organization=org)
        assert org.metadata == create_data['metadata']
        assert org.custom_fields == create_data['custom_fields']

        # Test patch meta/custom fields
        patch_data = {
            'metadata': {'priority': 2, 'status': 'reviewed'},
            'custom_fields': {'approved_by': 'testuser'}
        }
        detail_url = reverse('v1:base_models:organization:organization-detail', kwargs={'pk': org_id})
        response = api_client.patch(detail_url, patch_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        org.refresh_from_db()
        # Check metadata update (assuming PATCH replaces the entire JSON object)
        assert org.metadata['priority'] == 2
        assert org.metadata['status'] == 'reviewed'
        assert 'project' not in org.metadata # Verify old key is gone
        # Check custom_fields update (assuming PATCH replaces)
        assert org.custom_fields == patch_data['custom_fields']

    def test_tag_operations(self, api_client, list_url, org_type, user):
        """Test tag operations (add/update/remove). User needs membership and perms."""
        user.user_permissions.add(get_permission(Organization, 'add_organization'))
        user.user_permissions.add(get_permission(Organization, 'change_organization'))
        user.user_permissions.add(get_permission(Organization, 'view_organization')) # Needed for detail view
        api_client.force_authenticate(user=user)

        # Test create with tags
        create_data = {
            'name': 'Tagged Org', 'code': 'TAG01', 'organization_type': org_type.id,
            'tags': ['initial', 'test']
        }
        response = api_client.post(list_url, create_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        org_id = response.data['id']
        org = Organization.objects.get(pk=org_id)
        # Make user member to allow access
        OrganizationMembershipFactory(user=user, organization=org) 
        assert set(org.tags.names()) == {'initial', 'test'}

        # Test update (PUT) tags - should replace
        put_data = create_data.copy()
        # Need all required fields for PUT
        put_data.update({
            'status': org.status, 
            # Add other required non-nullable fields if any, based on serializer 
            # Or fetch the full object and reserialize if simpler
        }) 
        put_data['tags'] = ['updated', 'test']
        detail_url = reverse('v1:base_models:organization:organization-detail', kwargs={'pk': org_id})
        response = api_client.put(detail_url, put_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        org.refresh_from_db()
        assert set(org.tags.names()) == {'updated', 'test'}

        # Test update (PATCH) tags - should replace (TaggitSerializer behaviour)
        patch_data = {'tags': ['patched']}
        response = api_client.patch(detail_url, patch_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        org.refresh_from_db()
        assert set(org.tags.names()) == {'patched'}

        # Test remove tags via PATCH
        patch_data = {'tags': []}
        response = api_client.patch(detail_url, patch_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        org.refresh_from_db()
        assert org.tags.count() == 0

    # Need to re-add audit log cleanup to delete test
    def test_delete_organization(self, api_client, detail_url, organization, user):
        user.user_permissions.add(get_permission(Organization, 'delete_organization'))
        user.user_permissions.add(get_permission(Organization, 'view_organization')) # Needed for get_object check
        OrganizationMembershipFactory(user=user, organization=organization)
        api_client.force_authenticate(user=user)
        org_id = organization.id # Store ID before delete
        response = api_client.delete(detail_url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Organization.objects.filter(pk=org_id).exists()

        # --- AuditLog Cleanup ---
        from core.audit.models import AuditLog # Import here locally
        AuditLog.objects.filter(organization_id=org_id).delete()
        # --- End AuditLog Cleanup ---

@pytest.mark.django_db
class TestOrganizationMembershipEndpoints:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def superuser(self):
        return UserFactory(is_superuser=True, is_staff=True)

    # RBAC Roles Setup
    @pytest.fixture
    def org_manager_role(self):
        return setup_role_with_permissions(
            'OrgManager', 
            OrganizationMembership, 
            ['add_organizationmembership', 'change_organizationmembership', 'delete_organizationmembership', 'view_organizationmembership']
        )

    @pytest.fixture
    def org_viewer_role(self):
        return setup_role_with_permissions(
            'OrgViewer', 
            OrganizationMembership, 
            ['view_organizationmembership']
        )

    # Test Users with RBAC Roles
    @pytest.fixture
    def org_manager_user(self, organization, org_manager_role):
        user = UserFactory()
        OrganizationMembershipFactory(user=user, organization=organization, role=org_manager_role)
        # Also make them member of another org to test scope
        other_org = OrganizationFactory()
        OrganizationMembershipFactory(user=user, organization=other_org, role=org_manager_role)
        return user
        
    @pytest.fixture
    def org_viewer_user(self, organization, org_viewer_role):
        user = UserFactory()
        OrganizationMembershipFactory(user=user, organization=organization, role=org_viewer_role)
        return user
        
    @pytest.fixture
    def user_no_role_in_org(self, organization): # User is member, but no specific role granting mem perms
        user = UserFactory()
        OrganizationMembershipFactory(user=user, organization=organization, role=None)
        return user

    @pytest.fixture
    def user_other_org(self): # User not in the primary test organization
        user = UserFactory()
        other_org = OrganizationFactory()
        OrganizationMembershipFactory(user=user, organization=other_org)
        return user

    @pytest.fixture
    def organization(self):
        return OrganizationFactory()

    @pytest.fixture
    def target_user(self): # The user being added/modified in membership tests
        return UserFactory()

    @pytest.fixture
    def target_role(self): # The role being assigned in membership tests
        return GroupFactory(name='TargetRole') # Generic role for assignment

    @pytest.fixture
    def membership(self, target_user, organization, target_role):
        # A pre-existing membership for retrieve/update/delete tests
        return OrganizationMembershipFactory(user=target_user, organization=organization, role=target_role)

    @pytest.fixture
    def list_url(self):
        return reverse('v1:base_models:organization:organizationmembership-list')

    @pytest.fixture
    def detail_url(self, membership):
        return reverse('v1:base_models:organization:organizationmembership-detail', kwargs={'pk': membership.id})

    # --- Rewritten Tests using RBAC Roles --- 

    def test_list_memberships_superuser(self, api_client, superuser, membership, list_url):
        """Superuser can list all memberships."""
        # Create another membership in another org
        other_org = OrganizationFactory()
        other_user = UserFactory()
        other_membership = OrganizationMembershipFactory(user=other_user, organization=other_org)
        
        api_client.force_authenticate(user=superuser)
        response = api_client.get(list_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 2 # Should see both
        found_ids = {mem['id'] for mem in response.data['results']}
        assert membership.id in found_ids
        assert other_membership.id in found_ids

    def test_list_memberships_org_manager(self, api_client, org_manager_user, organization, membership, list_url):
        """Org Manager can list memberships for their orgs."""
        # Create membership in another org the manager is NOT part of
        unrelated_org = OrganizationFactory()
        unrelated_user = UserFactory()
        unrelated_membership = OrganizationMembershipFactory(user=unrelated_user, organization=unrelated_org)

        api_client.force_authenticate(user=org_manager_user)
        response = api_client.get(list_url)
        assert response.status_code == status.HTTP_200_OK
        
        found_ids = {mem['id'] for mem in response.data['results']}
        # Should see membership in their primary org
        assert membership.id in found_ids 
        # Should not see membership in unrelated org
        assert unrelated_membership.id not in found_ids
        # Check count is correct based on manager's orgs (includes manager's own memberships)
        manager_org_ids = list(org_manager_user.get_organizations().values_list('id', flat=True))
        assert len(found_ids) == OrganizationMembership.objects.filter(organization_id__in=manager_org_ids).count()

    def test_list_memberships_org_viewer(self, api_client, org_viewer_user, organization, membership, list_url):
        """Org Viewer can list memberships for their org (needs view perm)."""
        api_client.force_authenticate(user=org_viewer_user)
        response = api_client.get(list_url)
        assert response.status_code == status.HTTP_200_OK
        found_ids = {mem['id'] for mem in response.data['results']}
        assert membership.id in found_ids
        # Should only see memberships for the org they are viewer in
        assert len(found_ids) == OrganizationMembership.objects.filter(organization=organization).count()

    def test_list_memberships_user_other_org(self, api_client, user_other_org, membership, list_url):
        """User from another org cannot list memberships for the target org (Forbidden)."""
        api_client.force_authenticate(user=user_other_org)
        response = api_client.get(list_url)
        # HasModelPermissionInOrg will deny access if list is filtered to orgs user isn't in.
        # If get_queryset returned empty list for this user, status would be 200.
        # Current get_queryset filters by user's orgs, so the base permission check denies.
        assert response.status_code == status.HTTP_403_FORBIDDEN 
        # # Previous check (if 200 OK was expected with empty list for non-member orgs):
        # assert response.status_code == status.HTTP_200_OK 
        # found_ids = {mem['id'] for mem in response.data['results']}
        # assert membership.id not in found_ids 

    def test_create_membership_org_manager(self, api_client, org_manager_user, organization, target_user, target_role, list_url):
        """Org Manager can create membership in their org."""
        api_client.force_authenticate(user=org_manager_user)
        data = {
            'user': target_user.id,
            'organization': organization.id,
            'role': target_role.id,
            'is_active': True
        }
        response = api_client.post(list_url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert OrganizationMembership.objects.filter(user=target_user, organization=organization).exists()

    def test_create_membership_org_viewer_fail(self, api_client, org_viewer_user, organization, target_user, target_role, list_url):
        """Org Viewer cannot create membership (lacks add perm)."""
        api_client.force_authenticate(user=org_viewer_user)
        data = {'user': target_user.id, 'organization': organization.id, 'role': target_role.id, 'is_active': True}
        response = api_client.post(list_url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_create_membership_manager_other_org_fail(self, api_client, org_manager_user, target_user, target_role, list_url):
        """Org Manager cannot create membership in an org they don't manage."""
        other_org = OrganizationFactory() # Org manager isn't member of
        api_client.force_authenticate(user=org_manager_user)
        data = {'user': target_user.id, 'organization': other_org.id, 'role': target_role.id, 'is_active': True}
        response = api_client.post(list_url, data, format='json')
        # Fails at has_perm_in_org check inside perform_create
        assert response.status_code == status.HTTP_403_FORBIDDEN 

    def test_retrieve_membership_org_manager(self, api_client, org_manager_user, membership, detail_url):
        """Org Manager can retrieve membership in their org."""
        api_client.force_authenticate(user=org_manager_user)
        response = api_client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == membership.id

    def test_retrieve_membership_org_viewer(self, api_client, org_viewer_user, membership, detail_url):
        """Org Viewer can retrieve membership in their org."""
        api_client.force_authenticate(user=org_viewer_user)
        response = api_client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == membership.id
        
    def test_retrieve_membership_other_org_fail(self, api_client, user_other_org, membership, detail_url):
        """User from other org cannot retrieve membership (404 due to queryset filter)."""
        api_client.force_authenticate(user=user_other_org)
        response = api_client.get(detail_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_membership_org_manager(self, api_client, org_manager_user, membership, detail_url):
        """Org Manager can update membership in their org."""
        api_client.force_authenticate(user=org_manager_user)
        new_role = GroupFactory(name="NewRoleForUpdate")
        data = {'is_active': False, 'role': new_role.id}
        response = api_client.patch(detail_url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        membership.refresh_from_db()
        assert membership.is_active is False
        assert membership.role == new_role

    def test_update_membership_org_viewer_fail(self, api_client, org_viewer_user, membership, detail_url):
        """Org Viewer cannot update membership (lacks change perm)."""
        api_client.force_authenticate(user=org_viewer_user)
        data = {'is_active': False}
        response = api_client.patch(detail_url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_membership_org_manager(self, api_client, org_manager_user, membership, detail_url):
        """Org Manager can delete membership in their org."""
        api_client.force_authenticate(user=org_manager_user)
        response = api_client.delete(detail_url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not OrganizationMembership.objects.filter(pk=membership.id).exists()

    def test_delete_membership_org_viewer_fail(self, api_client, org_viewer_user, membership, detail_url):
        """Org Viewer cannot delete membership (lacks delete perm)."""
        api_client.force_authenticate(user=org_viewer_user)
        response = api_client.delete(detail_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN 