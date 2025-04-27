import pytest
from django.test import RequestFactory
from django.core.cache import cache
from django.conf import settings
from core.flags.manager import FeatureFlagsManager
from core.flags.models import Flag

@pytest.fixture
def flag_manager():
    return FeatureFlagsManager()

@pytest.fixture
def request_factory():
    return RequestFactory()

@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before and after each test."""
    cache.clear()
    yield
    cache.clear()

def test_flag_creation(flag_manager):
    """Test creating a new feature flag."""
    # Test successful creation
    assert flag_manager.create_flag("test_flag", default=True, description="Test flag")
    
    # Verify flag exists in database
    flag = Flag.objects.get(name="test_flag")
    assert flag.default is True
    assert flag.description == "Test flag"
    
    # Test duplicate creation
    assert not flag_manager.create_flag("test_flag", default=False)

def test_flag_enabled(flag_manager, request_factory):
    """Test checking if a flag is enabled."""
    # Create a flag
    flag_manager.create_flag("test_flag", default=True)
    
    # Test with default value
    request = request_factory.get('/')
    assert flag_manager.is_enabled("test_flag", request)
    
    # Test non-existent flag
    assert not flag_manager.is_enabled("non_existent_flag", request)

def test_redis_storage(flag_manager):
    """Test Redis storage integration."""
    if settings.FEATURE_FLAGS_STORAGE != 'redis':
        pytest.skip("Redis storage not configured")
        
    # Create a flag
    flag_manager.create_flag("redis_flag", default=True)
    
    # Verify Redis storage
    redis_value = flag_manager.redis.get("flag:redis_flag")
    assert redis_value == b'1'
    
    # Update flag
    flag_manager.update_flag("redis_flag", default=False)
    redis_value = flag_manager.redis.get("flag:redis_flag")
    assert redis_value == b'0'
    
    # Delete flag
    flag_manager.delete_flag("redis_flag")
    assert flag_manager.redis.get("flag:redis_flag") is None

def test_cache_storage(flag_manager):
    """Test cache storage integration."""
    if settings.FEATURE_FLAGS_STORAGE != 'cache':
        pytest.skip("Cache storage not configured")
        
    # Create a flag
    flag_manager.create_flag("cache_flag", default=True)
    
    # Verify cache storage
    cache_value = cache.get("flag:cache_flag")
    assert cache_value is True
    
    # Update flag
    flag_manager.update_flag("cache_flag", default=False)
    cache_value = cache.get("flag:cache_flag")
    assert cache_value is False
    
    # Delete flag
    flag_manager.delete_flag("cache_flag")
    assert cache.get("flag:cache_flag") is None

def test_flag_update(flag_manager):
    """Test updating a feature flag."""
    # Create initial flag
    flag_manager.create_flag("update_flag", default=False, description="Initial")
    
    # Test successful update
    assert flag_manager.update_flag("update_flag", default=True, description="Updated")
    
    # Verify updates
    flag = Flag.objects.get(name="update_flag")
    assert flag.default is True
    assert flag.description == "Updated"
    
    # Test updating non-existent flag
    assert not flag_manager.update_flag("non_existent", default=True)

def test_flag_deletion(flag_manager):
    """Test deleting a feature flag."""
    # Create a flag
    flag_manager.create_flag("delete_flag", default=True)
    
    # Test successful deletion
    assert flag_manager.delete_flag("delete_flag")
    assert not Flag.objects.filter(name="delete_flag").exists()
    
    # Test deleting non-existent flag
    assert not flag_manager.delete_flag("non_existent")

def test_flag_listing(flag_manager):
    """Test listing all feature flags."""
    # Create some flags
    flag_manager.create_flag("flag1", default=True, description="First flag")
    flag_manager.create_flag("flag2", default=False, description="Second flag")
    
    # Get list of flags
    flags = flag_manager.list_flags()
    
    # Verify list contents
    assert len(flags) == 2
    flag_names = {flag['name'] for flag in flags}
    assert flag_names == {'flag1', 'flag2'}

def test_get_flag(flag_manager):
    """Test getting a single flag's details."""
    # Create a flag
    flag_manager.create_flag("get_flag", default=True, description="Test flag")
    
    # Get flag details
    flag_info = flag_manager.get_flag("get_flag")
    
    # Verify details
    assert flag_info is not None
    assert flag_info['name'] == "get_flag"
    assert flag_info['default'] is True
    assert flag_info['description'] == "Test flag"
    
    # Test getting non-existent flag
    assert flag_manager.get_flag("non_existent") is None 