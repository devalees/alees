from django.db import models
from django.utils.translation import gettext_lazy as _
# Assuming Timestamped and Auditable are in core.models based on project structure
from core.models import Timestamped, Auditable

class Status(Timestamped, Auditable):
    slug = models.SlugField(
        _("Slug"),
        max_length=50,
        primary_key=True, # Use slug as the stable identifier
        help_text=_("Unique machine-readable identifier (e.g., 'pending_approval').")
    )
    name = models.CharField(
        _("Name"),
        max_length=100,
        unique=True, # Human-readable name should also be unique
        db_index=True,
        help_text=_("Human-readable status name (e.g., 'Pending Approval').")
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Optional description of what this status represents.")
    )
    category = models.CharField(
        _("Category"),
        max_length=50,
        blank=True,
        null=True, # Allow null in the database
        db_index=True,
        help_text=_("Optional category for grouping statuses (e.g., 'General', 'Order Lifecycle').")
    )
    color = models.CharField(
        _("Color"),
        max_length=7, # e.g., #RRGGBB
        blank=True,
        help_text=_("Optional HEX color code for UI representation.")
    )
    custom_fields = models.JSONField(
        _("Custom Fields"),
        default=dict,
        blank=True,
        help_text=_("Custom data associated with this status definition.")
    )

    class Meta:
        verbose_name = _("Status")
        verbose_name_plural = _("Statuses")
        ordering = ['category', 'name']
        # Define the app_label explicitly if the common app is not automatically detected
        # app_label = 'common'

    def __str__(self):
        return self.name 