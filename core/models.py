from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from crum import get_current_user

__all__ = ['Timestamped', 'Auditable', 'TestTimestampedModel', 'TestAuditableModel', 'OrganizationScoped']

User = get_user_model()

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

class Auditable(models.Model):
    """
    Abstract base model providing `created_by` and `updated_by` fields
    linked to the User model, automatically populated on save.
    Relies on middleware like django-crum to set the current user.
    """
    created_by = models.ForeignKey(
        User,
        verbose_name=_("Created by"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
        help_text=_("User who created the record.")
    )
    updated_by = models.ForeignKey(
        User,
        verbose_name=_("Updated by"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated",
        help_text=_("User who last updated the record.")
    )

    class Meta:
        abstract = True
        # Consider ordering if needed, maybe '-updated_at' if used with Timestamped

    def save(self, *args, **kwargs):
        """Override save to set created_by and updated_by."""
        user = get_current_user()
        if user and not user.pk:
            # User object might exist but not be saved yet (e.g., during tests)
            # Or user might be AnonymousUser which doesn't have pk
            user = None

        # Set created_by only on first save (when pk is None)
        if self.pk is None and user:
            self.created_by = user

        # Set updated_by on every save if user is available
        if user:
            self.updated_by = user

        super().save(*args, **kwargs)

class TestAuditableModel(Auditable):
    """
    Concrete model for testing the Auditable abstract base model.
    This model should only be used in tests.
    """
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'core'

class OrganizationScoped(models.Model):
    """
    Abstract base model providing organization scoping.
    """
    organization = models.ForeignKey(
        'api_v1_organization.Organization',  # Use string reference to avoid import
        verbose_name=_("Organization"),
        on_delete=models.PROTECT,  # Or CASCADE if appropriate, but PROTECT is safer
        related_name='%(app_label)s_%(class)s_set',  # Standard pattern
        db_index=True,
        help_text=_("The Organization this record belongs to.")
    )
    class Meta:
        abstract = True 