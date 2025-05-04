from django.apps import AppConfig


class CoreTestsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core.tests_app' # Path to the app
    label = 'core_tests_app' # Used in Meta.app_label and INSTALLED_APPS
    verbose_name = 'Core Test Utilities App' 