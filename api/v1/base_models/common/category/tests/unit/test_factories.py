import pytest

from ..factories import CategoryFactory
from api.v1.base_models.common.category.models import Category
from api.v1.base_models.common.category.choices import CategoryType

pytestmark = pytest.mark.django_db

class TestCategoryFactory:

    def test_factory_creation_basic(self):
        """Test that the factory creates a valid Category instance."""
        category = CategoryFactory()

        assert category is not None
        assert isinstance(category, Category)
        assert category.pk is not None
        assert category.name.startswith('Category ')
        assert category.slug is not None # Should be auto-generated
        assert category.category_type in [choice[0] for choice in CategoryType.choices]
        assert category.is_active is True
        assert isinstance(category.custom_fields, dict)
        assert category.parent is None
        assert category.created_by is not None
        assert category.updated_by is not None

    def test_factory_creation_with_parent(self):
        """Test creating a category with a parent using the factory."""
        parent_category = CategoryFactory()
        child_category = CategoryFactory(parent=parent_category)

        assert child_category.parent == parent_category
        # Refresh parent from DB to check children relationship
        parent_category.refresh_from_db()
        assert parent_category.children.count() == 1
        assert parent_category.children.first() == child_category
        assert child_category.level == 1
        assert child_category.tree_id == parent_category.tree_id

    def test_factory_creation_specific_type(self):
        """Test creating a category with a specific type."""
        category = CategoryFactory(category_type=CategoryType.ASSET_TYPE)
        assert category.category_type == CategoryType.ASSET_TYPE

    def test_factory_creation_inactive(self):
        """Test creating an inactive category."""
        category = CategoryFactory(is_active=False)
        assert category.is_active is False

    def test_factory_creation_with_custom_fields(self):
        """Test creating a category with custom fields."""
        custom_data = {'key1': 'value1', 'key2': 123}
        category = CategoryFactory(custom_fields=custom_data)
        assert category.custom_fields == custom_data

    def test_factory_batch_creation(self):
        """Test creating a batch of categories."""
        categories = CategoryFactory.create_batch(5)
        assert len(categories) == 5
        assert Category.objects.count() == 5
        # Check slugs are unique due to sequence in name
        slugs = {cat.slug for cat in categories}
        assert len(slugs) == 5 