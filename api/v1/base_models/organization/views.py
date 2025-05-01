from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import OrganizationType
from .serializers import OrganizationTypeSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Prefetch

from api.v1.base_models.organization.models import Organization
from api.v1.base_models.organization.serializers import OrganizationSerializer

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

class OrganizationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing organizations.
    """
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Optimize queryset with select_related and prefetch_related.
        """
        return super().get_queryset().select_related(
            'organization_type',
            'primary_contact',
            'primary_address',
            'currency',
            'parent'
        )

    @action(detail=True, methods=['get'])
    def descendants(self, request, pk=None):
        """
        Get all descendants of an organization.
        """
        organization = self.get_object()
        descendants = organization.get_descendants()
        serializer = self.get_serializer(descendants, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def ancestors(self, request, pk=None):
        """
        Get all ancestors of an organization.
        """
        organization = self.get_object()
        ancestors = organization.get_ancestors()
        serializer = self.get_serializer(ancestors, many=True)
        return Response(serializer.data) 