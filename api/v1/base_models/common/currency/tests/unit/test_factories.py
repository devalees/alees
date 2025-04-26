from django.test import TestCase
from ..factories import CurrencyFactory

class TestCurrencyFactory(TestCase):
    """Test cases for the CurrencyFactory."""

    def test_create_currency(self):
        """Test that CurrencyFactory creates valid Currency instances."""
        currency = CurrencyFactory()
        
        # Verify required fields
        self.assertIsNotNone(currency.code)
        self.assertIsNotNone(currency.name)
        
        # Verify default values
        self.assertEqual(currency.decimal_places, 2)
        self.assertTrue(currency.is_active)
        self.assertEqual(currency.custom_fields, {})
        
        # Verify string representation
        self.assertEqual(str(currency), currency.code)

    def test_create_multiple_currencies(self):
        """Test that CurrencyFactory creates multiple unique currencies."""
        currencies = [CurrencyFactory() for _ in range(3)]
        
        # Verify all currencies are unique
        codes = [c.code for c in currencies]
        self.assertEqual(len(set(codes)), len(currencies))
        
        # Verify each currency has correct attributes
        for currency in currencies:
            self.assertIsNotNone(currency.name)
            self.assertEqual(currency.decimal_places, 2)
            self.assertTrue(currency.is_active)

    def test_get_or_create(self):
        """Test that get_or_create prevents duplicate currencies."""
        # Create a currency
        currency1 = CurrencyFactory(code='USD')
        
        # Try to create another with the same code
        currency2 = CurrencyFactory(code='USD')
        
        # Verify it's the same instance
        self.assertEqual(currency1.pk, currency2.pk)
        self.assertEqual(currency1, currency2) 