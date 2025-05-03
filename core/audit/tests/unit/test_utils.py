import pytest
from unittest.mock import patch, Mock, call
from django.contrib.contenttypes.models import ContentType
import crum # Make sure crum is imported
import logging
# Import signal tools
from django.db.models.signals import post_save

# Import Organization model for fallback logic and signal disconnection
from api.v1.base_models.organization.models import Organization
# Import the specific signal handler to disconnect/reconnect by reference
from core.audit.signals import audit_post_save

from core.audit.models import AuditLog # To check the model being created
from core.audit.choices import AuditActionType
# Import the utils module to test
from core.audit import utils

# Need factories for test objects
from api.v1.base_models.user.tests.factories import UserFactory
from api.v1.base_models.organization.tests.factories import OrganizationFactory

# --- Fixtures ---

# Mock AuditLog.objects.create *specifically where it's called in the utils module*
@pytest.fixture
def mock_audit_log_create(mocker):
    # Patch the target within the utils module
    return mocker.patch('core.audit.utils.AuditLog.objects.create')

# Mock crum.get_current_request where it's used in the utils module
@pytest.fixture()
def mock_current_request(mocker):
    mock_request = Mock()
    mock_request.META = {'REMOTE_ADDR': '192.0.2.1'} # Example IP
    # Patch the lookup path used by core.audit.utils
    mocker.patch('core.audit.utils.get_current_request', return_value=mock_request)
    # --- ADDED: Explicitly set crum's thread-local request FOR THE TEST SCOPE --- 
    crum.set_current_request(mock_request)
    yield mock_request # Use yield to ensure cleanup
    # Restore thread-local state after test
    crum.set_current_request(None)

# --- Tests for get_object_repr --- #

@pytest.mark.django_db
def test_get_object_repr_standard(organization_factory):
    org = organization_factory(name="Test Org Name")
    repr_str = utils.get_object_repr(org)
    assert repr_str == "Test Org Name"

def test_get_object_repr_truncation():
    """Test that get_object_repr truncates long strings."""
    long_string = "B" * 500
    class LongStrObj:
        pk = 1
        _meta = Mock(verbose_name='Long Str Obj')
        def __str__(self):
            return long_string

    obj = LongStrObj()
    repr_str = utils.get_object_repr(obj)
    assert len(repr_str) == 255
    assert repr_str == long_string[:255]

def test_get_object_repr_no_str():
    """Test fallback representation when __str__ fails or isn't useful."""
    class NoStrObj:
        pk = 123
        _meta = Mock(verbose_name='No Str Obj') # Mock _meta
        def __str__(self):
            raise TypeError("Cannot stringify")

    obj = NoStrObj()
    repr_str = utils.get_object_repr(obj)
    assert repr_str == "<No Str Obj object (123)>"

def test_get_object_repr_none():
    assert utils.get_object_repr(None) is None

# --- Tests for calculate_changes --- #

# NOTE: These are placeholder tests as calculate_changes is not implemented
def test_calculate_changes_placeholder():
    assert utils.calculate_changes(None) is None

# --- Tests for get_request_context --- #

def test_get_request_context_with_request(mock_current_request):
    # mock_current_request fixture provides the request with META
    context = utils.get_request_context()
    assert context == {'ip_address': '192.0.2.1'}

@patch('core.audit.utils.get_current_request', return_value=None)
def test_get_request_context_no_request(mock_get_req):
    # Mock get_current_request directly to return None
    context = utils.get_request_context()
    assert context is None

# --- Tests for log_audit_event --- #

@pytest.mark.django_db
def test_log_audit_event_no_object(mock_audit_log_create, mock_current_request, user_factory, organization_factory):
    """Test logging an event without a specific content_object (e.g., LOGIN)."""
    user = user_factory()
    # Need the organization the user belongs to for the log
    # Get the organization created implicitly by the UserFactory for this user
    # Assuming UserFactory creates a user profile and associated org
    try:
        # This assumes the UserFactory setup ensures a single, clear org association
        # If UserFactory creates multiple orgs or memberships, this needs adjustment
        org = user.profile.memberships.first().organization # Get org via membership
    except AttributeError: # Fallback if structure is different or no membership/profile
        # If the above fails, perhaps the OrganizationFactory is implicitly linked?
        # This is less robust and depends heavily on factory side effects.
        # We might need a more reliable way to get the user's default org.
        # For now, let's query Organizations created *by* this user if Auditable is used.
        # This requires Organization to inherit Auditable.
        if hasattr(Organization, 'created_by'):
             org = Organization.objects.filter(created_by=user).first()
        else:
             # Last resort: Create a separate org? Or fail if context unknown?
             # Let's create one for the test if we can't find the implicit one.
             # This might not be ideal, indicates potential factory/setup issue.
             org = organization_factory() # Create a separate org if needed

    if not org: # If still no org found, create one explicitly
         org = organization_factory()

    action = AuditActionType.LOGIN_SUCCESS
    custom_context = {"session_key": "abc"}

    # --- Debugging: Verify mock is active --- #
    assert crum.get_current_request() is mock_current_request # Check fixture
    assert hasattr(crum.get_current_request(), 'META') # Check META exists
    assert crum.get_current_request().META.get('REMOTE_ADDR') == '192.0.2.1' # Check IP
    # --- End Debugging --- #

    # Clear mock calls potentially made by factories BEFORE the call under test
    mock_audit_log_create.reset_mock()

    utils.log_audit_event(
        user=user, organization=org, action_type=action,
        context=custom_context
    )

    # Assert that the specific call we expect was made exactly once
    expected_call_args = call(
        user=user,
        organization=org,
        action_type=action,
        content_type=None,
        object_id=None,
        object_repr='',
        changes=None,
        context={'ip_address': '192.0.2.1', 'session_key': 'abc'}
    )
    # Check if this specific call exists in the list of calls
    assert expected_call_args in mock_audit_log_create.call_args_list

