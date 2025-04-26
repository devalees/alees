import pytest
from django.core.cache import cache

@pytest.mark.feature_flag
@pytest.mark.django_db
class TestFeatureFlags:
    """Test feature flags functionality."""

    def test_flag_creation(self, flags_manager):
        """Test creating a new feature flag."""
        result = flags_manager.create_flag(
            name='test.flag',
            description='Test flag',
            default=True
        )
        assert result is True

    def test_flag_enabled(self, flags_manager):
        """Test checking if a flag is enabled."""
        flags_manager.create_flag(
            name='test.flag',
            description='Test flag',
            default=True
        )
        assert flags_manager.is_enabled('test.flag') is True

    def test_flag_disabled(self, flags_manager):
        """Test checking if a flag is disabled."""
        flags_manager.create_flag(
            name='test.flag',
            description='Test flag',
            default=False
        )
        assert flags_manager.is_enabled('test.flag') is False

    def test_flag_update(self, flags_manager):
        """Test updating a feature flag."""
        flags_manager.create_flag(
            name='test.flag',
            description='Test flag',
            default=False
        )
        result = flags_manager.update_flag('test.flag', default=True)
        assert result is True
        assert flags_manager.is_enabled('test.flag') is True

    def test_flag_deletion(self, flags_manager):
        """Test deleting a feature flag."""
        flags_manager.create_flag(
            name='test.flag',
            description='Test flag',
            default=False
        )
        result = flags_manager.delete_flag('test.flag')
        assert result is True
        assert flags_manager.get_flag('test.flag') is None

    def test_flag_listing(self, flags_manager):
        """Test listing all feature flags."""
        flags_manager.create_flag(
            name='test.flag1',
            description='Test flag 1',
            default=False
        )
        flags_manager.create_flag(
            name='test.flag2',
            description='Test flag 2',
            default=True
        )
        flags = flags_manager.list_flags()
        assert 'test.flag1' in flags
        assert 'test.flag2' in flags
        assert flags['test.flag1']['default'] is False
        assert flags['test.flag2']['default'] is True

    @pytest.mark.redis
    def test_redis_storage(self, flags_manager, mock_redis):
        """Test feature flags with Redis storage."""
        flags_manager.storage = 'redis'
        flags_manager.create_flag(
            name='test.redis.flag',
            description='Redis test flag',
            default=True
        )
        assert flags_manager.is_enabled('test.redis.flag') is True

    @pytest.mark.cache
    def test_cache_storage(self, flags_manager):
        """Test feature flags with cache storage."""
        flags_manager.storage = 'cache'
        flags_manager.create_flag(
            name='test.cache.flag',
            description='Cache test flag',
            default=True
        )
        assert flags_manager.is_enabled('test.cache.flag') is True 