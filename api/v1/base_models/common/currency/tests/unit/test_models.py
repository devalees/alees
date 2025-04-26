import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from api.v1.base_models.common.currency.models import Currency

class TestCurrencyModel(TestCase):
    """Unit tests for the Currency model."""

    def test_create_currency_with_required_fields(self):
        """Test that a Currency instance can be created with required fields."""
        currency = Currency.objects.create(
            code='USD',
            name='US Dollar'
        )
        self.assertEqual(currency.code, 'USD')
        self.assertEqual(currency.name, 'US Dollar')
        self.assertTrue(currency.is_active)  # Default value
        self.assertEqual(currency.decimal_places, 2)  # Default value
        self.assertEqual(currency.custom_fields, {})  # Default value

    def test_code_is_primary_key(self):
        """Test that code is the primary key."""
        currency = Currency.objects.create(
            code='USD',
            name='US Dollar'
        )
        self.assertEqual(currency.pk, 'USD')

    def test_unique_constraints(self):
        """Test unique constraints on name and numeric_code."""
        # Create first currency
        Currency.objects.create(
            code='USD',
            name='US Dollar',
            numeric_code='840'
        )

        # Test unique name constraint
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Currency.objects.create(
                    code='EUR',
                    name='US Dollar',  # Duplicate name
                    numeric_code='999'
                )

        # Test unique numeric_code constraint
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Currency.objects.create(
                    code='GBP',
                    name='British Pound',
                    numeric_code='840'  # Duplicate numeric_code
                )

    def test_default_values(self):
        """Test default values for decimal_places and is_active."""
        currency = Currency.objects.create(
            code='USD',
            name='US Dollar'
        )
        self.assertEqual(currency.decimal_places, 2)
        self.assertTrue(currency.is_active)

    def test_custom_fields_default(self):
        """Test that custom_fields defaults to an empty dict."""
        currency = Currency.objects.create(
            code='USD',
            name='US Dollar'
        )
        self.assertEqual(currency.custom_fields, {})

    def test_string_representation(self):
        """Test that __str__ method returns the code."""
        currency = Currency.objects.create(
            code='USD',
            name='US Dollar'
        )
        self.assertEqual(str(currency), 'USD')

    def test_inherited_fields_exist(self):
        """Test that inherited Timestamped and Auditable fields exist."""
        currency = Currency.objects.create(
            code='USD',
            name='US Dollar'
        )
        # Check Timestamped fields
        self.assertIsNotNone(currency.created_at)
        self.assertIsNotNone(currency.updated_at)
        # Check Auditable fields
        self.assertIsNone(currency.created_by)  # No user in test context
        self.assertIsNone(currency.updated_by)  # No user in test context
