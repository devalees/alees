import pytest
from django.urls import reverse
from rest_framework import status # Import status
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.mixins import CreateModelMixin
# from rest_framework.test import APIRequestFactory, force_authenticate # Remove APIRequestFactory
from rest_framework.test import APIClient, force_authenticate # Import APIClient
from rest_framework import permissions # Import permissions
from django.contrib.auth import get_user_model
from django.test import override_settings

# Import your models and factories
from api.v1.base_models.organization.models import Organization, OrganizationMembership
from api.v1.base_models.organization.tests.factories import OrganizationFactory, OrganizationMembershipFactory
from api.v1.base_models.user.tests.factories import UserFactory
# Import the concrete test model from the new test app
from core.tests_app.models import ConcreteScopedModel as TestScopedModel
# Import the Mixin
from core.views import OrganizationScopedViewSetMixin
# Import the new Create serializer
from core.tests_app.serializers import ConcreteCreateScopedSerializer

# --- Concrete ViewSet for testing ---
class ConcreteScopedViewSet(OrganizationScopedViewSetMixin, CreateModelMixin, ReadOnlyModelViewSet):
    queryset = TestScopedModel.objects.all()
    permission_classes = [permissions.IsAuthenticated] # Add permission class
    serializer_class = ConcreteCreateScopedSerializer # Add serializer class
    # Add a basic serializer if needed for list view, or test queryset directly
    # serializer_class = ...
# --- End Test ViewSet ---

