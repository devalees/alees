from rest_framework import generics, permissions
from .models import UserProfile
from .serializers import UserProfileSerializer

class MyProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for users to view and update their own profile.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        Get or create the user's profile.
        """
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile 