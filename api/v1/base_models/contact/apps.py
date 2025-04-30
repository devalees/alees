from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ContactConfig(AppConfig):
    """Contact app configuration."""
    
    name = 'api.v1.base_models.contact'
    label = 'contact'
    verbose_name = _('Contact Management')
    
    def ready(self):
        """Import signals when the app is ready."""
        try:
            import api.v1.base_models.contact.signals  # noqa F401
        except ImportError:
            pass
