from typing import Any, Dict, Optional
from django.conf import settings
from .state import flag_state
from .models import Flag

class FeatureFlagsManager:
    """Feature flags management system for Alees ERP."""
    
    def __init__(self):
        """Initialize the feature flags manager."""
        self.storage = settings.FEATURE_FLAGS_STORAGE

    def is_enabled(self, flag_name: str, request: Optional[Any] = None) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            flag_name: The name of the feature flag
            request: Optional request object for request-based conditions
            
        Returns:
            True if the feature is enabled, False otherwise
        """
        return flag_state(flag_name, request=request)

    def create_flag(self, name: str, description: str, default: bool = False) -> bool:
        """
        Create a new feature flag.
        
        Args:
            name: The name of the feature flag
            description: Description of the feature flag
            default: Default state of the flag
            
        Returns:
            True if successful, False otherwise
        """
        try:
            Flag.objects.create(
                name=name,
                description=description,
                default=default
            )
            return True
        except Exception:
            return False

    def update_flag(self, name: str, **kwargs) -> bool:
        """
        Update an existing feature flag.
        
        Args:
            name: The name of the feature flag
            **kwargs: Fields to update (description, default, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            flag = Flag.objects.get(name=name)
            for key, value in kwargs.items():
                setattr(flag, key, value)
            flag.save()
            return True
        except Flag.DoesNotExist:
            return False

    def delete_flag(self, name: str) -> bool:
        """
        Delete a feature flag.
        
        Args:
            name: The name of the feature flag to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            Flag.objects.get(name=name).delete()
            return True
        except Flag.DoesNotExist:
            return False

    def get_flag(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a feature flag.
        
        Args:
            name: The name of the feature flag
            
        Returns:
            Dictionary containing flag information or None if not found
        """
        try:
            flag = Flag.objects.get(name=name)
            return {
                'name': flag.name,
                'description': flag.description,
                'default': flag.default,
                'created': flag.created,
                'modified': flag.modified
            }
        except Flag.DoesNotExist:
            return None

    def list_flags(self) -> Dict[str, Dict[str, Any]]:
        """
        List all feature flags.
        
        Returns:
            Dictionary of all feature flags and their information
        """
        flags = {}
        for flag in Flag.objects.all():
            flags[flag.name] = {
                'description': flag.description,
                'default': flag.default,
                'created': flag.created,
                'modified': flag.modified
            }
        return flags 