from rest_framework import viewsets, permissions, filters
from .models import Status
from .serializers import StatusSerializer # Use relative import for serializer

class StatusViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint allowing statuses to be viewed.
    Statuses are typically managed via the Admin interface or migrations.
    """
    queryset = Status.objects.all() # Maybe filter is_active=True if added later
    serializer_class = StatusSerializer
    permission_classes = [permissions.AllowAny] # Or IsAuthenticatedOrReadOnly based on policy
    lookup_field = 'slug' # Use slug for retrieval
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['slug', 'name', 'description', 'category']
    ordering_fields = ['category', 'name', 'slug']
    ordering = ['category', 'name'] # Default ordering
    pagination_class = None # List is usually short, no pagination needed by default 