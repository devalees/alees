from django.test import TestCase, override_settings
import pytest
from django.core.cache import caches
from django.core.cache.backends.locmem import LocMemCache
from core.redis.config import get_cache, generate_cache_key, clear_cache_pattern, get_redis_client
from django.conf import settings
from unittest.mock import MagicMock, patch

@pytest.mark.django_db
class RedisConfigTests(TestCase):
    def setUp(self):
        """Set up test environment"""
        super().setUp()
        self.cache = get_cache()
        for cache in caches.all():
            cache.clear()

    def tearDown(self):
        """Clean up test environment"""
        super().tearDown()
        for cache in caches.all():
            cache.clear()

    def test_get_cache(self):
        """Test getting cache instance"""
        cache = get_cache()
        self.assertIsInstance(cache, LocMemCache)

    def test_cache_operations(self):
        """Test basic cache operations"""
        self.cache.set('test_key', 'test_value')
        self.assertEqual(self.cache.get('test_key'), 'test_value')
        self.cache.delete('test_key')
        self.assertIsNone(self.cache.get('test_key'))

    def test_generate_cache_key(self):
        """Test cache key generation"""
        key = generate_cache_key('test', 1, 'two')
        self.assertEqual(key, 'test:1:two')

    @patch('core.redis.config.get_cache')
    def test_clear_cache_pattern(self, mock_get_cache):
        """Test clearing cache by pattern"""
        # Create a mock cache with Redis-like behavior
        mock_cache = MagicMock()
        mock_cache.keys.return_value = ['test:1', 'test:2']
        mock_get_cache.return_value = mock_cache
        
        # Call the function
        clear_cache_pattern('test:*')
        
        # Verify the correct methods were called
        mock_cache.keys.assert_called_once_with('test:*')
        mock_cache.delete_many.assert_called_once_with(['test:1', 'test:2'])

    def test_get_redis_client(self):
        """Test getting raw Redis client"""
        # In test environment, Redis client operations should be handled by LocMemCache
        client = get_redis_client()
        self.assertIsNone(client)

    def test_multiple_cache_aliases(self):
        """Test using multiple cache aliases"""
        default_cache = get_cache('default')
        permissions_cache = get_cache('permissions')
        
        # Set values in different caches
        default_cache.set('shared_key', 'default_value')
        permissions_cache.set('shared_key', 'permissions_value')
        
        # Each cache should maintain its own value
        self.assertEqual(default_cache.get('shared_key'), 'default_value')
        self.assertEqual(permissions_cache.get('shared_key'), 'permissions_value')

    def test_cache_isolation(self):
        """Test cache isolation between instances"""
        # Get two separate cache instances
        cache1 = get_cache('default')
        cache2 = get_cache('permissions')
        
        # Set values in different caches
        cache1.set('shared_key', 'value1')
        cache2.set('shared_key', 'value2')
        
        # Each cache should maintain its own value
        self.assertEqual(cache1.get('shared_key'), 'value1')
        self.assertEqual(cache2.get('shared_key'), 'value2') 