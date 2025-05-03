from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey
from core.models import Timestamped, Auditable # Assuming this path is correct
from .choices import CategoryType # Import from local choices file


class Category(Timestamped, Auditable, MPTTModel):
    name = models.CharField(
        _("Name"), max_length=255, db_index=True
    )
    slug = models.SlugField(
        _("Slug"), max_length=255, unique=True, blank=True,
        help_text=_("Unique URL-friendly identifier. Auto-generated if blank.")
    )
    description = models.TextField(_("Description"), blank=True)
    parent = TreeForeignKey(
        'self',
        verbose_name=_("Parent Category"),
        on_delete=models.CASCADE, # Or PROTECT if children should prevent deletion
        null=True, blank=True, related_name='children', db_index=True
    )
    category_type = models.CharField(
        _("Category Type"), max_length=50, choices=CategoryType.choices, db_index=True,
        help_text=_("The type of entity this category classifies.")
    )
    is_active = models.BooleanField(
        _("Is Active"), default=True, db_index=True
    )
    custom_fields = models.JSONField(
        _("Custom Fields"), default=dict, blank=True
    )

    class MPTTMeta:
        order_insertion_by = ['name']
        parent_attr = 'parent'

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        unique_together = ('parent', 'name', 'category_type')
        ordering = ['tree_id', 'lft'] # MPTT default

    def __str__(self):
        # Example showing hierarchy in string representation
        prefix = '---' * self.get_level()
        return f"{prefix} {self.name}".strip() if prefix else self.name

    def save(self, *args, **kwargs):
        # Auto-populate slug if blank
        if not self.slug:
            self.slug = slugify(self.name)
            # TODO: Handle potential slug collisions if slug is unique
            # Simple approach: Check existence and append count (not robust for high concurrency)
            # More robust: Use django-autoslug or a library that handles this transactionally.
            # For now, rely on DB unique constraint to raise error on collision.
        super().save(*args, **kwargs) 