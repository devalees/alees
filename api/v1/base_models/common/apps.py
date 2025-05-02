from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.v1.base_models.common'
    label = 'api_v1_common'
    verbose_name = _("Common")

    def ready(self):
        # No longer need to import sub-app models here
        pass 