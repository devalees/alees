from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django.utils.translation import gettext_lazy as _

from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the Category model.
    
    This serializer is for a general-purpose model that is NOT organization-scoped.
    It does not include or require an organization field.
    """

    # Use SlugRelatedField for parent representation and lookup during create/update
    parent_slug = serializers.SlugRelatedField(
        slug_field='slug',
        source='parent', # Link this to the 'parent' model field
        queryset=Category.objects.all(),
        required=False,
        allow_null=True,
        help_text=_("Slug of the parent category. Null for root categories.")
    )

    # Optionally include children count or other computed fields for read operations
    # children_count = serializers.IntegerField(source='get_children.count', read_only=True)

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug',
            'description',
            'parent_slug',
            'category_type', 'is_active',
            'custom_fields',
            'lft', 'rght', 'tree_id', 'level', # MPTT fields (useful for clients)
            # 'children_count', # Example computed field
            'created_at', 'updated_at',
            'created_by', 'updated_by' # Include audit fields (read-only)
        ]
        read_only_fields = (
            'id', 'lft', 'rght', 'tree_id', 'level',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        )
        # extra_kwargs removed for parent
        validators = [
            UniqueTogetherValidator(
                queryset=Category.objects.all(),
                # Revert to using serializer field names
                fields=('parent_slug', 'name', 'category_type'),
                message=_("A category with this name and parent already exists for this type.")
            )
        ]

    def validate_custom_fields(self, value):
        """Perform basic validation that custom_fields is a dict."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(_("Custom fields must be a valid JSON object."))
        return value

    def update(self, instance, validated_data):
        """Handle parent update specifically before calling model save."""
        # Check if 'parent' exists in validated_data (set by parent_slug field)
        parent = validated_data.get('parent', None)
        parent_was_validated = 'parent' in validated_data

        # Remove parent from validated_data before calling super().update,
        # as super().update might call instance.save() which triggers MPTT
        # before we have a chance to set the parent correctly.
        if parent_was_validated:
            validated_data.pop('parent')

        # Update other fields using ModelSerializer's logic but *without* saving yet
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Now, explicitly set the parent if it was provided in the update data
        if parent_was_validated:
            instance.parent = parent

        # Finally, save the instance once all fields (including parent) are set
        instance.save()
        instance.refresh_from_db()
        return instance

    # Optional: Add validation logic (e.g., parent type consistency)
    # def validate(self, data):
    #     """Ensure parent has the same category_type if set."""
    #     parent = data.get('parent')
    #     category_type = data.get('category_type', getattr(self.instance, 'category_type', None))
    #     if parent and parent.category_type != category_type:
    #         raise serializers.ValidationError({
    #             'parent': _("Parent category must be of the same type.")
    #         })
    #     return data 