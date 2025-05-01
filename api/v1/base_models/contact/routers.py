from rest_framework.routers import DefaultRouter

class CustomRouter(DefaultRouter):
    """Custom router that includes HEAD actions in the actions mapping."""

    def get_method_map(self, viewset, method_map):
        """Add HEAD actions to the method map."""
        method_map = super().get_method_map(viewset, method_map)
        if 'get' in method_map:
            method_map['head'] = method_map['get']
        return method_map 