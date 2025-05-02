import pytest
from django.core.files.base import ContentFile

# Adjust import based on actual location
from ..factories import FileStorageFactory
from ...models import FileStorage # Import the model to check instance type
from api.v1.base_models.organization.models import Organization
# Import factories needed for custom values test
from api.v1.base_models.organization.tests.factories import OrganizationFactory
from api.v1.base_models.user.tests.factories import UserFactory
from django.contrib.auth import get_user_model

User = get_user_model()

pytestmark = pytest.mark.django_db

def test_filestorage_factory_creation():
    """Test that FileStorageFactory creates a FileStorage instance."""
    instance = FileStorageFactory.create()
    assert isinstance(instance, FileStorage)
    assert instance.pk is not None
    assert instance.file is not None
    assert instance.file.name is not None # Check that a file path was generated
    assert instance.organization is not None
    assert isinstance(instance.organization, Organization)
    assert instance.uploaded_by is not None
    assert isinstance(instance.uploaded_by, User)
    assert instance.created_by == instance.uploaded_by
    assert instance.updated_by == instance.uploaded_by
    assert instance.original_filename is not None
    assert instance.mime_type is not None
    assert isinstance(instance.custom_fields, dict)
    # Check default tags were applied (assuming the post_generation logic)
    assert instance.tags.exists()
    tag_names = [tag.name for tag in instance.tags.all()]
    assert 'factory_generated' in tag_names
    assert instance.mime_type.split('/')[0] in tag_names

def test_filestorage_factory_build():
    """Test that FileStorageFactory can build (not save) an instance."""
    instance = FileStorageFactory.build()
    assert isinstance(instance, FileStorage)
    assert instance.pk is None # Not saved
    assert instance.file is not None # File object exists but not saved to storage
    assert instance.organization is not None
    assert instance.uploaded_by is not None

def test_filestorage_factory_custom_values():
    """Test overriding values during factory creation."""
    custom_org = OrganizationFactory.create(name="Custom Org for File Test")
    custom_uploader = UserFactory.create(organization=custom_org, email="uploader@custom.org")
    custom_filename = "specific_report.docx"
    custom_tags = ['report', 'urgent']

    instance = FileStorageFactory.create(
        organization=custom_org,
        uploaded_by=custom_uploader,
        original_filename=custom_filename,
        tags=custom_tags
    )

    assert instance.organization == custom_org
    assert instance.uploaded_by == custom_uploader
    assert instance.original_filename == custom_filename
    tag_names = [tag.name for tag in instance.tags.all()]
    assert set(tag_names) == set(custom_tags)

def test_filestorage_factory_file_content():
    """Test creating a file with specific content."""
    content = b"Specific file content for testing."
    filename = "content_test.bin"
    instance = FileStorageFactory.create(
        file=ContentFile(content, name=filename)
    )
    # Read back the content to verify
    instance.file.open('rb')
    read_content = instance.file.read()
    instance.file.close()
    assert read_content == content
    # Check if original_filename was also set if not provided explicitly
    # The factory currently sets it independently, which is fine.
    assert instance.original_filename != filename # Default factory behavior 