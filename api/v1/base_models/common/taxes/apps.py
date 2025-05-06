from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TaxesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.v1.base_models.common.taxes'
    verbose_name = _('Taxes')

    def ready(self):
        # Import signals here if necessary
        pass 