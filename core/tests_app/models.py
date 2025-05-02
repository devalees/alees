from django.db import models
from core.models import OrganizationScoped

# --- Concrete model JUST for testing abstract models like OrganizationScoped ---
class ConcreteScopedModel(OrganizationScoped):
    """A concrete model inheriting OrganizationScoped for testing purposes."""
    name = models.CharField(max_length=100)

    class Meta:
        # app_label is automatically set by the app structure now
        verbose_name = "Concrete Test Model (Scoped)"

    def __str__(self):
        return self.name 