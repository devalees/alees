"""
Serializers for product models.
"""
import logging
from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from core.serializers.mixins import OrganizationScopedSerializerMixin
from api.v1.base_models.common.category.models import Category
from api.v1.base_models.common.uom.models import UnitOfMeasure
from core.rbac.utils import get_user_request_context
from .models import Product

logger = logging.getLogger(__name__)


class ProductSerializer(OrganizationScopedSerializerMixin, TaggitSerializer, serializers.ModelSerializer):
    """
    Serializer for Product model with organization scoping.
    
    Inherits from OrganizationScopedSerializerMixin to automatically handle
    organization context for users.
    """
    tags = TagListSerializerField(required=False)
    
    # Use PrimaryKeyRelatedField with querysets that respect constraints
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(category_type='PRODUCT'),
        allow_null=True, 
        required=False
    )
    
    base_uom = serializers.PrimaryKeyRelatedField(
        queryset=UnitOfMeasure.objects.all(),
        pk_field=serializers.CharField()
    )
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'description', 'product_type',
            'category', 'status', 'base_uom',
            'is_inventory_tracked', 'is_purchasable', 'is_sellable',
            'tags', 'attributes', 'custom_fields',
            'organization', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        """
        Create a new Product instance.
        
        Handles the organization context and tags, respecting any explicitly passed
        organization parameter.
        """
        # Get tags data before removing it from validated_data
        tags_data = None
        if 'tags' in validated_data:
            tags_data = validated_data.pop('tags')
        
        # Log validated data for debugging
        logger.debug("Creating product with validated data: %s", validated_data)
        
        # Check if organization isn't already set 
        if 'organization' not in validated_data and 'organization_id' not in validated_data:
            # Get user from request context
            request = self.context.get('request')
            if request and hasattr(request, 'user'):
                user = request.user
                # Get organization context
                active_org_ids, is_single_org = get_user_request_context(user)
                if is_single_org and active_org_ids:
                    validated_data['organization_id'] = active_org_ids[0]
                    logger.debug("Setting organization_id to %s for single-org user", active_org_ids[0])
        
        # Create the product with organization set
        product = Product.objects.create(**validated_data)
        
        # Add tags if provided
        if tags_data:
            product.tags.add(*tags_data)
        
        return product
    
    def validate_custom_fields(self, value):
        """Validate custom fields format if needed."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Custom fields must be a dictionary")
        return value
    
    def validate_sku(self, value):
        """Validate SKU format if needed."""
        # Example: ensure SKU is uppercase
        return value.upper() 