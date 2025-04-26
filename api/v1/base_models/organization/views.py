from rest_framework import viewsets, permissions
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
    pagination_class = None  # Usually not needed for short lists 