from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from taggit.managers import TaggableManager

from core.models import Timestamped, Auditable, OrganizationScoped
from api.v1.base_models.common.fileStorage.models import FileStorage
from api.v1.base_models.common.category.models import Category


class DocumentStatus:
    """Status choices for Document model."""
    DRAFT = 'draft'
    ACTIVE = 'active'
    ARCHIVED = 'archived'
    PENDING_REVIEW = 'pending_review'
    
    CHOICES = [
        (DRAFT, _('Draft')),
        (ACTIVE, _('Active')),
        (ARCHIVED, _('Archived')),
        (PENDING_REVIEW, _('Pending Review')),
    ]


class Document(OrganizationScoped, Timestamped, Auditable):
    """
    Model representing logical documents, linking metadata to a FileStorage record.
    Uses GenericForeignKey for linking to other business entities.
    Scoped by Organization. Includes tagging.
    """
    title = models.CharField(
        _("Title"), 
        max_length=255, 
        db_index=True,
        help_text=_("Primary display name or title of the document.")
    )
    document_type = models.ForeignKey(
        Category,
        verbose_name=_("Document Type"),
        related_name='typed_documents',
        on_delete=models.PROTECT,
        limit_choices_to={'category_type': 'DOCUMENT_TYPE'}, 
        null=True, 
        blank=True,
        help_text=_("Classification using the generic Category model.")
    )
    status = models.CharField(
        _("Status"), 
        max_length=50, 
        choices=DocumentStatus.CHOICES,
        default=DocumentStatus.DRAFT, 
        db_index=True,
        help_text=_("Status of the document.")
    )
    # Link to the actual file stored
    file = models.ForeignKey(
        FileStorage,
        verbose_name=_("File"),
        on_delete=models.PROTECT,
        related_name='documents',
        help_text=_("Links to the metadata record of the actual underlying file content.")
    )
    version = models.PositiveIntegerField(
        _("Version"), 
        default=1,
        help_text=_("Simple integer representing the document version number.")
    )
    description = models.TextField(
        _("Description"), 
        blank=True,
        help_text=_("Optional description or summary.")
    )
    tags = TaggableManager(
        blank=True, 
        verbose_name=_("Tags"),
        help_text=_("For flexible classification.")
    )
    custom_fields = models.JSONField(
        _("Custom Fields"), 
        default=dict, 
        blank=True,
        help_text=_("Stores values for dynamically defined custom fields relevant to the document.")
    )

    # Generic relation to parent object (e.g., Invoice, Project, Organization)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True, 
        blank=True,
        verbose_name=_("Related Object Type"),
        help_text=_("Content type of the related business entity.")
    )
    object_id = models.CharField(
        _("Related Object ID"), 
        max_length=255,
        null=True, 
        blank=True, 
        db_index=True,
        help_text=_("ID of the related business entity.")
    )
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=["document_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["content_type", "object_id"]), # For GFK lookup
        ]
        permissions = [
            ('can_version_document', _('Can create new versions of a document')),
        ]

    def __str__(self):
        return f"{self.title} (v{self.version})" 