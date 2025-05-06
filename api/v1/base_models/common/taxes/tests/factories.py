import factory
from factory.django import DjangoModelFactory
from django.utils import timezone
from decimal import Decimal

from api.v1.base_models.common.taxes.models import TaxJurisdiction, TaxCategory, TaxRate, TaxType, JurisdictionType


class TaxJurisdictionFactory(DjangoModelFactory):
    class Meta:
        model = TaxJurisdiction

    code = factory.Sequence(lambda n: f'JURIS-{n}')
    name = factory.Sequence(lambda n: f'Jurisdiction {n}')
    jurisdiction_type = factory.Iterator([choice[0] for choice in JurisdictionType.CHOICES])
    is_active = True
    custom_fields = {}


class TaxCategoryFactory(DjangoModelFactory):
    class Meta:
        model = TaxCategory

    code = factory.Sequence(lambda n: f'CAT-{n}')
    name = factory.Sequence(lambda n: f'Tax Category {n}')
    description = factory.Faker('paragraph', nb_sentences=2)
    is_active = True


class TaxRateFactory(DjangoModelFactory):
    class Meta:
        model = TaxRate

    jurisdiction = factory.SubFactory(TaxJurisdictionFactory)
    tax_category = factory.SubFactory(TaxCategoryFactory)
    name = factory.Sequence(lambda n: f'Tax Rate {n}')
    rate = factory.Faker('pydecimal', left_digits=1, right_digits=4, positive=True)
    tax_type = factory.Iterator([choice[0] for choice in TaxType.CHOICES])
    is_compound = False
    priority = 0
    valid_from = factory.LazyFunction(lambda: timezone.now().date())
    valid_to = factory.LazyFunction(lambda: timezone.now().date().replace(year=timezone.now().year + 1))
    is_active = True
    custom_fields = {} 