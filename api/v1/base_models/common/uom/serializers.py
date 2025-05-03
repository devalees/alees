from rest_framework import serializers

from .models import UomType, UnitOfMeasure

__all__ = ['UomTypeSerializer', 'UnitOfMeasureSerializer']


class UomTypeSerializer(serializers.ModelSerializer):
    """Serializer for the UomType model (Read-Only)."""
    class Meta:
        model = UomType
        fields = [
            'code',
            'name',
            'description',
            'is_active',
            'custom_fields',
            # Add audit fields if needed for display, mark read_only
            # 'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        # Since this is intended as ReadOnly via ViewSet, mark all as read_only
        read_only_fields = fields


class UnitOfMeasureSerializer(serializers.ModelSerializer):
    """Serializer for the UnitOfMeasure model (Read-Only)."""

    # DRF automatically handles nested serialization with depth
    # uom_type = UomTypeSerializer(read_only=True) # Use explicit serializer for more control if needed

    class Meta:
        model = UnitOfMeasure
        fields = [
            'code',
            'name',
            'uom_type', # This will now show nested data due to depth=1
            'symbol',
            'is_active',
            'custom_fields',
        ]
        read_only_fields = (
            'code',
            'name',
            'symbol',
            'is_active',
            'custom_fields',
            'uom_type',
        )
        depth = 1 # Automatically nest related fields one level deep

    # Keep custom validation, but simplify access to uom_type for read-only context
    # This validation will primarily be useful if the serializer is reused for writes later.
    def validate_custom_fields(self, value):
        """Validate the custom_fields based on UomType."""
        uom_type_code = None
        # For read/representation context, the instance is available
        if self.instance and self.instance.uom_type:
            uom_type_code = self.instance.uom_type.code
        # If used for writing (which it currently isn't set up for easily),
        # accessing initial_data would be needed, but let's focus on read context.

        # --- Apply Validation Rules ---
        # Example Rule: If type is MASS, require 'required_prop' key
        if uom_type_code == 'MASS' and 'required_prop' not in value:
            # In a read-only context, this validation might not be strictly necessary,
            # but we keep the logic for potential future use or data integrity checks.
            # Depending on requirements, you might raise an error or just log a warning.
            print(f"Warning: Custom field 'required_prop' is missing for MASS unit '{self.instance.code if self.instance else 'N/A'}'.")
            # raise serializers.ValidationError(
            #     "Custom field 'required_prop' is required for units with type 'MASS'."
            # )

        # Add other validation rules as needed...

        return value 