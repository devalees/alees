import pytest
import os
from django.db import models
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from taggit.managers import TaggableManager

# Assuming model location and mixins
# Adjust imports if model structure changes
from core.models import Timestamped, Auditable, OrganizationScoped
# We'll import FileStorage after it's defined and use a fixture
# from api.v1.base_models.common.fileStorage.models import FileStorage
# Import factories needed for testing relationships/properties
from api.v1.base_models.organization.tests.factories import OrganizationFactory
from api.v1.base_models.user.tests.factories import UserFactory


pytestmark = pytest.mark.django_db

User = get_user_model()

# --- Placeholder Model ---
# This allows writing tests before the actual model exists.
# The `real_filestorage_model` fixture will replace this with the actual model later.
class PlaceholderFileStorage:
    # Minimal attributes to allow basic tests to run
    _meta = type('Meta', (object,), {'get_field': lambda self, name: None})() # Mock _meta

# Use a variable that the fixture can overwrite
ModelUnderTest = PlaceholderFileStorage
FactoryUnderTest = None # Will be set by fixture later if factory exists

# --- Fixtures ---

@pytest.fixture(scope='function', autouse=True)
def real_filestorage_model(django_db_setup, django_db_blocker):
    """Fixture to replace the placeholder model with the real one once defined."""
    global ModelUnderTest, FactoryUnderTest
    try:
        from api.v1.base_models.common.fileStorage.models import FileStorage as RealModel
        ModelUnderTest = RealModel
        try:
            # Also try to load the factory if it exists
            from api.v1.base_models.common.fileStorage.tests.factories import FileStorageFactory as RealFactory
            FactoryUnderTest = RealFactory
        except ImportError:
            FactoryUnderTest = None # Factory not defined yet
        yield # Let tests run with the real model/factory
    except ImportError:
        # If import fails (model not defined yet), keep the placeholder
        ModelUnderTest = PlaceholderFileStorage
        FactoryUnderTest = None
        yield # Let tests run with the placeholder
    finally:
        # Reset after test if necessary (though typically not needed with function scope)
        ModelUnderTest = PlaceholderFileStorage
        FactoryUnderTest = None


# --- Model Tests ---

def test_filestorage_inheritance():
    """Verify FileStorage inherits required mixins."""
    if ModelUnderTest is PlaceholderFileStorage:
        pytest.skip("Skipping inheritance check until model is defined.")
    assert issubclass(ModelUnderTest, Timestamped)
    assert issubclass(ModelUnderTest, Auditable)
    assert issubclass(ModelUnderTest, OrganizationScoped)


def test_filestorage_fields_exist():
    """Verify required fields are present on the model."""
    if ModelUnderTest is PlaceholderFileStorage:
        pytest.skip("Skipping field existence check until model is defined.")

    expected_fields = [
        'file', 'original_filename', 'file_size', 'mime_type',
        'uploaded_by', 'tags', 'custom_fields',
        'organization', # From OrganizationScoped
        'created_at', 'updated_at', # From Timestamped
        'created_by', 'updated_by' # From Auditable
    ]
    actual_fields = [field.name for field in ModelUnderTest._meta.get_fields()]

    for field_name in expected_fields:
        assert field_name in actual_fields, f"Field '{field_name}' not found on {ModelUnderTest.__name__}"


def test_filestorage_field_types():
    """Verify the field types of the FileStorage model."""
    if ModelUnderTest is PlaceholderFileStorage:
        pytest.skip("Skipping field type check until model is defined.")

    meta = ModelUnderTest._meta
    assert isinstance(meta.get_field('file'), models.FileField)
    assert isinstance(meta.get_field('original_filename'), models.CharField)
    assert isinstance(meta.get_field('file_size'), models.PositiveBigIntegerField)
    assert isinstance(meta.get_field('mime_type'), models.CharField)
    assert isinstance(meta.get_field('uploaded_by'), models.ForeignKey)
    assert meta.get_field('uploaded_by').remote_field.model == User
    assert isinstance(meta.get_field('tags'), TaggableManager)
    assert isinstance(meta.get_field('custom_fields'), models.JSONField)
    # Mixin fields checked implicitly by inheritance test and field existence


def test_filestorage_str_representation():
    """Verify the string representation uses original_filename."""
    if FactoryUnderTest is None:
        pytest.skip("Skipping __str__ test until factory is defined.")

    file_content = b"dummy content"
    # Use create() as __str__ requires a saved instance with relations typically
    instance = FactoryUnderTest.create(
        original_filename="test_document.pdf",
        # Provide minimal file content; factory should handle path generation
        file=ContentFile(file_content, name="irrelevant_factory_name.pdf")
    )
    assert str(instance) == "test_document.pdf"


def test_filestorage_filename_property():
    """Verify the filename property returns the basename of the stored file."""
    if FactoryUnderTest is None:
        pytest.skip("Skipping filename property test until factory is defined.")

    org = OrganizationFactory.create()
    # Generate a realistic-looking stored path (factory should handle this ideally)
    # Example: org_1/files/some_uuid.txt
    # We need to control the .file.name attribute for this test
    expected_basename = "some_uuid_test_file.txt"
    controlled_path = os.path.join(f"org_{org.id}", "files", expected_basename)

    # Create instance, then manually set the file name attribute for testing
    instance = FactoryUnderTest.create(
        original_filename="upload_name.txt",
        organization=org,
        file=ContentFile(b"dummy", name="upload_name.txt") # Initial content
    )
    # Simulate the file being saved with a specific path by the storage backend
    instance.file.name = controlled_path
    # Save again to ensure the name sticks if needed (though property shouldn't require it)
    # instance.save() # Usually not needed for property read

    assert instance.filename == expected_basename

def test_filestorage_filename_property_no_file():
    """Verify the filename property returns None if file field is empty."""
    if FactoryUnderTest is None:
        pytest.skip("Skipping filename property (no file) test until factory is defined.")

    # Build an instance without saving a file
    instance = FactoryUnderTest.build(file=None)
    assert instance.filename is None


def test_filestorage_get_secure_url_exists():
    """Verify the get_secure_url method exists (placeholder check)."""
    if ModelUnderTest is PlaceholderFileStorage:
        pytest.skip("Skipping get_secure_url check until model is defined.")

    # Build an instance (doesn't need DB usually)
    instance = FactoryUnderTest.build() if FactoryUnderTest else ModelUnderTest()

    assert hasattr(instance, 'get_secure_url')
    assert callable(instance.get_secure_url)
    # We will test the permission logic in serializer/view tests


def test_filestorage_meta_options():
    """Test Meta class options like ordering, app_label, verbose_name."""
    if ModelUnderTest is PlaceholderFileStorage:
        pytest.skip("Skipping Meta options check until model is defined.")

    meta = ModelUnderTest._meta
    assert meta.verbose_name == "File Storage Record"
    assert meta.verbose_name_plural == "File Storage Records"
    assert meta.ordering == ['-created_at']
    # No longer explicitly setting app_label, it defaults correctly
    # assert meta.app_label == 'file_storage' # Check the resolved app label

    # Check if defined indexes exist by name
    index_names = [index.name for index in meta.indexes]
    assert 'file_storage_organiz_idx' in index_names # Use corrected index name
    assert 'file_storage_upl_by_idx' in index_names # Use corrected index name
    assert 'file_storage_mime_idx' in index_names # Use corrected index name
    assert 'file_storage_orig_fname_idx' in index_names # Use corrected index name 