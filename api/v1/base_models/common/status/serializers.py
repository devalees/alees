from rest_framework import serializers
from .models import Status
from api.v1.base_models.common.category.models import Category
from api.v1.base_models.common.category.serializers import CategorySerializer

class StatusSerializer(serializers.ModelSerializer):
    # Add a nested representation of the category
    category_detail = CategorySerializer(source='category', read_only=True)
    
    # Add a field to handle category selection by slug
    category_slug = serializers.SlugRelatedField(
        source='category',
        slug_field='slug',
        queryset=Category.objects.filter(category_type='OTHER', is_active=True),
        required=False,
        allow_null=True,
        write_only=True
    )
    
    class Meta:
        model = Status
        fields = [
            'slug',
            'name',
            'description',
            'category',
            'category_slug',
            'category_detail',
            'color',
            'custom_fields',
            # Include Timestamped/Auditable fields if needed by API consumers
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
        # Allow CRUD operations - remove read_only_fields
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
            'created_by': {'read_only': True},
            'updated_by': {'read_only': True},
            'category': {'read_only': True},  # Use category_slug for write operations
        } 