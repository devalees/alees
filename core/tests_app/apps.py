from django.apps import AppConfig


class CoreTestsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core.tests_app'
    label = 'core_tests_app' # Explicit label
    verbose_name = "Core Test Utilities" 