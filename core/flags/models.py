from django.db import models
from django.utils.translation import gettext_lazy as _

class Flag(models.Model):
    """
    Model for storing feature flags.
    """
    name = models.CharField(
        _("Name"),
        max_length=100,
        unique=True,
        help_text=_("Name of the feature flag.")
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Description of what this flag controls.")
    )
    enabled = models.BooleanField(
        _("Enabled"),
        default=False,
        help_text=_("Whether this flag is currently enabled.")
    )
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True,
        help_text=_("When this flag was created.")
    )
    updated_at = models.DateTimeField(
        _("Updated At"),
        auto_now=True,
        help_text=_("When this flag was last updated.")
    )

    class Meta:
        verbose_name = _("Flag")
        verbose_name_plural = _("Flags")
        ordering = ['name']

    def __str__(self):
        return self.name 