import factory
from factory.django import DjangoModelFactory
from django.core.files.base import ContentFile
import uuid

# Assuming models are in the same app/directory structure
from ..models import FileStorage
from api.v1.base_models.organization.tests.factories import OrganizationFactory
from api.v1.base_models.user.tests.factories import UserFactory


class FileStorageFactory(DjangoModelFactory):
    """Factory for the FileStorage model."""
    class Meta:
        model = FileStorage

    # Link to required related factories
    organization = factory.SubFactory(OrganizationFactory)
    # uploaded_by needs access to the organization created above
    uploaded_by = factory.SubFactory(UserFactory, organization=factory.SelfAttribute('..organization'))
    created_by = factory.SelfAttribute('uploaded_by') # Default created_by to uploaded_by
    updated_by = factory.SelfAttribute('uploaded_by') # Default updated_by to uploaded_by

    # File-specific fields
    original_filename = factory.LazyAttribute(lambda o: f"{uuid.uuid4()}.txt")
    # Use LazyFunction for ContentFile to generate unique content/name per instance
    file = factory.LazyFunction(
        # Force Faker evaluation to string before encoding
        lambda: ContentFile(str(factory.Faker('text')).encode('utf-8'), name=f"{uuid.uuid4()}.dat")
    )
    # file_size and mime_type are often populated post-save or by signals/views,
    # but can be set here for testing if needed.
    # file_size = factory.LazyAttribute(lambda o: len(o.file.read())) # Requires reading file
    mime_type = factory.Faker('mime_type')

    # Custom fields and tags
    custom_fields = factory.Dict({"project_code": factory.Faker('ean', length=8)})
    # tags = factory.PostGenerationMethodCall('set', ['test', 'document']) # Example post-generation

    # Ensure tags are handled correctly after creation
    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return
        if extracted:
            # A list of tags were passed in, use them.
            self.tags.set(extracted)
        else:
            # Default tags if none provided
            self.tags.set(['factory_generated', self.mime_type.split('/')[0]]) # e.g., ['factory', 'image'] 