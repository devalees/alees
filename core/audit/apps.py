from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.audit"
    verbose_name = _('Audit Logging')

    def ready(self):
        """Connect signal handlers when the app is ready."""
        try:
            # Import signals here to ensure models are loaded
            import core.audit.signals # noqa F401
        except ImportError:
            # Handle cases where signals might not be importable yet
            # (e.g., during initial setup or specific management commands)
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Could not import core.audit.signals. Audit signals may not be connected.")
            pass
