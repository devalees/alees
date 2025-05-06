import factory
from factory.django import DjangoModelFactory
from django.contrib.contenttypes.models import ContentType

from api.v1.features.documents.models import Document
from api.v1.base_models.common.fileStorage.tests.factories import FileStorageFactory
from api.v1.base_models.common.category.tests.factories import CategoryFactory
from api.v1.base_models.organization.tests.factories import OrganizationFactory


class DocumentFactory(DjangoModelFactory):
    """Factory for Document model."""
    
    class Meta:
        model = Document
    
    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('paragraph')
    status = 'draft'
    version = 1
    organization = factory.SubFactory(OrganizationFactory)
    file = factory.SubFactory(FileStorageFactory)
    document_type = factory.SubFactory(
        CategoryFactory,
        category_type='DOCUMENT_TYPE'
    )
    custom_fields = {}
    
    # Content type and object_id will remain None by default
    # To set them, pass content_object as a parameter when creating a Document
    
    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        """Add tags to the document."""
        if not create:
            return
        
        if extracted:
            # Add provided tags
            for tag in extracted:
                self.tags.add(tag)
                
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        Handle setting the content_object if provided.
        This will automatically set content_type and object_id.
        """
        content_object = kwargs.pop('content_object', None)
        obj = super()._create(model_class, *args, **kwargs)
        
        if content_object is not None:
            # Set the generic foreign key relation
            obj.content_type = ContentType.objects.get_for_model(content_object)
            obj.object_id = str(content_object.pk)
            obj.save()
            
        return obj 