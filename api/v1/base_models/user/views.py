from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.contrib.auth import get_user_model
from .models import UserProfile
from .serializers import UserProfileSerializer
from rest_framework_api_key.permissions import HasAPIKey

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