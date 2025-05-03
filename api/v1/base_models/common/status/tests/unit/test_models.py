# Placeholder for Status model unit tests
import pytest
from django.db import IntegrityError
# Correct relative import for models and factories
from ...models import Status
from ..factories import StatusFactory

pytestmark = pytest.mark.django_db

# Basic tests based on implementation doc steps

def test_status_creation():
    """Test basic Status creation with required fields."""
    initial_count = Status.objects.count()
    status = StatusFactory(slug='test-slug', name='Test Name')
    # Assert count increased and the object exists with correct data
    assert Status.objects.count() == initial_count + 1
    assert status.slug == 'test-slug'
    assert status.name == 'Test Name'
    assert status.description is not None # Factory provides default
    assert status.custom_fields == {}
    assert str(status) == 'Test Name'

def test_status_slug_pk():
    """Test that slug is the primary key."""
    status = StatusFactory()
    assert status.pk == status.slug

def test_status_slug_unique():
    """Test slug unique constraint using direct object creation."""
    # Use direct creation to bypass factory's get_or_create
    Status.objects.create(slug='unique-slug', name='Name For Unique Slug')
    with pytest.raises(IntegrityError):
        Status.objects.create(slug='unique-slug', name='Another Name')

def test_status_name_unique():
    """Test name unique constraint using direct object creation."""
    # Use direct creation to bypass factory's get_or_create
    Status.objects.create(slug='slug-for-unique-name', name='Unique Name')
    with pytest.raises(IntegrityError):
        Status.objects.create(slug='another-slug', name='Unique Name')

def test_status_optional_fields():
    """Test setting optional fields."""
    status = StatusFactory(
        description='A specific description',
        category='Specific Cat',
        color='#123456',
        custom_fields={'key': 'value'}
    )
    assert status.description == 'A specific description'
    assert status.category == 'Specific Cat'
    assert status.color == '#123456'
    assert status.custom_fields == {'key': 'value'}

# Add tests for Timestamped/Auditable fields if mixins are confirmed
# def test_status_timestamps():
#     status = StatusFactory()
#     assert status.created_at is not None
#     assert status.updated_at is not None

# def test_status_audit_fields():
#     # Requires mocking user or passing created_by/updated_by
#     pass 