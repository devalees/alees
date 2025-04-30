
# Audit Logging System - Implementation Steps

## 1. Overview

**Model Name(s):**
`AuditLog`

**Corresponding PRD:**
`audit_logging_system_prd.md`

**Depends On:**
`Timestamped` (for inheritance), `User` (`settings.AUTH_USER_MODEL`), `Organization`, `ContentType` framework, potentially Celery (for async logging), middleware like `django-crum` (for user context).

**Key Features:**
Creates a historical trail of significant data changes (CRUD) and events (Login, Permissions) in a dedicated `AuditLog` model. Uses signals for automatic event capturing. Provides Admin/API for viewing logs.

**Primary Location(s):**
`audit/` (New dedicated app) or `core/`

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `User`, `Organization`, `ContentType`) are implemented and migrated.
[ ] **Create new Django app:** `python manage.py startapp audit`.
[ ] Add `'audit'` (or `core` if placed there) and `'django.contrib.contenttypes'` to `INSTALLED_APPS`.
[ ] Ensure middleware for getting current user (e.g., `django-crum`) is configured.
[ ] Ensure Celery is set up if asynchronous logging is desired (Decision: Sync or Async? Assuming **Sync initially**).
[ ] Ensure `factory-boy` is set up. Factories for `User`, `Organization`, and representative auditable models (e.g., `Product`) exist.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 `AuditLog` Model Definition (`audit/models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`audit/tests/unit/test_models.py`) verifying:
      *   An `AuditLog` instance can be created with required/nullable fields (`user`, `organization`, `action_type`, `content_type`, `object_id`, etc.).
      *   Default timestamping (via `Timestamped.created_at`) works.
      *   `changes` and `context` store JSON correctly.
      *   `__str__` method provides a useful representation.
      Run; expect failure (`AuditLog` doesn't exist).
  [ ] Define the `AuditLog` class in `audit/models.py`.
  [ ] Add required inheritance: `Timestamped`.
      ```python
      # audit/models.py
      from django.conf import settings
      from django.contrib.contenttypes.fields import GenericForeignKey
      from django.contrib.contenttypes.models import ContentType
      from django.db import models
      from django.utils import timezone # If using separate timestamp
      from django.utils.translation import gettext_lazy as _

      from core.models import Timestamped # Adjust import path
      # Import Organization based on final location
      from api.v1.base_models.organization.models import Organization # Adjust path

      # Define Action Type Choices (Store centrally, e.g., audit/choices.py)
      class AuditActionType:
          CREATE = 'CREATE'
          UPDATE = 'UPDATE'
          DELETE = 'DELETE'
          LOGIN_SUCCESS = 'LOGIN_SUCCESS'
          LOGIN_FAILED = 'LOGIN_FAILED'
          LOGOUT = 'LOGOUT'
          PERMISSION_ASSIGN = 'PERMISSION_ASSIGN'
          PERMISSION_REVOKE = 'PERMISSION_REVOKE'
          # ... add more specific types as needed

          CHOICES = [
              (CREATE, _('Create')),
              (UPDATE, _('Update')),
              (DELETE, _('Delete')),
              (LOGIN_SUCCESS, _('Login Success')),
              (LOGIN_FAILED, _('Login Failed')),
              (LOGOUT, _('Logout')),
              (PERMISSION_ASSIGN, _('Permission Assigned')),
              (PERMISSION_REVOKE, _('Permission Revoked')),
              # ...
          ]

      class AuditLog(Timestamped): # Inherits created_at, updated_at
          user = models.ForeignKey(
              settings.AUTH_USER_MODEL,
              verbose_name=_("User"),
              on_delete=models.SET_NULL,
              null=True, blank=True, db_index=True
          )
          organization = models.ForeignKey(
              Organization,
              verbose_name=_("Organization Context"),
              on_delete=models.SET_NULL,
              null=True, blank=True, db_index=True
          )
          action_type = models.CharField(
              _("Action Type"), max_length=50, choices=AuditActionType.CHOICES, db_index=True
          )
          # Generic relation to the object acted upon
          content_type = models.ForeignKey(
              ContentType,
              verbose_name=_("Content Type"),
              on_delete=models.SET_NULL, # Keep log even if model type is deleted
              null=True, blank=True, db_index=True
          )
          object_id = models.CharField(
              _("Object ID"), max_length=255, null=True, blank=True, db_index=True,
              help_text=_("Primary key of the object as string.")
          )
          content_object = GenericForeignKey('content_type', 'object_id')

          object_repr = models.CharField(
              _("Object Representation"), max_length=255, blank=True,
              help_text=_("A human-readable representation of the object.")
          )
          changes = models.JSONField(
              _("Changes"), null=True, blank=True, default=None, # Use None default for nullable JSON
              help_text=_("JSON detailing field changes for UPDATE actions (e.g., {'field': {'old': 'val1', 'new': 'val2'}}).")
          )
          context = models.JSONField(
              _("Context"), null=True, blank=True, default=None,
              help_text=_("Additional context (e.g., IP address, session key).")
          )

          class Meta:
              verbose_name = _("Audit Log Entry")
              verbose_name_plural = _("Audit Log Entries")
              ordering = ['-created_at'] # Show newest first
              indexes = [
                  models.Index(fields=['content_type', 'object_id']),
                  models.Index(fields=['organization', 'user']),
                  models.Index(fields=['action_type']),
              ]

          def __str__(self):
              return f"{self.get_action_type_display()} on {self.object_repr or self.object_id or 'System'} by {self.user or 'System'}"

      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.2 Factory Definition (`audit/tests/factories.py`)

  [ ] Define `AuditLogFactory` in `audit/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from django.contrib.contenttypes.models import ContentType
      from ..models import AuditLog, AuditActionType
      # Import factories for User, Organization, potentially a sample model like Product
      from api.v1.base_models.user.tests.factories import UserFactory
      from api.v1.base_models.organization.tests.factories import OrganizationFactory
      # from api.v1.base_models.common.tests.factories import ProductFactory

      class AuditLogFactory(DjangoModelFactory):
          class Meta:
              model = AuditLog

          user = factory.SubFactory(UserFactory)
          organization = factory.SubFactory(OrganizationFactory)
          action_type = factory.Iterator([choice[0] for choice in AuditActionType.CHOICES])
          # Example: Link to a product instance
          # content_object = factory.SubFactory(ProductFactory)
          # object_repr = factory.LazyAttribute(lambda o: str(o.content_object) if o.content_object else '')
          changes = None
          context = None

          # Correctly set GFK fields if content_object is set
          @factory.lazy_attribute
          def content_type(self):
              if self.content_object:
                  return ContentType.objects.get_for_model(self.content_object)
              return None

          @factory.lazy_attribute
          def object_id(self):
              if self.content_object:
                  return str(self.content_object.pk) # Use string representation
              return None
      ```
  [ ] **(Test)** Write simple tests ensuring the factory creates valid instances, including setting the GFK correctly.

  ### 3.3 Helper Function (`audit/utils.py` or `audit/services.py`)

  [ ] **(Test First)** Write Unit Tests for the `log_audit_event` helper function. Mock the `AuditLog.objects.create` call and verify it's called with the correct arguments based on inputs. Test masking logic if implemented here. Test context merging.
  [ ] Create `audit/utils.py`. Define `log_audit_event` helper:
      ```python
      # audit/utils.py
      from django.contrib.contenttypes.models import ContentType
      from django.utils.encoding import smart_str
      from crum import get_current_request # To get IP/context if needed
      from .models import AuditLog

      def get_object_repr(instance):
          """Get a limited string representation."""
          if instance is None:
              return None
          try:
              return smart_str(instance)[:255] # Limit length
          except Exception:
              return f"<{instance._meta.verbose_name} object ({instance.pk})>"

      def calculate_changes(instance, update_fields=None):
          """
          Calculates the changes dictionary for an UPDATE event.
          Placeholder: Implement actual diffing logic here.
          This is complex - requires comparing current state to previous state.
          Libraries like django-simple-history or careful signal handling needed.
          Returns None if no changes detected or not applicable.
          """
          # TODO: Implement robust change detection logic
          # Basic example (only works if update_fields is reliable AND old values known)
          # if update_fields:
          #    # Need mechanism to get old values (e.g., fetch from DB before save)
          #    pass
          return None # Placeholder

      def get_request_context():
          """Extract basic context from the current request."""
          request = get_current_request()
          if request:
              ip_address = request.META.get('REMOTE_ADDR')
              # Add other context like session key if needed
              return {'ip_address': ip_address}
          return None

      def log_audit_event(
          user, action_type, content_object=None, organization=None,
          changes=None, context=None, object_repr_override=None
      ):
          """Creates an AuditLog entry."""
          ctype = None
          object_id_str = None
          obj_repr = object_repr_override

          if content_object:
              ctype = ContentType.objects.get_for_model(content_object)
              object_id_str = str(content_object.pk)
              if obj_repr is None: # Only get default repr if not overridden
                  obj_repr = get_object_repr(content_object)

          # TODO: Implement sensitive field masking for 'changes' dict here

          final_context = get_request_context() or {}
          if context: # Merge provided context
              final_context.update(context)

          try:
              AuditLog.objects.create(
                  user=user,
                  organization=organization,
                  action_type=action_type,
                  content_type=ctype,
                  object_id=object_id_str,
                  object_repr=obj_repr,
                  changes=changes,
                  context=final_context or None # Store None if empty
              )
          except Exception as e:
              # Log error to standard logging, but don't crash primary operation
              import logging
              logger = logging.getLogger(__name__)
              logger.error(f"Failed to create AuditLog entry: {e}", exc_info=True)

      ```
  [ ] Run tests for helper; expect pass. Refactor.

  ### 3.4 Signal Receivers (`audit/signals.py`)

  [ ] **(Test First)** Write Integration Tests (`audit/tests/integration/test_signals.py`) using `@pytest.mark.django_db`.
      *   Test `post_save` on a sample audited model (e.g., `Product`):
          *   Create instance -> verify AuditLog created with `action_type='CREATE'`, correct user, object details.
          *   Update instance -> verify AuditLog created with `action_type='UPDATE'`, correct user, object details, and placeholder `changes=None` (or basic diff if implemented).
      *   Test `post_delete` -> verify `AuditLog` created with `action_type='DELETE'`.
      *   Test auth signals (`user_logged_in`, etc.) -> verify correct AuditLog created with user and context (mock request for IP).
      Run; expect failure (receivers not connected).
  [ ] Create `audit/signals.py`. Define signal receivers using the helper function.
      ```python
      # audit/signals.py
      from django.conf import settings
      from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
      from django.db.models.signals import post_save, post_delete
      from django.dispatch import receiver
      from crum import get_current_user

      from .models import AuditLog, AuditActionType
      from .utils import log_audit_event, calculate_changes # Import helper

      # List of models to automatically audit on CRUD
      # Get this from settings or explicitly list them
      AUDITED_MODELS = [
          'organization.Organization', 'user.UserProfile', 'common.Product', # etc.
          # Use 'app_label.ModelName' format
      ]

      def get_model_from_string(model_string):
          from django.apps import apps
          try:
              app_label, model_name = model_string.split('.')
              return apps.get_model(app_label, model_name)
          except (ValueError, LookupError):
              return None

      def get_org_from_instance(instance):
          # Helper to find organization context
          if hasattr(instance, 'organization'):
              return instance.organization
          if hasattr(instance, 'user') and hasattr(instance.user, 'profile') \
             and hasattr(instance.user.profile, 'primary_organization'):
              return instance.user.profile.primary_organization
          # Add other common ways to find org context
          return None

      @receiver(post_save)
      def audit_post_save(sender, instance, created, raw, using, update_fields, **kwargs):
          """Audit model CREATE and UPDATE events."""
          model_label = f"{sender._meta.app_label}.{sender._meta.model_name}"
          if raw or model_label not in AUDITED_MODELS: # Ignore fixture loading and non-audited models
              return

          user = get_current_user()
          organization = get_org_from_instance(instance)
          action = AuditActionType.CREATE if created else AuditActionType.UPDATE
          changes = None
          if not created:
              changes = calculate_changes(instance, update_fields) # Basic diff logic here

          log_audit_event(
              user=user,
              organization=organization,
              action_type=action,
              content_object=instance,
              changes=changes,
          )

      @receiver(post_delete)
      def audit_post_delete(sender, instance, using, **kwargs):
          """Audit model DELETE events."""
          model_label = f"{sender._meta.app_label}.{sender._meta.model_name}"
          if model_label not in AUDITED_MODELS:
              return

          user = get_current_user()
          organization = get_org_from_instance(instance)

          log_audit_event(
              user=user,
              organization=organization,
              action_type=AuditActionType.DELETE,
              content_object=instance, # Pass instance for object_repr even though it's deleted
              object_repr_override=str(instance) # Ensure representation captured
          )

      # --- Auth Signals ---
      @receiver(user_logged_in)
      def audit_user_logged_in(sender, request, user, **kwargs):
          # Note: organization context might be harder to get here reliably
          log_audit_event(user=user, action_type=AuditActionType.LOGIN_SUCCESS)

      @receiver(user_login_failed)
      def audit_user_login_failed(sender, credentials, request, **kwargs):
          # User object isn't available here
          log_audit_event(user=None, action_type=AuditActionType.LOGIN_FAILED, context={'username_attempt': credentials.get('username')})

      @receiver(user_logged_out)
      def audit_user_logged_out(sender, request, user, **kwargs):
           if user: # User might be None if session expired before logout
               log_audit_event(user=user, action_type=AuditActionType.LOGOUT)

      # --- Connect signals dynamically based on AUDITED_MODELS list ---
      # Or connect explicitly if list is small
      # Example explicit connection:
      # post_save.connect(audit_post_save, sender=Product)
      # post_delete.connect(audit_post_delete, sender=Product)

      # TODO: Implement dynamic connection based on AUDITED_MODELS setting
      # TODO: Add receivers for permission/role changes (m2m_changed)

      ```
  [ ] Connect signals in `audit/apps.py`:
      ```python
      # audit/apps.py
      from django.apps import AppConfig

      class AuditConfig(AppConfig):
          default_auto_field = 'django.db.models.BigAutoField'
          name = 'audit'

          def ready(self):
              try:
                  import audit.signals # Connect signals
              except ImportError:
                  pass
      ```
  [ ] Run signal integration tests; expect pass. Refactor receiver logic, especially change calculation and org context retrieval.

  ### 3.5 Admin Registration (`audit/admin.py`)

  [ ] Create `audit/admin.py`. Define `AuditLogAdmin`.
      ```python
      # audit/admin.py
      from django.contrib import admin
      from django.utils.html import format_html
      # Consider django-json-widget for better JSON display
      # from jsoneditor.forms import JSONEditor
      # from django.db import models

      from .models import AuditLog

      @admin.register(AuditLog)
      class AuditLogAdmin(admin.ModelAdmin):
          list_display = ('created_at', 'user_display', 'organization', 'action_type', 'object_link', 'object_repr')
          list_filter = ('action_type', 'content_type', ('created_at', admin.DateFieldListFilter), 'organization', 'user')
          search_fields = ('user__username', 'object_repr', 'object_id', 'changes', 'context') # Searching JSON might be slow
          list_select_related = ('user', 'organization', 'content_type')
          readonly_fields = [f.name for f in AuditLog._meta.fields] # Make all fields read-only
          # formfield_overrides = { # Example using django-json-widget
          #     models.JSONField: {'widget': JSONEditor},
          # }

          def has_add_permission(self, request): return False
          def has_change_permission(self, request, obj=None): return False
          def has_delete_permission(self, request, obj=None): return False

          @admin.display(description='User')
          def user_display(self, obj):
              return obj.user or 'System'

          @admin.display(description='Object')
          def object_link(self, obj):
              # Create link to the related object's admin page if possible
              if obj.content_object and obj.content_type:
                  try:
                      admin_url = admin.site.get_admin_url(obj.content_object)
                      return format_html('<a href="{}">{}</a>', admin_url, obj.object_repr or obj.object_id)
                  except Exception:
                       return obj.object_repr or obj.object_id
              return obj.object_repr or obj.object_id

      ```
  [ ] **(Manual Test):** Perform actions (create/update/delete audited models, login/logout). Verify logs appear in Admin. Check filters/search. Verify read-only nature.

  ### 3.6 API Endpoint Definition (Optional - Read-Only)

  [ ] **(Test First)** Write API tests for `/api/v1/audit-logs/`. Test permissions (admin/auditor only). Test filtering by user, org, type, date, object. Test pagination.
  [ ] Define `AuditLogSerializer` (read-only).
  [ ] Define `AuditLogViewSet` (inheriting `ReadOnlyModelViewSet`). Add necessary filters (`django-filter` recommended here). Secure with appropriate permission class.
  [ ] Define URL routing.
  [ ] Run API tests; expect pass.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=audit`). Review uncovered signal/helper logic.
[ ] Manually test Audit Log generation and viewing via Admin for key scenarios.
[ ] Review related documentation.

## 5. Follow-up Actions

[ ] Address TODOs (robust change calculation, dynamic signal connection, M2M auditing).
[ ] Implement Archiving/Purging strategy (requires separate command/task).
[ ] Implement Data Masking for sensitive fields in `changes`.
[ ] Create Pull Request.
[ ] Update documentation (list of audited models, action types, etc.).

--- END OF FILE auditlogging_implementation_steps.md ---