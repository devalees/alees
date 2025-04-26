import pytest
from unittest.mock import MagicMock
from core.secrets.manager import SecretsManager

@pytest.fixture
def mock_secrets_manager(mocker):
    """Fixture that provides a mocked SecretsManager instance."""
    mock = MagicMock(spec=SecretsManager)
    return mock

@pytest.fixture
def secrets_manager():
    """Fixture that provides a real SecretsManager instance."""
    manager = SecretsManager()
    return manager 