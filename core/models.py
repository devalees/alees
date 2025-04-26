from core.flags.models import Flag
from django.db import models
from django.utils.translation import gettext_lazy as _

__all__ = ['Flag', 'Timestamped', 'TestTimestampedModel']

class Timestamped(models.Model):
    """
    Abstract base model providing self-updating `created_at` and `updated_at` fields.
    """
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True,
        editable=False,
        help_text=_("Timestamp when the record was created.")
    )
    updated_at = models.DateTimeField(
        _("Updated At"),
        auto_now=True,
        editable=False,
        help_text=_("Timestamp when the record was last updated.")
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']  # Default ordering for inheriting models

class TestTimestampedModel(Timestamped):
    """
    Concrete model for testing the Timestamped abstract base model.
    This model should only be used in tests.
    """
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'core' 