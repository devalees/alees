# RBAC Integration Guide: Adding Organization-Aware Access Control to Your App

This guide provides a step-by-step process for integrating the Organization-Aware RBAC system into your application. It uses the Contact app as a practical example to demonstrate the integration process.

## 1. Overview

Integrating the RBAC system involves several key steps:

1. Make your models organization-scoped
2. Update serializers with organization handling
3. Update ViewSets with permission and filtering logic
4. Set up proper permission checks in views and functions
5. Test the integration

## 2. Prerequisites

Before starting the integration, ensure:

- The core RBAC components are installed and configured
- `core.rbac` functions and classes are available
- `core.serializers.mixins` and `core.viewsets.mixins` are available
- You have a good understanding of your app's data model and access patterns

## 3. Step-by-Step Integration

### 3.1. Make Your Models Organization-Scoped

**Step 1:** Make your model inherit from `OrganizationScoped`

```python
# Before
from django.db import models
from core.models import AuditableModel

class Contact(AuditableModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    # ... other fields
```

```python
# After
from django.db import models
from core.models import AuditableModel, OrganizationScoped

class Contact(OrganizationScoped, AuditableModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    # ... other fields
```

**Step 2:** Update related models if necessary

If your main model has related models (like `ContactEmailAddress` for `Contact`), decide if they should also be organization-scoped or if they'll inherit the parent's organization.

```python
# Example: ContactEmailAddress inherits organization from Contact
class ContactEmailAddress(models.Model):
    contact = models.ForeignKey(
        Contact, 
        on_delete=models.CASCADE,
        related_name='email_addresses'
    )
    email = models.EmailField()
    # ... other fields
```

**Step 3:** Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3.2. Update Serializers

**Step 1:** Make your serializer inherit from `OrganizationScopedSerializerMixin`

```python
# Before
from rest_framework import serializers
from .models import Contact

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'first_name', 'last_name', ...]
```

```python
# After
from rest_framework import serializers
from core.serializers.mixins import OrganizationScopedSerializerMixin
from .models import Contact

class ContactSerializer(OrganizationScopedSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'first_name', 'last_name', 'organization', ...]
```

**Step 2:** Update the `create` method if necessary

The mixin provides basic organization handling, but you may need to customize it if your model has complex creation logic:

```python
def create(self, validated_data):
    """Create a contact with nested relations."""
    # Get tags data before TaggitSerializer pops it
    tags_data = validated_data.get('tags', None)
    
    # Extract nested objects
    emails_data = validated_data.pop('email_addresses', None)
    phones_data = validated_data.pop('phone_numbers', None)
    addresses_data = validated_data.pop('addresses', None)
    
    # Create the main instance (parent create handles organization)
    instance = super().create(validated_data)
    
    # Handle tags explicitly
    if tags_data is not None:
        for tag in tags_data:
            instance.tags.add(tag)
    
    # Create nested related objects
    if emails_data:
        self.create_email_addresses(instance, emails_data)
    
    # ... handle other nested objects
    
    return instance
```

**Step 3:** Update the `update` method if necessary

Similar to `create`, you may need to customize the `update` method for complex models:

```python
def update(self, instance, validated_data):
    """Update a contact and its nested related objects."""
    # Get tags data before TaggitSerializer pops it
    tags_data = validated_data.get('tags', None)
    
    # Extract nested objects
    emails_data = validated_data.pop('email_addresses', None)
    phones_data = validated_data.pop('phone_numbers', None)
    addresses_data = validated_data.pop('addresses', None)
    
    # Update the main instance
    instance = super().update(instance, validated_data)
    
    # Handle tags explicitly
    if tags_data is not None:
        instance.tags.clear()
        for tag in tags_data:
            instance.tags.add(tag)
    
    # Update nested related objects
    if emails_data is not None:
        self.update_email_addresses(instance, emails_data)
    
    # ... handle other nested objects
    
    return instance
```

**Step 4:** Implement helper methods for nested objects if needed

For complex serializers with nested objects, implement helper methods:

```python
def update_email_addresses(self, instance, emails_data):
    """Helper method to update email addresses for a contact."""
    existing_ids = set(instance.email_addresses.values_list('id', flat=True))
    updated_ids = set()
    
    for email_data in emails_data:
        email_id = email_data.get('id')
        if email_id:
            if email_id in existing_ids:
                # Update existing email
                email = instance.email_addresses.get(id=email_id)
                serializer = ContactEmailAddressSerializer(
                    email, data=email_data, partial=True, 
                    context={'contact': instance, 'request': self.context.get('request')}
                )
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    updated_ids.add(email_id)
        else:
            # Create new email
            serializer = ContactEmailAddressSerializer(
                data=email_data, 
                context={'contact': instance, 'request': self.context.get('request')}
            )
            if serializer.is_valid(raise_exception=True):
                email = serializer.save()
                if email and hasattr(email, 'id'):
                    updated_ids.add(email.id)
    
    # Delete emails not in the update data
    to_delete_ids = existing_ids - updated_ids
    if to_delete_ids:
        instance.email_addresses.filter(id__in=to_delete_ids).delete()
    
    return instance
```

