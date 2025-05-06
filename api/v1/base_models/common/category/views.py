# api/v1/base_models/common/category/views.py
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Category
from .serializers import CategorySerializer
# Import DRF's standard permissions since Category is not org-scoped
from rest_framework.permissions import IsAuthenticatedOrReadOnly


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Categories.
    
    NOTE: Category is a general-purpose model that is NOT organization-scoped.
    It uses Django's standard permission system instead of the organization-scoped RBAC.
    """
    serializer_class = CategorySerializer
    # Use IsAuthenticatedOrReadOnly to allow read access for anyone and write access for authenticated users
    permission_classes = [IsAuthenticatedOrReadOnly]
    # Default queryset: Show only active categories
    queryset = Category.objects.filter(is_active=True).prefetch_related('children') # Prefetch for efficiency
    lookup_field = 'slug' # Use slug in URL for detail view

    # Filtering, Searching, Ordering
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = {
        'category_type': ['exact', 'in'],
        'parent__slug': ['exact', 'isnull'], # Filter by parent slug or root nodes
        'level': ['exact', 'gte', 'lte'],
    }
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['name', 'lft', 'tree_id'] # Allow ordering by name or tree structure
    ordering = ['tree_id', 'lft'] # Default ordering by MPTT structure

    # Example custom action (implementation needs refinement)
    # @action(detail=False, methods=['get'], url_path='tree/(?P<type>[^/.]+)')
    # def get_tree_by_type(self, request, type=None):
    #     """Retrieve the full category tree for a specific type."""
    #     queryset = self.get_queryset().filter(category_type=type, level=0) # Start from root nodes
    #     # Need a recursive serializer or manual tree building logic here
    #     # serializer = RecursiveCategorySerializer(queryset, many=True, context=self.get_serializer_context())
    #     # return Response(serializer.data)
    #     return Response({"message": "Tree retrieval not fully implemented yet."}, status=501)

    def perform_create(self, serializer):
        """Automatically set the created_by user."""
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        """Automatically set the updated_by user."""
        serializer.save(updated_by=self.request.user) 