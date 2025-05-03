from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import Timestamped # Import Timestamped from core.models
from api.v1.base_models.organization.models import Organization # Import Organization
from .choices import AuditActionType # Import choices from the same app

class AuditLog(Timestamped): # Inherits created_at, updated_at
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("User"),
        on_delete=models.SET_NULL, # Keep log even if user deleted
        null=True, blank=True, db_index=True
    )
    organization = models.ForeignKey(
        Organization,
        verbose_name=_("Organization Context"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        db_index=True
    )
    action_type = models.CharField(
        _("Action Type"), max_length=50, choices=AuditActionType.CHOICES, db_index=True
    )
    # Generic relation to the object acted upon
    content_type = models.ForeignKey(
        ContentType,
        verbose_name=_("Content Type"),
        on_delete=models.SET_NULL, # Keep log even if model type is deleted
        null=True, blank=True, db_index=True
    )
    object_id = models.CharField(
        _("Object ID"), max_length=255, null=True, blank=True, db_index=True,
        help_text=_("Primary key of the object as string.")
    )
    content_object = GenericForeignKey('content_type', 'object_id')

    object_repr = models.CharField(
        _("Object Representation"), max_length=255, blank=True,
        help_text=_("A human-readable representation of the object.")
    )
    changes = models.JSONField(
        _("Changes"), null=True, blank=True, default=None, # Use None default for nullable JSON
        help_text=_("JSON detailing field changes for UPDATE actions (e.g., {'field': {'old': 'val1', 'new': 'val2'}}).")
    )
    context = models.JSONField(
        _("Context"), null=True, blank=True, default=None,
        help_text=_("Additional context (e.g., IP address, session key).")
    )

    class Meta:
        verbose_name = _("Audit Log Entry")
        verbose_name_plural = _("Audit Log Entries")
        ordering = ['-created_at'] # Show newest first
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['organization', 'user']),
            models.Index(fields=['action_type']),
        ]

    def __str__(self):
        action = self.get_action_type_display()
        target = self.object_repr or self.object_id or 'System'
        actor = self.user or 'System'
        return f"{action} on {target} by {actor}"
