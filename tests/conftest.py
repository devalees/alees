import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client
from rest_framework.test import APIClient

from core.flags import FeatureFlagsManager
from core.secrets import SecretsManager

User = get_user_model()

@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test."""
    cache.clear()
    yield
    cache.clear()

@pytest.fixture
def client():
    """Django test client."""
    return Client()

@pytest.fixture
def api_client():
    """DRF API test client."""
    return APIClient()

@pytest.fixture
def user():
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.fixture
def authenticated_client(api_client, user):
    """Authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def admin_user():
    """Create a test admin user."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )

@pytest.fixture
def admin_client(api_client, admin_user):
    """Authenticated admin API client."""
    api_client.force_authenticate(user=admin_user)
    return api_client

@pytest.fixture
def flags_manager():
    """Feature flags manager."""
    return FeatureFlagsManager()

@pytest.fixture
def secrets_manager():
    """Secrets manager."""
    return SecretsManager()

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests."""
    pass

@pytest.fixture
def mock_redis(monkeypatch):
    """Mock Redis connection."""
    from fakeredis import FakeRedis
    monkeypatch.setattr('redis.Redis', FakeRedis)
    return FakeRedis()

@pytest.fixture
def mock_celery(monkeypatch):
    """Mock Celery tasks."""
    from unittest.mock import patch
    with patch('celery.app.task.Task.delay') as mock:
        yield mock

@pytest.fixture
def mock_secrets_manager(monkeypatch):
    """Mock secrets manager."""
    from unittest.mock import MagicMock
    mock = MagicMock(spec=SecretsManager)
    monkeypatch.setattr('core.secrets.SecretsManager', lambda: mock)
    return mock

@pytest.fixture
def mock_flags_manager(monkeypatch):
    """Mock feature flags manager."""
    from unittest.mock import MagicMock
    mock = MagicMock(spec=FeatureFlagsManager)
    monkeypatch.setattr('core.flags.FeatureFlagsManager', lambda: mock)
    return mock 