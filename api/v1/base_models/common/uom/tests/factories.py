import factory
from factory.django import DjangoModelFactory

# Use absolute import for models
from api.v1.base_models.common.uom.models import UomType, UnitOfMeasure

__all__ = ['UomTypeFactory', 'UnitOfMeasureFactory']


class UomTypeFactory(DjangoModelFactory):
    """Factory for creating UomType instances."""
    class Meta:
        model = UomType
        django_get_or_create = ('code',) # Use code to find existing instances

    code = factory.Iterator(['LENGTH', 'MASS', 'COUNT', 'VOLUME', 'TIME', 'AREA', 'ENERGY', 'TEMP', 'FREQUENCY'])
    name = factory.LazyAttribute(lambda o: o.code.capitalize())
    description = factory.Faker('sentence', nb_words=6)
    is_active = True
    custom_fields = {}
    # created_by / updated_by will be handled by Auditable model's save method


class UnitOfMeasureFactory(DjangoModelFactory):
    """Factory for creating UnitOfMeasure instances."""
    class Meta:
        model = UnitOfMeasure
        django_get_or_create = ('code',) # Use code to find existing instances

    # Ensure unique codes even if tests run multiple times
    code = factory.Sequence(lambda n: f'UOM{n:03d}')
    name = factory.Sequence(lambda n: f'Unit Name {n:03d}')
    # Link to the UomTypeFactory, automatically creating/getting a UomType
    uom_type = factory.SubFactory(UomTypeFactory)
    symbol = factory.LazyAttribute(lambda o: o.code.lower()[:5]) # Generate short symbol
    is_active = True
    custom_fields = {}
    # created_by / updated_by handled by Auditable 