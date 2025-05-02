from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FileStorageConfig(AppConfig):
    """Configuration for the FileStorage app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "api.v1.base_models.common.fileStorage"
    label = "file_storage"  # Use a simple label for commands
    verbose_name = _("File Storage")

    def ready(self):
        """Perform initialization tasks when the app is ready."""
        # Import signals here if needed in the future
        pass 