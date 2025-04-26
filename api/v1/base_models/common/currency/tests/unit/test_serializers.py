from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import serializers
from ..factories import CurrencyFactory
from ...serializers import CurrencySerializer

class TestCurrencySerializer(TestCase):
    """Unit tests for CurrencySerializer."""

    def setUp(self):
        self.currency = CurrencyFactory()
        self.serializer = CurrencySerializer(instance=self.currency)

    def test_contains_expected_fields(self):
        """Test that serializer contains all expected fields."""
        data = self.serializer.data
        expected_fields = {
            'code', 'name', 'symbol', 'numeric_code', 
            'decimal_places', 'is_active', 'custom_fields'
        }
        self.assertEqual(set(data.keys()), expected_fields)

    def test_code_validation(self):
        """Test code field validation."""
        # Test valid code
        data = {
            'code': 'EUR',
            'name': 'Euro',
            'decimal_places': 2,
            'is_active': True
        }
        serializer = CurrencySerializer(data=data)
        is_valid = serializer.is_valid()
        if not is_valid:
            print("Validation errors:", serializer.errors)
        self.assertTrue(is_valid)

        # Test invalid code length
        data = {
            'code': 'EU',
            'name': 'Euro Short',
            'decimal_places': 2,
            'is_active': True
        }
        serializer = CurrencySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('code', serializer.errors)

        # Test invalid code length
        data = {
            'code': 'EURO',
            'name': 'Euro Long',
            'decimal_places': 2,
            'is_active': True
        }
        serializer = CurrencySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('code', serializer.errors)

    def test_custom_fields_validation(self):
        """Test custom_fields validation."""
        # Test valid custom fields
        data = {
            'code': 'GBP',
            'name': 'British Pound',
            'decimal_places': 2,
            'is_active': True,
            'custom_fields': {'key': 'value'}
        }
        serializer = CurrencySerializer(data=data)
        is_valid = serializer.is_valid()
        if not is_valid:
            print("Validation errors:", serializer.errors)
        self.assertTrue(is_valid)

        # Test invalid custom fields (non-dict)
        data = {
            'code': 'USD',
            'name': 'US Dollar',
            'custom_fields': 'invalid'
        }
        serializer = CurrencySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('custom_fields', serializer.errors)

    def test_representation(self):
        """Test serializer representation."""
        data = self.serializer.data
        self.assertEqual(data['code'], self.currency.code)
        self.assertEqual(data['name'], self.currency.name)
        self.assertEqual(data['symbol'], self.currency.symbol)
        self.assertEqual(data['numeric_code'], self.currency.numeric_code)
        self.assertEqual(data['decimal_places'], self.currency.decimal_places)
        self.assertEqual(data['is_active'], self.currency.is_active)
        self.assertEqual(data['custom_fields'], self.currency.custom_fields)
