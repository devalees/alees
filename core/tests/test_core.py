import pytest
from django.test import TestCase
from django.conf import settings

@pytest.mark.django_db
class TestCoreApp(TestCase):
    """Test cases for the core app functionality."""

    def test_core_app_loaded(self):
        """Test that the core app is properly loaded in settings."""
        assert 'core.apps.CoreConfig' in settings.INSTALLED_APPS

    def test_feature_flags_configured(self):
        """Test that feature flags are properly configured."""
        assert hasattr(settings, 'FEATURE_FLAGS_STORAGE')
        assert hasattr(settings, 'FEATURE_FLAGS_REDIS_URL')
        assert hasattr(settings, 'FLAGS')

    def test_default_feature_flags(self):
        """Test that default feature flags are set."""
        assert 'auth.two_factor.enabled' in settings.FLAGS
        assert 'project.new_dashboard' in settings.FLAGS
        assert 'billing.invoice_auto_generate' in settings.FLAGS 