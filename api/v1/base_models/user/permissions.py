from rest_framework import permissions

class IsSelfOrAdminOrReadOnly(permissions.BasePermission):
    """
    Allows read access to any authenticated user, but write access only to the user themselves or admin users.
    """

    def has_permission(self, request, view):
        # Allow any authenticated user for list views
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user (for retrieve)
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Write permissions are only allowed to the user themselves or superusers.
        # Assumes the object 'obj' is the user model instance.
        return obj == request.user or request.user.is_superuser 