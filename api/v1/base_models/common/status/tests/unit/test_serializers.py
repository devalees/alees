# Placeholder for Status serializer unit tests
import pytest
# Correct relative import for serializers and factories
from ...serializers import StatusSerializer
from ..factories import StatusFactory
from rest_framework.exceptions import ValidationError

pytestmark = pytest.mark.django_db

def test_status_serializer_output():
    """Test the output format of the StatusSerializer."""
    # Create status using the factory
    status = StatusFactory(
        slug='active-test', # Use a unique slug to avoid conflicts
        name='Active Test',
        description='Is active for testing',
        category='Testing',
        color='#ABCDEF',
        custom_fields={'test_key': 'test_value'}
    )
    serializer = StatusSerializer(status)
    # Expected data should match the factory-generated instance
    expected_data = {
        'slug': status.slug,
        'name': status.name,
        'description': status.description,
        'category': status.category,
        'color': status.color,
        'custom_fields': status.custom_fields,
    }
    assert serializer.data == expected_data

def test_status_serializer_read_only():
    """Test that fields are read-only."""
    serializer = StatusSerializer()
    assert set(serializer.Meta.read_only_fields) == set(serializer.Meta.fields)

# Add validation tests if custom validation is added later 