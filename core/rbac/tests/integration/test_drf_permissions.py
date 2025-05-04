import pytest
from unittest import mock
from unittest.mock import MagicMock, patch, ANY
from django.core.exceptions import PermissionDenied, ValidationError

from rest_framework.test import APIRequestFactory, APIClient
from rest_framework.views import APIView
from rest_framework import viewsets, status
from django.contrib.auth.models import AnonymousUser, User, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.utils import IntegrityError

# Adjust imports based on actual locations
from api.v1.base_models.organization.models import Organization, OrganizationMembership
from api.v1.base_models.user.tests.factories import UserFactory
from api.v1.base_models.organization.tests.factories import (
    OrganizationFactory,
    OrganizationTypeFactory,
    OrganizationMembershipFactory
)
# Import RBAC utils
from core.rbac.utils import get_user_request_context, get_validated_request_org_id
# Import core permission checker
from core.rbac.permissions import has_perm_in_org

# This import will fail until the class is created (TDD) - Now it should exist
from core.rbac.drf_permissions import HasModelPermissionInOrg

# Import the model from the test app
from core.tests_app.models import ConcreteScopedModel

# --- Fixtures ---

@pytest.fixture(scope="module") # Make module-scoped
def api_client():
    """Provides an APIClient instance for the entire test module."""
    return APIClient()

@pytest.fixture
def factory():
    return APIRequestFactory()

@pytest.fixture
def request_factory():
    return APIRequestFactory()

# Use a viewset based on a *real* model for permission codename generation
class MockConcreteScopedViewSet(viewsets.ViewSet):
    queryset = ConcreteScopedModel.objects.none() # Needs a queryset for model meta access
    permission_classes = [HasModelPermissionInOrg] # Apply the permission

    # Simulate standard actions
    def list(self, request): pass
    def create(self, request): pass
    def retrieve(self, request, pk=None): pass
    def update(self, request, pk=None): pass
    def partial_update(self, request, pk=None): pass
    def destroy(self, request, pk=None): pass

# --- Tests ---

