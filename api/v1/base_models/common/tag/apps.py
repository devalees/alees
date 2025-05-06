from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TagConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.v1.base_models.common.tag'
    label = 'api_v1_tag'
    verbose_name = _("Tag")
    
    def ready(self):
        pass 