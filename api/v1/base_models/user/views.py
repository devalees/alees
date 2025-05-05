from rest_framework import generics, permissions, viewsets, mixins
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.contrib.auth import get_user_model
from .models import UserProfile
from .serializers import UserProfileSerializer, UserSerializer
from rest_framework_api_key.permissions import HasAPIKey
from core.rbac.drf_permissions import HasModelPermissionInOrg
from .permissions import IsSelfOrAdminOrReadOnly
from core.rbac.utils import get_user_request_context

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

class UserViewSet(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    serializer_class = UserProfileSerializer
    serializer_class = UserSerializer
    queryset = User.objects.all().select_related('profile')
    permission_classes = [
        permissions.IsAuthenticated,
        IsSelfOrAdminOrReadOnly
    ]

    def get_queryset(self):
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

    def get_permissions(self):
        # Return the permissions defined in permission_classes
        return [permission() for permission in self.permission_classes]

    # No perform_create (creation likely handled elsewhere, e.g., registration)
    # perform_update relies on HasModelPermissionInOrg for object check 