@pytest.mark.django_db
class TestHasModelPermissionInOrg:
    """Tests for the HasModelPermissionInOrg permission class."""

    @pytest.fixture
    def view_instance(self):
        """Provides a view instance."""
        return MockConcreteScopedViewSet()

    @pytest.fixture
    def permission_instance(self):
        """Provides a permission class instance."""
        return HasModelPermissionInOrg()

    # --- has_permission Tests (List/Create) ---

    @pytest.mark.parametrize(
        "user_context, request_data, mock_has_perm_result, expected_result, expected_exception",
        [
            # === LIST Action ===
            # Single Org User, has 'view' perm -> PASS
            (("single", [1]), {}, True, True, None),
            # Single Org User, lacks 'view' perm -> FAIL
            (("single", [1]), {}, False, False, None),
            # Multi Org User, has 'view' perm in at least one org -> PASS
            (("multi", [1, 2]), {}, True, True, None),
             # Multi Org User, lacks 'view' perm in all orgs -> FAIL
            (("multi", [1, 2]), {}, False, False, None),
             # User with No Active Orgs -> FAIL
            (("none", []), {}, False, False, None),
        ]
    )
    def test_has_permission_list(
        self, mocker, factory, user, view_instance, permission_instance,
        user_context, request_data, mock_has_perm_result, expected_result, expected_exception
    ):
        """Tests has_permission specifically for the 'list' action."""
        view_instance.action = 'list'
        request = factory.get('/mock/', data=request_data)
        request.user = user

        context_type, active_org_ids = user_context
        is_single_org = context_type == "single"

        # Mock helpers
        mock_get_context = mocker.patch('core.rbac.drf_permissions.get_user_request_context', return_value=(active_org_ids, is_single_org))
        # Mock has_perm_in_org to check if it's called correctly for list
        mock_core_has_perm = mocker.patch('core.rbac.drf_permissions.has_perm_in_org', return_value=mock_has_perm_result)

        if expected_exception:
            with pytest.raises(expected_exception):
                permission_instance.has_permission(request, view_instance)
        else:
            result = permission_instance.has_permission(request, view_instance)
            assert result is expected_result

        # Verification
        mock_get_context.assert_called_once_with(user)
        if active_org_ids: # Only check has_perm if user has orgs
            # Check that has_perm_in_org was called correctly based on expected result
            expected_perm = 'core_tests_app.view_concretescopedmodel'
            if expected_result:
                # If permission expected, it should be called AT LEAST once
                mock_core_has_perm.assert_any_call(user, expected_perm, ANY)
                # Verify it was called with an ID from the active list
                first_call_args = mock_core_has_perm.call_args_list[0]
                assert first_call_args[0][0] == user
                assert first_call_args[0][1] == expected_perm
                assert first_call_args[0][2] in active_org_ids
            else:
                # If permission NOT expected, it must be called for ALL orgs
                expected_calls = [
                    mocker.call(user, expected_perm, org_id)
                    for org_id in active_org_ids
                ]
                assert mock_core_has_perm.call_count == len(active_org_ids)
                mock_core_has_perm.assert_has_calls(expected_calls, any_order=True)

    @pytest.mark.parametrize(
        "user_context, request_data, mock_validate_org_id_return, mock_has_perm_result, expected_result, expected_exception",
        [
            # === CREATE Action ===
            # Single Org User, Org ID not provided (implicit), has 'add' perm -> PASS (validate returns org_id)
            (("single", [1]), {}, 1, True, True, None),
            # Single Org User, Org ID not provided (implicit), lacks 'add' perm -> FAIL (validate returns org_id)
            (("single", [1]), {}, 1, False, False, None),
            # Single Org User, provides *correct* Org ID, has 'add' perm -> PASS (validate returns org_id)
            (("single", [1]), {'organization': '1'}, 1, True, True, None),
            # Single Org User, provides *incorrect* Org ID -> FAIL (validate raises ValidationError)
            (("single", [1]), {'organization': '2'}, ValidationError("dummy"), False, False, ValidationError),
             # Single Org User, provides *invalid format* Org ID -> FAIL (validate raises ValidationError)
            (("single", [1]), {'organization': 'abc'}, ValidationError("dummy"), False, False, ValidationError),

            # Multi Org User, Org ID provided, has 'add' perm -> PASS (validate returns org_id)
            (("multi", [1, 2]), {'organization': '1'}, 1, True, True, None),
            # Multi Org User, Org ID provided, lacks 'add' perm -> FAIL (validate returns org_id)
            (("multi", [1, 2]), {'organization': '1'}, 1, False, False, None),
            # Multi Org User, Org ID *not* provided -> FAIL (validate raises ValidationError)
            (("multi", [1, 2]), {}, ValidationError("dummy"), False, False, ValidationError),
            # Multi Org User, provides *invalid* Org ID (not member) -> FAIL (validate raises PermissionDenied)
            (("multi", [1, 2]), {'organization': '3'}, PermissionDenied("dummy"), False, False, PermissionDenied),
            # Multi Org User, provides *invalid format* Org ID -> FAIL (validate raises ValidationError)
            (("multi", [1, 2]), {'organization': 'abc'}, ValidationError("dummy"), False, False, ValidationError),

            # User with No Active Orgs -> FAIL (validate raises PermissionDenied)
            (("none", []), {}, PermissionDenied("dummy"), False, False, PermissionDenied),
        ]
    )
    def test_has_permission_create(
        self, mocker, factory, user, view_instance, permission_instance,
        user_context, request_data, mock_validate_org_id_return, mock_has_perm_result, expected_result, expected_exception
    ):
        """Tests has_permission specifically for the 'create' action."""
        view_instance.action = 'create'
        request = factory.post('/mock/', data=request_data) # Use POST for create
        request.user = user

        # Mock helpers
        if isinstance(mock_validate_org_id_return, Exception):
             mock_validate = mocker.patch('core.rbac.drf_permissions.get_validated_request_org_id', side_effect=mock_validate_org_id_return)
        else:
             mock_validate = mocker.patch('core.rbac.drf_permissions.get_validated_request_org_id', return_value=mock_validate_org_id_return)

        mock_core_has_perm = mocker.patch('core.rbac.drf_permissions.has_perm_in_org', return_value=mock_has_perm_result)

        if expected_exception:
            # We expect the permission class to *catch* validation/permission errors from the helper
            # and return False, not raise the exception itself.
            result = permission_instance.has_permission(request, view_instance)
            assert result is False, f"Expected False when helper raises {expected_exception}, but got {result}"
            mock_validate.assert_called_once_with(request, required_for_action=True)
            # has_perm should not be called if validation failed
            mock_core_has_perm.assert_not_called()
        else:
            result = permission_instance.has_permission(request, view_instance)
            assert result is expected_result
            # Verification
            mock_validate.assert_called_once_with(request, required_for_action=True)
            # has_perm_in_org should be called only if validation succeeded
            if not isinstance(mock_validate_org_id_return, Exception) and mock_validate_org_id_return is not None:
                 mock_core_has_perm.assert_called_once_with(user, 'core_tests_app.add_concretescopedmodel', mock_validate_org_id_return)
            else:
                 mock_core_has_perm.assert_not_called() # Not called if validation fails or returns None (shouldn't for create)

    # --- has_object_permission Tests (Retrieve/Update/Delete) ---

    @pytest.mark.parametrize(
        "action, method, setup_object, should_have_perm, expected_result",
        [
            # === has_object_permission ===
            # Retrieve (View) - Has Perm
            ("retrieve", "get", True, True, True),
            # Retrieve (View) - Lacks Perm
            ("retrieve", "get", True, False, False),
            # Update (Change) - Has Perm
            ("update", "put", True, True, True),
            # Update (Change) - Lacks Perm
            ("update", "put", True, False, False),
            # Partial Update (Change) - Has Perm
            ("partial_update", "patch", True, True, True),
            # Partial Update (Change) - Lacks Perm
            ("partial_update", "patch", True, False, False),
            # Destroy (Delete) - Has Perm
            ("destroy", "delete", True, True, True),
            # Destroy (Delete) - Lacks Perm
            ("destroy", "delete", True, False, False),
        ]
    )
    def test_has_object_permission_checks(
        self, mocker, factory, user, org_a, obj_in_org_a, view_instance, permission_instance, # Use obj_in_org_a
        action, method, setup_object, should_have_perm, expected_result
    ):
        """Tests has_object_permission scenarios."""
        assert setup_object is True # These tests are only for object permissions

        view_instance.action = action
        obj = obj_in_org_a # Use the concrete model object
        request = factory.generic(method, f'/mock/{obj.pk}/')
        request.user = user

        # Mock the core permission checker
        mock_has_perm = mocker.patch('core.rbac.drf_permissions.has_perm_in_org', return_value=should_have_perm)

        # Test has_object_permission
        result = permission_instance.has_object_permission(request, view_instance, obj)
        assert result is expected_result, f"Test {action} failed! Expected {expected_result} but got {result}."

        # Check if the correct permission was checked via the helper
        # Need to manually construct the expected perm codename based on the ConcreteScopedModel
        perm_map = {
            'retrieve': 'view_concretescopedmodel',
            'update': 'change_concretescopedmodel',
            'partial_update': 'change_concretescopedmodel',
            'destroy': 'delete_concretescopedmodel',
        }
        expected_perm_check = f'core_tests_app.{perm_map[action]}' # core_tests_app is the app label
        mock_has_perm.assert_called_once_with(user, expected_perm_check, obj)

    # --- General Access Tests ---

    def test_superuser_access(self, factory, super_user, obj_in_org_a, view_instance, permission_instance):
        """Superusers should always have access."""
        # Test has_permission (list)
        request_list = factory.get('/mock/')
        request_list.user = super_user
        view_instance.action = 'list'
        assert permission_instance.has_permission(request_list, view_instance) is True

        # Test has_permission (create)
        request_create = factory.post('/mock/')
        request_create.user = super_user
        view_instance.action = 'create'
        assert permission_instance.has_permission(request_create, view_instance) is True

        # Test has_object_permission (retrieve)
        request_retrieve = factory.get(f'/mock/{obj_in_org_a.pk}/')
        request_retrieve.user = super_user
        view_instance.action = 'retrieve'
        assert permission_instance.has_object_permission(request_retrieve, view_instance, obj_in_org_a) is True

    def test_unauthenticated_user(self, factory, obj_in_org_a, view_instance, permission_instance):
        """Unauthenticated users should be denied."""
        anon_user = AnonymousUser()

        # Test has_permission (list)
        request_list = factory.get('/mock/')
        request_list.user = anon_user
        view_instance.action = 'list'
        assert permission_instance.has_permission(request_list, view_instance) is False

        # Test has_permission (create)
        request_create = factory.post('/mock/')
        request_create.user = anon_user
        view_instance.action = 'create'
        assert permission_instance.has_permission(request_create, view_instance) is False

        # Test has_object_permission (retrieve)
        request_retrieve = factory.get(f'/mock/{obj_in_org_a.pk}/')
        request_retrieve.user = anon_user
        view_instance.action = 'retrieve'
        assert permission_instance.has_object_permission(request_retrieve, view_instance, obj_in_org_a) is False

# Remove the entire TestCanAccessOrganizationObject class
# class TestCanAccessOrganizationObject:
#     ... (all tests removed) ... 