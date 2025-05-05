# api/v1/base_models/contact/tests/api/test_contact_scoping_perms.py
import pytest
from django.urls import reverse
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.test import APITestCase

# Import necessary factories
from api.v1.base_models.user.tests.factories import UserFactory
from api.v1.base_models.organization.tests.factories import (
    OrganizationFactory,
    OrganizationMembershipFactory,
    GroupFactory, # Renamed from RoleFactory
)
from api.v1.base_models.contact.models import Contact
from api.v1.base_models.contact.tests.factories import ContactFactory


@pytest.mark.django_db(transaction=True) # Ensure transactions for reliable testing
class ContactScopingPermissionsAPITests(APITestCase):
    """
    Tests API endpoint scoping and permissions for ContactViewSet based on 
    Organization Membership and Roles.
    """

    @classmethod
    def setUpTestData(cls):
        # --- Permissions ---
        # Use get_for_model to be robust
        contact_ct = ContentType.objects.get_for_model(Contact)
        cls.view_perm = Permission.objects.get(content_type=contact_ct, codename='view_contact')
        cls.add_perm = Permission.objects.get(content_type=contact_ct, codename='add_contact')
        cls.change_perm = Permission.objects.get(content_type=contact_ct, codename='change_contact')
        cls.delete_perm = Permission.objects.get(content_type=contact_ct, codename='delete_contact')

        # --- Roles (Groups) ---
        cls.viewer_role = GroupFactory(name="ContactViewer", permissions=[cls.view_perm])
        cls.editor_role = GroupFactory(name="ContactEditor", permissions=[cls.view_perm, cls.add_perm, cls.change_perm])
        cls.admin_role = GroupFactory(name="ContactAdmin", permissions=[cls.view_perm, cls.add_perm, cls.change_perm, cls.delete_perm])
        cls.no_perm_role = GroupFactory(name="NoContactPerms")

        # --- Organizations ---
        cls.org1 = OrganizationFactory(name="Org 1")
        cls.org2 = OrganizationFactory(name="Org 2")

        # --- Users and Memberships ---
        cls.superuser = UserFactory(is_superuser=True)
        
        cls.user_org1_admin = UserFactory()
        OrganizationMembershipFactory(organization=cls.org1, user=cls.user_org1_admin, role=cls.admin_role)

        cls.user_org1_editor = UserFactory()
        OrganizationMembershipFactory(organization=cls.org1, user=cls.user_org1_editor, role=cls.editor_role)
        
        cls.user_org1_viewer = UserFactory()
        OrganizationMembershipFactory(organization=cls.org1, user=cls.user_org1_viewer, role=cls.viewer_role)

        cls.user_org1_no_perm = UserFactory()
        OrganizationMembershipFactory(organization=cls.org1, user=cls.user_org1_no_perm, role=cls.no_perm_role)

        cls.user_org2_viewer = UserFactory()
        OrganizationMembershipFactory(organization=cls.org2, user=cls.user_org2_viewer, role=cls.viewer_role)

        cls.user_no_member = UserFactory()

        # --- Contacts ---
        cls.contact_org1_a = ContactFactory(organization=cls.org1, first_name="Contact", last_name="A-Org1")
        cls.contact_org1_b = ContactFactory(organization=cls.org1, first_name="Contact", last_name="B-Org1")
        cls.contact_org2_a = ContactFactory(organization=cls.org2, first_name="Contact", last_name="A-Org2")

        # --- URLs ---
        cls.list_create_url = reverse('v1:base_models:contact:contact-list')
        cls.detail_url_org1_a = reverse('v1:base_models:contact:contact-detail', kwargs={'pk': cls.contact_org1_a.pk})
        cls.detail_url_org2_a = reverse('v1:base_models:contact:contact-detail', kwargs={'pk': cls.contact_org2_a.pk})

    def get_detail_url(self, pk):
        # Correct URL reversing
        return reverse('v1:base_models:contact:contact-detail', kwargs={'pk': pk})

    def force_authenticate(self, user):
        """Custom authentication helper to ensure is_superuser flag is properly respected."""
        # Call the client's force_authenticate
        self.client.force_authenticate(user=user)
        
        # Add debug logging for clarity in test execution
        if user.is_superuser:
            print(f"DEBUG: Authenticated superuser: {user.username}, is_superuser={user.is_superuser}")

    # === LIST Tests (Scoping & View Permission) ===

    def test_list_superuser_sees_all(self):
        self.force_authenticate(self.superuser)
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3) # Sees Org1 and Org2 contacts
        contact_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.contact_org1_a.pk, contact_ids)
        self.assertIn(self.contact_org1_b.pk, contact_ids)

    def test_list_user_no_member_sees_none(self):
        self.force_authenticate(self.user_no_member)
        response = self.client.get(self.list_create_url)
        # Expect 403 because user isn't in any org and permission check fails
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_org1_admin_sees_only_org1(self):
        self.force_authenticate(self.user_org1_admin)
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # With the current implementation, a user with access to an organization 
        # only sees contacts from that organization
        self.assertEqual(response.data['count'], 2) # Only Org1 contacts
        contact_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.contact_org1_a.pk, contact_ids)
        self.assertIn(self.contact_org1_b.pk, contact_ids)
        self.assertNotIn(self.contact_org2_a.pk, contact_ids) # Should not see org2 contacts
        
    def test_list_org1_viewer_sees_only_org1(self):
        # Viewer also has view permission
        self.force_authenticate(self.user_org1_viewer)
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        
    def test_list_org1_no_perm_sees_none(self):
        # Member of Org1 but lacks view_contact perm
        self.force_authenticate(self.user_org1_no_perm)
        response = self.client.get(self.list_create_url)
        # Expect 403 because user lacks view perm in their only org
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # === CREATE Tests (Add Permission in Target Org) ===

    def test_create_superuser_succeeds(self):
        self.force_authenticate(self.superuser)
        data = {'first_name': 'New', 'last_name': 'SuperContact', 'organization_id': self.org1.pk}
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Contact.objects.count(), 4)
        self.assertEqual(response.data['organization']['id'], self.org1.pk)
        
    def test_create_org1_admin_in_org1_succeeds(self):
        self.force_authenticate(self.user_org1_admin)
        data = {'first_name': 'New', 'last_name': 'AdminContact1', 'organization_id': self.org1.pk}
        response = self.client.post(self.list_create_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Contact.objects.filter(last_name='AdminContact1', organization=self.org1).exists())
        
    def test_create_org1_admin_in_org2_fails(self):
        self.force_authenticate(self.user_org1_admin)
        data = {'first_name': 'New', 'last_name': 'AdminContact2Fail', 'organization_id': self.org2.pk}
        response = self.client.post(self.list_create_url, data)
        # perform_create in mixin checks add perm in target org
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_create_org1_viewer_in_org1_fails(self):
        self.force_authenticate(self.user_org1_viewer)
        data = {'first_name': 'New', 'last_name': 'ViewerContact1Fail', 'organization_id': self.org1.pk}
        response = self.client.post(self.list_create_url, data)
        # Viewer lacks add_contact perm
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_create_without_organization_fails(self):
        """Test creating a contact without organization for multi-org user fails but succeeds for single-org user."""
        # For a multi-organization user, the organization_id should be required
        self.force_authenticate(self.user_org1_admin)
        
        # Create a second organization membership to make this a multi-org user
        org2_membership = OrganizationMembershipFactory(
            organization=self.org2, 
            user=self.user_org1_admin,
            role=self.admin_role
        )
        
        data = {'first_name': 'New', 'last_name': 'NoOrgMulti'} # Missing organization_id
        response = self.client.post(self.list_create_url, data)
        # Multi-org users receive a 403 Forbidden with permission denied error
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('permission', str(response.data).lower())
        
        # Remove the second organization to make this a single-org user
        org2_membership.delete()
        
        # For a single-organization user, the organization should be auto-determined
        data = {'first_name': 'New', 'last_name': 'NoOrgSingle'} # Missing organization_id
        response = self.client.post(self.list_create_url, data)
        # Should succeed for single-org users
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the contact was created with the correct organization
        new_contact = Contact.objects.get(last_name='NoOrgSingle')
        self.assertEqual(new_contact.organization, self.org1)

    # === RETRIEVE Tests (View Permission on Object's Org) ===
    
    def test_retrieve_superuser_succeeds(self):
        self.force_authenticate(self.superuser)
        response = self.client.get(self.detail_url_org1_a)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.contact_org1_a.pk)
        response = self.client.get(self.detail_url_org2_a)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.contact_org2_a.pk)
        
    def test_retrieve_org1_admin_for_org1_succeeds(self):
        self.force_authenticate(self.user_org1_admin)
        response = self.client.get(self.detail_url_org1_a)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_retrieve_org1_viewer_for_org1_succeeds(self):
        self.force_authenticate(self.user_org1_viewer)
        response = self.client.get(self.detail_url_org1_a)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_retrieve_org1_admin_for_org2_fails(self):
        self.force_authenticate(self.user_org1_admin)
        response = self.client.get(self.detail_url_org2_a)
        # With the current implementation, a user with access to an organization
        # cannot retrieve contacts from other organizations
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_retrieve_org1_no_perm_for_org1_fails(self):
        self.force_authenticate(self.user_org1_no_perm)
        response = self.client.get(self.get_detail_url(self.contact_org1_a.pk))
        # Should be 403 Forbidden because the user is in the org but lacks the permission
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    # === UPDATE Tests (Change Permission on Object's Org) ===

    def test_update_superuser_succeeds(self):
        self.force_authenticate(self.superuser)
        data = {'first_name': 'UpdatedSuper'}
        response = self.client.patch(self.detail_url_org1_a, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.contact_org1_a.refresh_from_db()
        self.assertEqual(self.contact_org1_a.first_name, 'UpdatedSuper')
        
    def test_update_org1_admin_for_org1_succeeds(self):
        self.force_authenticate(self.user_org1_admin)
        data = {'first_name': 'UpdatedAdmin'}
        response = self.client.patch(self.detail_url_org1_a, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.contact_org1_a.refresh_from_db()
        self.assertEqual(self.contact_org1_a.first_name, 'UpdatedAdmin')
        
    def test_update_org1_editor_for_org1_succeeds(self):
        self.force_authenticate(self.user_org1_editor)
        data = {'first_name': 'UpdatedEditor'}
        response = self.client.patch(self.detail_url_org1_a, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.contact_org1_a.refresh_from_db()
        self.assertEqual(self.contact_org1_a.first_name, 'UpdatedEditor')
        
    def test_update_org1_viewer_for_org1_fails(self):
        self.force_authenticate(self.user_org1_viewer)
        data = {'first_name': 'UpdatedViewerFail'}
        response = self.client.patch(self.detail_url_org1_a, data)
        # Viewer lacks change_contact perm
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_update_org1_admin_for_org2_fails(self):
        self.force_authenticate(self.user_org1_admin)
        data = {'first_name': 'UpdatedAdminFail'}
        response = self.client.patch(self.detail_url_org2_a, data)
        # Checks change_contact perm on object's org (Org2)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    # === DELETE Tests (Delete Permission on Object's Org) ===
    
    def test_delete_superuser_succeeds(self):
        self.force_authenticate(self.superuser)
        response = self.client.delete(self.detail_url_org1_a)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Contact.objects.filter(pk=self.contact_org1_a.pk).exists())
        
    def test_delete_org1_admin_for_org1_succeeds(self):
        self.force_authenticate(self.user_org1_admin)
        contact_pk = self.contact_org1_b.pk # Use B to avoid affecting other tests
        detail_url = self.get_detail_url(contact_pk)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Contact.objects.filter(pk=contact_pk).exists())
        
    def test_delete_org1_editor_for_org1_fails(self):
        self.force_authenticate(self.user_org1_editor)
        response = self.client.delete(self.detail_url_org1_a)
        # Member lacks delete_contact perm
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_delete_org1_viewer_for_org1_fails(self):
        self.force_authenticate(self.user_org1_viewer)
        response = self.client.delete(self.detail_url_org1_a)
        # Viewer lacks delete_contact perm
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_delete_org1_admin_for_org2_fails(self):
        self.force_authenticate(self.user_org1_admin)
        response = self.client.delete(self.detail_url_org2_a)
        # With the current implementation, a user with access to an organization
        # cannot delete contacts from other organizations
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # The contact still exists
        self.assertTrue(Contact.objects.filter(pk=self.contact_org2_a.pk).exists())

    # === Helper setup check ===
    def test_initial_contact_count(self):
        # Sanity check that setUpTestData created the right number initially
        self.assertEqual(Contact.objects.count(), 3) 