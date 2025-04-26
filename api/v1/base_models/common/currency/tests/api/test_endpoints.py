from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ..factories import CurrencyFactory
from ...models import Currency

class CurrencyAPITests(APITestCase):
    def setUp(self):
        # Create some test currencies
        self.currencies = [
            CurrencyFactory(code='USD', name='US Dollar', is_active=True),
            CurrencyFactory(code='EUR', name='Euro', is_active=True),
            CurrencyFactory(code='JPY', name='Japanese Yen', is_active=False)
        ]
        self.list_url = '/api/v1/currencies/'
        self.detail_url = lambda code: f'/api/v1/currencies/{code}/'

    def test_list_currencies_unauthenticated(self):
        """Test that unauthenticated users can list currencies"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)  # Only active currencies
        self.assertTrue(all(currency['is_active'] for currency in data))

    def test_list_currencies_authenticated(self):
        """Test that authenticated users can list currencies"""
        # Create a test user and authenticate
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=user)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)  # Only active currencies
        self.assertTrue(all(currency['is_active'] for currency in data))

    def test_retrieve_currency_unauthenticated(self):
        """Test that unauthenticated users can retrieve a currency"""
        response = self.client.get(self.detail_url('USD'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['code'], 'USD')
        self.assertEqual(data['name'], 'US Dollar')

    def test_retrieve_currency_authenticated(self):
        """Test that authenticated users can retrieve a currency"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=user)

        response = self.client.get(self.detail_url('USD'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['code'], 'USD')
        self.assertEqual(data['name'], 'US Dollar')

    def test_retrieve_nonexistent_currency(self):
        """Test retrieving a non-existent currency returns 404"""
        response = self.client.get(self.detail_url('XXX'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_inactive_currency_not_in_list(self):
        """Test that inactive currencies are not included in the list"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertNotIn('JPY', [currency['code'] for currency in data])

    def test_retrieve_inactive_currency(self):
        """Test that inactive currencies can still be retrieved"""
        response = self.client.get(self.detail_url('JPY'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['code'], 'JPY')
        self.assertEqual(data['is_active'], False)
