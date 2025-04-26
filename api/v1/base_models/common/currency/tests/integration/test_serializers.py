from django.test import TestCase
from rest_framework.test import APITestCase
from ..factories import CurrencyFactory
from ...serializers import CurrencySerializer
from ...models import Currency

class TestCurrencySerializerIntegration(TestCase):
    """Integration tests for CurrencySerializer."""

    def setUp(self):
        self.currency = CurrencyFactory()
        self.serializer = CurrencySerializer(instance=self.currency)

    def test_create_currency(self):
        """Test creating a new currency through serializer."""
        data = {
            'code': 'NZD',
            'name': 'New Zealand Dollar',
            'symbol': '$',
            'numeric_code': '554',
            'decimal_places': 2,
            'is_active': True,
            'custom_fields': {'region': 'Oceania'}
        }
        serializer = CurrencySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        currency = serializer.save()
        
        # Verify the currency was created correctly
        self.assertEqual(currency.code, 'NZD')
        self.assertEqual(currency.name, 'New Zealand Dollar')
        self.assertEqual(currency.symbol, '$')
        self.assertEqual(currency.numeric_code, '554')
        self.assertEqual(currency.decimal_places, 2)
        self.assertTrue(currency.is_active)
        self.assertEqual(currency.custom_fields, {'region': 'Oceania'})

    def test_update_currency(self):
        """Test updating an existing currency through serializer."""
        data = {
            'code': self.currency.code,
            'name': 'Updated Name',
            'symbol': 'U',
            'numeric_code': '999',
            'decimal_places': 3,
            'is_active': False,
            'custom_fields': {'updated': True}
        }
        serializer = CurrencySerializer(instance=self.currency, data=data)
        self.assertTrue(serializer.is_valid())
        currency = serializer.save()
        
        # Verify the currency was updated correctly
        self.assertEqual(currency.name, 'Updated Name')
        self.assertEqual(currency.symbol, 'U')
        self.assertEqual(currency.numeric_code, '999')
        self.assertEqual(currency.decimal_places, 3)
        self.assertFalse(currency.is_active)
        self.assertEqual(currency.custom_fields, {'updated': True})

    def test_unique_constraints(self):
        """Test serializer respects unique constraints."""
        # Create initial currency
        CurrencyFactory(code='TST', name='Test Currency')
        
        # Try to create another with same code
        data = {
            'code': 'TST',
            'name': 'Another Test Currency'
        }
        serializer = CurrencySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('code', serializer.errors)
        
        # Try to create another with same name
        data = {
            'code': 'TS2',
            'name': 'Test Currency'
        }
        serializer = CurrencySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors) 