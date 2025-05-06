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
from core.rbac.utils import get_user_request_context
from core.rbac.drf_permissions import HasModelPermissionInOrg
from core.rbac.permissions import has_perm_in_org
from rest_framework.exceptions import PermissionDenied, ValidationError
import logging

logger = logging.getLogger(__name__)

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

    def get_queryset(self):
        """
        Filter organizations based on user membership. Superusers see all.
        Optimize queryset with select_related and prefetch_related.
        """
        user = self.request.user
        queryset = super().get_queryset()

        if user.is_superuser:
            # Superusers see all organizations
            pass # No additional filtering needed
        else:
            # Regular users see only organizations they are members of
            # Use the utility function to get active org IDs
            active_org_ids, is_single_org = get_user_request_context(user)
            
            if not active_org_ids:
                 # If user belongs to no active organizations, return an empty queryset
                return queryset.none()

            queryset = queryset.filter(id__in=active_org_ids)

        # Apply optimizations
        return queryset.select_related(
            'organization_type',
            'primary_contact',
            'primary_address',
            'currency',
            'parent'
        ).prefetch_related('tags')

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
            'roles': ['exact'],
            'is_active': ['exact'],
        }

class OrganizationMembershipViewSet(viewsets.ModelViewSet):
    """ViewSet for OrganizationMembership model, integrated with RBAC"""
    
    queryset = OrganizationMembership.objects.select_related('user', 'organization').prefetch_related('roles').all()
    serializer_class = OrganizationMembershipSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = OrganizationMembershipFilter
    search_fields = ['user__username', 'organization__name', 'roles__name']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_permissions(self):
        """Use the RBAC permission class as per the guide."""
        return [HasModelPermissionInOrg()]

    def get_queryset(self):
        """
        Filter memberships based on user's organization access.
        Users see memberships for organizations they are part of.
        Superusers see all memberships.
        """
        user = self.request.user
        queryset = super().get_queryset()

        if user.is_superuser:
            return queryset # Superusers see everything

        # Regular users see memberships associated with organizations they are members of
        active_org_ids, is_single_org = get_user_request_context(user)

        if not active_org_ids:
            # If user belongs to no active organizations, return an empty queryset
            return queryset.none()
            
        # Filter memberships where the organization is one the user belongs to
        return queryset.filter(organization_id__in=active_org_ids)

    def perform_create(self, serializer):
        """
        Set audit fields and verify creation permission in the target organization.
        """
        user = self.request.user
        organization_id = serializer.validated_data.get('organization').id
        target_user = serializer.validated_data.get('user')

        logger.info(
            f"User '{user.username}' attempting to add user '{target_user.username}' "
            f"to organization ID {organization_id}"
        )

        # Explicit permission check as per RBAC guide
        if not has_perm_in_org(user, 'add_organizationmembership', organization_id):
            logger.warning(
                f"Permission denied for user '{user.username}' to add membership "
                f"in organization ID {organization_id}"
            )
            raise PermissionDenied(
                f"You do not have permission to add members to organization ID {organization_id}."
            )

        logger.info(
            f"Permission granted. Saving membership for user '{target_user.username}' "
            f"in organization ID {organization_id}, created by '{user.username}'."
        )
        serializer.save(created_by=user, updated_by=user)

    def perform_update(self, serializer):
        """
        Set updated_by field. Object-level permission check is handled by HasModelPermissionInOrg.
        """
        # has_object_permission in HasModelPermissionInOrg should handle the check
        # based on the membership's organization.
        serializer.save(updated_by=self.request.user)

    # perform_destroy implicitly uses has_object_permission from HasModelPermissionInOrg 