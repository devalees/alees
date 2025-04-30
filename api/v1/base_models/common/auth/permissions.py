from rest_framework import permissions
from rest_framework_api_key.permissions import HasAPIKey

class IsAuthenticatedOrHasAPIKey(permissions.BasePermission):
    """
    Allows access if the user is authenticated OR has a valid API key.
    """
    def has_permission(self, request, view):
        return (
            permissions.IsAuthenticated().has_permission(request, view) or
            HasAPIKey().has_permission(request, view)
        )

    def has_object_permission(self, request, view, obj):
        # Implement object-level permission logic
        return True

    def has_object_permission(self, request, view, obj):
        # Implement object-level permission logic
        return True 