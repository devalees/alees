from django.apps import AppConfig


class UserConfig(AppConfig):
    """Configuration for the User app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.v1.base_models.user'
    verbose_name = 'User Management'

    def ready(self):
        """Initialize app-specific configurations."""
        try:
            import api.v1.base_models.user.signals  # noqa
        except ImportError:
            pass 