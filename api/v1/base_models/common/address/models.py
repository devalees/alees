from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from core.models import Timestamped, Auditable


class Address(Timestamped, Auditable):
    """
    Model representing a physical postal address.

    Architectural Note:
    ------------------
    Addresses are managed as nested objects within their parent entities (e.g., Organization, UserProfile)
    rather than through standalone endpoints. This approach:
    1. Maintains data integrity by preventing orphaned addresses
    2. Ensures addresses are always associated with a parent entity
    3. Simplifies API design by reducing the number of endpoints
    4. Better represents real-world relationships where addresses belong to entities

    If standalone address management becomes necessary in the future, a ViewSet and URLs can be added.
    See the implementation steps document for more details.
    """

    street_address_1 = models.CharField(
        _("Street Address 1"),
        max_length=255,
        help_text=_("Primary street address line."),
    )
    street_address_2 = models.CharField(
        _("Street Address 2"),
        max_length=255,
        blank=True,
        help_text=_("Secondary street address line (e.g., apartment, suite)."),
    )
    city = models.CharField(
        _("City"), max_length=100, db_index=True, help_text=_("City or locality name.")
    )
    state_province = models.CharField(
        _("State/Province/Region"),
        max_length=100,
        blank=True,
        db_index=True,
        help_text=_("State, province, or region name."),
    )
    postal_code = models.CharField(
        _("Postal/ZIP Code"),
        max_length=20,
        blank=True,
        db_index=True,
        help_text=_("Postal or ZIP code."),
    )
    country = CountryField(
        _("Country"), db_index=True, help_text=_("ISO 3166-1 alpha-2 country code.")
    )
    latitude = models.DecimalField(
        _("Latitude"),
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text=_("Geographic latitude coordinate."),
    )
    longitude = models.DecimalField(
        _("Longitude"),
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text=_("Geographic longitude coordinate."),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        blank=True,
        default="Active",
        db_index=True,
        help_text=_("Current status of the address (e.g., Active, Inactive)."),
    )
    custom_fields = models.JSONField(
        _("Custom Fields"),
        default=dict,
        blank=True,
        help_text=_("Additional custom fields as JSON data."),
    )

    class Meta:
        verbose_name = _("Address")
        verbose_name_plural = _("Addresses")
        indexes = [
            models.Index(fields=["country", "postal_code"]),
        ]

    def __str__(self):
        """Return a string representation of the address."""
        parts = [self.street_address_1, self.city, str(self.country)]
        return ", ".join(filter(None, parts))
