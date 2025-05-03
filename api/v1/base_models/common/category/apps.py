from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CategoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.v1.base_models.common.category'
    label = 'api_v1_category' # Give it a distinct label
    verbose_name = _("Category")

    def ready(self):
        # Import signals if any
        pass 