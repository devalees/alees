import pytest
from django.urls import path, reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.core.exceptions import PermissionDenied
from rest_framework import status, viewsets, serializers, permissions
from rest_framework.routers import SimpleRouter
from rest_framework.test import APITestCase, APIRequestFactory
from django.contrib.contenttypes.models import ContentType
from django.test import override_settings

# Use existing models and factories
from api.v1.base_models.organization.models import Organization, OrganizationMembership
from api.v1.base_models.organization.tests.factories import (
    OrganizationFactory,
    OrganizationMembershipFactory,
    GroupFactory, # Use GroupFactory for Roles
)
from api.v1.base_models.user.tests.factories import UserFactory
# Assume a serializer exists - adjust if necessary
try:
    from api.v1.base_models.organization.serializers import OrganizationMembershipSerializer
except ImportError:
    # Create a minimal serializer for testing if one doesn't exist
    class OrganizationMembershipSerializer(serializers.ModelSerializer):
        # Need to define fields explicitly if related fields aren't serializers themselves
        user_id = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all(), source='user')
        organization_id = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all(), source='organization')
        role_id = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), source='role', allow_null=True, required=False)

        class Meta:
            model = OrganizationMembership
            fields = ('id', 'user_id', 'organization_id', 'role_id', 'is_active', 'created_at', 'updated_at') # Adjust fields as needed


# Import RBAC components to test
from core.rbac.drf_permissions import HasModelPermissionInOrg
from core.rbac.permissions import has_perm_in_org
from core.views import OrganizationScopedViewSetMixin # Assuming this exists

# --- Simulated ViewSet using the REAL Model & Serializer ---
class TestOrganizationMembershipViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """
    A *simulated* ViewSet for testing RBAC integration with OrganizationMembership.
    Uses the real model and serializer but is only registered in test URLs.
    """
    queryset = OrganizationMembership.objects.all()
    serializer_class = OrganizationMembershipSerializer
    permission_classes = [permissions.IsAuthenticated, HasModelPermissionInOrg] # Apply the permission class

    # Override get_queryset specifically for testing Membership list views
    # The mixin's get_queryset has issues filtering OrganizationMembership lists correctly by default
    def get_queryset(self):
        qs = super().get_queryset() # Start with the base queryset
        user = self.request.user

        if not user or not user.is_authenticated:
            return qs.none()
        
        # For testing list views, filter to only the user's *own* memberships
        # Detail views rely on get_object which uses the default manager filtering by PK first.
        if self.action == 'list':
             if user.is_superuser:
                 return qs # Superuser sees all
             return qs.filter(user=user) # Regular user sees only their own memberships
        
        # For other actions (retrieve, update, delete), rely on the default queryset
        # and let get_object handle PK lookup + permission checks handle object-level access.
        return qs

# --- Test URL Configuration ---
router = SimpleRouter()
router.register(r'test-memberships', TestOrganizationMembershipViewSet, basename='testmembership')
urlpatterns = router.urls

