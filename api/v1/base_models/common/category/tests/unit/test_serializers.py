# api/v1/base_models/common/category/tests/unit/test_serializers.py
import pytest
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model

# Use factories to create data
from ..factories import CategoryFactory
# Corrected model and choices imports to be absolute
from api.v1.base_models.common.category.models import Category
from api.v1.base_models.common.category.choices import CategoryType

# Import the serializer
from api.v1.base_models.common.category.serializers import CategorySerializer

User = get_user_model()
pytestmark = pytest.mark.django_db

@pytest.fixture
def user(db):
    """Fixture for creating a user."""
    return User.objects.create_user(username='serializer_test_user', password='password')

@pytest.fixture
def serializer_context(user):
    """Provides context for the serializer, including the request user."""
    # Mock request object needed for AuditableModelSerializerMixin (if used)
    # or if serializer needs access to request.
    # For now, just include user if needed by Auditable fields set manually.
    return {'request': None} # Add mock request if needed

class TestCategorySerializer:

    def test_serialization_output_fields(self, serializer_context):
        """Verify serialized output contains expected fields."""
        category = CategoryFactory()
        serializer = CategorySerializer(category, context=serializer_context)
        data = serializer.data

        expected_fields = [
            'id', 'name', 'slug', 'description', 'parent_slug',
            'category_type', 'is_active', 'custom_fields',
            'lft', 'rght', 'tree_id', 'level',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        for field in expected_fields:
            assert field in data

        assert data['name'] == category.name
        assert data['slug'] == category.slug
        assert data['parent_slug'] is None # Root node
        assert data['created_by'] == category.created_by.id
        assert data['updated_by'] == category.updated_by.id

    def test_serialization_parent_slug(self, serializer_context):
        """Verify parent_slug is correctly serialized."""
        parent = CategoryFactory()
        child = CategoryFactory(parent=parent)
        serializer = CategorySerializer(child, context=serializer_context)
        assert serializer.data['parent_slug'] == parent.slug

    def test_deserialization_create_minimal(self, user, serializer_context):
        """Test creating a category with minimal valid data."""
        data = {
            'name': 'New Root Category',
            'category_type': CategoryType.PRODUCT,
            'parent_slug': None, # Explicitly pass None to satisfy validator
        }
        serializer = CategorySerializer(data=data, context=serializer_context)
        assert serializer.is_valid(raise_exception=True)

        # Need to manually set audit fields if not handled by context/view
        instance = serializer.save(created_by=user, updated_by=user)

        assert isinstance(instance, Category)
        assert instance.name == data['name']
        assert instance.category_type == CategoryType.PRODUCT
        assert instance.slug == 'new-root-category' # Auto-generated
        assert instance.parent is None
        assert instance.created_by == user
        assert instance.updated_by == user

    def test_deserialization_create_with_parent_slug(self, user, serializer_context):
        """Test creating a child category specifying parent by slug."""
        parent = CategoryFactory(slug='parent-cat')
        data = {
            'name': 'New Child Category',
            'category_type': parent.category_type,
            'parent_slug': parent.slug # Reference parent by its slug
        }
        serializer = CategorySerializer(data=data, context=serializer_context)
        assert serializer.is_valid(raise_exception=True)
        instance = serializer.save(created_by=user, updated_by=user)

        assert instance.parent == parent
        assert instance.name == data['name']

    def test_deserialization_update(self, user, serializer_context):
        """Test updating non-parent fields of an existing category."""
        category = CategoryFactory(name="Original Name", description="Old desc", parent=None)

        # Data for non-parent updates
        data = {
            'name': 'Updated Name',
            'description': 'New desc',
            'is_active': False,
            'custom_fields': {'new': 'data'}
        }
        serializer = CategorySerializer(category, data=data, partial=True, context=serializer_context)
        assert serializer.is_valid(raise_exception=True)

        # Save changes
        instance = serializer.save(updated_by=user)
        instance.refresh_from_db()

        # Assert non-parent fields are updated
        assert instance.name == data['name']
        assert instance.description == data['description']
        assert instance.is_active == data['is_active']
        assert instance.custom_fields == data['custom_fields']
        assert instance.updated_by == user
        assert instance.updated_at > instance.created_at
        assert instance.parent is None # Verify parent didn't change

    def test_read_only_fields_ignored(self, user, serializer_context):
        """Verify read-only fields are ignored during deserialization."""
        category = CategoryFactory()
        original_created_at = category.created_at
        original_id = category.id
        data = {
            'name': 'Trying to Change ReadOnly',
            'category_type': category.category_type,
            'id': 9999, # Should be ignored
            'lft': 100, # Should be ignored
            'created_at': '2000-01-01T00:00:00Z', # Should be ignored
            'created_by': None # Should be ignored
        }
        serializer = CategorySerializer(category, data=data, partial=True, context=serializer_context)
        assert serializer.is_valid(raise_exception=True)
        instance = serializer.save(updated_by=user)

        assert instance.id == original_id
        assert instance.created_at == original_created_at
        assert instance.lft != 100 # MPTT handles this
        assert instance.created_by is not None

    def test_validation_required_fields_on_create(self, serializer_context):
        """Test required fields ('name', 'category_type') fail validation if missing."""
        data = {}
        serializer = CategorySerializer(data=data, context=serializer_context)
        with pytest.raises(ValidationError) as excinfo:
            serializer.is_valid(raise_exception=True)
        assert 'name' in excinfo.value.detail
        assert 'category_type' in excinfo.value.detail

    def test_validation_parent_slug_does_not_exist(self, serializer_context):
        """Test validation fails if provided parent_slug does not exist."""
        data = {
            'name': 'Category With Bad Parent',
            'category_type': CategoryType.PRODUCT,
            'parent_slug': 'non-existent-slug'
        }
        serializer = CategorySerializer(data=data, context=serializer_context)
        with pytest.raises(ValidationError) as excinfo:
            serializer.is_valid(raise_exception=True)
        # SlugRelatedField raises error on the field itself
        assert 'parent_slug' in excinfo.value.detail
        assert 'does not exist' in str(excinfo.value.detail['parent_slug'][0])

    def test_validation_custom_fields_not_dict(self, serializer_context):
        """Test custom_fields validation fails if not a dict."""
        data = {
            'name': 'Bad Custom Fields',
            'category_type': CategoryType.OTHER,
            'custom_fields': [1, 2, 3] # Send a list instead of dict
        }
        serializer = CategorySerializer(data=data, context=serializer_context)
        with pytest.raises(ValidationError) as excinfo:
            serializer.is_valid(raise_exception=True)
        assert 'custom_fields' in excinfo.value.detail
        assert 'valid JSON object' in str(excinfo.value.detail['custom_fields'][0])

    # Note: unique_together validation is typically handled by the model's save method
    # and raises an IntegrityError. DRF serializers usually report this back
    # as a non_field_error or attach it to relevant fields after the DB error.
    # Testing this interaction might be better suited for integration/API tests.
    # def test_validation_unique_together(self, user, serializer_context):
    #     """Verify serializer reports unique_together violation (requires DB save)."""
    #     parent = CategoryFactory()
    #     CategoryFactory(name="Unique Child", parent=parent, category_type=parent.category_type)
    #     data = {
    #         'name': 'Unique Child',
    #         'category_type': parent.category_type,
    #         'parent_slug': parent.slug
    #     }
    #     serializer = CategorySerializer(data=data, context=serializer_context)
    #     assert serializer.is_valid(raise_exception=True)
    #     with pytest.raises(IntegrityError): # Or handle potential ValidationError wrapper
    #         serializer.save(created_by=user, updated_by=user)

    # Example test if parent type validation was added:
    # def test_validation_parent_type_mismatch(self, user, serializer_context):
    #     """Test validation fails if parent has different category_type."""
    #     parent = CategoryFactory(category_type=CategoryType.PRODUCT)
    #     data = {
    #         'name': 'Mismatched Child',
    #         'category_type': CategoryType.DOCUMENT_TYPE, # Different type
    #         'parent_slug': parent.slug
    #     }
    #     serializer = CategorySerializer(data=data, context=serializer_context)
    #     with pytest.raises(ValidationError) as excinfo:
    #         serializer.is_valid(raise_exception=True)
    #     assert 'parent' in excinfo.value.detail or 'non_field_errors' in excinfo.value.detail 