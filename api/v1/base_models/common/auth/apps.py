from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.v1.base_models.common.auth'
    label = 'api_auth'  # Unique label to avoid conflict with Django's auth
    verbose_name = 'Authentication' 