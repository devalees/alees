from django.core.cache import caches
from django.conf import settings
from django.core.cache.backends.locmem import LocMemCache
import fnmatch
import re

def get_cache(alias='default'):
    """
    Get a specific cache backend by alias
    """
    return caches[alias]

def generate_cache_key(prefix, *args):
    """
    Helper function to generate consistent cache keys
    Args:
        prefix (str): The prefix for the cache key
        *args: Additional arguments to include in the key
    Returns:
        str: Generated cache key
    """
    return f"{prefix}:{':'.join(str(arg) for arg in args)}"

def clear_cache_pattern(pattern):
    """
    Helper function to clear cache keys matching a pattern
    Args:
        pattern (str): The pattern to match cache keys against (Redis-style pattern with *)
    """
    cache = get_cache()
    if hasattr(cache, 'keys'):
        # Redis backend
        keys = cache.keys(pattern)
        if keys:
            cache.delete_many(keys)
    else:
        # LocMemCache backend
        if hasattr(cache, '_cache'):
            # Convert Redis pattern to regex pattern
            pattern_parts = pattern.split('*')
            pattern_start = pattern_parts[0]
            
            # Find all matching keys
            for key_tuple in list(cache._cache.keys()):
                if isinstance(key_tuple, tuple) and len(key_tuple) >= 2:
                    cache_key = key_tuple[1]  # The actual key is the second element
                    if isinstance(cache_key, str) and cache_key.startswith(pattern_start):
                        cache.delete(cache_key)
                elif isinstance(key_tuple, str) and key_tuple.startswith(pattern_start):
                    cache.delete(key_tuple)

def get_redis_client(alias='default'):
    """
    Get the raw Redis client for a specific cache backend
    Args:
        alias (str): The cache alias to get the client for
    Returns:
        redis.Redis: The Redis client instance
    """
    cache = get_cache(alias)
    if hasattr(cache, 'client'):
        return cache.client.get_client()
    return None
