from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter
from django_filters import filters as django_filters
from taggit.managers import TaggableManager
from .models import OrganizationType, Organization
from .serializers import OrganizationTypeSerializer, OrganizationSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Prefetch
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from api.v1.base_models.organization.models import OrganizationMembership
from api.v1.base_models.organization.serializers import OrganizationMembershipSerializer

class OrganizationFilter(FilterSet):
    """
    Custom filter set for Organization model.
    """
    tags = CharFilter(method='filter_tags')

    def filter_tags(self, queryset, name, value):
        if value:
            return queryset.filter(tags__name__in=[value])
        return queryset

    class Meta:
        model = Organization
        fields = {
            'organization_type': ['exact'],
            'status': ['exact'],
            'parent': ['exact'],
            'tags': ['exact'],
        }

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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = OrganizationFilter
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code', 'status', 'created_at']
    ordering = ['name']  # Default ordering

    def get_permissions(self):
        """
        Add model-level permissions based on the action.
        """
        if self.action == 'list':
            permission = 'organization.view_organization'
        elif self.action == 'retrieve':
            permission = 'organization.view_organization'
        elif self.action == 'create':
            permission = 'organization.add_organization'
        elif self.action in ['update', 'partial_update']:
            permission = 'organization.change_organization'
        elif self.action == 'destroy':
            permission = 'organization.delete_organization'
        else:
            permission = None

        if permission:
            return [permissions.IsAuthenticated(), permissions.DjangoModelPermissions()]
        return [permissions.IsAuthenticated()]

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
        ).prefetch_related('tags')

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

class OrganizationMembershipFilter(FilterSet):
    """Filter set for OrganizationMembership"""
    class Meta:
        model = OrganizationMembership
        fields = {
            'user': ['exact'],
            'organization': ['exact'],
            'role': ['exact'],
            'is_active': ['exact'],
        }

class IsAdminOrReadOwnMemberships(permissions.BasePermission):
    """Custom permission to only allow admins to perform all actions and users to read their own memberships"""

    def has_permission(self, request, view):
        # Allow admins full access
        if request.user.is_staff:
            return True

        # Allow users to list their own memberships
        if request.method == 'GET' and request.query_params.get('user') == str(request.user.id):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # Allow admins full access
        if request.user.is_staff:
            return True

        # Allow users to view their own memberships
        if request.method in permissions.SAFE_METHODS and obj.user == request.user:
            return True

        return False

class OrganizationMembershipViewSet(viewsets.ModelViewSet):
    """ViewSet for OrganizationMembership model"""
    
    queryset = OrganizationMembership.objects.all()
    serializer_class = OrganizationMembershipSerializer
    permission_classes = [IsAdminOrReadOwnMemberships]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = OrganizationMembershipFilter
    search_fields = ['user__username', 'organization__name', 'role__name']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        """Set created_by and updated_by to the current user"""
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        """Set updated_by to the current user"""
        serializer.save(updated_by=self.request.user) 