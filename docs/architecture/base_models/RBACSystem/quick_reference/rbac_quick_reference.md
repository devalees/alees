# RBAC Quick Reference Card

## Core Components

### 1. Models
```python
# Make models organization-scoped
from core.models import OrganizationScoped

class YourModel(OrganizationScoped, AuditableModel):
    # Your fields
    
    class Meta:
        permissions = [
            ('custom_action', 'Can perform custom action'),
        ]
```

### 2. Serializers
```python
# Make serializers organization-aware
from core.serializers.mixins import OrganizationScopedSerializerMixin

class YourSerializer(OrganizationScopedSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = YourModel
        fields = [..., 'organization']
```

### 3. ViewSets
```python
# Make viewsets organization-aware
from core.viewsets.mixins import OrganizationScopedViewSetMixin
from core.rbac.drf_permissions import HasModelPermissionInOrg

class YourViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = YourModel.objects.all()
    serializer_class = YourSerializer
    
    def get_permissions(self):
        return [HasModelPermissionInOrg()]
```

## Permission Checks

### 1. In Views
```python
from core.rbac.permissions import has_perm_in_org
from rest_framework.exceptions import PermissionDenied

# In a method
if not has_perm_in_org(request.user, 'add_yourmodel', organization_id):
    raise PermissionDenied("You don't have permission")
```

### 2. In Serializers
```python
from rest_framework.exceptions import PermissionDenied
from core.rbac.permissions import has_perm_in_org

def validate(self, data):
    user = self.context['request'].user
    if not has_perm_in_org(user, 'change_yourmodel', data['organization'].id):
        raise PermissionDenied("No permission to change in this organization")
    return data
```

### 3. In Business Logic
```python
def your_function(user, object_id, organization_id):
    # Check permissions
    if not has_perm_in_org(user, 'custom_action', organization_id):
        raise PermissionDenied("No permission for this action")
    
    # Proceed with logic
```

## Organization Context

### 1. In Requests
```python
# Get user's organization context
from core.rbac.utils import get_user_request_context

def your_view(request):
    context = get_user_request_context(request.user)
    active_org_ids = context['active_org_ids']
    current_org_id = context['current_org_id']
```

### 2. Switching Organizations
```
# In client requests, add header:
HTTP_X_ORGANIZATION_ID: 123
```

## Testing

### 1. Mock Request for Serializers
```python
class MockRequest:
    def __init__(self, user=None, data=None):
        self.user = user
        self.data = data or {}
        self.method = 'POST'

# Use in tests
context = {'request': MockRequest(user=user)}
serializer = YourSerializer(data=data, context=context)
```

### 2. Testing Permissions
```python
from rest_framework.test import APIClient

# Test organization scoping
client = APIClient()
client.force_authenticate(user=user)

# Test with specific organization
response = client.get('/your-endpoint/', HTTP_X_ORGANIZATION_ID=str(org.id))
```

## Common Error Patterns

### 1. Organization Not Set
- Check if request context is provided to serializer
- Ensure `perform_create` properly handles organization

### 2. Permission Denied for Superusers
- Check for `user.is_superuser` bypass in custom permission logic

### 3. Cross-Organization Access
- Add validation in business logic:
```python
if obj1.organization_id != obj2.organization_id:
    raise ValidationError("Objects must be in the same organization")
```

## Debugging

### 1. Log Permission Checks
```python
import logging
logger = logging.getLogger(__name__)

logger.debug(f"Permission check: {user.username}, {permission}, org {org_id}")
```

### 2. Check Cache
```python
from django.core.cache import caches
cache = caches['rbac']
perms = cache.get(f"rbac:perms:user:{user_id}:org:{org_id}")
```

### 3. Test Direct Permission
```python
from core.rbac.permissions import has_perm_in_org
result = has_perm_in_org(user, 'your_permission', org_id)
``` 