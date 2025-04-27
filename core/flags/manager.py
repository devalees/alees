from typing import Dict, List, Optional, Any
from django.core.cache import cache
from django.conf import settings
from django.core.exceptions import ValidationError
from .models import Flag
from .state import flag_state

class FeatureFlagsManager:
    """Manager class for handling feature flags."""
    
    def __init__(self):
        self.storage = settings.FEATURE_FLAGS_STORAGE
        if self.storage == 'redis':
            from django_redis import get_redis_connection
            self.redis = get_redis_connection("default")

    def is_enabled(self, flag_name: str, request: Optional[Any] = None) -> bool:
        """Check if a feature flag is enabled."""
        return flag_state(flag_name, request)

    def create_flag(self, name: str, enabled: bool = False, description: str = "") -> bool:
        """Create a new feature flag."""
        try:
            # Check if flag already exists
            if Flag.objects.filter(name=name).exists():
                return False
                
            flag = Flag.objects.create(
                name=name,
                enabled=enabled,
                description=description
            )
            
            # Update cache/redis
            if self.storage == 'redis':
                self.redis.set(f"flag:{name}", '1' if enabled else '0')
            elif self.storage == 'cache':
                cache.set(f"flag:{name}", enabled)
                
            return True
        except ValidationError:
            return False

    def update_flag(self, name: str, enabled: bool, description: Optional[str] = None) -> bool:
        """Update an existing feature flag."""
        try:
            flag = Flag.objects.get(name=name)
            flag.enabled = enabled
            if description is not None:
                flag.description = description
            flag.save()
            
            # Update cache/redis
            if self.storage == 'redis':
                self.redis.set(f"flag:{name}", '1' if enabled else '0')
            elif self.storage == 'cache':
                cache.set(f"flag:{name}", enabled)
                
            return True
        except Flag.DoesNotExist:
            return False

    def delete_flag(self, name: str) -> bool:
        """Delete a feature flag."""
        try:
            Flag.objects.get(name=name).delete()
            
            # Clear from cache/redis
            if self.storage == 'redis':
                self.redis.delete(f"flag:{name}")
            elif self.storage == 'cache':
                cache.delete(f"flag:{name}")
                
            return True
        except Flag.DoesNotExist:
            return False

    def get_flag(self, name: str) -> Optional[Dict]:
        """Get a feature flag's details."""
        try:
            flag = Flag.objects.get(name=name)
            return {
                'name': flag.name,
                'enabled': flag.enabled,
                'description': flag.description
            }
        except Flag.DoesNotExist:
            return None

    def list_flags(self) -> List[Dict]:
        """List all feature flags."""
        flags = Flag.objects.all()
        return [
            {
                'name': flag.name,
                'enabled': flag.enabled,
                'description': flag.description
            }
            for flag in flags
        ] 