### 3.3. Update ViewSets

**Step 1:** Make your ViewSet inherit from `OrganizationScopedViewSetMixin`

```python
# Before
from rest_framework import viewsets
from .models import Contact
from .serializers import ContactSerializer

class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filterset_class = ContactFilter
```

```python
# After
from rest_framework import viewsets
from core.viewsets.mixins import OrganizationScopedViewSetMixin
from core.rbac.drf_permissions import HasModelPermissionInOrg
from .models import Contact
from .serializers import ContactSerializer

class ContactViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filterset_class = ContactFilter
    
    def get_permissions(self):
        return [HasModelPermissionInOrg()]
```

**Step 2:** Update `perform_create` to handle organization context properly

For proper organization handling, you need to customize the creation process to account for different user types (single-org users, multi-org users, and superusers):

```python
def perform_create(self, serializer):
    """Ensure organization context is properly set when creating a contact."""
    user = self.request.user
    logger.info(f"Creating contact by user {user.username} (superuser: {user.is_superuser})")
    
    # Get organization_id from request data
    organization_id = self.request.data.get('organization_id')
    
    # If superuser, use the specified organization_id directly
    if user.is_superuser:
        if organization_id:
            try:
                organization = Organization.objects.get(pk=organization_id)
                serializer.save(created_by=user, updated_by=user, organization=organization)
                return
            except Organization.DoesNotExist:
                raise ValidationError({"organization_id": f"Organization with id {organization_id} does not exist."})
    
    # For non-superusers, handle organization context
    from core.rbac.utils import get_user_request_context
    from core.rbac.permissions import has_perm_in_org
    
    # Get user's active organizations
    active_org_ids, is_single_org = get_user_request_context(user)
    
    if not active_org_ids:
        raise PermissionDenied("You do not belong to any active organizations.")
    
    # Single-org user: use their only organization
    if is_single_org and not organization_id:
        org_id = active_org_ids[0]
        try:
            organization = Organization.objects.get(pk=org_id)
            serializer.save(created_by=user, updated_by=user, organization=organization)
            return
        except Organization.DoesNotExist:
            logger.error(f"Organization with ID {org_id} not found for single-org user")
            raise ValidationError({"organization_id": f"Your organization with ID {org_id} does not exist."})
    
    # Multi-org user with specified organization_id
    if organization_id:
        # Convert organization_id to integer if it's a string
        try:
            org_id = int(organization_id)
        except (ValueError, TypeError):
            raise ValidationError({"organization_id": "Invalid organization ID format"})
        
        # Check if targeted organization is in user's active orgs
        if org_id not in active_org_ids:
            raise PermissionDenied(
                f"You cannot create contacts in organization {org_id} as you are not a member."
            )
        
        # Check if user has the appropriate permission in the organization
        if not has_perm_in_org(user, "add_contact", org_id):
            raise PermissionDenied(
                f"You don't have permission to create contacts in organization {org_id}."
            )
        
        # Get the organization object
        try:
            organization = Organization.objects.get(pk=org_id)
            serializer.save(created_by=user, updated_by=user, organization=organization)
            return
        except Organization.DoesNotExist:
            raise ValidationError({"organization_id": f"Organization with id {org_id} does not exist."})
    
    # If we get here, it's a multi-org user without organization_id
    raise ValidationError({"organization_id": "Organization ID is required for users with multiple organizations."})
```

This implementation handles three key scenarios:

1. **Superusers**: Can explicitly specify an organization_id, which will be used if valid
2. **Single-Organization Users**: Automatically uses their only organization when no organization_id is provided
3. **Multi-Organization Users**: Must explicitly provide a valid organization_id

The key improvements over the basic implementation:

- Properly retrieves `is_single_org` flag from `get_user_request_context()`
- Automatically sets the organization for single-org users
- Validates permissions in the specified organization
- Provides clear error messages for each validation failure case
- Never saves a record without an organization, preventing null constraint violations

**Step 3:** Update other methods if necessary

You might need to customize other ViewSet methods like `perform_update` or `get_queryset` depending on your app's requirements.

### 3.4. Set Up Proper Permission Checks

