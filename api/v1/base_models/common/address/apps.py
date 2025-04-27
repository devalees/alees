from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class AddressConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.v1.base_models.common.address'
    label = 'api_v1_address'
    verbose_name = _("Address")

    def ready(self):
        # Import signals or other initialization code here if needed
        pass 