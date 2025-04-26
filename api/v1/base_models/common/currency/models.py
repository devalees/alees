from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class Currency(models.Model):
    # Timestamped fields
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True,
        help_text=_("When this record was created.")
    )
    updated_at = models.DateTimeField(
        _("Updated At"),
        auto_now=True,
        help_text=_("When this record was last updated.")
    )

    # Auditable fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Created By"),
        related_name="%(app_label)s_%(class)s_created",
        on_delete=models.PROTECT,
        help_text=_("User who created this record."),
        null=True,
        blank=True
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Updated By"),
        related_name="%(app_label)s_%(class)s_updated",
        on_delete=models.PROTECT,
        help_text=_("User who last updated this record."),
        null=True,
        blank=True
    )

    # Currency fields
    code = models.CharField(
        _("ISO 4217 Code"),
        max_length=3,
        primary_key=True,
        help_text=_("ISO 4217 3-letter currency code.")
    )
    name = models.CharField(
        _("Name"),
        max_length=100,
        unique=True,
        db_index=True,
        help_text=_("Official name of the currency.")
    )
    symbol = models.CharField(
        _("Symbol"),
        max_length=5,
        blank=True,  # Some currencies might not have a common symbol
        help_text=_("Common symbol for the currency (e.g., $, €).")
    )
    numeric_code = models.CharField(
        _("ISO 4217 Numeric Code"),
        max_length=3,
        unique=True,
        null=True,  # Allow null as not all might have it / be known
        blank=True,
        db_index=True,
        help_text=_("ISO 4217 3-digit numeric currency code.")
    )
    decimal_places = models.PositiveSmallIntegerField(
        _("Decimal Places"),
        default=2,
        help_text=_("Number of decimal places commonly used.")
    )
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        db_index=True,
        help_text=_("Is this currency available for use?")
    )
    custom_fields = models.JSONField(
        _("Custom Fields"),
        default=dict,
        blank=True,
        help_text=_("Custom data associated with this currency.")
    )

    class Meta:
        app_label = 'api_v1_currency'
        verbose_name = _("Currency")
        verbose_name_plural = _("Currencies")
        ordering = ['code']

    def __str__(self):
        return self.code
