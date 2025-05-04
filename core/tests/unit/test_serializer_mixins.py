# core/tests/unit/test_serializer_mixins.py
import pytest
from unittest.mock import patch, MagicMock

from rest_framework import serializers
from django.core.exceptions import PermissionDenied, ValidationError

from core.serializers.mixins import OrganizationScopedSerializerMixin

# Dummy classes for testing
class MockOrganizationScopedModel:
    # Minimal model mock
    pk: int
    organization_id: int

    def __init__(self, pk=None, organization_id=None):
        self.pk = pk
        self.organization_id = organization_id

# Remove placeholder mixin
# class OrganizationScopedSerializerMixin(serializers.Serializer):
#     ...

class DummyScopedSerializer(OrganizationScopedSerializerMixin, serializers.Serializer):
    name = serializers.CharField(max_length=100)
    # Organization field comes from mixin

    class Meta:
        # model = MockOrganizationScopedModel # Meta model not needed if not ModelSerializer
        fields = ['name', 'organization']

# --- Fixtures ---

@pytest.fixture
def mock_user():
    user = MagicMock()
    user.is_authenticated = True
    user.is_superuser = False
    user.pk = 123
    return user

@pytest.fixture
def serializer_context(mock_user):
    """ Provides a basic serializer context with a request and user. """
    request = MagicMock()
    request.user = mock_user
    request.data = {} # Test can override this
    return {'request': request}

# --- Tests ---

@pytest.mark.django_db
class TestOrganizationScopedSerializerMixin:

    # --- Test validate method ---
    @pytest.mark.parametrize(
        "user_context_return, initial_data, expected_exception, expected_msg_part",
        [
            # === Single-Org User ===
            # Org *not* provided -> PASS
            (("single", [1]), {"name": "Test"}, None, None),
            # Org provided as None/null -> PASS (field is read_only, won't be in validated_data)
            (("single", [1]), {"name": "Test", "organization": None}, None, None),

            # === Multi-Org User ===
            # REMOVED: Mixin no longer validates multi-org input
            # (("multi", [1, 2]), {"name": "Test", "organization": 1}, None, None),
            # (("multi", [1, 2]), {"name": "Test", "organization": 2}, None, None),
            # (("multi", [1, 2]), {"name": "Test"}, ValidationError, "must be provided"),
            # (("multi", [1, 2]), {"name": "Test", "organization": 3}, ValidationError, "do not have access"),
            # (("multi", [1, 2]), {"name": "Test", "organization": None}, ValidationError, "must be provided"),

            # === No-Org User ===
            # Org provided -> FAIL (Shouldn't have access anyway)
            (("none", []), {"name": "Test", "organization": 1}, PermissionDenied, "any active organizations"),
            # Org not provided -> FAIL
            (("none", []), {"name": "Test"}, PermissionDenied, "any active organizations"),
        ]
    )
    @patch('core.serializers.mixins.get_user_request_context') # Patch the helper location
    def test_validate_organization_field_on_create(
        self, mock_get_context, serializer_context, mock_user,
        user_context_return, initial_data, expected_exception, expected_msg_part
    ):
        """ Tests the validation logic based on user org context during creation. """
        context_type, active_org_ids = user_context_return
        is_single_org = context_type == "single"
        mock_get_context.return_value = (active_org_ids, is_single_org)

        # Set initial_data directly for testing validate with multi-org provided org
        serializer_context['request'].data = initial_data # Simulate request data for multi-org check
        serializer = DummyScopedSerializer(data=initial_data, context=serializer_context)

        if expected_exception:
            with pytest.raises(expected_exception) as excinfo:
                serializer.is_valid(raise_exception=True)
            if expected_msg_part:
                # Check if the error message contains the expected text part
                error_str = str(excinfo.value).lower()
                assert expected_msg_part in error_str
                # Specifically check for the 'organization' field error if ValidationError
                if isinstance(excinfo.value, ValidationError):
                     assert 'organization' in excinfo.value.detail or expected_msg_part in error_str
        else:
            assert serializer.is_valid(raise_exception=True) is True
            # Optionally check validated_data if needed, but create test is separate

        # Verify context helper was called
        mock_get_context.assert_called_once_with(mock_user)

        # Ensure request.data is set for the no-org test case if it relies on it indirectly
        if context_type == "none":
             serializer_context['request'].data = initial_data

    # TODO: Add tests for validate on update (e.g., ensure org cannot be changed)

    # --- Test create method ---
    @pytest.mark.parametrize(
        "user_context_return, initial_data, expected_org_id_in_create",
        [
            # === Single-Org User ===
            # Org not provided -> Should be set automatically
            (("single", [1]), {"name": "Test"}, 1),
            # Org provided as None -> Should be set automatically
            (("single", [1]), {"name": "Test", "organization": None}, 1),

            # === Multi-Org User ===
            # REMOVED: Mixin does not auto-set for multi-org
            # (("multi", [1, 2]), {"name": "Test", "organization": 2}, 2),
        ]
    )
    @patch('core.serializers.mixins.get_user_request_context')
    def test_create_sets_organization_id(
        self, mock_get_context, serializer_context, mock_user,
        user_context_return, initial_data, expected_org_id_in_create
    ):
        """ Tests that the create method correctly sets organization_id in validated_data. """
        context_type, active_org_ids = user_context_return
        is_single_org = context_type == "single"
        mock_get_context.return_value = (active_org_ids, is_single_org)

        # Simulate request data for multi-org check within validate
        serializer_context['request'].data = initial_data
        serializer = DummyScopedSerializer(data=initial_data, context=serializer_context)

        assert serializer.is_valid(raise_exception=True) is True

        # Access validated_data *after* is_valid() but *before* create()
        validated_data_before_create = serializer.validated_data.copy()

        # Call the mixin's create method to modify validated_data
        # We don't expect a return value anymore
        serializer.create(validated_data_before_create)

        # Assert that the organization_id was correctly set in the validated_data dict
        assert 'organization_id' in validated_data_before_create
        assert validated_data_before_create['organization_id'] == expected_org_id_in_create
        # Ensure the original read-only field key is gone
        assert 'organization' not in validated_data_before_create

        # Verify context helper was called by validate
        mock_get_context.assert_called_once_with(mock_user)

    @patch('core.serializers.mixins.get_user_request_context')
    def test_create_fails_if_org_id_missing_unexpectedly(
        self, mock_get_context, serializer_context, mock_user
    ):
        """ Tests that create raises an error if org ID wasn't determined (defensive check). """
        # Simulate a scenario where validate might somehow pass without setting the internal ID
        mock_get_context.return_value = ([], False) # e.g., user loses org access between validate and create?

        serializer = DummyScopedSerializer(data={"name": "Test"}, context=serializer_context)

        # We expect validate to fail first in a real scenario, but test create defensively
        # Manually call create with data that *would* be valid if org was set
        with pytest.raises(ValidationError) as excinfo:
             # We need to bypass the initial is_valid() call for this specific test
             # and manually call create with potentially incomplete validated data.
             # Normally, is_valid() would fail first if get_user_request_context returns ([], False)
             # Let's simulate validated_data that passed *before* org context changed.
             validated_data_simulated = {"name": "Test"} 
             # Directly call create, assuming _validated_organization_id wasn't set
             if hasattr(serializer, '_validated_organization_id'):
                  delattr(serializer, '_validated_organization_id') # Ensure it's not set
             serializer.create(validated_data_simulated)

        assert "valid organization context" in str(excinfo.value).lower()
        # Note: mock_get_context won't be called here as we bypassed is_valid

