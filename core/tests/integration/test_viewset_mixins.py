# core/tests/integration/test_viewset_mixins.py
import pytest
from unittest.mock import patch, MagicMock

from rest_framework import viewsets
from rest_framework.test import APIRequestFactory
from django.contrib.auth.models import AnonymousUser, Group

# Dummy user/org classes for fixtures (can use factories later if needed)
from api.v1.base_models.user.tests.factories import UserFactory
from api.v1.base_models.organization.tests.factories import OrganizationFactory

# Import the mixin and the test model from their new locations
from core.viewsets.mixins import OrganizationScopedViewSetMixin
from core.tests_app.models import MockOrgScopedModel # <-- Import from models.py

# Import OrganizationMembership model
from api.v1.base_models.organization.models import OrganizationMembership

# Placeholder for the actual mixin
# class OrganizationScopedViewSetMixin: # <-- Remove placeholder mixin
#     def get_queryset(self):
#         # Placeholder logic
#         print("Original get_queryset called")
#         # In a real ViewSet, this would be `self.queryset` or `super().get_queryset()`
#         # For testing, we'll mock the base queryset behavior
#         if hasattr(self, '_base_queryset'):
#              return self._base_queryset
#         # Try to get from class attribute if not set on instance
#         return self.__class__.queryset

# Dummy Model - REMOVE from here
# class MockOrgScopedModel(models.Model):
#     name = models.CharField(max_length=100)
#     organization = models.ForeignKey(
#         'api_v1_organization.Organization', # Use string to avoid direct import
#         on_delete=models.CASCADE,
#         related_name='mock_scoped_items'
#     )
#
#     class Meta:
#         # Required to prevent AppRegistryNotReady error if models aren't fully loaded
#         app_label = 'core_tests_app' # Use an existing test app or create one
#         # Add unique constraint to avoid accidental identical objects if needed
#         # unique_together = ('name', 'organization')
#
#     def __str__(self):
#         return self.name

