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

# Dummy Model for testing core components (like mixins)
class MockOrgScopedModel(models.Model):
    name = models.CharField(max_length=100)
    organization = models.ForeignKey(
        'api_v1_organization.Organization', # Use string to avoid direct import
        on_delete=models.CASCADE,
        related_name='mock_scoped_items' # Keep related_name if used elsewhere
    )

    class Meta:
        app_label = 'core_tests_app' # Matches AppConfig label
        # Make sure table name doesn't clash if you have other test models
        # db_table = 'core_tests_mock_org_scoped_model'
        verbose_name = 'Mock Organization Scoped Model'
        verbose_name_plural = 'Mock Organization Scoped Models'

    def __str__(self):
        return self.name 