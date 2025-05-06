import pytest
from taggit.models import Tag

# Use absolute import path
from api.v1.base_models.common.tag.tests.factories import TagFactory

pytestmark = pytest.mark.django_db


def test_tag_factory():
    """Test that the TagFactory creates a valid Tag instance."""
    tag = TagFactory()
    assert isinstance(tag, Tag)
    assert Tag.objects.count() == 1
    assert tag.name.startswith("Common Tag ")
    assert tag.slug is not None
    assert tag.slug == tag.name.lower().replace(" ", "-")

    # Test uniqueness with get_or_create
    tag2 = TagFactory(name=tag.name)
    assert tag2.id == tag.id
    assert Tag.objects.count() == 1


def test_tag_no_organization_required():
    """
    Test that Tag model works without organization scoping.
    The Tag model should not have an organization field.
    """
    tag = TagFactory()
    
    # Verify Tag model doesn't have organization field
    assert not hasattr(tag, 'organization')
    
    # Create a new tag directly to verify no organization needed
    new_tag = Tag.objects.create(name="Test Tag")
    assert new_tag.name == "Test Tag"
    assert new_tag.slug == "test-tag" 