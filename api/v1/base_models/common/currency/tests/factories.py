import factory
from factory.django import DjangoModelFactory
from ..models import Currency

class CurrencyFactory(DjangoModelFactory):
    """
    Factory for creating Currency instances for testing.
    Uses factory-boy to generate test data with realistic defaults.
    """
    class Meta:
        model = Currency
        # Use code as the lookup field for get_or_create
        django_get_or_create = ('code',)

    code = factory.Iterator(['USD', 'EUR', 'JPY', 'GBP', 'CAD', 'AUD'])
    name = factory.LazyAttribute(lambda o: {
        'USD': 'US Dollar',
        'EUR': 'Euro',
        'JPY': 'Japanese Yen',
        'GBP': 'Pound Sterling',
        'CAD': 'Canadian Dollar',
        'AUD': 'Australian Dollar'
    }.get(o.code, f'Currency {o.code}'))
    symbol = factory.LazyAttribute(lambda o: {
        'USD': '$',
        'EUR': '€',
        'JPY': '¥',
        'GBP': '£',
        'CAD': '$',
        'AUD': '$'
    }.get(o.code, ''))
    numeric_code = factory.LazyAttribute(lambda o: {
        'USD': '840',
        'EUR': '978',
        'JPY': '392',
        'GBP': '826',
        'CAD': '124',
        'AUD': '036'
    }.get(o.code, None))
    decimal_places = 2
    is_active = True
    custom_fields = {}
