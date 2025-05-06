from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import UomType, UnitOfMeasure
from .serializers import UomTypeSerializer, UnitOfMeasureSerializer
from core.rbac.drf_permissions import HasGeneralModelPermission

__all__ = ['UomTypeViewSet', 'UnitOfMeasureViewSet']


class UomTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows UoM Types to be viewed.
    Provides read-only access, filtering by search, and ordering.
    Uses general permissions without organization requirements.
    Lookup is performed by the 'code' field.
    """
    queryset = UomType.objects.filter(is_active=True)
    serializer_class = UomTypeSerializer
    permission_classes = [HasGeneralModelPermission]
    lookup_field = 'code' # Use code (PK) for detail view lookup
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name', 'description'] # Fields to search against
    ordering_fields = ['name', 'code'] # Allow ordering by name or code
    ordering = ['name'] # Default ordering


class UnitOfMeasureViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows Units of Measure to be viewed.
    Provides read-only access, filtering by UoM Type code and search, plus ordering.
    Uses general permissions without organization requirements.
    Lookup is performed by the 'code' field.
    Optimizes queryset using select_related for uom_type.
    """
    # Optimize by selecting related uom_type to avoid N+1 queries in serializer
    queryset = UnitOfMeasure.objects.filter(is_active=True).select_related('uom_type')
    serializer_class = UnitOfMeasureSerializer
    permission_classes = [HasGeneralModelPermission]
    lookup_field = 'code' # Use code (PK) for detail view lookup
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'uom_type__code': ['exact'], # Allow exact filtering on type code e.g., /uoms/?uom_type__code=LENGTH
        # Add other filterable fields if needed
        # 'is_active': ['exact'],
    }
    search_fields = [
        'code', 'name', 'symbol',
        'uom_type__code', 'uom_type__name' # Allow searching by related type fields
    ]
    ordering_fields = ['uom_type__name', 'name', 'code'] # Allow ordering
    ordering = ['uom_type__name', 'name'] # Default ordering by type, then name