**Step 1:** Add permission checks in custom view methods

For any custom actions or views, add proper permission checks:

```python
@action(detail=True, methods=['post'])
def mark_as_primary(self, request, pk=None):
    """Mark a contact as primary."""
    contact = self.get_object()  # This will check object permissions
    
    # Additional explicit check if needed
    if not has_perm_in_org(request.user, 'change_contact', contact.organization_id):
        raise PermissionDenied("You don't have permission to modify this contact")
    
    # Perform the action
    contact.is_primary = True
    contact.save()
    
    return Response({"status": "success"})
```

**Step 2:** Add permission checks in non-view functions if needed

For business logic outside of views, add explicit permission checks:

```python
def merge_contacts(user, primary_contact_id, secondary_contact_id):
    """Merge two contacts, keeping the primary one."""
    primary = Contact.objects.get(id=primary_contact_id)
    secondary = Contact.objects.get(id=secondary_contact_id)
    
    # Check permissions
    if not has_perm_in_org(user, 'change_contact', primary.organization_id):
        raise PermissionDenied("You don't have permission to modify the primary contact")
        
    if not has_perm_in_org(user, 'delete_contact', secondary.organization_id):
        raise PermissionDenied("You don't have permission to delete the secondary contact")
    
    # Check organization match
    if primary.organization_id != secondary.organization_id:
        raise ValidationError("Contacts must belong to the same organization")
    
    # Perform the merge
    # ...
```

### 3.5. Update Admin Interfaces

If you're using Django Admin, update the admin classes:

```python
from django.contrib import admin
from .models import Contact

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'organization', 'created_at']
    list_filter = ['organization']
    search_fields = ['first_name', 'last_name', 'organization__name']
```

### 3.6. Test the Integration

**Step 1:** Write unit tests for serializers

```python
def test_contact_serializer_organization_validation():
    """Test that organization validation works correctly."""
    # Setup
    organization = OrganizationFactory()
    user = UserFactory()
    user.organization_memberships.create(organization=organization, is_active=True)
    
    # Test serializer with organization
    data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'organization': organization.id
    }
    context = {'request': MockRequest(user=user)}
    serializer = ContactSerializer(data=data, context=context)
    
    # If user is in single org, providing org ID should fail
    if len(get_user_request_context(user)['active_org_ids']) == 1:
        assert not serializer.is_valid()
        assert 'organization' in serializer.errors
    else:
        assert serializer.is_valid()
```

**Step 2:** Write integration tests for ViewSets

```python
def test_contact_scoping_permissions():
    """Test that contact scoping and permissions work correctly."""
    # Setup organizations and users
    org1 = OrganizationFactory()
    org2 = OrganizationFactory()
    
    admin_user = UserFactory()
    admin_role = Group.objects.get(name="Admin")
    admin_user.organization_memberships.create(
        organization=org1, 
        is_active=True, 
        role=admin_role
    )
    
    viewer_user = UserFactory()
    viewer_role = Group.objects.get(name="Viewer")
    viewer_user.organization_memberships.create(
        organization=org1, 
        is_active=True, 
        role=viewer_role
    )
    
    # Create test data
    contact1 = ContactFactory(organization=org1)
    contact2 = ContactFactory(organization=org2)
    
    # Test list endpoint as admin
    client = APIClient()
    client.force_authenticate(user=admin_user)
    response = client.get('/api/v1/contacts/')
    
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == contact1.id
    
    # Test create endpoint as admin (should succeed)
    data = {
        'first_name': 'Jane',
        'last_name': 'Smith'
    }
    response = client.post('/api/v1/contacts/', data)
    assert response.status_code == 201
    
    # Test create endpoint as viewer (should fail)
    client.force_authenticate(user=viewer_user)
    response = client.post('/api/v1/contacts/', data)
    assert response.status_code == 403
```

**Step 3:** Run the tests

```bash
python manage.py test api.v1.base_models.contact
# or
pytest api/v1/base_models/contact/
```

## 4. Common Patterns and Best Practices

### 4.1. Handling Nested Objects

For models with nested relationships, follow these patterns:

**1. Define helper methods in serializers:**

```python
def create_email_addresses(self, contact, emails_data):
    """Create email addresses for a new contact."""
    for email_data in emails_data:
        # Create email address with proper context
        serializer = ContactEmailAddressSerializer(
            data=email_data,
            context={'contact': contact, 'request': self.context.get('request')}
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
```

**2. Handle primary flags properly:**

