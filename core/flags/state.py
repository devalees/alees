from typing import Any, Optional
from django.core.cache import cache
from django.conf import settings
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
    # First check cache/redis
    storage = settings.FEATURE_FLAGS_STORAGE
    if storage == 'redis':
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection("default")
        state = redis_conn.get(f"flag:{flag_name}")
        if state is not None:
            return state == b'1'
    elif storage == 'cache':
        state = cache.get(f"flag:{flag_name}")
        if state is not None:
            return state
            
    # Fall back to database
    try:
        flag = Flag.objects.get(name=flag_name)
        # Cache the result
        if storage == 'redis':
            redis_conn.set(f"flag:{flag_name}", '1' if flag.enabled else '0')
        elif storage == 'cache':
            cache.set(f"flag:{flag_name}", flag.enabled)
        return flag.enabled
    except Flag.DoesNotExist:
        return False 