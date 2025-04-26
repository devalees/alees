from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import OrganizationType
from .serializers import OrganizationTypeSerializer

class OrganizationTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows organization types to be viewed.
    Management is typically done via Admin interface.
    """
    queryset = OrganizationType.objects.all()
    serializer_class = OrganizationTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    ordering = ['name']  # Default ordering
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name']  # Enable filtering by name
    lookup_field = 'name'  # Use name as the lookup field
    # Removed pagination_class = None to use default pagination 