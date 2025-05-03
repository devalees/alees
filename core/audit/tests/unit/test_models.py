import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

# Need to import Organization model - assuming path from docs
from api.v1.base_models.organization.models import Organization

# Import the future AuditLog model and choices
# These imports will fail initially, which is expected in TDD
from core.audit.models import AuditLog
from core.audit.choices import AuditActionType

User = get_user_model()

@pytest.mark.django_db
def test_auditlog_creation_minimal(user_factory, organization_factory):
    """Test creating an AuditLog with minimal required fields."""
    user = user_factory()
    org = organization_factory()
    log = AuditLog.objects.create(
        user=user,
        organization=org,
        action_type=AuditActionType.LOGIN_SUCCESS,
        object_repr="User Login"
    )
    assert log.pk is not None
    assert log.user == user
    assert log.organization == org
    assert log.action_type == AuditActionType.LOGIN_SUCCESS
    assert log.content_type is None
    assert log.object_id is None
    assert log.object_repr == "User Login"
    assert log.changes is None
    assert log.context is None
    assert log.created_at is not None # From Timestamped

@pytest.mark.django_db
def test_auditlog_creation_with_generic_relation(user_factory, organization_factory):
    """Test creating an AuditLog linked to another model instance."""
    user = user_factory()
    org = organization_factory() # Create an org instance to link
    org_ctype = ContentType.objects.get_for_model(org)

    log = AuditLog.objects.create(
        user=user,
        organization=org, # Assume action happens within user's org context
        action_type=AuditActionType.UPDATE,
        content_type=org_ctype,
        object_id=str(org.pk), # Must be string
        object_repr=f"Organization {org.name}",
        changes={"name": {"old": "Old Name", "new": org.name}},
        context={"ip_address": "192.168.1.1"}
    )
    assert log.pk is not None
    assert log.content_type == org_ctype
    assert log.object_id == str(org.pk)
    assert log.content_object == org # Check GFK resolution
    assert log.object_repr == f"Organization {org.name}"
    assert log.changes == {"name": {"old": "Old Name", "new": org.name}}
    assert log.context == {"ip_address": "192.168.1.1"}
    assert log.created_at is not None

@pytest.mark.django_db
def test_auditlog_nullable_fields(organization_factory):
    """Test creating an AuditLog with nullable user and organization."""
    org = organization_factory() # Org context might still exist
    org_ctype = ContentType.objects.get_for_model(org)
    log = AuditLog.objects.create(
        user=None, # System action
        organization=org, # Action occurred within this org
        action_type=AuditActionType.DELETE,
        content_type=org_ctype,
        object_id=str(org.pk),
        object_repr=f"Deleted Org {org.pk}" # repr might be custom on delete
    )
    assert log.pk is not None
    assert log.user is None
    assert log.organization == org
    assert log.action_type == AuditActionType.DELETE

@pytest.mark.django_db
def test_auditlog_str_representation(user_factory, organization_factory):
    """Test the __str__ method of the AuditLog model."""
    user = user_factory(username="testuser")
    org = organization_factory(name="Test Org")
    org_ctype = ContentType.objects.get_for_model(org)

    # Log with user and object
    log1 = AuditLog.objects.create(
        user=user, organization=org, action_type=AuditActionType.CREATE,
        content_type=org_ctype, object_id=str(org.pk), object_repr=str(org)
    )
    assert str(log1) == f"Create on {str(org)} by {user}"

    # Log with system user (user=None)
    log2 = AuditLog.objects.create(
        user=None, organization=org, action_type=AuditActionType.SYSTEM_EVENT, # Use the new type
        object_repr="System Maintenance"
    )
    # Need to add SYSTEM_EVENT to choices for this test or use another type
    # For now, let's use LOGIN_FAILED as an example of system context
    # log2.action_type = AuditActionType.LOGIN_FAILED # Removed workaround
    # log2.save() # Removed workaround
    assert str(log2) == f"System Event on System Maintenance by System"

    # Log without object_repr, uses object_id
    log3 = AuditLog.objects.create(
        user=user, organization=org, action_type=AuditActionType.DELETE,
        content_type=org_ctype, object_id=str(org.pk) # No object_repr
    )
    assert str(log3) == f"Delete on {str(org.pk)} by {user}"

    # Log without user or object repr/id
    log4 = AuditLog.objects.create(
        user=None, organization=org, action_type=AuditActionType.LOGOUT # User logged out, no specific object
    )
    assert str(log4) == f"Logout on System by System"


@pytest.mark.django_db
def test_auditlog_ordering():
    """Test that logs are ordered by created_at descending by default."""
    # Create logs with slight time differences (requires freezegun or manual time setting)
    # This is harder without factories yet, skipping detailed implementation for now
    # Basic check: QuerySet ordering matches Meta
    assert AuditLog.objects.all().ordered # Checks if QuerySet is ordered
    assert AuditLog._meta.ordering == ['-created_at']

@pytest.mark.django_db
def test_auditlog_json_field_storage():
    """Verify JSON fields store and retrieve dicts correctly."""
    changes_data = {"field_a": {"old": 1, "new": 2}}
    context_data = {"ip": "1.1.1.1", "session": "xyz"}
    log = AuditLog.objects.create(
        action_type=AuditActionType.UPDATE,
        changes=changes_data,
        context=context_data
    )
    retrieved_log = AuditLog.objects.get(pk=log.pk)
    assert retrieved_log.changes == changes_data
    assert retrieved_log.context == context_data

@pytest.mark.django_db
def test_auditlog_blank_json_fields():
    """Verify JSON fields can be blank/null."""
    log = AuditLog.objects.create(
        action_type=AuditActionType.CREATE,
        changes=None, # Explicitly None
        context={}    # Empty dict
    )
    retrieved_log = AuditLog.objects.get(pk=log.pk)
    assert retrieved_log.changes is None
    assert retrieved_log.context == {} # Stored as empty dict

    log2 = AuditLog.objects.create(action_type=AuditActionType.CREATE) # Defaults
    retrieved_log2 = AuditLog.objects.get(pk=log2.pk)
    assert retrieved_log2.changes is None # Default should be None
    assert retrieved_log2.context is None # Default should be None 