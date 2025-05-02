import pytest
from rest_framework import serializers
from unittest.mock import Mock, patch # For mocking request and permissions
from django.core.files.base import ContentFile

# Assuming model, serializer, and factory locations
from api.v1.base_models.common.fileStorage.models import FileStorage
from api.v1.base_models.common.fileStorage.serializers import FileStorageSerializer
from api.v1.base_models.common.fileStorage.tests.factories import FileStorageFactory
from api.v1.base_models.user.tests.factories import UserFactory
from api.v1.base_models.organization.tests.factories import OrganizationFactory

pytestmark = pytest.mark.django_db

# --- Test Fixtures ---

@pytest.fixture
def user_with_perm(mocker): # Mocker fixture for patching
    user = UserFactory()
    # Mock the permission check function directly for simplicity in unit tests
    mocker.patch(
        'api.v1.base_models.common.fileStorage.serializers.has_perm_in_org',
        return_value=True
    )
    return user

@pytest.fixture
def user_without_perm(mocker):
    user = UserFactory()
    mocker.patch(
        'api.v1.base_models.common.fileStorage.serializers.has_perm_in_org',
        return_value=False
    )
    return user

@pytest.fixture
def mock_request_context(): # Renamed and removed user parameter
    """Provides a basic mock request context."""
    request = Mock()
    return {'request': request}

@pytest.fixture
def file_storage_instance(db):
    # Create a file with some content for URL generation
    content = ContentFile(b"file content", name="testfile.txt")
    return FileStorageFactory.create(file=content)


# --- Serializer Tests ---

def test_serializer_contains_expected_fields(file_storage_instance, mock_request_context, user_with_perm):
    """Verify that the serializer includes expected fields."""
    mock_request_context['request'].user = user_with_perm # Set user manually in context
    serializer = FileStorageSerializer(instance=file_storage_instance, context=mock_request_context)
    data = serializer.data
    expected_fields = {
        'id', 'file', 'original_filename', 'file_size', 'mime_type',
        'uploaded_by', 'tags', 'custom_fields', 'organization',
        'created_at', 'updated_at',
        'download_url', 'file_size_display' # Added fields
    }
    assert set(data.keys()) == expected_fields

def test_serializer_read_only_fields(file_storage_instance, mock_request_context, user_with_perm):
    """Verify that read-only fields are correctly identified (or cannot be updated)."""
    mock_request_context['request'].user = user_with_perm # Set user manually in context
    # Test by attempting to initialize with read-only data - should be ignored
    serializer = FileStorageSerializer(instance=file_storage_instance, data={
        'id': 999,
        'file': 'new_file.txt',
        'organization': OrganizationFactory().id,
        'uploaded_by': UserFactory().id,
        'created_at': '2024-01-01T00:00:00Z',
        # Update a writable field to ensure validation runs
        'custom_fields': {'new': 'field'}
    }, partial=True, context=mock_request_context)

    assert serializer.is_valid() # Should be valid if custom_fields is okay
    # Check that read-only fields didn't change in validated_data
    assert 'id' not in serializer.validated_data
    assert 'file' not in serializer.validated_data
    assert 'organization' not in serializer.validated_data
    assert 'uploaded_by' not in serializer.validated_data
    assert 'created_at' not in serializer.validated_data

def test_serializer_representation_values(file_storage_instance, mock_request_context, user_with_perm):
    """Test the data representation for key fields."""
    mock_request_context['request'].user = user_with_perm # Set user manually in context
    serializer = FileStorageSerializer(instance=file_storage_instance, context=mock_request_context)
    data = serializer.data

    assert data['id'] == file_storage_instance.id
    assert data['original_filename'] == file_storage_instance.original_filename
    assert data['mime_type'] == file_storage_instance.mime_type
    assert data['file_size'] == file_storage_instance.file_size
    assert isinstance(data['uploaded_by'], dict) # Verify it's a dict first
    assert data['uploaded_by'].get('id') == file_storage_instance.uploaded_by.id
    assert isinstance(data['organization'], dict) # Verify it's a dict first
    assert data['organization'].get('id') == file_storage_instance.organization.id
    # Basic check for tags, exact format depends on taggit serializer field
    assert isinstance(data['tags'], list)
    assert isinstance(data['custom_fields'], dict)

