from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AddressConfig(AppConfig):
    """Configuration for the Address app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "api.v1.base_models.common.address"
    label = "address"
    verbose_name = _("Address")

    def ready(self):
        """Perform initialization tasks when the app is ready."""
        pass
