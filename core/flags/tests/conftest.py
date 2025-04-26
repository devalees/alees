import pytest
from core.flags.manager import FeatureFlagsManager

@pytest.fixture
def flags_manager():
    """Fixture that provides a FeatureFlagsManager instance."""
    manager = FeatureFlagsManager()
    return manager

@pytest.fixture
def mock_redis(mocker):
    """Fixture that provides a mocked Redis client."""
    mock = mocker.patch('django.core.cache.cache')
    return mock 