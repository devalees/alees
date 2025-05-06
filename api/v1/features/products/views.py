"""
ViewSets for product models.
"""
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from core.viewsets.mixins import OrganizationScopedViewSetMixin
from core.rbac.drf_permissions import HasModelPermissionInOrg
from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """
    Organization-aware ViewSet for Product model.
    
    Inherits from OrganizationScopedViewSetMixin to ensure that users can only
    access products from organizations they are members of, and have the appropriate
    permissions in those organizations.
    """
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related(
        'organization', 'category', 'base_uom'
    ).prefetch_related('tags').all()
    
    # Use HasModelPermissionInOrg to check permissions in organization context
    permission_classes = [permissions.IsAuthenticated, HasModelPermissionInOrg]
    
    # Filtering and searching
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = {
        'product_type': ['exact'],
        'status': ['exact'],
        'category': ['exact'],
        'is_inventory_tracked': ['exact'],
        'is_purchasable': ['exact'],
        'is_sellable': ['exact'],
        'created_at': ['gte', 'lte'],
        'updated_at': ['gte', 'lte'],
    }
    search_fields = ['name', 'sku', 'description']
    ordering_fields = [
        'name', 'sku', 'product_type', 'status', 
        'created_at', 'updated_at'
    ]
    ordering = ['name'] 