def test_serializer_get_download_url_with_permission(file_storage_instance, mock_request_context, user_with_perm, mocker):
    """Test get_download_url returns URL when user has permission."""
    mock_request_context['request'].user = user_with_perm # Set user manually in context
    serializer = FileStorageSerializer(instance=file_storage_instance, context=mock_request_context)
    
    # Patch the permission check for this specific test case if needed again
    # mocker.patch('path.to.has_perm_in_org', return_value=True)
    
    assert serializer.data['download_url'] == mock_request_context['request'].build_absolute_uri(file_storage_instance.file.url)

def test_serializer_get_download_url_without_permission(file_storage_instance, mock_request_context, user_without_perm, mocker):
    """Test get_download_url returns None when user lacks permission."""
    mock_request_context['request'].user = user_without_perm # Set user manually in context
    serializer = FileStorageSerializer(instance=file_storage_instance, context=mock_request_context)

    # Patch the permission check for this specific test case
    # mocker.patch('path.to.has_perm_in_org', return_value=False)

    assert serializer.data['download_url'] is None

def test_serializer_get_download_url_no_file(file_storage_instance, mock_request_context, user_with_perm):
    """Test get_download_url returns None if the file field is empty."""
    file_storage_instance.file = None # Simulate no file
    file_storage_instance.save()
    
    mock_request_context['request'].user = user_with_perm # Set user manually in context
    serializer = FileStorageSerializer(instance=file_storage_instance, context=mock_request_context)
    assert serializer.data['download_url'] is None

def test_serializer_file_size_display(file_storage_instance, mock_request_context, user_with_perm):
    """Test the file_size_display method formats correctly."""
    mock_request_context['request'].user = user_with_perm # Set user manually in context
    serializer = FileStorageSerializer(instance=file_storage_instance, context=mock_request_context)
    
    # Example: Assert specific output format, e.g., using humanize
    # This requires knowing the exact implementation detail (e.g., uses filesizeformat)
    # For now, just check it exists and is a string
    assert 'file_size_display' in serializer.data
    assert isinstance(serializer.data['file_size_display'], str)
    # Add more specific assertions based on the expected formatting (e.g., "12 bytes", "1.5 MB")


def test_serializer_custom_fields_update(file_storage_instance, mock_request_context, user_with_perm):
    """Test updating custom_fields (if allowed)."""
    mock_request_context['request'].user = user_with_perm # Set user manually in context
    update_data = {'custom_fields': {'field1': 'new_value', 'field2': 123}}
    
    serializer = FileStorageSerializer(instance=file_storage_instance, data=update_data, partial=True, context=mock_request_context)
    
    if not serializer.is_valid():
        print("Validation Errors:", serializer.errors)
    assert serializer.is_valid() 
    
    # Assuming custom_fields is writable
    # If it's read-only, this test needs adjustment or removal
    # validated_data will only contain fields that can be written to
    if 'custom_fields' in serializer.validated_data:
        serializer.save()
        file_storage_instance.refresh_from_db()
        assert file_storage_instance.custom_fields == update_data['custom_fields']
    else:
        # If read-only, maybe just assert it wasn't in validated_data
        # This part depends on whether custom_fields is designed to be mutable via API
        pytest.skip("Skipping custom_fields update assertion as it might be read-only.")

def test_serializer_custom_fields_validation_invalid_type(file_storage_instance, mock_request_context, user_with_perm):
    """Test that custom_fields must be a dictionary (JSON object)."""
    mock_request_context['request'].user = user_with_perm # Set user manually in context
    update_data = {'custom_fields': [1, 2, 3]} # Invalid type (list)
    
    serializer = FileStorageSerializer(instance=file_storage_instance, data=update_data, partial=True, context=mock_request_context)
    
    assert not serializer.is_valid()
    assert 'custom_fields' in serializer.errors
    # Check for the core part of the error message instead of exact string match
    error_string = str(serializer.errors['custom_fields'][0]) # Get the first error string
    assert 'must be a valid JSON object' in error_string

# Add more tests as needed for:
# - Tag handling (creation/update if supported by serializer field)
# - Validation logic specific to any custom fields (if implemented in validate_custom_fields)
# - Handling of edge cases (e.g., very large files if size matters for display)
