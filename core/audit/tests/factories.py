import factory
from factory.django import DjangoModelFactory
from django.contrib.contenttypes.models import ContentType

# Import model and choices from the audit app
from core.audit.models import AuditLog
from core.audit.choices import AuditActionType

# Import factories for User, Organization from their respective locations
# Assuming standard paths based on project structure and previous steps
from api.v1.base_models.user.tests.factories import UserFactory
from api.v1.base_models.organization.tests.factories import OrganizationFactory
# from api.v1.base_models.common.tests.factories import ProductFactory # Example for later

class AuditLogFactory(DjangoModelFactory):
    class Meta:
        model = AuditLog

    user = factory.SubFactory(UserFactory)
    organization = factory.SubFactory(OrganizationFactory)
    action_type = factory.Iterator([choice[0] for choice in AuditActionType.CHOICES])

    # Define content_object default to handle LazyAttribute access
    content_object = None

    # Set object_repr based on content_object if it exists
    object_repr = factory.LazyAttribute(lambda o: str(o.content_object)[:255] if o.content_object else '')

    changes = None # Default to None
    context = None # Default to None

    # Correctly set GFK fields *after* content_object is resolved
    @factory.lazy_attribute
    def content_type(self):
        if self.content_object:
            return ContentType.objects.get_for_model(self.content_object)
        return None

    @factory.lazy_attribute
    def object_id(self):
        if self.content_object:
            # Ensure pk is accessed only if content_object exists and has a pk
            if self.content_object.pk:
                return str(self.content_object.pk) # Use string representation
        return None

    # If you want to easily create logs linked to specific objects:
    @factory.post_generation
    def set_content_object(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted: # If a model instance was passed to the factory
            self.content_object = extracted
            # Re-calculate GFK fields based on the extracted object
            self.content_type = ContentType.objects.get_for_model(extracted)
            self.object_id = str(extracted.pk)
            if not self.object_repr: # Set repr if not already set
                 self.object_repr = str(extracted)[:255]
            # No save needed here, factory handles it if create=True