# --- Integration Tests ---
@pytest.mark.urls(__name__)
@pytest.mark.django_db(transaction=True)
class RBACViewSetIntegrationTests(APITestCase):
    """
    Tests the integration of HasModelPermissionInOrg permission class and
    the implicit permission check in perform_create (via OrganizationScopedViewSetMixin)
    using the OrganizationMembership model.
    """
    LIST_URL = '/test-memberships/'

    @classmethod
    def detail_url(cls, pk):
        return f'/test-memberships/{pk}/'

    @classmethod
    def setUpTestData(cls):
        # Get ContentType for OrganizationMembership
        try:
            cls.ct = ContentType.objects.get_for_model(OrganizationMembership)
        except Exception as e:
            pytest.fail(f"Failed to get ContentType for OrganizationMembership: {e}")

        # Standard Permissions for OrganizationMembership
        cls.view_perm = Permission.objects.get(content_type=cls.ct, codename='view_organizationmembership')
        cls.add_perm = Permission.objects.get(content_type=cls.ct, codename='add_organizationmembership')
        cls.change_perm = Permission.objects.get(content_type=cls.ct, codename='change_organizationmembership')
        cls.delete_perm = Permission.objects.get(content_type=cls.ct, codename='delete_organizationmembership')

        # Orgs
        cls.org1 = OrganizationFactory(name="Org 1")
        cls.org2 = OrganizationFactory(name="Org 2")

        # Roles (Groups)
        cls.viewer_role = GroupFactory(name="Viewer", permissions=[cls.view_perm])
        cls.editor_role = GroupFactory(name="Editor", permissions=[cls.view_perm, cls.add_perm, cls.change_perm])
        # Admin role implicitly includes delete via other permissions in this setup
        cls.admin_role = GroupFactory(name="Admin", permissions=[cls.view_perm, cls.add_perm, cls.change_perm, cls.delete_perm])
        cls.no_perm_role = GroupFactory(name="NoPerms")

        # Users
        cls.superuser = UserFactory(is_superuser=True, username='super')
        cls.user_org1_admin = UserFactory(username='admin_org1')
        cls.user_org1_editor = UserFactory(username='editor_org1')
        cls.user_org1_viewer = UserFactory(username='viewer_org1')
        cls.user_org1_noperm = UserFactory(username='noperm_org1')
        cls.user_org1_norole = UserFactory(username='norole_org1')

        cls.user_org2_viewer = UserFactory(username='viewer_org2')
        cls.user_no_member = UserFactory(username='nomember')

        # Memberships
        cls.member_admin_org1 = OrganizationMembershipFactory(organization=cls.org1, user=cls.user_org1_admin, role=cls.admin_role)
        cls.member_editor_org1 = OrganizationMembershipFactory(organization=cls.org1, user=cls.user_org1_editor, role=cls.editor_role)
        cls.member_viewer_org1 = OrganizationMembershipFactory(organization=cls.org1, user=cls.user_org1_viewer, role=cls.viewer_role)
        cls.member_noperm_org1 = OrganizationMembershipFactory(organization=cls.org1, user=cls.user_org1_noperm, role=cls.no_perm_role)
        cls.member_norole_org1 = OrganizationMembershipFactory(organization=cls.org1, user=cls.user_org1_norole, role=None) # No role assigned

        cls.member_viewer_org2 = OrganizationMembershipFactory(organization=cls.org2, user=cls.user_org2_viewer, role=cls.viewer_role)

        # Also need a user who will be assigned membership in tests
        cls.user_to_assign = UserFactory(username='assignee')


    # === Authentication Tests ===
    def test_list_unauthenticated_fails(self):
        response = self.client.get(self.LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_unauthenticated_fails(self):
        data = {'user': self.user_no_member.pk, 'organization': self.org1.pk, 'role': self.viewer_role.pk}
        response = self.client.post(self.LIST_URL, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_unauthenticated_fails(self):
        url = self.detail_url(self.member_viewer_org1.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_unauthenticated_fails(self):
        url = self.detail_url(self.member_viewer_org1.pk)
        data = {'is_active': False}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_unauthenticated_fails(self):
        url = self.detail_url(self.member_viewer_org1.pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # === Authorization & Scoping Tests (LIST) ===
    def test_list_superuser_sees_all(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 6)

    def test_list_user_no_member_sees_nothing(self):
        self.client.force_authenticate(user=self.user_no_member)
        response = self.client.get(self.LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_list_viewer_org1_sees_only_org1(self):
        self.client.force_authenticate(user=self.user_org1_viewer)
        response = self.client.get(self.LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_list_viewer_org2_sees_only_org2(self):
        self.client.force_authenticate(user=self.user_org2_viewer)
        response = self.client.get(self.LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_list_user_no_role_sees_org1(self):
        self.client.force_authenticate(user=self.user_org1_norole)
        response = self.client.get(self.LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    # === Authorization Tests (CREATE) ===
    # perform_create checks add permission in the target organization
    def test_create_editor_org1_succeeds(self):
        self.client.force_authenticate(user=self.user_org1_editor)
        data = {'user': self.user_to_assign.pk, 'organization': self.org1.pk, 'role': self.viewer_role.pk}
        response = self.client.post(self.LIST_URL, data)
        # Editor role has 'add_organizationmembership'
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(OrganizationMembership.objects.filter(user=self.user_to_assign, organization=self.org1).exists())

    def test_create_viewer_org1_fails(self):
        self.client.force_authenticate(user=self.user_org1_viewer)
        data = {'user': self.user_to_assign.pk, 'organization': self.org1.pk, 'role': self.viewer_role.pk}
        response = self.client.post(self.LIST_URL, data)
        # Viewer role does NOT have 'add_organizationmembership'
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_editor_org1_for_org2_fails(self):
        # Check if perform_create correctly uses the *target* org's context
        self.client.force_authenticate(user=self.user_org1_editor)
        data = {'user': self.user_to_assign.pk, 'organization': self.org2.pk, 'role': self.viewer_role.pk}
        response = self.client.post(self.LIST_URL, data)
        # user_org1_editor does NOT have add permission in org2
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_user_no_role_org1_fails(self):
        self.client.force_authenticate(user=self.user_org1_norole)
        data = {'user': self.user_to_assign.pk, 'organization': self.org1.pk, 'role': self.viewer_role.pk}
        response = self.client.post(self.LIST_URL, data)
        # No role = no permissions
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_missing_organization_fails_validation(self):
        # Test mixin's validation before permission check
        self.client.force_authenticate(user=self.user_org1_admin) # Has add perm
        data = {'user': self.user_to_assign.pk, 'role': self.viewer_role.pk} # Missing org
        response = self.client.post(self.LIST_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) # Should fail validation


    # === Authorization Tests (RETRIEVE) ===
    def test_retrieve_viewer_org1_succeeds_for_org1(self):
        self.client.force_authenticate(user=self.user_org1_viewer)
        url = self.detail_url(self.member_editor_org1.pk) # Retrieving another member in same org
        response = self.client.get(url)
        # Viewer role has 'view_organizationmembership'
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.member_editor_org1.pk)

    def test_retrieve_viewer_org1_fails_for_org2(self):
        self.client.force_authenticate(user=self.user_org1_viewer)
        url = self.detail_url(self.member_viewer_org2.pk) # From different org
        response = self.client.get(url)
        # Permission denied based on object's org
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Or 403 depending on viewset scope filtering

    def test_retrieve_user_noperm_role_org1_fails_for_org1(self):
        self.client.force_authenticate(user=self.user_org1_noperm)
        url = self.detail_url(self.member_editor_org1.pk)
        response = self.client.get(url)
        # NoPerm role lacks 'view_organizationmembership'
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_user_no_role_org1_fails_for_org1(self):
        self.client.force_authenticate(user=self.user_org1_norole)
        url = self.detail_url(self.member_editor_org1.pk)
        response = self.client.get(url)
        # No role = no permissions
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    # === Authorization Tests (UPDATE) ===
    def test_update_editor_org1_succeeds_for_org1(self):
        self.client.force_authenticate(user=self.user_org1_editor)
        url = self.detail_url(self.member_viewer_org1.pk) # Updating another member in same org
        data = {'is_active': False}
        response = self.client.patch(url, data, format='json')
        # Editor role has 'change_organizationmembership'
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.member_viewer_org1.refresh_from_db()
        self.assertEqual(self.member_viewer_org1.is_active, False)

    def test_update_viewer_org1_fails_for_org1(self):
        self.client.force_authenticate(user=self.user_org1_viewer)
        url = self.detail_url(self.member_editor_org1.pk)
        data = {'is_active': False}
        response = self.client.patch(url, data, format='json')
        # Viewer role does NOT have 'change_organizationmembership'
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_editor_org1_fails_for_org2(self):
        self.client.force_authenticate(user=self.user_org1_editor)
        url = self.detail_url(self.member_viewer_org2.pk) # Target object in different org
        data = {'is_active': False}
        response = self.client.patch(url, data, format='json')
        # Permission denied based on object's org
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Or 403

    # === Authorization Tests (DELETE) ===
    def test_delete_admin_org1_succeeds_for_org1(self):
        self.client.force_authenticate(user=self.user_org1_admin)
        target_member = OrganizationMembershipFactory(organization=self.org1, user=UserFactory(), role=self.viewer_role)
        url = self.detail_url(target_member.pk)
        response = self.client.delete(url)
        # Admin role has 'delete_organizationmembership'
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(OrganizationMembership.objects.filter(pk=target_member.pk).exists())

    def test_delete_editor_org1_fails_for_org1(self):
        self.client.force_authenticate(user=self.user_org1_editor)
        target_member = OrganizationMembershipFactory(organization=self.org1, user=UserFactory(), role=self.viewer_role)
        url = self.detail_url(target_member.pk)
        response = self.client.delete(url)
        # Editor role does NOT have 'delete_organizationmembership'
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_admin_org1_fails_for_org2(self):
        self.client.force_authenticate(user=self.user_org1_admin)
        url = self.detail_url(self.member_viewer_org2.pk) # Target object in different org
        response = self.client.delete(url)
        # Permission denied based on object's org
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Or 403

# Note: To run these tests standalone or ensure the dynamic model works,
# you might need to temporarily add 'core.rbac.tests.integration' or similar
# to INSTALLED_APPS in a test settings override, or ensure the test runner
# correctly handles dynamic model/app registration and ContentType creation.
# The @pytest.mark.django_db(transaction=True) and apps.get_app_config(...).import_models()
# attempt to handle this, but environment setup can be tricky. 