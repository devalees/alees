from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import Timestamped, Auditable

class OrganizationType(Timestamped, Auditable):
    """
    Model representing different types of organizations in the system.
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text=_("The unique name of the organization type")
    )
    description = models.TextField(
        blank=True,
        help_text=_("Optional description of the organization type")
    )

    class Meta:
        app_label = 'api_v1_organization'
        verbose_name = _("Organization Type")
        verbose_name_plural = _("Organization Types")
        ordering = ['name']

    def __str__(self):
        return self.name 