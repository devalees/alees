from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    """Configuration for the Documents app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.v1.features.documents'
    verbose_name = 'Documents' 