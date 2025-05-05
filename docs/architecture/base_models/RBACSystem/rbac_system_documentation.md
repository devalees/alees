# Organization-Aware RBAC System Documentation

## 1. Overview

The Organization-Aware Role-Based Access Control (RBAC) system provides a comprehensive permissions framework for the ERP application. It ensures proper data isolation between organizations while offering fine-grained control over user actions within each organization context.

### Key Features

- **Multi-Organization Support**: Users can belong to multiple organizations with different roles in each
- **Organization Context Awareness**: Automatically handles organization context for single-org users; enforces explicit context for multi-org users
- **Permission Caching**: Caches organization memberships and permissions for performance
- **Centralized Permission Checking**: Unified API for permission checks respecting organization context
- **Integration with Django Rest Framework**: Custom permission classes for API endpoints

### Core Principles

1. **Organization Scoping**: All business objects belong to a specific organization
2. **Role-Based Permissions**: Users have roles (Django Groups) within specific organizations
3. **Context-Aware Authorization**: Permissions are checked within an organization context
4. **Explicit vs. Implicit Context**: Single-org users have implicit context; multi-org users need explicit context

## 2. Architecture

### 2.1 Core Components

The RBAC system consists of the following components:

#### Models and Base Classes

- `OrganizationScoped` (abstract model): Base class for all organization-scoped models
- `OrganizationMembership`: Links users to organizations with specific roles
- `User.get_organizations()`: Returns organizations a user is a member of

#### RBAC Core Components

- `core.rbac.permissions`: Contains permission check functions
- `core.rbac.drf_permissions`: Contains DRF permission classes
- `core.rbac.utils`: Contains helper functions for organization context
- `core.rbac.signals`: Contains signals for cache invalidation

#### Serializer and ViewSet Mixins

- `OrganizationScopedSerializerMixin`: Handles organization context in serializers
- `OrganizationScopedViewSetMixin`: Filters querysets based on user's organization context

### 2.2 Data Flow

1. **Authentication**: User authenticates, and active organization memberships are cached
2. **API Request**: Request includes organization context (explicit or implicit)
3. **Authorization**: Permission checks use organization context
4. **Response Filtering**: Data is filtered based on user's organization access

## 3. Core Components in Detail

### 3.1 OrganizationScoped Models

```python
# core/models.py
class OrganizationScoped(models.Model):
    """Base model for all models that belong to an organization."""
    organization = models.ForeignKey(
        'organization.Organization',
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )
    
    class Meta:
        abstract = True
```

All business models should inherit from this class to ensure proper organization scoping.

### 3.2 Permission Check Functions

```python
# core/rbac/permissions.py
def has_perm_in_org(user, perm_codename, org_or_obj):
    """
    Check if user has a permission in the context of an organization.
    
    Args:
        user: The user to check permissions for
        perm_codename: Permission codename (e.g., 'view_contact')
        org_or_obj: Organization instance, ID, or an organization-scoped object
        
    Returns:
        bool: True if user has permission, False otherwise
    """
    # Implementation details...
```

This is the core permission check function used throughout the system.

### 3.3 DRF Permission Classes

```python
# core/rbac/drf_permissions.py
class HasModelPermissionInOrg(permissions.BasePermission):
    """
    Permission class that checks if the user has the required model
    permission in the organization context.
    """
    
    def has_permission(self, request, view):
        # Implementation details...
    
    def has_object_permission(self, request, view, obj):
        # Implementation details...
```

This permission class should be used in ViewSets to enforce organization-scoped permissions.

### 3.4 Organization Context Utilities

```python
# core/rbac/utils.py
def get_user_request_context(user):
    """
    Get user's organization context, including active organization IDs.
    
    Args:
        user: The user to get context for
        
    Returns:
        dict: Context including active_org_ids, is_single_org_user, etc.
    """
    # Implementation details...

def get_validated_request_org_id(request, required_for_action=False):
    """
    Validate and extract organization ID from request.
    
    Args:
        request: The request object
        required_for_action: Whether org ID is required for this action
        
    Returns:
        int: Organization ID if valid
        
    Raises:
        ValidationError: If org ID is invalid or missing when required
        PermissionDenied: If user doesn't have access to the organization
    """
    # Implementation details...
```

These utility functions handle organization context resolution and validation.

### 3.5 Serializer Mixin

```python
# core/serializers/mixins.py
class OrganizationScopedSerializerMixin:
    """
    Mixin for serializers that deal with organization-scoped models.
    
    Automatically handles organization field validation and population
    based on user's context.
    """
    
    def validate(self, attrs):
        # Implementation details...
    
    def create(self, validated_data):
        # Implementation details...
```

This mixin should be used in serializers for organization-scoped models.

### 3.6 ViewSet Mixin

```python
# core/viewsets/mixins.py
class OrganizationScopedViewSetMixin:
    """
    Mixin for viewsets that deal with organization-scoped models.
    
    Automatically filters querysets based on user's organization memberships.
    """
    
    def get_queryset(self):
        # Implementation details...
```

This mixin should be used in ViewSets for organization-scoped models.

## 4. Permission Caching

