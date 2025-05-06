from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class StatusConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.v1.base_models.common.status'
    label = 'api_v1_status'  # Give it a distinct label
    verbose_name = _("Status")

    def ready(self):
        # Import signals if any
        pass 