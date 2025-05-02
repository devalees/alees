from django.apps import AppConfig


class RbacConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.rbac"

    def ready(self):
        # Implicitly connect signal handlers decorated with @receiver.
        from . import signals # noqa F401
