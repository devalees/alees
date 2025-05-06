from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import Timestamped, Auditable # Import base models

# Create __all__ for explicit export
__all__ = ['UomType', 'UnitOfMeasure']

class UomType(Timestamped, Auditable):
    """
    Represents a classification or type of Unit of Measure (e.g., Length, Mass, Count).
    """
    code = models.CharField(
        _("Code"),
        max_length=50,
        primary_key=True,
        help_text=_("Unique code for the UoM Type (e.g., LENGTH, MASS).")
    )
    name = models.CharField(
        _("Name"),
        max_length=100,
        unique=True,
        db_index=True,
        help_text=_("Human-readable name (e.g., Length, Mass).")
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Optional description of the UoM type.") # Added help text
    )
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        db_index=True,
        help_text=_("Indicates if this UoM type is currently active and usable.") # Added help text
    )
    custom_fields = models.JSONField(
        _("Custom Fields"),
        default=dict,
        blank=True,
        help_text=_("Custom attributes for this UoM type.") # Added help text
    )

    class Meta:
        verbose_name = _("Unit of Measure Type")
        verbose_name_plural = _("Unit of Measure Types")
        ordering = ['name']
        # Define app_label if needed, assuming 'common' or similar based on path
        # app_label = 'common_uom' # Example if registered separately

    def __str__(self):
        """Return the human-readable name of the UoM type."""
        return self.name 

class UnitOfMeasure(Timestamped, Auditable):
    """
    Represents a specific Unit of Measure (e.g., Meter, Kilogram, Each)
    belonging to a specific UomType.
    """
    code = models.CharField(
        _("Code"),
        max_length=20,
        primary_key=True,
        help_text=_("Unique code for the unit (e.g., KG, M, EA, BOX_12).")
    )
    name = models.CharField(
        _("Name"),
        max_length=100,
        unique=True,
        db_index=True,
        help_text=_("Full name of the unit (e.g., Kilogram, Meter, Each).")
    )
    uom_type = models.ForeignKey(
        UomType, # Link to the UomType model
        verbose_name=_("Type"),
        related_name='units',
        on_delete=models.PROTECT, # Prevent deleting UomType if Units exist
        help_text=_("Category of measurement (e.g., Length, Mass, Count).")
    )
    symbol = models.CharField(
        _("Symbol"),
        max_length=10,
        blank=True,
        help_text=_("Common symbol (e.g., kg, m, L).")
    )
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        db_index=True,
        help_text=_("Indicates if this unit is currently active and usable.") # Added help text
    )
    custom_fields = models.JSONField(
        _("Custom Fields"),
        default=dict,
        blank=True,
        help_text=_("Custom attributes for this unit.") # Added help text
    )

    class Meta:
        verbose_name = _("Unit of Measure")
        verbose_name_plural = _("Units of Measure")
        ordering = ['uom_type__name', 'name'] # Order by type name, then unit name
        # app_label = 'common_uom' # Example if registered separately

    def __str__(self):
        """Return the human-readable name of the unit."""
        return self.name