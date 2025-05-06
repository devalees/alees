from rest_framework import viewsets, permissions, filters
from .models import Status
from .serializers import StatusSerializer # Use relative import for serializer

class StatusViewSet(viewsets.ModelViewSet):
    """
    API endpoint allowing statuses to be viewed and edited.
    
    Statuses can be created, retrieved, updated, and deleted through this endpoint.
    Anonymous users can only view statuses, while authenticated users can perform
    all CRUD operations.
    """
    queryset = Status.objects.all()
    serializer_class = StatusSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['slug', 'name', 'description', 'category__name']
    ordering_fields = ['name', 'slug', 'category__name']
    ordering = ['category__name', 'name'] # Default ordering
    pagination_class = None # List is usually short, no pagination needed by default 