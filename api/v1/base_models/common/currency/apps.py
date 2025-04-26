from django.apps import AppConfig


class CurrencyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.v1.base_models.common.currency'
    label = 'api_v1_currency'
    verbose_name = 'Currency'
