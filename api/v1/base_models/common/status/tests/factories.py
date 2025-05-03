import factory
from factory.django import DjangoModelFactory
from ..models import Status

class StatusFactory(DjangoModelFactory):
    class Meta:
        model = Status
        django_get_or_create = ('slug',) # Use slug for get_or_create

    slug = factory.Sequence(lambda n: f'status_{n}')
    name = factory.Sequence(lambda n: f'Status Name {n}')
    description = factory.Faker('sentence')
    category = factory.Iterator(['General', 'Order', 'User', None])
    color = factory.Faker('hex_color')
    custom_fields = {} 