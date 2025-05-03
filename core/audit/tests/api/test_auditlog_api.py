import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.audit.models import AuditLog
from core.audit.choices import AuditActionType
from core.audit.tests.factories import AuditLogFactory
from api.v1.base_models.organization.tests.factories import OrganizationFactory
from api.v1.base_models.user.tests.factories import UserFactory

User = get_user_model()

# Use the new 'core' namespace
AUDIT_NAMESPACE = "core"

AUDIT_LOG_LIST_URL = reverse(f"{AUDIT_NAMESPACE}:auditlog-list")


def detail_url(audit_log_id):
    return reverse(f"{AUDIT_NAMESPACE}:auditlog-detail", args=[audit_log_id])


@pytest.mark.django_db
class TestAuditLogViewSetPermissions:
    """Tests for access control on the AuditLogViewSet."""

    @pytest.fixture(autouse=True)
    def setup_data(self, db):
        # Clear existing logs before creating test-specific ones
        AuditLog.objects.all().delete()

        self.admin_user = UserFactory(is_staff=True, is_superuser=True)
        self.regular_user = UserFactory()
        self.organization = OrganizationFactory()
        # Create some logs - these might also trigger audit logs for THEIR creation if signals are active
        # Let's create logs directly AFTER creating users/orgs to have cleaner counts
        AuditLog.objects.all().delete() # Clear again after factory triggers

        self.log_detail = AuditLogFactory(organization=self.organization, user=self.admin_user)
        AuditLogFactory.create_batch(3, organization=self.organization, user=self.regular_user)
        # Now we should have exactly 4 logs for this test class scope

        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin_user)

        self.regular_client = APIClient()
        self.regular_client.force_authenticate(user=self.regular_user)

        self.unauthenticated_client = APIClient()

    def test_list_unauthenticated_denied(self):
        """Verify unauthenticated users cannot list audit logs."""
        response = self.unauthenticated_client.get(AUDIT_LOG_LIST_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_unauthenticated_denied(self):
        """Verify unauthenticated users cannot retrieve an audit log."""
        response = self.unauthenticated_client.get(detail_url(self.log_detail.pk))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_regular_user_denied(self):
        """Verify regular (non-admin) users cannot list audit logs."""
        response = self.regular_client.get(AUDIT_LOG_LIST_URL)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_regular_user_denied(self):
        """Verify regular (non-admin) users cannot retrieve an audit log."""
        response = self.regular_client.get(detail_url(self.log_detail.pk))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_admin_user_allowed(self):
        """Verify admin users can list audit logs."""
        response = self.admin_client.get(AUDIT_LOG_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        # Should see exactly the 4 logs created in setup_data after cleanup
        assert response.data['count'] == 4
        assert len(response.data['results']) == 4

    def test_retrieve_admin_user_allowed(self):
        """Verify admin users can retrieve an audit log."""
        response = self.admin_client.get(detail_url(self.log_detail.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == self.log_detail.pk

    def test_non_read_methods_disallowed(self):
        """Verify POST, PUT, PATCH, DELETE are not allowed (ReadOnlyViewSet)."""
        list_response_post = self.admin_client.post(AUDIT_LOG_LIST_URL, {})
        detail_response_put = self.admin_client.put(detail_url(self.log_detail.pk), {})
        detail_response_patch = self.admin_client.patch(detail_url(self.log_detail.pk), {})
        detail_response_delete = self.admin_client.delete(detail_url(self.log_detail.pk))

        assert list_response_post.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert detail_response_put.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert detail_response_patch.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert detail_response_delete.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestAuditLogViewSetFilteringAndPagination:
    """Tests for filtering and pagination on the AuditLogViewSet."""

    @pytest.fixture(autouse=True)
    def setup_data(self, db):
        # Create users and orgs first (these might trigger logs)
        self.admin_user = UserFactory(is_staff=True, is_superuser=True)
        self.user1 = UserFactory()
        self.user2 = UserFactory()
        self.org1 = OrganizationFactory(name="Org Alpha")
        self.org2 = OrganizationFactory(name="Org Beta")

        # Clear ALL logs (including any created by factories above) BEFORE creating specific test logs
        AuditLog.objects.all().delete()

        # Create specific logs for filtering tests
        self.log1_user1_org1_create = AuditLogFactory(user=self.user1, organization=self.org1, action_type=AuditActionType.CREATE)
        self.log2_user1_org2_update = AuditLogFactory(user=self.user1, organization=self.org2, action_type=AuditActionType.UPDATE)
        self.log3_user2_org1_delete = AuditLogFactory(user=self.user2, organization=self.org1, action_type=AuditActionType.DELETE)
        self.log4_user2_org2_login = AuditLogFactory(user=self.user2, organization=self.org2, action_type=AuditActionType.LOGIN_SUCCESS)
        self.log5_admin_org1_event = AuditLogFactory(user=self.admin_user, organization=self.org1, action_type=AuditActionType.SYSTEM_EVENT)
        # Now we should have exactly 5 logs relevant to these filter tests

        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)

    def test_filter_by_user(self):
        response = self.client.get(AUDIT_LOG_LIST_URL, {'user': self.user1.pk})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2 # Expecting log1 and log2
        log_ids = {item['id'] for item in response.data['results']}
        assert log_ids == {self.log1_user1_org1_create.pk, self.log2_user1_org2_update.pk}

    def test_filter_by_organization(self):
        response = self.client.get(AUDIT_LOG_LIST_URL, {'organization': self.org1.pk})
        assert response.status_code == status.HTTP_200_OK

        # --- Debugging --- 
        # print("\n--- Debugging test_filter_by_organization ---")
        # print(f"Filtering for org1 PK: {self.org1.pk}")
        # print(f"Expected log IDs: {{log1: {self.log1_user1_org1_create.pk}, log3: {self.log3_user2_org1_delete.pk}, log5: {self.log5_admin_org1_event.pk}}}")
        # actual_ids = {item['id'] for item in response.data['results']}
        # print(f"Actual log IDs found: {actual_ids}")
        # print(f"Actual response count: {response.data['count']}")
        # print("--- End Debugging ---\n")
        # --- End Debugging ---

        assert response.data['count'] == 3 # Expecting log1, log3, log5
        log_ids = {item['id'] for item in response.data['results']}
        assert log_ids == {self.log1_user1_org1_create.pk, self.log3_user2_org1_delete.pk, self.log5_admin_org1_event.pk}

    def test_filter_by_action_type(self):
        response = self.client.get(AUDIT_LOG_LIST_URL, {'action_type': AuditActionType.UPDATE})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1 # Expecting log2
        assert response.data['results'][0]['id'] == self.log2_user1_org2_update.pk

    # TODO: Add tests for timestamp filtering (before/after)
    # Need to use created_at_before / created_at_after query params now

    # TODO: Add tests for content_type filtering
    # TODO: Add tests for object_id filtering

    def test_pagination_works(self):
        # Now that logs are cleaned, default list should show exactly 5
        response = self.client.get(AUDIT_LOG_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5
        assert 'next' in response.data
        assert 'previous' in response.data
        assert 'results' in response.data
        assert len(response.data['results']) == 5 # Assuming default page size >= 5

        # TODO: Test requesting a specific page size (needs pagination class configured)
        # response_small_page = self.client.get(AUDIT_LOG_LIST_URL, {'page_size': 2})
        # assert response_small_page.status_code == status.HTTP_200_OK
        # assert len(response_small_page.data['results']) == 2
        # assert response_small_page.data['count'] == 5
        # assert response_small_page.data['next'] is not None
        pass

    def test_ordering_by_timestamp_desc_default(self):
        response = self.client.get(AUDIT_LOG_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        # Check against the 5 specific logs created in setup
        assert [item['id'] for item in results] == [
            self.log5_admin_org1_event.pk,
            self.log4_user2_org2_login.pk,
            self.log3_user2_org1_delete.pk,
            self.log2_user1_org2_update.pk,
            self.log1_user1_org1_create.pk,
        ]

    def test_ordering_by_user_asc(self):
        # Create a log with no user to test None handling
        log_no_user = AuditLogFactory(user=None, organization=self.org1, action_type=AuditActionType.SYSTEM_EVENT)

        response = self.client.get(AUDIT_LOG_LIST_URL, {'ordering': 'user__username'})
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        # Check if usernames (or None for system logs) are sorted ascending, None last
        usernames = []
        for item in results:
            if item['user']: # Check if user exists
                usernames.append(item['user']['username'])
            else:
                usernames.append(None) # Represent system user as None

        # Expected order: admin_user, user1, user1, user2, user2, then None (system log)
        # Database default sort usually puts NULLs last when ascending
        non_none_usernames = sorted([u for u in usernames if u is not None])
        expected_order = non_none_usernames + [None] # Expect None at the end

        assert usernames == expected_order, f"Expected order {expected_order}, but got {usernames}"

# TODO: Add tests for remaining filters (timestamp, content_type, object_id)
# TODO: Refine pagination tests once Pagination class is set on ViewSet
# TODO: Modify UserSummarySerializer to handle null users gracefully for ordering test

# TODO: Add tests for remaining filters (timestamp, content_type, object_id)
# TODO: Refine pagination tests once Pagination class is set on ViewSet
# TODO: Refine ordering tests once Serializer is implemented to check actual user/org PKs 