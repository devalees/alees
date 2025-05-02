import os
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from taggit.managers import TaggableManager

from core.models import Timestamped, Auditable, OrganizationScoped


def get_file_upload_path(instance, filename):
    """Generates a unique path for uploaded files based on organization and UUID."""
    # Extract file extension
    ext = filename.split('.')[-1]
    # Generate a unique filename using UUID
    unique_filename = f"{uuid.uuid4()}.{ext}"
    # Return the path within the organization's folder
    # Ensure instance.organization is set before calling this during save
    org_id = getattr(instance.organization, 'id', 'misc') # Handle cases where org might not be set yet
    return os.path.join(f'org_{org_id}', 'files', unique_filename)


class FileStorage(Timestamped, Auditable, OrganizationScoped):
    """Model to store metadata about uploaded files."""
    file = models.FileField(
        _("File"),
        upload_to=get_file_upload_path,
        help_text=_("The actual stored file.")
    )
    original_filename = models.CharField(
        _("Original Filename"),
        max_length=255,
        db_index=True,
        help_text=_("Filename as it was originally uploaded.")
    )
    file_size = models.PositiveBigIntegerField(
        _("File Size (bytes)"),
        null=True,
        blank=True, # Allow blank as it's populated post-upload
        help_text=_("Size of the file in bytes.")
    )
    mime_type = models.CharField(
        _("MIME Type"),
        max_length=100,
        blank=True,
        db_index=True,
        help_text=_("Detected MIME type of the file.")
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Uploaded By"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True, # Allow blank temporarily during initial save by system?
        related_name='uploaded_files',
        help_text=_("User who uploaded the file.")
    )
    tags = TaggableManager(
        verbose_name=_("Tags"),
        blank=True,
        help_text=_("Tags associated with the file.")
    )
    custom_fields = models.JSONField(
        _("Custom Fields"),
        default=dict,
        blank=True,
        help_text=_("Custom metadata associated with the file.")
    )

    class Meta:
        verbose_name = _("File Storage Record")
        verbose_name_plural = _("File Storage Records")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization'], name='file_storage_organiz_idx'),
            models.Index(fields=['uploaded_by'], name='file_storage_upl_by_idx'),
            models.Index(fields=['mime_type'], name='file_storage_mime_idx'),
            models.Index(fields=['original_filename'], name='file_storage_orig_fname_idx'),
        ]

    def __str__(self):
        return self.original_filename

    @property
    def filename(self):
        """Returns the basename of the stored file path."""
        if self.file:
            try:
                return os.path.basename(self.file.name)
            except Exception:
                 return None # Handle cases where file.name might be invalid
        return None

    def get_secure_url(self, requesting_user):
        """Placeholder for returning a secure URL after permission checks.

        Permission logic will be implemented primarily in serializers/views.
        This method currently returns the standard URL if the file exists.
        Requires the `requesting_user` parameter for future permission checks.
        """
        # TODO: Implement permission check logic here or confirm it's handled
        # solely in serializer/view based on final design.
        # Example check (needs RBAC function):
        # if has_perm_in_org(requesting_user, 'common.view_filestorage', self.organization):
        #     if self.file:
        #         try: return self.file.url
        #         except ValueError: return None
        # return None

        # Placeholder implementation (returns URL if file exists):
        if self.file:
            try:
                return self.file.url
            except ValueError:
                # Handle cases where storage backend is misconfigured or file not saved.
                return None
        return None

    def save(self, *args, **kwargs):
        # Attempt to populate file size automatically if not set
        # This is basic; more robust handling might be in forms/serializers/signals
        if self.file and not self.file_size:
             try:
                 self.file_size = self.file.size
             except Exception:
                 # Could log this error. File might not be accessible yet.
                 pass

        # TODO: Consider adding logic to auto-detect mime_type if needed,
        # potentially using python-magic (requires dependency).

        super().save(*args, **kwargs)

    # Optional: Add a clean method for validations run before saving
    # def clean(self):
    #     super().clean()
    #     if self.file_size is not None and settings.MAX_UPLOAD_SIZE is not None:
    #          if self.file_size > settings.MAX_UPLOAD_SIZE:
    #               raise ValidationError({
    #                   'file_size': _('File size exceeds the allowed limit of {limit}.').format(
    #                       limit=settings.MAX_UPLOAD_SIZE # Add human-readable format here
    #                   )
    #               }) 