```python
def update_email_addresses(self, contact, emails_data):
    """Update email addresses for a contact."""
    # ... other logic
    
    # Handle primary flag
    primary_count = sum(1 for data in emails_data if data.get('is_primary', False))
    if primary_count > 1:
        raise ValidationError({"email_addresses": ["Only one email can be primary"]})
    
    # ... rest of the update logic
```

### 4.2. Handling Tags

For models using django-taggit:

```python
def create(self, validated_data):
    """Create a contact with tags."""
    # Get tags before TaggitSerializer pops them
    tags_data = validated_data.get('tags', None)
    
    # Create the instance
    instance = super().create(validated_data)
    
    # Add tags explicitly
    if tags_data:
        for tag in tags_data:
            instance.tags.add(tag)
    
    return instance
```

### 4.3. Testing with Organization Context

**1. Create a MockRequest class:**

```python
class MockRequest:
    """Mock request object for testing serializers with user context."""
    
    def __init__(self, user=None, data=None):
        self.user = user
        self.data = data or {}
        self.method = 'POST'  # Default to POST
```

**2. Use it in tests:**

```python
def test_serializer_with_user_context():
    """Test serializer with user context."""
    user = UserFactory()
    org = OrganizationFactory()
    user.organization_memberships.create(organization=org, is_active=True)
    
    data = {'name': 'Test Contact'}
    mock_request = MockRequest(user=user, data=data)
    
    serializer = ContactSerializer(
        data=data,
        context={'request': mock_request}
    )
    assert serializer.is_valid()
```

### 4.4. Filtering and Ordering

Add filtering and ordering to your ViewSets:

```python
class ContactViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filterset_class = ContactFilter
    ordering_fields = ['created_at', 'first_name', 'last_name']
    ordering = ['-created_at']
```

## 5. Troubleshooting

### 5.1. Common Issues

**1. "Organization field is required" for single-org users**

This typically happens when the serializer context is missing the request:

```python
# Solution: Always provide request in context
serializer = ContactSerializer(data=data, context={'request': request})
```

**2. Permission denied for superusers**

Check if you're overriding the permission check logic:

```python
# Correct approach in viewsets
def get_queryset(self):
    queryset = super().get_queryset()
    # Apply additional filtering but preserve superuser access
    if not self.request.user.is_superuser:
        # Add your custom filters
    return queryset
```

**3. Tags not updating correctly**

Tags need explicit handling:

```python
# Solution: Handle tags explicitly in update method
if 'tags' in validated_data:
    instance.tags.clear()
    for tag in validated_data.get('tags', []):
        instance.tags.add(tag)
```

### 5.2. Debugging Tips

**1. Add logging to permission checks:**

```python
def perform_create(self, serializer):
    user = self.request.user
    logger.info(f"User {user.username} (superuser: {user.is_superuser}) "
                f"attempting to create {self.get_serializer_class().__name__}")
    logger.info(f"Active org IDs: {get_user_request_context(user)['active_org_ids']}")
    logger.info(f"Request data: {self.request.data}")
    
    super().perform_create(serializer)
```

**2. Check cache contents:**

```python
def debug_cache(user_id, org_id):
    """Debug helper to check cache contents."""
    from django.core.cache import caches
    
    cache = caches['rbac']
    active_orgs = cache.get(f"user:{user_id}:active_org_ids")
    perms = cache.get(f"rbac:perms:user:{user_id}:org:{org_id}")
    
    print(f"Active orgs: {active_orgs}")
    print(f"Permissions: {perms}")
```

**3. Test permission checks directly:**

```python
def test_permission_directly(user, perm, org_id):
    """Test a permission check directly."""
    from core.rbac.permissions import has_perm_in_org
    
    result = has_perm_in_org(user, perm, org_id)
    print(f"Permission check for {user.username}, {perm}, org {org_id}: {result}")
    
    # If failed, check group memberships
    group_names = user.groups.values_list('name', flat=True)
    print(f"User groups: {list(group_names)}")
    
    # Check org membership
    membership = user.organization_memberships.filter(organization_id=org_id).first()
    if membership:
        print(f"Org membership: active={membership.is_active}, role={membership.role}")
    else:
        print("No membership found")
```

## 6. Conclusion

Integrating the RBAC system with your app involves:

1. Making models organization-scoped
2. Using the provided mixins for serializers and ViewSets
3. Implementing custom logic for complex relationships
4. Adding proper permission checks
5. Testing thoroughly

By following this guide, you should be able to successfully integrate the Organization-Aware RBAC system with your app, providing secure, context-aware access control.

## 7. Further Resources

- See [RBAC System Documentation](./rbac_system_documentation.md) for complete system details
- Examine the Contact app implementation for a comprehensive example
- Review the tests in the Contact app for testing patterns 