### 4.1 Cache Structure

The RBAC system uses Redis to cache:

- **Active Organization IDs**: `user:<user_id>:active_org_ids` → List of org IDs
- **Organization Permissions**: `rbac:perms:user:<user_id>:org:<org_id>` → Set of permission codenames

### 4.2 Cache Invalidation

Cache is invalidated when:

- User's organization memberships change
- User's roles (groups) change
- Permissions assigned to groups change

```python
# core/rbac/signals.py
@receiver(post_save, sender=OrganizationMembership)
def invalidate_on_membership_save(sender, instance, **kwargs):
    """Invalidate cache when membership changes."""
    # Implementation details...

@receiver(post_delete, sender=OrganizationMembership)
def invalidate_on_membership_delete(sender, instance, **kwargs):
    """Invalidate cache when membership is deleted."""
    # Implementation details...
```

## 5. Usage Patterns

### 5.1 Model Definition

```python
from core.models import OrganizationScoped

class Contact(OrganizationScoped, AuditableModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    # Other fields...
```

### 5.2 Serializer Definition

```python
from core.serializers.mixins import OrganizationScopedSerializerMixin

class ContactSerializer(OrganizationScopedSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'first_name', 'last_name', 'organization', ...]
```

### 5.3 ViewSet Definition

```python
from core.viewsets.mixins import OrganizationScopedViewSetMixin
from core.rbac.drf_permissions import HasModelPermissionInOrg

class ContactViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    queryset = Contact.objects.all()
    filterset_class = ContactFilter
    
    def get_permissions(self):
        return [HasModelPermissionInOrg()]
```

### 5.4 Direct Permission Checks

```python
from core.rbac.permissions import has_perm_in_org

def some_function(user, organization_id):
    if has_perm_in_org(user, 'view_contact', organization_id):
        # User has permission to view contacts in this organization
        return Contact.objects.filter(organization_id=organization_id)
    else:
        # User doesn't have permission
        raise PermissionDenied()
```

## 6. Multi-Organization User Experience

### 6.1 Serializer Behavior

- **Single-Org User**: Organization field is automatically set; providing it raises an error
- **Multi-Org User**: Must explicitly provide organization field for create operations
- **Superuser**: Can provide any valid organization ID

### 6.2 ViewSet Filtering

- **Regular User**: Sees only objects from organizations they're members of
- **Superuser**: Sees all objects by default

### 6.3 Error Handling

- Missing organization ID for multi-org users: ValidationError
- Invalid organization ID: ValidationError
- No permission in organization: PermissionDenied

## 7. Permissions and Roles

### 7.1 Permission Structure

Permission codenames follow Django convention:
- `add_<model>`: Create model objects
- `change_<model>`: Update model objects
- `delete_<model>`: Delete model objects
- `view_<model>`: View model objects

### 7.2 Role Structure

Roles are implemented as Django Groups with assigned permissions. Example roles:
- Admin: All permissions
- Editor: Add, change, view permissions
- Viewer: View permissions only

## 8. Security Considerations

- **Superuser Bypass**: Superusers bypass organization permission checks but not model permission checks
- **Object-Level Permissions**: Check owner/creator permissions if needed
- **Permission Checks Coverage**: Ensure all views/endpoints have permission checks
- **Cache Security**: Cache uses user-specific keys to prevent leaks

## 9. Performance Considerations

- **Cache Hit Rate**: Monitor cache hit rate and adjust timeout settings
- **Query Optimization**: Organization filtering adds a condition to queries
- **Bulk Operations**: Consider organization context in bulk operations
- **Cache Invalidation**: Targeted invalidation to minimize cache rebuilds

## 10. Troubleshooting

### Common Issues

1. **Permission Denied Unexpectedly**:
   - Check if user is member of the organization
   - Verify user has the required role/permissions
   - Check if organization context is correctly identified

2. **Organization Field Issues**:
   - For single-org users: Should not provide organization field
   - For multi-org users: Must provide valid organization field

3. **Cache Inconsistencies**:
   - Check if signals are connected properly
   - Manually invalidate cache if needed: `cache.delete(f"user:{user.id}:active_org_ids")`

## 11. Extending the System

To extend the RBAC system for new requirements:

1. **Custom Permission Checks**: Subclass `HasModelPermissionInOrg` for special cases
2. **Advanced Filtering**: Override `get_queryset` in ViewSets
3. **Additional Context**: Extend `get_user_request_context` for additional user context
4. **Custom Roles**: Create new Groups with appropriate permissions

## 12. Maintenance and Monitoring

- **Audit Logging**: Log permission checks and denied access
- **Performance Monitoring**: Track cache hit rates and permission check times
- **Security Reviews**: Regularly review permission assignments
- **Dependency Updates**: Keep Django and DRF updated for security fixes

## 13. Future Enhancements

Potential improvements to consider:

- **API for User-Organization Context**: Endpoints to get/set active organization
- **Permission Templates**: Pre-defined permission sets for common roles
- **UI Integration**: Admin interface for role/permission management
- **Organization Hierarchies**: Support parent-child organization relationships
- **Delegation**: Allow temporary permission delegation 