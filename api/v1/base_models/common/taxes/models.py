from django.db import models
from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey
from core.models import Timestamped, Auditable


class JurisdictionType:
    COUNTRY = 'COUNTRY'
    STATE_PROVINCE = 'STATE_PROVINCE'  # Avoid slash in code
    COUNTY = 'COUNTY'
    CITY = 'CITY'
    OTHER = 'OTHER'
    CHOICES = [
        (COUNTRY, _('Country')),
        (STATE_PROVINCE, _('State/Province')),
        (COUNTY, _('County')),
        (CITY, _('City')),
        (OTHER, _('Other')),
    ]


class TaxJurisdiction(Timestamped, Auditable, MPTTModel):
    """
    Represents a geographic tax jurisdiction such as a country, state, county, or city.
    Uses MPTT for hierarchical relationships.
    """
    code = models.CharField(
        _("Code"), max_length=50, unique=True, db_index=True, primary_key=True,
        help_text=_("Unique code for the jurisdiction (e.g., 'US', 'US-CA')")
    )
    name = models.CharField(
        _("Name"), max_length=255,
        help_text=_("Name of the jurisdiction (e.g., 'United States', 'California')")
    )
    jurisdiction_type = models.CharField(
        _("Jurisdiction Type"), max_length=20, choices=JurisdictionType.CHOICES, db_index=True,
        help_text=_("Type of jurisdiction (country, state, etc.)")
    )
    parent = TreeForeignKey(
        'self', verbose_name=_("Parent Jurisdiction"),
        on_delete=models.PROTECT, null=True, blank=True, related_name='children', db_index=True,
        help_text=_("Parent jurisdiction (e.g., country for a state)")
    )
    is_active = models.BooleanField(
        _("Is Active"), default=True, db_index=True,
        help_text=_("Whether this jurisdiction is currently active")
    )
    custom_fields = models.JSONField(
        _("Custom Fields"), default=dict, blank=True,
        help_text=_("Additional custom fields for extensibility")
    )

    class MPTTMeta:
        order_insertion_by = ['name']
        parent_attr = 'parent'

    class Meta:
        verbose_name = _("Tax Jurisdiction")
        verbose_name_plural = _("Tax Jurisdictions")
        
    def __str__(self):
        return self.name


class TaxCategory(Timestamped, Auditable):
    """
    Represents a category or type of tax such as GST, VAT, Sales Tax, etc.
    """
    code = models.CharField(
        _("Code"), max_length=50, unique=True, db_index=True,
        help_text=_("Unique code for the tax category (e.g., 'GST', 'VAT')")
    )
    name = models.CharField(
        _("Name"), max_length=255,
        help_text=_("Name of the tax category (e.g., 'Goods and Services Tax')")
    )
    description = models.TextField(
        _("Description"), null=True, blank=True,
        help_text=_("Detailed description of the tax category")
    )
    is_active = models.BooleanField(
        _("Is Active"), default=True, db_index=True,
        help_text=_("Whether this tax category is currently active")
    )

    class Meta:
        verbose_name = _("Tax Category")
        verbose_name_plural = _("Tax Categories")
        
    def __str__(self):
        return self.name


class TaxType:
    """Types of taxes that can be applied."""
    VAT = 'VAT'
    GST = 'GST'
    SALES = 'SALES'
    OTHER = 'OTHER'
    CHOICES = [
        (VAT, _('Value Added Tax')),
        (GST, _('Goods and Services Tax')),
        (SALES, _('Sales Tax')),
        (OTHER, _('Other')),
    ]


class TaxRate(Timestamped, Auditable):
    """
    Represents a specific tax rate applied to a jurisdiction and optionally a tax category.
    Includes validity period and other tax calculation parameters.
    """
    jurisdiction = models.ForeignKey(
        TaxJurisdiction, 
        on_delete=models.CASCADE,
        verbose_name=_("Jurisdiction"),
        help_text=_("The jurisdiction where this tax rate applies")
    )
    tax_category = models.ForeignKey(
        TaxCategory, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name=_("Tax Category"),
        help_text=_("The category of tax (if applicable)")
    )
    name = models.CharField(
        _("Name"), 
        max_length=100, 
        help_text=_("Name of the tax rate (e.g., 'CA State Sales Tax')")
    )
    rate = models.DecimalField(
        _("Rate"), 
        max_digits=10, 
        decimal_places=5, 
        help_text=_("Tax rate as a decimal (e.g., 0.0825 for 8.25%)")
    )
    tax_type = models.CharField(
        _("Tax Type"), 
        max_length=10, 
        choices=TaxType.CHOICES, 
        db_index=True,
        help_text=_("The type of tax (VAT, GST, Sales, etc.)")
    )
    is_compound = models.BooleanField(
        _("Is Compound"), 
        default=False,
        help_text=_("Whether this tax is applied after other taxes")
    )
    priority = models.IntegerField(
        _("Priority"), 
        default=0, 
        help_text=_("Apply lower priorities first for compounding")
    )
    valid_from = models.DateField(
        _("Valid From"), 
        null=True, 
        blank=True, 
        db_index=True,
        help_text=_("Start date when this tax rate is valid")
    )
    valid_to = models.DateField(
        _("Valid To"), 
        null=True, 
        blank=True, 
        db_index=True,
        help_text=_("End date when this tax rate expires")
    )
    is_active = models.BooleanField(
        _("Is Active"), 
        default=True, 
        db_index=True,
        help_text=_("Whether this tax rate is currently active")
    )
    custom_fields = models.JSONField(
        _("Custom Fields"), 
        default=dict, 
        blank=True,
        help_text=_("Additional custom fields for extensibility")
    )

    class Meta:
        verbose_name = _("Tax Rate")
        verbose_name_plural = _("Tax Rates")
        ordering = ['jurisdiction__code', 'priority', '-valid_from']
        indexes = [
            models.Index(fields=['jurisdiction', 'tax_category', 'valid_from', 'valid_to'])
        ]

    def __str__(self):
        if self.name:
            return self.name
        return f"{self.jurisdiction.code} {self.rate * 100:.1f}%" 