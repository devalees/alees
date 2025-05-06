# Placeholder for Status serializer unit tests
import pytest
# Correct relative import for serializers and factories
from ...serializers import StatusSerializer
from ..factories import StatusFactory, CategoryFactory
from rest_framework.exceptions import ValidationError

pytestmark = pytest.mark.django_db

def test_status_serializer_output():
    """Test the output format of the StatusSerializer."""
    # Create a category first
    category = CategoryFactory(name='Testing Category')
    
    # Create status using the factory
    status = StatusFactory(
        slug='active-test', # Use a unique slug to avoid conflicts
        name='Active Test',
        description='Is active for testing',
        category=category,
        color='#ABCDEF',
        custom_fields={'test_key': 'test_value'}
    )
    serializer = StatusSerializer(status)
    
    # Verify key fields are present in serialized data
    assert serializer.data['slug'] == status.slug
    assert serializer.data['name'] == status.name
    assert serializer.data['description'] == status.description
    assert serializer.data['category'] == category.pk  # Category should be shown as primary key (ID)
    assert serializer.data['category_detail']['slug'] == category.slug  # Category detail nested object
    assert serializer.data['color'] == status.color
    assert serializer.data['custom_fields'] == status.custom_fields

def test_status_serializer_read_only_fields():
    """Test that specific fields are read-only."""
    serializer = StatusSerializer()
    # Check for read-only fields specified in extra_kwargs
    assert 'created_at' in serializer.Meta.extra_kwargs
    assert serializer.Meta.extra_kwargs['created_at']['read_only'] is True
    assert 'updated_at' in serializer.Meta.extra_kwargs
    assert serializer.Meta.extra_kwargs['updated_at']['read_only'] is True
    assert 'created_by' in serializer.Meta.extra_kwargs
    assert serializer.Meta.extra_kwargs['created_by']['read_only'] is True
    assert 'updated_by' in serializer.Meta.extra_kwargs
    assert serializer.Meta.extra_kwargs['updated_by']['read_only'] is True
    assert 'category' in serializer.Meta.extra_kwargs
    assert serializer.Meta.extra_kwargs['category']['read_only'] is True

# Add validation tests if custom validation is added later 