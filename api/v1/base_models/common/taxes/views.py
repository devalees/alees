from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import TaxJurisdiction, TaxCategory, TaxRate
from .serializers import TaxJurisdictionSerializer, TaxCategorySerializer, TaxRateSerializer


class TaxJurisdictionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TaxJurisdiction model.
    
    Provides CRUD operations with appropriate permission checks.
    Uses Django's standard model permissions system.
    """
    queryset = TaxJurisdiction.objects.all()
    serializer_class = TaxJurisdictionSerializer
    permission_classes = [permissions.DjangoModelPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['jurisdiction_type', 'is_active', 'parent']
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name', 'jurisdiction_type']


class TaxCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TaxCategory model.
    
    Provides CRUD operations with appropriate permission checks.
    Uses Django's standard model permissions system.
    """
    queryset = TaxCategory.objects.all()
    serializer_class = TaxCategorySerializer
    permission_classes = [permissions.DjangoModelPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['code', 'name']


class TaxRateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TaxRate model.
    
    Provides CRUD operations with appropriate permission checks.
    Uses Django's standard model permissions system.
    """
    queryset = TaxRate.objects.select_related('jurisdiction', 'tax_category').all()
    serializer_class = TaxRateSerializer
    permission_classes = [permissions.DjangoModelPermissions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['jurisdiction__code', 'tax_category__code', 'tax_type', 'is_active']
    search_fields = ['name', 'jurisdiction__name', 'tax_category__name']
    ordering_fields = ['jurisdiction__code', 'priority', 'valid_from', 'rate', 'name'] 