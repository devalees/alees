from typing import Any, Optional
from django.core.cache import cache
from .models import Flag

def flag_state(flag_name: str, request: Optional[Any] = None) -> bool:
    """
    Get the current state of a feature flag.
    
    Args:
        flag_name: The name of the feature flag
        request: Optional request object for request-based conditions
        
    Returns:
        True if the feature is enabled, False otherwise
    """
    try:
        flag = Flag.objects.get(name=flag_name)
        return flag.default
    except Flag.DoesNotExist:
        return False 