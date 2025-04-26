from django.apps import AppConfig

class CoreConfig(AppConfig):
    """Configuration for the core app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core'

    def ready(self):
        """Import signals when app is ready."""
        # noqa 