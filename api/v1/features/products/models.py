"""
Product models for the products app.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager
from core.models import Timestamped, Auditable, OrganizationScoped


class ProductType(models.TextChoices):
    """Types of products."""
    PHYSICAL = 'PHYSICAL', _('Physical Product')
    SERVICE = 'SERVICE', _('Service')
    DIGITAL = 'DIGITAL', _('Digital Product')
    SUBSCRIPTION = 'SUBSCRIPTION', _('Subscription')


class ProductStatus(models.TextChoices):
    """Status of products."""
    ACTIVE = 'ACTIVE', _('Active')
    DRAFT = 'DRAFT', _('Draft')
    ARCHIVED = 'ARCHIVED', _('Archived')
    DISCONTINUED = 'DISCONTINUED', _('Discontinued')


class Product(OrganizationScoped, Timestamped, Auditable):
    """
    Product model - Central catalog item.
    
    Products represent items or services that can be purchased, sold, or tracked.
    They are organization-scoped and can be tagged.
    """
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    product_type = models.CharField(
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.PHYSICAL,
    )
    
    category = models.ForeignKey(
        'api_v1_category.Category',
        on_delete=models.SET_NULL,
        related_name='products',
        null=True,
        blank=True,
        limit_choices_to={'category_type': 'PRODUCT'},
    )
    
    status = models.CharField(
        max_length=20,
        choices=ProductStatus.choices,
        default=ProductStatus.DRAFT,
    )
    
    base_uom = models.ForeignKey(
        'api_v1_common.UnitOfMeasure',
        on_delete=models.PROTECT,
        related_name='products',
    )
    
    is_inventory_tracked = models.BooleanField(default=False)
    is_purchasable = models.BooleanField(default=False)
    is_sellable = models.BooleanField(default=False)
    
    # Using JSONField for flexible attributes and custom fields
    attributes = models.JSONField(blank=True, default=dict)
    custom_fields = models.JSONField(blank=True, default=dict)
    
    # Tagging support
    tags = TaggableManager(blank=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['organization', 'sku']
        permissions = [
            # Custom permissions can be added here
        ]
    
    def __str__(self):
        return f"{self.sku} - {self.name}" 