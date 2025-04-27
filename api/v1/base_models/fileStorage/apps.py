from django.apps import AppConfig


class FileStorageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.v1.base_models.fileStorage'
    verbose_name = 'File Storage'

    def ready(self):
        try:
            import api.v1.base_models.fileStorage.signals  # noqa
        except ImportError:
            pass 