# Dummy ViewSet using the Mixin
class MockScopedViewSet(OrganizationScopedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    # Define a base queryset for the viewset to work with
    queryset = MockOrgScopedModel.objects.all()
    serializer_class = MagicMock() # Don't need a real serializer for queryset tests

# --- Fixtures ---

@pytest.fixture
def factory():
    return APIRequestFactory()

# Define org fixtures
@pytest.fixture
def org_a(db):
    return OrganizationFactory(name="Org A")

@pytest.fixture
def org_b(db):
    return OrganizationFactory(name="Org B")

# Define role fixtures using Django Group
@pytest.fixture
def role_viewer_org_a(db):
    # Using Group model directly
    group, _ = Group.objects.get_or_create(name="Org A Viewer Role")
    # Optionally add permissions if needed for other tests, but likely not for this mixin test
    # perm = Permission.objects.get(codename='view_mockorgscopedmodel')
    # group.permissions.add(perm)
    return group

@pytest.fixture
def role_viewer_org_b(db):
    group, _ = Group.objects.get_or_create(name="Org B Viewer Role")
    return group

@pytest.fixture
def view(request): # Pass request to associate it
    view = MockScopedViewSet()
    view.request = request
    # Set a base queryset on the instance for the mixin's super() call simulation
    # view._base_queryset = MockOrgScopedModel.objects.all()
    return view

@pytest.fixture
def user_no_orgs(db):
    return UserFactory()

@pytest.fixture
def user_org_a(db, org_a, role_viewer_org_a):
    user = UserFactory()
    # Create membership directly
    membership = OrganizationMembership.objects.create(
        user=user,
        organization=org_a,
        is_active=True # Ensure membership is active
    )
    membership.roles.add(role_viewer_org_a)
    return user

@pytest.fixture
def user_org_b(db, org_b, role_viewer_org_b):
    user = UserFactory()
    # Create membership directly
    membership = OrganizationMembership.objects.create(
        user=user,
        organization=org_b,
        is_active=True
    )
    membership.roles.add(role_viewer_org_b)
    return user

@pytest.fixture
def user_org_a_b(db, org_a, org_b, role_viewer_org_a, role_viewer_org_b):
    user = UserFactory()
    # Create multiple memberships
    membership_a = OrganizationMembership.objects.create(
        user=user,
        organization=org_a,
        is_active=True
    )
    membership_a.roles.add(role_viewer_org_a)
    
    membership_b = OrganizationMembership.objects.create(
        user=user,
        organization=org_b,
        is_active=True
    )
    membership_b.roles.add(role_viewer_org_b)
    return user

@pytest.fixture
def super_user(db):
    return UserFactory(is_superuser=True)

@pytest.fixture
def obj_in_org_a(db, org_a):
    return MockOrgScopedModel.objects.create(name="ObjA", organization=org_a)

@pytest.fixture
def obj_in_org_b(db, org_b):
    return MockOrgScopedModel.objects.create(name="ObjB", organization=org_b)

# --- Tests ---

@pytest.mark.django_db
class TestOrganizationScopedViewSetMixin:

    # Remove placeholder test
    # def test_placeholder(self):
    #     """ Placeholder test to ensure file is runnable. """
    #     assert True

    @patch('core.viewsets.mixins.get_user_request_context')
    def test_queryset_filters_for_user_org_a(self, mock_get_context, factory, user_org_a, obj_in_org_a, obj_in_org_b):
        """ Test user in Org A only sees objects from Org A. """
        # Mock the helper to return org A context
        mock_get_context.return_value = ([obj_in_org_a.organization_id], True) # org_a ID, is_single

        request = factory.get('/dummy/')
        request.user = user_org_a

        # Instantiate view and call get_queryset
        view = MockScopedViewSet(request=request) # Pass request during init
        # view.request = request # Setting after init might also work
        filtered_qs = view.get_queryset()

        # Assertions
        assert obj_in_org_a in filtered_qs
        assert obj_in_org_b not in filtered_qs
        assert filtered_qs.count() == 1
        mock_get_context.assert_called_once_with(user_org_a)

    @patch('core.viewsets.mixins.get_user_request_context')
    def test_queryset_filters_for_user_org_b(self, mock_get_context, factory, user_org_b, obj_in_org_a, obj_in_org_b):
        """ Test user in Org B only sees objects from Org B. """
        mock_get_context.return_value = ([obj_in_org_b.organization_id], True)

        request = factory.get('/dummy/')
        request.user = user_org_b
        view = MockScopedViewSet(request=request)
        filtered_qs = view.get_queryset()

        assert obj_in_org_a not in filtered_qs
        assert obj_in_org_b in filtered_qs
        assert filtered_qs.count() == 1
        mock_get_context.assert_called_once_with(user_org_b)

    @patch('core.viewsets.mixins.get_user_request_context')
    def test_queryset_filters_for_user_org_a_b(self, mock_get_context, factory, user_org_a_b, obj_in_org_a, obj_in_org_b):
        """ Test user in Org A & B sees objects from both. """
        org_a_id = obj_in_org_a.organization_id
        org_b_id = obj_in_org_b.organization_id
        mock_get_context.return_value = ([org_a_id, org_b_id], False)

        request = factory.get('/dummy/')
        request.user = user_org_a_b
        view = MockScopedViewSet(request=request)
        filtered_qs = view.get_queryset()

        assert obj_in_org_a in filtered_qs
        assert obj_in_org_b in filtered_qs
        assert filtered_qs.count() == 2
        mock_get_context.assert_called_once_with(user_org_a_b)

    @patch('core.viewsets.mixins.get_user_request_context')
    def test_queryset_filters_for_user_no_orgs(self, mock_get_context, factory, user_no_orgs, obj_in_org_a, obj_in_org_b):
        """ Test user in no orgs sees nothing. """
        mock_get_context.return_value = ([], False)

        request = factory.get('/dummy/')
        request.user = user_no_orgs
        view = MockScopedViewSet(request=request)
        filtered_qs = view.get_queryset()

        assert obj_in_org_a not in filtered_qs
        assert obj_in_org_b not in filtered_qs
        assert filtered_qs.count() == 0
        mock_get_context.assert_called_once_with(user_no_orgs)

    @patch('core.viewsets.mixins.get_user_request_context')
    def test_queryset_filters_for_superuser(self, mock_get_context, factory, super_user, obj_in_org_a, obj_in_org_b):
        """ Test superuser sees all objects, bypassing org filter. """
        request = factory.get('/dummy/')
        request.user = super_user
        view = MockScopedViewSet(request=request)
        filtered_qs = view.get_queryset()

        assert obj_in_org_a in filtered_qs
        assert obj_in_org_b in filtered_qs
        assert filtered_qs.count() == 2
        # IMPORTANT: get_user_request_context should NOT be called for superuser
        mock_get_context.assert_not_called()

    @patch('core.viewsets.mixins.get_user_request_context')
    def test_queryset_filters_for_anonymous(self, mock_get_context, factory, obj_in_org_a, obj_in_org_b):
        """ Test anonymous user sees nothing (or raises error depending on view permissions). """
        # Assuming default IsAuthenticated permission denies anonymous
        # The mixin itself might still return an empty queryset if called.
        # mock_get_context.return_value = ([], False) # Context for anonymous - Not needed as mixin checks auth first

        request = factory.get('/dummy/')
        request.user = AnonymousUser()
        view = MockScopedViewSet(request=request)

        # Depending on base viewset permissions, this might raise NotAuthenticated
        # or proceed to get_queryset. Let's assume it proceeds for this test.
        filtered_qs = view.get_queryset()

        assert filtered_qs.count() == 0
        # get_user_request_context should NOT be called for anonymous users
        mock_get_context.assert_not_called() 