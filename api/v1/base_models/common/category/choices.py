from django.db import models
from django.utils.translation import gettext_lazy as _


class CategoryType(models.TextChoices):
    PRODUCT = 'PRODUCT', _('Product Category')
    DOCUMENT_TYPE = 'DOCUMENT_TYPE', _('Document Type')
    ASSET_TYPE = 'ASSET_TYPE', _('Asset Type')
    ORG_COST_CENTER = 'ORG_COST_CENTER', _('Org/Cost Center')
    OTHER = 'OTHER', _('Other') 