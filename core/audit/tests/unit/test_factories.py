import pytest
from django.contrib.contenttypes.models import ContentType

from core.audit.models import AuditLog
from core.audit.choices import AuditActionType
from ..factories import AuditLogFactory

# We also need the factories for User and Organization for these tests
from api.v1.base_models.user.tests.factories import UserFactory
from api.v1.base_models.organization.tests.factories import OrganizationFactory

@pytest.mark.django_db
def test_auditlog_factory_basic_creation():
    """Test creating a basic AuditLog instance using the factory."""
    log = AuditLogFactory()
    assert log.pk is not None
    assert log.user is not None
    assert log.organization is not None
    assert log.action_type in [choice[0] for choice in AuditActionType.CHOICES]
    assert log.created_at is not None
    # Default GFK fields should be None if content_object isn't set
    assert log.content_type is None
    assert log.object_id is None
    assert log.content_object is None
    assert log.changes is None
    assert log.context is None

@pytest.mark.django_db
def test_auditlog_factory_with_content_object(organization_factory):
    """Test creating an AuditLog linked to a specific object via post-generation."""
    linked_org = organization_factory() # Create an object to link to
    org_ctype = ContentType.objects.get_for_model(linked_org)

    log = AuditLogFactory(set_content_object=linked_org)

    assert log.pk is not None
    assert log.content_type == org_ctype
    assert log.object_id == str(linked_org.pk)
    assert log.content_object == linked_org
    # Verify object_repr was set automatically if not provided
    assert log.object_repr == str(linked_org)[:255]

@pytest.mark.django_db
def test_auditlog_factory_with_explicit_fields(user_factory, organization_factory):
    """Test overriding fields during factory creation."""
    user = user_factory()
    org = organization_factory()
    changes_data = {"status": "updated"}
    context_data = {"ip": "10.0.0.1"}

    log = AuditLogFactory(
        user=user,
        organization=org,
        action_type=AuditActionType.UPDATE,
        changes=changes_data,
        context=context_data,
        object_repr="Specific Repr"
    )

    assert log.user == user
    assert log.organization == org
    assert log.action_type == AuditActionType.UPDATE
    assert log.changes == changes_data
    assert log.context == context_data
    assert log.object_repr == "Specific Repr"
    # GFK should still be None as no content_object was linked
    assert log.content_type is None
    assert log.object_id is None

@pytest.mark.django_db
def test_auditlog_factory_gfk_override_repr(organization_factory):
    """Test linking an object but also overriding the object_repr."""
    linked_org = organization_factory()
    custom_repr = "My Custom Org Representation"

    log = AuditLogFactory(
        set_content_object=linked_org,
        object_repr=custom_repr
    )

    assert log.content_object == linked_org
    assert log.object_repr == custom_repr # Should use the override

@pytest.mark.django_db
def test_auditlog_factory_no_user_or_org():
    """Test creating a log without a user or organization context."""
    log = AuditLogFactory(user=None, organization=None)
    assert log.user is None
    assert log.organization is None
    assert log.action_type is not None # Still gets an action type 