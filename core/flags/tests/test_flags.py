import pytest
from django.core.cache import cache
from django.conf import settings
from unittest.mock import MagicMock, patch

@pytest.mark.feature_flag
@pytest.mark.django_db
class TestFeatureFlags:
    """Test feature flags functionality."""

    def test_flag_creation(self, flags_manager):
        """Test creating a new feature flag."""
        result = flags_manager.create_flag(
            name='test.flag',
            description='Test flag',
            enabled=True
        )
        assert result is True

    def test_flag_enabled(self, flags_manager):
        """Test checking if a flag is enabled."""
        flags_manager.create_flag(
            name='test.flag',
            description='Test flag',
            enabled=True
        )
        assert flags_manager.is_enabled('test.flag') is True

    def test_flag_disabled(self, flags_manager):
        """Test checking if a flag is disabled."""
        flags_manager.create_flag(
            name='test.flag',
            description='Test flag',
            enabled=False
        )
        assert flags_manager.is_enabled('test.flag') is False

    def test_flag_update(self, flags_manager):
        """Test updating a feature flag."""
        flags_manager.create_flag(
            name='test.flag',
            description='Test flag',
            enabled=False
        )
        result = flags_manager.update_flag('test.flag', enabled=True)
        assert result is True
        assert flags_manager.is_enabled('test.flag') is True

    def test_flag_deletion(self, flags_manager):
        """Test deleting a feature flag."""
        flags_manager.create_flag(
            name='test.flag',
            description='Test flag',
            enabled=False
        )
        result = flags_manager.delete_flag('test.flag')
        assert result is True
        assert flags_manager.get_flag('test.flag') is None

    def test_flag_listing(self, flags_manager):
        """Test listing all feature flags."""
        flags_manager.create_flag(
            name='test.flag1',
            description='Test flag 1',
            enabled=False
        )
        flags_manager.create_flag(
            name='test.flag2',
            description='Test flag 2',
            enabled=True
        )
        flags = flags_manager.list_flags()
        assert len(flags) == 2
        flag_names = {flag['name'] for flag in flags}
        assert flag_names == {'test.flag1', 'test.flag2'}
        flag1 = next(flag for flag in flags if flag['name'] == 'test.flag1')
        flag2 = next(flag for flag in flags if flag['name'] == 'test.flag2')
        assert flag1['enabled'] is False
        assert flag2['enabled'] is True

    @pytest.mark.redis
    def test_redis_storage(self, flags_manager, settings):
        """Test feature flags with Redis storage."""
        # Configure Redis storage with mock
        settings.FEATURE_FLAGS_STORAGE = 'redis'
        flags_manager.storage = 'redis'
        mock_redis = MagicMock()
        mock_redis.get.return_value = b'1'
        
        # Mock both the manager's Redis connection and the get_redis_connection function
        with patch('django_redis.get_redis_connection', return_value=mock_redis):
            flags_manager.redis = mock_redis
            
            # Create and test flag
            flags_manager.create_flag(
                name='test.redis.flag',
                description='Redis test flag',
                enabled=True
            )
            assert flags_manager.is_enabled('test.redis.flag') is True
            
            # Verify Redis mock was called correctly
            mock_redis.set.assert_called_with("flag:test.redis.flag", '1')
            mock_redis.get.assert_called_with("flag:test.redis.flag")

    @pytest.mark.cache
    def test_cache_storage(self, flags_manager):
        """Test feature flags with cache storage."""
        flags_manager.storage = 'cache'
        flags_manager.create_flag(
            name='test.cache.flag',
            description='Cache test flag',
            enabled=True
        )
        assert flags_manager.is_enabled('test.cache.flag') is True 