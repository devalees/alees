import pytest
from django.db import IntegrityError
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

# Corrected imports to be absolute from the app root
from api.v1.base_models.common.category.models import Category
from api.v1.base_models.common.category.choices import CategoryType
from core.models import Timestamped, Auditable # Import base models

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def user(db):
    """Fixture to create a user for Auditable fields."""
    return User.objects.create_user(username='testuser', password='password')


class TestCategoryModel:

    def test_category_creation_minimal(self, user):
        """Verify Category can be created with minimal required fields."""
        category = Category.objects.create(
            name="Test Category",
            category_type=CategoryType.PRODUCT,
            created_by=user, # Required by Auditable
            updated_by=user  # Required by Auditable
        )
        category.refresh_from_db()

        assert category.pk is not None
        assert category.name == "Test Category"
        assert category.category_type == CategoryType.PRODUCT
        assert category.slug == slugify("Test Category")
        assert category.is_active is True
        assert category.custom_fields == {}
        assert category.parent is None
        assert category.description == ""

        # Test Timestamped fields
        assert category.created_at is not None
        assert category.updated_at is not None

        # Test Auditable fields
        assert category.created_by == user
        assert category.updated_by == user

    def test_slug_auto_generation(self, user):
        """Verify slug is auto-generated from name if blank."""
        category = Category.objects.create(
            name="Another Test with Spaces",
            category_type=CategoryType.DOCUMENT_TYPE,
            created_by=user, updated_by=user
        )
        assert category.slug == "another-test-with-spaces"

    def test_slug_provided_is_used(self, user):
        """Verify provided slug is used instead of auto-generating."""
        category = Category.objects.create(
            name="Some Name", slug="my-custom-slug",
            category_type=CategoryType.ASSET_TYPE,
            created_by=user, updated_by=user
        )
        assert category.slug == "my-custom-slug"

    def test_slug_uniqueness(self, user):
        """Verify slug field enforces database uniqueness."""
        Category.objects.create(
            name="Unique Slug", category_type=CategoryType.PRODUCT,
            created_by=user, updated_by=user
        )
        with pytest.raises(IntegrityError):
            # Attempt to create another category with the same auto-generated slug
            Category.objects.create(
                name="Unique Slug", category_type=CategoryType.OTHER,
                created_by=user, updated_by=user
            )

    def test_unique_together_constraint(self, user):
        """Verify (parent, name, category_type) unique_together constraint."""
        # --- Setup distinct categories first ---
        parent = Category.objects.create(
            name="Parent", category_type=CategoryType.PRODUCT,
            created_by=user, updated_by=user
        )
        # Create one child successfully
        Category.objects.create(
            name="Child", parent=parent, category_type=CategoryType.PRODUCT,
            created_by=user, updated_by=user
        )
        # Create another child with the same name but different type (should be OK)
        Category.objects.create(
            name="Child", slug="child-doc", parent=parent, category_type=CategoryType.DOCUMENT_TYPE,
            created_by=user, updated_by=user
        )
        # Create another child with the same name but different parent (should be OK)
        Category.objects.create(
            name="Child", slug="child-root", parent=None, category_type=CategoryType.PRODUCT,
            created_by=user, updated_by=user
        )

        # --- Test the constraint violation ---
        # Now, attempt to create the duplicate that should fail the unique_together constraint
        with pytest.raises(IntegrityError) as excinfo:
            Category.objects.create(
                name="Child", parent=parent, category_type=CategoryType.PRODUCT,
                created_by=user, updated_by=user
            )

        # Optional: Check the specific constraint name if needed and stable
        # assert 'api_v1_category_category_parent_id_name_category__7ad316fe_uniq' in str(excinfo.value)

    def test_parent_assignment(self, user):
        """Verify parent ForeignKey relationship works."""
        parent = Category.objects.create(
            name="Parent Cat", category_type=CategoryType.ASSET_TYPE,
            created_by=user, updated_by=user
        )
        child = Category.objects.create(
            name="Child Cat", parent=parent, category_type=CategoryType.ASSET_TYPE,
            created_by=user, updated_by=user
        )
        assert child.parent == parent
        assert parent.children.count() == 1
        assert parent.children.first() == child

    def test_mptt_fields_populated(self, user):
        """Verify MPTT fields (lft, rght, tree_id, level) are set."""
        root = Category.objects.create(
            name="Root", category_type=CategoryType.ORG_COST_CENTER,
            created_by=user, updated_by=user
        )
        child = Category.objects.create(
            name="Child", parent=root, category_type=CategoryType.ORG_COST_CENTER,
            created_by=user, updated_by=user
        )
        grandchild = Category.objects.create(
            name="Grandchild", parent=child, category_type=CategoryType.ORG_COST_CENTER,
            created_by=user, updated_by=user
        )

        # Reload from DB to ensure MPTT fields are calculated and saved
        root.refresh_from_db()
        child.refresh_from_db()
        grandchild.refresh_from_db()

        assert root.lft is not None and root.rght is not None
        assert root.tree_id is not None and root.level == 0
        assert child.level == 1
        assert grandchild.level == 2

        assert child.lft > root.lft and child.rght < root.rght
        assert grandchild.lft > child.lft and grandchild.rght < child.rght
        assert child.tree_id == root.tree_id == grandchild.tree_id

    def test_str_representation(self, user):
        """Verify the __str__ method returns the name with hierarchy prefix."""
        root = Category.objects.create(
            name="Root Node", category_type=CategoryType.PRODUCT,
            created_by=user, updated_by=user
        )
        child = Category.objects.create(
            name="Level 1 Node", parent=root, category_type=CategoryType.PRODUCT,
            created_by=user, updated_by=user
        )
        grandchild = Category.objects.create(
            name="Level 2 Node", parent=child, category_type=CategoryType.PRODUCT,
            created_by=user, updated_by=user
        )

        # Refresh to get correct level for __str__ calculation
        root.refresh_from_db()
        child.refresh_from_db()
        grandchild.refresh_from_db()

        assert str(root) == "Root Node"
        assert str(child) == "--- Level 1 Node"
        assert str(grandchild) == "------ Level 2 Node"

    def test_default_values(self, user):
        """Verify default values for is_active and custom_fields."""
        category = Category.objects.create(
            name="Default Test", category_type=CategoryType.OTHER,
            created_by=user, updated_by=user
        )
        assert category.is_active is True
        assert category.custom_fields == {}

    def test_custom_fields_can_be_set(self, user):
        """Verify JSONField for custom_fields works."""
        custom_data = {"color": "blue", "priority": 1}
        category = Category.objects.create(
            name="Custom Fields Test", category_type=CategoryType.PRODUCT,
            custom_fields=custom_data,
            created_by=user, updated_by=user
        )
        assert category.custom_fields == custom_data

    def test_category_type_choices_validation(self, user):
        """Verify model validation prevents saving invalid category_type choices."""
        category = Category(
            name="Invalid Type", category_type="INVALID_CHOICE",
            created_by=user, updated_by=user
        )
        with pytest.raises(ValidationError) as excinfo:
            category.full_clean() # Trigger model validation

        # Check that the error messages contain the field name
        assert 'category_type' in excinfo.value.message_dict
        # Optional: Check for specific error message part
        assert 'is not a valid choice' in str(excinfo.value)

    # TODO: Add test for slug collision handling if the save method is updated. 