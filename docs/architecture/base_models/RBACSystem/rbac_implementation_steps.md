Okay, let's generate the implementation steps for the core parts of the **RBAC System**, focusing on setting up the `FieldPermission` model and the basic integration points. This assumes we are using Django's built-in `User`, `Group` (as Role), and `Permission` models as the foundation.

**Note:** Implementing the *full enforcement* within serializers and the `has_field_permission` check function with caching involves significant logic that will likely be refined iteratively. These steps focus on establishing the structure.

--- START OF FILE rbac_implementation_steps.md ---

# RBAC System (Field-Level Ext) - Implementation Steps

## 1. Overview

**Model Name(s):**
`FieldPermission` (plus usage of Django `User`, `Group`, `Permission`)

**Corresponding PRD:**
`rbac_prd.md` (Refined version for Field-Level CRUD)

**Depends On:**
`Timestamped`, `Auditable`, Django `auth` app (`User`, `Group`, `Permission`), `ContentType` framework, Caching strategy (`cache_redis.md`).

**Key Features:**
Extends Django's model-level permissions with field-level Create, Read, Update control via a `FieldPermission` model linked to Groups (Roles). Defines the structure and basic management approach.

**Primary Location(s):**
`rbac/` (New dedicated app for RBAC extensions) or potentially `core/`

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`) are implemented.
[ ] Verify Django `auth` and `contenttypes` apps are in `INSTALLED_APPS`.
[ ] Ensure base User/Group setup is functional (users can be created and assigned to groups).
[ ] **Create new Django app:** `python manage.py startapp rbac`.
[ ] Add `'rbac'` to `INSTALLED_APPS` in `config/settings/base.py`.
[ ] Ensure caching backend (Redis) and strategy are configured.
[ ] Ensure `factory-boy` is set up. Factories for `User`, `Group`, `ContentType` exist.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 `FieldPermission` Model Definition (`rbac/models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`rbac/tests/unit/test_models.py`) verifying:
      *   A `FieldPermission` instance can be created linking a `Group`, `ContentType`, and `field_name`.
      *   Boolean flags (`can_create`, `can_read`, `can_update`) default to `False`.
      *   `unique_together` constraint (`group`, `content_type`, `field_name`) is enforced.
      *   Inherited `Timestamped`/`Auditable` fields exist.
      *   `__str__` method provides a readable representation.
      Run; expect failure (`FieldPermission` doesn't exist).
  [ ] Define the `FieldPermission` class in `rbac/models.py`.
  [ ] Add required inheritance: `Timestamped`, `Auditable`.
      ```python
      # rbac/models.py
      from django.contrib.auth.models import Group
      from django.contrib.contenttypes.models import ContentType
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from core.models import Timestamped, Auditable # Adjust import path

      class FieldPermission(Timestamped, Auditable):
          group = models.ForeignKey(
              Group,
              verbose_name=_("Role (Group)"),
              on_delete=models.CASCADE,
              related_name='field_permissions'
          )
          content_type = models.ForeignKey(
              ContentType,
              verbose_name=_("Model"),
              on_delete=models.CASCADE,
              help_text=_("The model this permission applies to.")
          )
          field_name = models.CharField(
              _("Field Name"),
              max_length=255,
              help_text=_("The name of the field on the specified model.")
          )
          can_create = models.BooleanField(
              _("Can Create"),
              default=False,
              help_text=_("Can provide a value for this field during record creation?")
          )
          can_read = models.BooleanField(
              _("Can Read"),
              default=False,
              help_text=_("Can read (view) the value of this field?")
          )
          can_update = models.BooleanField(
              _("Can Update"),
              default=False,
              help_text=_("Can update (change) the value on an existing record?")
          )

          class Meta:
              verbose_name = _("Field Permission")
              verbose_name_plural = _("Field Permissions")
              unique_together = ('group', 'content_type', 'field_name')
              indexes = [
                  models.Index(fields=['group', 'content_type', 'field_name']),
              ]
              ordering = ['group__name', 'content_type__app_label', 'content_type__model', 'field_name']

          def __str__(self):
              return f"{self.group.name} - {self.content_type.app_label}.{self.content_type.model}.{self.field_name}"
      ```
  [ ] Run tests; expect pass. Refactor model code if needed.

  ### 3.2 Factory Definition (`rbac/tests/factories.py`)

  [ ] Define `FieldPermissionFactory` in `rbac/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from django.contrib.auth.models import Group
      from django.contrib.contenttypes.models import ContentType
      from ..models import FieldPermission
      # Import UserFactory if needed for Auditable fields implicitly

      class GroupFactory(DjangoModelFactory): # Define basic Group factory if needed
          class Meta:
              model = Group
              django_get_or_create = ('name',)
          name = factory.Sequence(lambda n: f'Role {n}')

      # Factory assumes a model exists to get a ContentType for, e.g., Product
      # from api.v1.base_models.common.models import Product # Example path

      class FieldPermissionFactory(DjangoModelFactory):
          class Meta:
              model = FieldPermission

          group = factory.SubFactory(GroupFactory)
          # Example: Get ContentType for Product model
          # content_type = factory.LazyFunction(lambda: ContentType.objects.get_for_model(Product))
          content_type = None # Must be set explicitly in tests or provide default model
          field_name = factory.Sequence(lambda n: f'field_{n}')
          can_create = factory.Faker('boolean')
          can_read = factory.Faker('boolean')
          can_update = factory.Faker('boolean')

          @factory.lazy_attribute
          def content_type(self):
              # Default requires a model to exist, adjust as needed
              try:
                  # Replace 'app_label', 'modelname' with a real model
                  return ContentType.objects.get(app_label='some_app', model='somemodel')
              except ContentType.DoesNotExist:
                  # Create a dummy model content type for testing if necessary,
                  # or raise error / handle differently.
                  # This highlights dependency on other models being migrated.
                  print("WARN: Default ContentType not found for FieldPermissionFactory")
                  return None
      ```
  [ ] **(Test)** Write simple tests ensuring the factory creates valid `FieldPermission` instances, paying attention to setting a valid `content_type`.

  ### 3.3 Admin Registration (`rbac/admin.py`)

  [ ] Create `rbac/admin.py`.
  [ ] Define `FieldPermissionAdmin`:
      ```python
      from django.contrib import admin
      from .models import FieldPermission

      @admin.register(FieldPermission)
      class FieldPermissionAdmin(admin.ModelAdmin):
          list_display = (
              'group', 'content_type', 'field_name',
              'can_create', 'can_read', 'can_update', 'updated_at'
          )
          list_filter = ('group', 'content_type')
          search_fields = ('group__name', 'content_type__app_label', 'content_type__model', 'field_name')
          list_editable = ('can_create', 'can_read', 'can_update') # Allow easy editing
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
          # Consider using raw_id_fields for group and content_type if lists get long
          # raw_id_fields = ('group', 'content_type')
          # TODO: Improve field_name selection - requires custom widget/form
          #       to dynamically populate choices based on selected content_type.
          #       Start with simple CharField input.
      ```
  [ ] **(Manual Test):** Verify basic CRUD operations for `FieldPermission` via Django Admin. Acknowledge `field_name` is currently free-text.

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations rbac`.
  [ ] **Review generated migration file carefully.** Check FKs, indexes, `unique_together`.
  [ ] Run `python manage.py migrate` locally.

  ### 3.5 Permission Check Function (`rbac/permissions.py` or similar)

  [ ] **(Test First)**
      Write **Unit Tests** (`rbac/tests/unit/test_permissions.py`) for the `has_field_permission` function. These tests require mocking database lookups (`FieldPermission.objects.filter`, `user.groups.all`, `user.has_perm`).
      *   Test superuser bypass -> returns `True`.
      *   Test user lacks model-level permission -> returns `False`.
      *   Test user has model permission but no specific `FieldPermission` record exists -> returns `False`.
      *   Test user has model permission and a `FieldPermission` record grants the specific action (`create`, `read`, `update`) -> returns `True`.
      *   Test user has model permission but the `FieldPermission` record denies the specific action -> returns `False`.
      *   Test user belongs to multiple groups, one grants, one denies (grant should win if any grant).
      *   Test caching interaction (mock cache `get`/`set`).
      Run; expect failure (`has_field_permission` doesn't exist or is incorrect).
  [ ] Create `rbac/permissions.py`. Define the `has_field_permission` function:
      ```python
      # rbac/permissions.py
      from functools import lru_cache # Basic in-memory cache example
      from django.contrib.contenttypes.models import ContentType
      from django.core.cache import caches # Use Django cache framework
      from .models import FieldPermission

      # Choose appropriate cache backend alias from settings
      permission_cache = caches['permissions'] # Example alias

      def _get_model_perm_codename(action, opts):
          """Helper to get default model permission codename."""
          if action == 'read':
              return f'{opts.app_label}.view_{opts.model_name}'
          elif action == 'create':
              return f'{opts.app_label}.add_{opts.model_name}'
          elif action == 'update':
              return f'{opts.app_label}.change_{opts.model_name}'
          # Add 'delete' if needed later
          return None

      def _get_user_field_perms(user, model_or_instance):
          """Gets (and caches) field permissions for a user and model."""
          if not user or not user.is_authenticated:
              return {}

          ctype = ContentType.objects.get_for_model(model_or_instance)
          # Use a versioned cache key
          # Invalidate this cache version when FieldPermission or Group memberships change
          cache_version = permission_cache.get(f'rbac:vsn:user:{user.pk}:model:{ctype.pk}', 1)
          cache_key = f'rbac:perms:user:{user.pk}:model:{ctype.pk}:v{cache_version}'

          cached_perms = permission_cache.get(cache_key)
          if cached_perms is not None:
              return cached_perms

          # Cache miss - calculate permissions
          user_groups = user.groups.all().values_list('pk', flat=True)
          if not user_groups:
               permission_cache.set(cache_key, {}, timeout=...) # Cache empty result
               return {}

          # Query all relevant FieldPermission rules for the user's groups & model
          qs = FieldPermission.objects.filter(
              group_id__in=list(user_groups),
              content_type=ctype
          ).values_list('field_name', 'can_create', 'can_read', 'can_update')

          # Aggregate permissions (True wins)
          resolved_perms = {}
          for field_name, can_create, can_read, can_update in qs:
              if field_name not in resolved_perms:
                  resolved_perms[field_name] = {'create': False, 'read': False, 'update': False}
              resolved_perms[field_name]['create'] = resolved_perms[field_name]['create'] or can_create
              resolved_perms[field_name]['read'] = resolved_perms[field_name]['read'] or can_read
              resolved_perms[field_name]['update'] = resolved_perms[field_name]['update'] or can_update

          permission_cache.set(cache_key, resolved_perms, timeout=...) # Cache calculated perms
          return resolved_perms

      def has_field_permission(user, action, model_or_instance, field_name):
          """
          Checks if a user has permission for a specific action on a model field.
          Action must be 'create', 'read', or 'update'.
          """
          if not user or not user.is_authenticated:
              return False

          if user.is_superuser:
              return True

          opts = model_or_instance._meta
          model_perm_codename = _get_model_perm_codename(action, opts)

          # 1. Check required model-level permission first
          if not model_perm_codename or not user.has_perm(model_perm_codename, model_or_instance if action != 'create' else None):
               # For 'create', object is None, so check global add perm
               # For 'read'/'update', check object perm if available, else global change/view perm
               if action == 'create' and not user.has_perm(model_perm_codename): # Check global add perm
                   return False
               # Note: user.has_perm handles object-level checks if obj is provided
               # and django-guardian or similar is used, otherwise checks global perm.
               # If specific object-level model perms are needed, ensure has_perm check is correct.
               if action != 'create' and not user.has_perm(model_perm_codename, model_or_instance):
                   return False


          # 2. Check explicit field-level grant (using cached helper)
          all_field_perms = _get_user_field_perms(user, model_or_instance)
          field_perms = all_field_perms.get(field_name, None)

          if not field_perms:
              # No specific field rule found for this user/field, default to False
              # Or decide on default behaviour: maybe allow if model perm granted?
              # Current logic: Explicit field permission is required.
              return False

          # Check the specific action permission
          if action == 'create':
              return field_perms.get('create', False)
          elif action == 'read':
              return field_perms.get('read', False)
          elif action == 'update':
              return field_perms.get('update', False)

          return False # Should not be reached if action is valid
      ```
      *(Note: This implementation requires careful testing, especially the caching and interaction with model permissions. The `_get_user_field_perms` should ideally be cached.)*
  [ ] Run tests; expect pass. Refactor for clarity, performance, and robustness.

  ### 3.6 Serializer Integration (Example - Requires Base Serializer)

  [ ] **(Test First)** Write Integration tests for a *sample* model's serializer (e.g., `OrganizationSerializer`) that verify:
      *   Fields are excluded from output if user lacks `can_read=True` field permission.
      *   API `CREATE` fails if data includes fields where user lacks `can_create=True`.
      *   API `UPDATE/PATCH` fails if data includes fields where user lacks `can_update=True`.
  [ ] Define or modify a Base Serializer Mixin that application serializers will inherit:
      ```python
      # core/serializers.py (Example location)
      from rest_framework import serializers
      from rbac.permissions import has_field_permission # Adjust import

      class FieldPermissionSerializerMixin:
          """Mixin to apply field-level read/write permissions."""

          def _check_field_permissions(self, user, instance, fields, action):
              """Helper to check multiple fields."""
              allowed = set()
              if instance is None and action == 'create': # Getting model class for create
                   model_class = self.Meta.model
              else:
                   model_class = instance.__class__

              for field_name in fields:
                   # Skip checking relation fields managed by nested serializers directly? TBD.
                   # Skip checking read_only fields for write actions?
                   if field_name in self.Meta.read_only_fields and action != 'read':
                       continue # No need to check write permission for read_only field

                   if has_field_permission(user, action, instance or model_class, field_name):
                       allowed.add(field_name)
              return allowed

          def __init__(self, *args, **kwargs):
              super().__init__(*args, **kwargs)
              # Apply read permissions on initialization
              request = self.context.get('request')
              user = getattr(request, 'user', None)

              if user and user.is_authenticated and not user.is_superuser:
                   instance = getattr(self, 'instance', None)
                   # instance might be a list in ListSerializer context, handle carefully
                   if instance and not isinstance(instance, list):
                       allowed_read_fields = self._check_field_permissions(user, instance, self.fields.keys(), 'read')
                       # Drop fields the user cannot read
                       for field_name in set(self.fields.keys()) - allowed_read_fields:
                           self.fields.pop(field_name, None)

          def validate(self, data):
              """Check update/create permissions during validation."""
              request = self.context.get('request')
              user = getattr(request, 'user', None)
              instance = getattr(self, 'instance', None)

              if user and user.is_authenticated and not user.is_superuser:
                  action = 'update' if instance else 'create'
                  # Check permission for fields present in the input `data`
                  for field_name in data.keys():
                      if field_name not in self.Meta.read_only_fields: # Don't check write perms for read-only
                           if not has_field_permission(user, action, instance or self.Meta.model, field_name):
                               raise serializers.ValidationError(
                                   f"Permission denied for field '{field_name}' during {action}."
                               )
              return super().validate(data)
      ```
  [ ] Make concrete serializers (like `OrganizationSerializer`) inherit this mixin: `class OrganizationSerializer(FieldPermissionSerializerMixin, TaggitSerializer, serializers.ModelSerializer): ...`
  [ ] Run integration tests for the sample serializer; expect pass. Refactor mixin/permission check.

  ### 3.7 ViewSet/URL Integration

  [ ] Ensure relevant ViewSets use standard DRF permission classes (`permission_classes`) to check **model-level** permissions. Field-level control happens in the serializer driven by the mixin.

  ### 3.8 Cache Invalidation

  [ ] **(Test First)** Write tests verifying that changing a `Group`'s membership, changing a `Group`'s model permissions, or changing `FieldPermission` records correctly invalidates the permission cache for affected users/models.
  [ ] Implement signal receivers for `m2m_changed` on `User.groups` / `Group.permissions`, and `post_save`/`post_delete` on `FieldPermission`.
  [ ] These receivers need to increment the cache version key (e.g., `rbac:vsn:user:{user.pk}:model:{ctype.pk}`) or delete specific permission keys from the cache (`rbac:perms:user:{user.pk}:model:{ctype.pk}`). Versioning is generally more robust against race conditions than direct deletion.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`), paying close attention to permission tests.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=rbac`). Review uncovered lines in permission logic and caching.
[ ] Manually test API interactions with different users/roles, verifying field visibility and create/update restrictions. Test Admin interface for managing `FieldPermission`.
[ ] Review API documentation draft related to field permissions.

## 5. Follow-up Actions

[ ] Address TODOs (e.g., Admin widget for `field_name`, refine cache invalidation).
[ ] Create Pull Request.
[ ] Update API/RBAC documentation.
[ ] Ensure relevant concrete serializers inherit the `FieldPermissionSerializerMixin`.

--- END OF FILE rbac_implementation_steps.md ---