@pytest.mark.django_db
class TestOrganizationScopedViewSetMixin:
    @pytest.fixture
    def org_a(self): return OrganizationFactory(name="Org A")
    
    @pytest.fixture
    def org_b(self): return OrganizationFactory(name="Org B")

    @pytest.fixture
    def user_a(self, org_a): # User only in Org A
        user = UserFactory(username='user_a')
        OrganizationMembershipFactory(user=user, organization=org_a)
        return user

    @pytest.fixture
    def user_b(self, org_b): # User only in Org B
        user = UserFactory(username='user_b')
        OrganizationMembershipFactory(user=user, organization=org_b)
        return user

    @pytest.fixture
    def user_ab(self, org_a, org_b): # User in Org A and B
        user = UserFactory(username='user_ab')
        OrganizationMembershipFactory(user=user, organization=org_a)
        OrganizationMembershipFactory(user=user, organization=org_b)
        return user

    @pytest.fixture
    def user_none(self): # User in no orgs
        return UserFactory(username='user_none')

    @pytest.fixture
    def super_user(self):
        return UserFactory(is_superuser=True, username='super')

    @pytest.fixture
    def items(self, org_a, org_b):
        item_a1 = TestScopedModel.objects.create(name="Item A1", organization=org_a)
        item_a2 = TestScopedModel.objects.create(name="Item A2", organization=org_a)
        item_b1 = TestScopedModel.objects.create(name="Item B1", organization=org_b)
        return {'a1': item_a1, 'a2': item_a2, 'b1': item_b1}

    @pytest.fixture
    def client(self): # Add APIClient fixture
        return APIClient()

    def test_superuser_sees_all(self, client, super_user, items):
        # Define URL inside the test method
        test_url = reverse('test-scoped-item-list')
        client.force_authenticate(user=super_user)
        response = client.get(test_url)
        
        assert response.status_code == status.HTTP_200_OK
        # Assuming default list response format, check IDs in results
        result_ids = {item['id'] for item in response.data['results']}
        expected_ids = {items['a1'].pk, items['a2'].pk, items['b1'].pk}
        assert response.data['count'] == 3
        assert result_ids == expected_ids

    def test_user_a_sees_org_a_only(self, client, user_a, items):
        test_url = reverse('test-scoped-item-list')
        client.force_authenticate(user=user_a)
        response = client.get(test_url)

        assert response.status_code == status.HTTP_200_OK
        result_ids = {item['id'] for item in response.data['results']}
        expected_ids = {items['a1'].pk, items['a2'].pk}
        assert response.data['count'] == 2
        assert result_ids == expected_ids

    def test_user_b_sees_org_b_only(self, client, user_b, items):
        test_url = reverse('test-scoped-item-list')
        client.force_authenticate(user=user_b)
        response = client.get(test_url)
        
        assert response.status_code == status.HTTP_200_OK
        result_ids = {item['id'] for item in response.data['results']}
        expected_ids = {items['b1'].pk}
        assert response.data['count'] == 1
        assert result_ids == expected_ids

    def test_user_ab_sees_both(self, client, user_ab, items):
        test_url = reverse('test-scoped-item-list')
        client.force_authenticate(user=user_ab)
        response = client.get(test_url)
        
        assert response.status_code == status.HTTP_200_OK
        result_ids = {item['id'] for item in response.data['results']}
        expected_ids = {items['a1'].pk, items['a2'].pk, items['b1'].pk}
        assert response.data['count'] == 3
        assert result_ids == expected_ids

    def test_user_none_sees_nothing(self, client, user_none, items):
        test_url = reverse('test-scoped-item-list')
        client.force_authenticate(user=user_none)
        response = client.get(test_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0
        assert len(response.data['results']) == 0

    # --- Tests for perform_create --- (Added from Task Block 3)
    def test_perform_create_success_with_permission(self, client, user_a, org_a):
        """Verify successful creation when permission check passes.
           Requires user_a to actually have add_concretescopedmodel perm in org_a.
           (We need to grant this permission for the test setup)
        """
        # --- Grant Permission for Test ---
        from django.contrib.auth.models import Permission, Group
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(TestScopedModel)
        add_perm = Permission.objects.get(content_type=ct, codename=f'add_{TestScopedModel._meta.model_name}')
        test_group = Group.objects.create(name='ScopedModel Adders')
        test_group.permissions.add(add_perm)
        # Find user_a's membership and assign the group
        membership_a = OrganizationMembership.objects.get(user=user_a, organization=org_a)
        membership_a.role = test_group # Assign group as role
        membership_a.save()
        # --- End Permission Grant ---

        data = {'name': 'New Item A', 'organization': org_a.pk}
        test_url = reverse('test-scoped-item-list') # POST goes to the list endpoint
        client.force_authenticate(user=user_a)
        response = client.post(test_url, data=data)

        # Assertions
        assert response.status_code == status.HTTP_201_CREATED # Check for 201 Created
        assert TestScopedModel.objects.count() == 1
        new_item = TestScopedModel.objects.first()
        assert new_item.name == 'New Item A'
        assert new_item.organization == org_a
        # Verify the permission check was called correctly (implicitly by mixin)

    def test_perform_create_fail_without_permission(self, client, user_a, org_b):
        """Verify creation fails if permission check returns False.
           User A should NOT have permission in Org B by default.
        """
        data = {'name': 'New Item B', 'organization': org_b.pk}
        test_url = reverse('test-scoped-item-list')
        client.force_authenticate(user=user_a)
        response = client.post(test_url, data=data)

        assert response.status_code == status.HTTP_403_FORBIDDEN # Check for 403 Forbidden
        assert TestScopedModel.objects.count() == 0
        # Check permission mock call (implicitly done by mixin)

    def test_perform_create_fail_missing_organization(self, client, user_a):
        """Verify validation error if organization is missing in POST data."""
        data = {'name': 'New Item Missing Org'} # Missing organization
        test_url = reverse('test-scoped-item-list')
        client.force_authenticate(user=user_a)
        response = client.post(test_url, data=data)

        # Serializer validation should catch this
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'organization' in response.data # Check error message relates to org
        assert TestScopedModel.objects.count() == 0

    # Test case for non-existent organization PK might be good too, handled by serializer validation
    def test_perform_create_fail_invalid_organization_pk(self, client, user_a):
        """Verify validation error if organization PK does not exist."""
        non_existent_org_pk = 99999
        data = {'name': 'New Item Invalid Org', 'organization': non_existent_org_pk}
        test_url = reverse('test-scoped-item-list')
        client.force_authenticate(user=user_a)
        response = client.post(test_url, data=data)

        # Serializer validation should catch this
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'organization' in response.data
        assert "Invalid pk" in str(response.data['organization'])
        assert TestScopedModel.objects.count() == 0 