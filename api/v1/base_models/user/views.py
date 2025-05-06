from rest_framework import generics, permissions, viewsets, mixins
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied
from django.contrib.auth import get_user_model
from .models import UserProfile
from .serializers import UserProfileSerializer, UserSerializer
from rest_framework_api_key.permissions import HasAPIKey
from core.rbac.drf_permissions import HasModelPermissionInOrg
from core.rbac.permissions import has_perm_in_org
from .permissions import IsSelfOrAdminOrReadOnly
from core.rbac.utils import get_user_request_context, get_validated_request_org_id
from core.viewsets.mixins import OrganizationScopedViewSetMixin
from api.v1.base_models.organization.models import Organization
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class MyProfileView(generics.RetrieveUpdateAPIView):
    """
    View to retrieve or update user profile.
    Access is granted either through user authentication or valid API key.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated | HasAPIKey]

    def get_object(self):
        if self.request.user and self.request.user.is_authenticated:
            # For authenticated users, get or create their profile
            profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
            return profile
        
        # For API key requests, use a default user
        default_user, _ = User.objects.get_or_create(
            username='api_default_user',
            defaults={
                'email': 'api@example.com',
                'is_active': True
            }
        )
        profile, _ = UserProfile.objects.get_or_create(user=default_user)
        return profile 

class UserViewSet(OrganizationScopedViewSetMixin,
                  mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    """
    API endpoint for managing users.
    
    list: Returns list of users accessible to the requesting user
    retrieve: Returns details of a specific user
    create: Creates a new user with organization membership
    update: Updates an existing user
    partial_update: Partially updates an existing user
    """
    serializer_class = UserSerializer
    queryset = User.objects.all().select_related('profile')
    
    def get_permissions(self):
        """
        Get permissions based on action.
        - For self-related actions (retrieve/update own profile): use IsSelfOrAdminOrReadOnly
        - For all other actions: use HasModelPermissionInOrg
        """
        if self.action in ['retrieve', 'update', 'partial_update']:
            return [permissions.IsAuthenticated(), IsSelfOrAdminOrReadOnly()]
        return [HasModelPermissionInOrg()]
    
    def get_queryset(self):
        """
        Return organization-aware queryset filtered based on user's permissions.
        """
        user = self.request.user
        if user.is_superuser:
            return User.objects.all().select_related('profile')

        # For non-superusers, filter users belonging to shared active organizations
        context = get_user_request_context(user)
        active_org_ids = context.get('active_org_ids', [])

        if not active_org_ids:
            # If user is not in any active org, they can only see themselves
            return User.objects.filter(pk=user.pk).select_related('profile')

        # Find users who are active members in any of the requesting user's active orgs
        return User.objects.filter(
            organization_memberships__organization_id__in=active_org_ids,
            organization_memberships__is_active=True
        ).distinct().select_related('profile')
    
    def perform_create(self, serializer):
        """
        Custom create method that handles organization membership.
        """
        user = self.request.user
        logger.info(f"Creating user by user {user.username} (superuser: {user.is_superuser})")
        
        # Get organization_id from request data
        organization_id = self.request.data.get('organization_id')
        
        # For superusers, validate and use the specified organization_id
        if user.is_superuser:
            if organization_id:
                try:
                    organization = Organization.objects.get(pk=organization_id)
                    # Create the user first
                    new_user = serializer.save()
                    
                    # Then create the organization membership
                    role_id = self.request.data.get('role_id')
                    if role_id:
                        new_user.organization_memberships.create(
                            organization=organization,
                            is_active=True,
                            role_id=role_id
                        )
                    else:
                        new_user.organization_memberships.create(
                            organization=organization,
                            is_active=True
                        )
                    
                    return
                except Organization.DoesNotExist:
                    raise ValidationError({"organization_id": f"Organization with id {organization_id} does not exist."})
        
        # For non-superusers, handle organization context
        active_org_ids, is_single_org = get_user_request_context(user)
        
        if not active_org_ids:
            raise PermissionDenied("You do not belong to any active organizations.")
        
        # Validate target organization and permission
        try:
            target_org_id = get_validated_request_org_id(self.request, required_for_action=True)
            
            # Check if user has permission to create users in this organization
            if not user.is_superuser and not has_perm_in_org(user, "add_user", target_org_id):
                raise PermissionDenied(f"You don't have permission to create users in organization {target_org_id}.")
            
            # Get the organization object
            try:
                organization = Organization.objects.get(pk=target_org_id)
                
                # Create the user
                new_user = serializer.save()
                
                # Add organization membership
                role_id = self.request.data.get('role_id')
                if role_id:
                    new_user.organization_memberships.create(
                        organization=organization,
                        is_active=True,
                        role_id=role_id
                    )
                else:
                    new_user.organization_memberships.create(
                        organization=organization,
                        is_active=True
                    )
                
                return
                
            except Organization.DoesNotExist:
                raise ValidationError({"organization_id": f"Organization with id {target_org_id} does not exist."})
            
        except (ValidationError, PermissionDenied) as e:
            # Re-raise any validation or permission errors from the helper
            raise
    
    def perform_update(self, serializer):
        """
        Custom update method that enforces permission checks.
        """
        # Default update behavior, permission checks handled by get_permissions
        serializer.save() 