@pytest.mark.django_db
def test_log_audit_event_with_object(mock_audit_log_create, mock_current_request, user_factory, organization_factory):
    """Test logging an event related to a specific model instance (e.g., UPDATE)."""
    user = user_factory()
    
    # Factory creation will likely trigger the mock via signals
    org_obj = organization_factory(name="Linked Org") 
        
    org_ctype = ContentType.objects.get_for_model(org_obj)
    action = AuditActionType.UPDATE
    changes = {"name": {"old": "Old", "new": "Linked Org"}}

    # --- Debugging: Verify mock is active --- #
    assert crum.get_current_request() is mock_current_request # Check fixture
    # --- End Debugging --- #

    # Clear mock calls potentially made by factories BEFORE the call under test
    mock_audit_log_create.reset_mock()

    utils.log_audit_event(
        user=user, 
        organization=org_obj,
        action_type=action,
        content_object=org_obj,
        changes=changes
    )

    # Assert the specific call exists in the list of calls
    expected_call_args = call(
        user=user,
        organization=org_obj,
        action_type=action,
        content_type=org_ctype,
        object_id=str(org_obj.pk),
        object_repr="Linked Org",
        changes=changes,
        context={'ip_address': '192.0.2.1'}
    )
    assert expected_call_args in mock_audit_log_create.call_args_list

@pytest.mark.django_db
def test_log_audit_event_object_repr_override(mock_audit_log_create, mock_current_request, organization_factory):
    """Test overriding the object representation."""
    # Factory creation will likely trigger the mock
    org_obj = organization_factory()
        
    custom_repr = "My Custom Representation"

    # Clear mock calls potentially made by factories BEFORE the call under test
    mock_audit_log_create.reset_mock()

    utils.log_audit_event(
        user=None, # System action
        organization=org_obj,
        action_type=AuditActionType.DELETE,
        content_object=org_obj,
        object_repr_override=custom_repr
    )

    expected_call_args = call(
        user=None,
        organization=org_obj,
        action_type=AuditActionType.DELETE,
        content_type=ContentType.objects.get_for_model(org_obj),
        object_id=str(org_obj.pk),
        object_repr=custom_repr,
        changes=None,
        context={'ip_address': '192.0.2.1'}
    )
    assert expected_call_args in mock_audit_log_create.call_args_list

@pytest.mark.django_db
def test_log_audit_event_no_request_context(mock_audit_log_create, mocker, user_factory, organization_factory):
    """Test logging when crum doesn't find a request."""
    # Ensure crum thread local is clear for this test
    if crum.get_current_request():
        crum.set_current_request(None) # Use set(None) for cleanup

    # Mock the function called by get_request_context to return None
    mocker.patch('core.audit.utils.get_current_request', return_value=None)
    user = user_factory()

    # Get organization associated with user (similar logic to test_log_audit_event_no_object)
    try:
        org = user.profile.memberships.first().organization
    except AttributeError:
         if hasattr(Organization, 'created_by'):
             org = Organization.objects.filter(created_by=user).first()
         else:
             org = organization_factory() # Create separate org if needed
    if not org:
         org = organization_factory()

    # Clear mock calls potentially made by factories BEFORE the call under test
    mock_audit_log_create.reset_mock()

    utils.log_audit_event(
        user=user,
        organization=org,
        action_type=AuditActionType.LOGOUT
    )

    expected_call_args = call(
        user=user,
        organization=org,
        action_type=AuditActionType.LOGOUT,
        content_type=None,
        object_id=None,
        object_repr='',
        changes=None,
        context=None # Expect no context here
    )
    assert expected_call_args in mock_audit_log_create.call_args_list

@pytest.mark.django_db
def test_log_audit_event_creation_error(mock_audit_log_create, mock_current_request, user_factory, organization_factory):
    """Test that an error during AuditLog creation is logged but doesn't raise."""
    mock_audit_log_create.side_effect = Exception("DB Error!")
    user = user_factory()
    
    # Initialize org to None before trying to find it
    org = None 
    try:
        org = user.profile.memberships.first().organization
    except AttributeError:
        if hasattr(Organization, 'created_by'):
             org = Organization.objects.filter(created_by=user).first()
        # If the above didn't find an org, we still need one for the test
        # The explicit factory call below will handle it if org remains None

    # If no org was found via profile/creator, create one explicitly
    if not org:
         org = organization_factory()

    # Clear mock calls potentially made by factories BEFORE the call under test
    mock_audit_log_create.reset_mock()

    # Call the function and assert it does NOT raise the exception
    try:
        utils.log_audit_event(
            user=user,
            organization=org,
            action_type=AuditActionType.LOGIN_FAILED
        )
    except Exception as e:
        pytest.fail(f"log_audit_event should not have raised an exception, but raised {e}")

    # Verify that the mocked create method WAS called exactly once (before raising the exception)
    mock_audit_log_create.assert_called_once()
