import factory
from factory.django import DjangoModelFactory
from ..models import Status
from api.v1.base_models.common.category.models import Category
from api.v1.base_models.common.category.choices import CategoryType

class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ('slug',)
    
    name = factory.Sequence(lambda n: f'Category {n}')
    slug = factory.Sequence(lambda n: f'category-{n}')
    description = factory.Faker('sentence')
    category_type = CategoryType.OTHER
    is_active = True
    custom_fields = {}

class StatusFactory(DjangoModelFactory):
    class Meta:
        model = Status
        django_get_or_create = ('slug',) # Use slug for get_or_create

    slug = factory.Sequence(lambda n: f'status_{n}')
    name = factory.Sequence(lambda n: f'Status Name {n}')
    description = factory.Faker('sentence')
    category = factory.SubFactory(CategoryFactory)
    color = factory.Faker('hex_color')
    custom_fields = {} 