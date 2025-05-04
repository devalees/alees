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