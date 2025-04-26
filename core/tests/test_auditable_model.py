import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from crum import set_current_user
from core.models import TestAuditableModel
from api.v1.base_models.user.tests.factories import UserFactory

User = get_user_model()

@pytest.fixture
def user1():
    return UserFactory()

@pytest.fixture
def user2():
    return UserFactory()

@pytest.mark.django_db
def test_user_set_on_create(user1):
    """Verify created_by and updated_by are set on creation."""
    set_current_user(user1)  # Set user context using crum
    instance = TestAuditableModel.objects.create(name="Test Create")
    set_current_user(None)  # Clear context after operation

    assert instance.created_by == user1
    assert instance.updated_by == user1

@pytest.mark.django_db
def test_updated_by_changes_on_update(user1, user2):
    """Verify updated_by changes on save() but created_by doesn't."""
    set_current_user(user1)
    instance = TestAuditableModel.objects.create(name="Test Update")
    set_current_user(None)  # Clear user1 context

    created_by_user = instance.created_by

    # Simulate update by a different user
    instance.name = "Updated Name"
    set_current_user(user2)
    instance.save()
    set_current_user(None)  # Clear user2 context

    instance.refresh_from_db()

    assert instance.created_by == created_by_user  # Should still be user1
    assert instance.updated_by == user2  # Should now be user2

@pytest.mark.django_db
def test_users_are_null_if_no_user_in_context():
    """Verify fields are null if no user is set."""
    set_current_user(None)  # Explicitly no user
    instance = TestAuditableModel.objects.create(name="Test No User")

    assert instance.created_by is None
    assert instance.updated_by is None

    instance.name = "Update No User"
    instance.save()
    instance.refresh_from_db()

    assert instance.created_by is None  # Still None
    assert instance.updated_by is None  # Still None 