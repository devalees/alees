
# Notification System - Implementation Steps

## 1. Overview

**System Name:**
Notification System

**Corresponding PRD:**
`notification_prd.md` (Simplified version)

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `UserProfile` (for preferences), `Organization`, `ContentType` (for GFKs), Celery infrastructure, Django Email Backend configuration.

**Key Features:**
Provides in-app notifications (`Notification` model) and triggers asynchronous email sending via Celery. Includes optional templating (`NotificationTemplate`) and respects user preferences stored on `UserProfile`. Exposes APIs for users to view/manage their notifications.

**Primary Location(s):**
*   Models: `notifications/models.py` (New dedicated app recommended)
*   Service Function: `notifications/services.py`
*   Celery Tasks: `notifications/tasks.py`
*   Admin: `notifications/admin.py`
*   API: `api/v1/notifications/` (New app or within an existing API structure)
*   Templates (Email): `notifications/templates/notifications/email/`

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `UserProfile`, `Organization`, `ContentType`) are implemented and migrated.
[ ] Verify Celery infrastructure (Broker like Redis, worker setup) is configured and operational.
[ ] Verify Django Email Backend is configured in settings (e.g., Console backend for dev, SMTP/API service for prod).
[ ] Verify `UserProfile` model has the `notification_preferences` JSONField defined.
[ ] **Create new Django app:** `python manage.py startapp notifications`.
[ ] Add `'notifications'` to `INSTALLED_APPS`.
[ ] Ensure `factory-boy` is set up. Factories for `User`, `UserProfile`, `Organization` exist.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 `NotificationTemplate` Model Definition (Optional but Recommended)

  [ ] **(Test First)** Write Unit Tests (`notifications/tests/unit/test_models.py`) verifying `NotificationTemplate` creation, unique `template_key`, field storage, `__str__`.
  [ ] Define `NotificationTemplate` in `notifications/models.py`. Inherit `Timestamped`, `Auditable`.
      ```python
      # notifications/models.py
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from core.models import Timestamped, Auditable # Adjust path

      class NotificationTemplate(Timestamped, Auditable):
          template_key = models.CharField(
              _("Template Key"), max_length=100, unique=True, db_index=True,
              help_text=_("Unique key to identify this template (e.g., 'invoice_approved_email').")
          )
          name = models.CharField(_("Template Name"), max_length=255) # For admin identification
          subject_template = models.TextField(
              _("Subject Template"), help_text=_("Django template syntax for email subject.")
          )
          body_template_txt = models.TextField(
              _("Text Body Template"), help_text=_("Django template syntax for plain text email body.")
          )
          body_template_html = models.TextField(
              _("HTML Body Template"), blank=True,
              help_text=_("Django template syntax for HTML email body (optional).")
          )

          class Meta:
              verbose_name = _("Notification Template")
              verbose_name_plural = _("Notification Templates")
              ordering = ['template_key']

          def __str__(self):
              return self.name or self.template_key
      ```
  [ ] Run template model tests; expect pass. Refactor.

  ### 3.2 `Notification` Model Definition (`notifications/models.py`)

  [ ] **(Test First)** Write Unit Tests (`notifications/tests/unit/test_models.py`) verifying:
      *   `Notification` creation with required fields (`recipient`).
      *   Defaults (`level`, `status`). `read_at` is null initially.
      *   FKs (`recipient`, `organization`, `content_type`) work.
      *   GFK (`content_object`) works.
      *   `__str__` works. Inheritance works.
      Run; expect failure.
  [ ] Define `Notification` model in `notifications/models.py`. Inherit `Timestamped`, `Auditable`, `OrganizationScoped`.
      ```python
      # notifications/models.py
      # ... (imports for models, Timestamped, Auditable, OrganizationScoped, User, Org, ContentType) ...
      from django.utils import timezone

      class NotificationLevel:
          INFO = 'INFO'; SUCCESS = 'SUCCESS'; WARNING = 'WARNING'; ERROR = 'ERROR'; ACTION = 'ACTION'
          CHOICES = [...]
      class NotificationStatus:
          UNSENT = 'UNSENT'; SENT = 'SENT'; DELIVERED = 'DELIVERED'; READ = 'READ'; ACTIONED = 'ACTIONED'; ERROR = 'ERROR'
          CHOICES = [...]

      class Notification(Timestamped, Auditable, OrganizationScoped):
          # organization field from OrganizationScoped
          # created_by/updated_by from Auditable (often system/triggering user)
          # created_at/updated_at from Timestamped

          recipient = models.ForeignKey(
              settings.AUTH_USER_MODEL, verbose_name=_("Recipient"),
              on_delete=models.CASCADE, related_name='notifications', db_index=True
          )
          level = models.CharField(
              _("Level"), max_length=10, choices=NotificationLevel.CHOICES,
              default=NotificationLevel.INFO, db_index=True
          )
          title = models.CharField(_("Title"), max_length=255, blank=True)
          message = models.TextField(_("Message"))
          status = models.CharField(
              _("Status"), max_length=10, choices=NotificationStatus.CHOICES,
              default=NotificationStatus.UNSENT, db_index=True
          )
          read_at = models.DateTimeField(_("Read At"), null=True, blank=True)
          action_url = models.URLField(_("Action URL"), blank=True, max_length=1024)
          action_text = models.CharField(_("Action Text"), max_length=50, blank=True)

          # Generic link to originating object
          content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
          object_id = models.CharField(_("Object ID"), max_length=255, null=True, blank=True, db_index=True)
          content_object = GenericForeignKey('content_type', 'object_id')

          # For filtering and user preferences
          notification_type = models.CharField(
              _("Notification Type Code"), max_length=100, blank=True, db_index=True,
              help_text=_("Code identifying the event type (e.g., 'invoice_approved').")
          )

          class Meta:
              verbose_name = _("Notification")
              verbose_name_plural = _("Notifications")
              ordering = ['-created_at']
              indexes = [
                  models.Index(fields=['recipient', 'status']),
                  models.Index(fields=['recipient', 'read_at']),
                  models.Index(fields=['content_type', 'object_id']),
                  models.Index(fields=['notification_type']),
              ]

          def __str__(self):
              return self.title or f"Notification for {self.recipient_id}"

          def mark_as_read(self):
              if not self.read_at:
                  self.status = NotificationStatus.READ
                  self.read_at = timezone.now()
                  self.save(update_fields=['status', 'read_at', 'updated_at']) # Optimize save

          def mark_as_unread(self): # If needed
              if self.read_at:
                  self.status = NotificationStatus.DELIVERED # Or SENT?
                  self.read_at = None
                  self.save(update_fields=['status', 'read_at', 'updated_at'])
      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.3 Factory Definitions (`notifications/tests/factories.py`)

  [ ] Define `NotificationTemplateFactory` (if using templates) and `NotificationFactory`.
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from ..models import Notification, NotificationTemplate, NotificationLevel, NotificationStatus
      from api.v1.base_models.user.tests.factories import UserFactory
      from api.v1.base_models.organization.tests.factories import OrganizationFactory

      class NotificationTemplateFactory(DjangoModelFactory): ...

      class NotificationFactory(DjangoModelFactory):
          class Meta: model = Notification

          recipient = factory.SubFactory(UserFactory)
          organization = factory.LazyAttribute(lambda o: o.recipient.profile.primary_organization) # Needs profile link setup
          level = factory.Iterator([choice[0] for choice in NotificationLevel.CHOICES])
          title = factory.Faker('sentence', nb_words=4)
          message = factory.Faker('paragraph')
          status = NotificationStatus.SENT # Or UNSENT
          notification_type = factory.Sequence(lambda n: f'test_event_{n}')
          # Add content_object if needed for tests
      ```
  [ ] **(Test)** Write simple tests ensuring factories create valid instances.

  ### 3.4 Admin Registration (`notifications/admin.py`)

  [ ] Create `notifications/admin.py`. Register `NotificationTemplate` (if used) and `Notification`.
      ```python
      from django.contrib import admin
      from .models import Notification, NotificationTemplate

      @admin.register(NotificationTemplate)
      class NotificationTemplateAdmin(admin.ModelAdmin): ... # Basic setup

      @admin.register(Notification)
      class NotificationAdmin(admin.ModelAdmin):
          list_display = ('id', 'recipient', 'organization', 'level', 'title', 'notification_type', 'status', 'created_at')
          list_filter = ('status', 'level', 'notification_type', 'organization', 'created_at')
          search_fields = ('recipient__username', 'title', 'message', 'notification_type')
          list_select_related = ('recipient', 'organization')
          readonly_fields = [f.name for f in Notification._meta.fields if f.name != 'status'] # Allow changing status? Or only via API?
          # Make read_only usually, as they are system generated
          def has_add_permission(self, request): return False
          def has_change_permission(self, request, obj=None): return True # Allow status change?
          def has_delete_permission(self, request, obj=None): return True # Allow deletion?
      ```
  [ ] **(Manual Test):** Verify Admin interface.

  ### 3.5 Migrations

  [ ] Run `python manage.py makemigrations notifications`.
  [ ] **Review generated migration file(s) carefully.** Check FKs, indexes, choices.
  [ ] Run `python manage.py migrate` locally.
  [ ] Create data migration to populate initial `NotificationTemplate`s if needed. Run migrate again.

  ### 3.6 Notification Service/Function (`notifications/services.py`)

  [ ] **(Test First)** Write Unit Tests (`notifications/tests/unit/test_services.py`) for the `send_notification` function.
      *   Mock `Notification.objects.create`. Mock Celery `task.delay()`. Mock `UserProfile.notification_preferences`.
      *   Test case where user opted out -> assert nothing created/queued.
      *   Test case requesting 'in_app' -> assert `Notification.objects.create` called.
      *   Test case requesting 'email' -> assert `send_email_notification_task.delay` called with correct args.
      *   Test template rendering logic if applicable.
      Run; expect failure.
  [ ] Create `notifications/services.py`. Implement `send_notification` logic.
      ```python
      # notifications/services.py
      from django.template.loader import render_to_string
      from .models import Notification, NotificationTemplate, NotificationLevel, NotificationStatus
      from .tasks import send_email_notification_task # Import celery task

      def send_notification(recipient, notification_type, context=None,
                          level=NotificationLevel.INFO, title=None, message=None,
                          action_url=None, action_text=None,
                          content_object=None, organization=None,
                          channels=['in_app', 'email']):
          """
          Central function to create and dispatch notifications.
          Checks user preferences before sending.
          """
          if not recipient or not recipient.is_active: return
          context = context or {}

          # 1. Check User Preferences
          prefs = getattr(recipient, 'profile', {}).notification_preferences or {}
          type_prefs = prefs.get(notification_type, {'in_app': True, 'email': True}) # Default to True

          active_channels = [
              ch for ch in channels
              if type_prefs.get(ch, True) # Send if preference exists and is True, or if no preference set
          ]
          if not active_channels: return # User opted out of all requested channels

          # 2. Determine Organization context
          if not organization:
              organization = getattr(recipient, 'profile', None).primary_organization # Example lookup

          # 3. Prepare Content (Use defaults or Template)
          final_title = title
          final_message = message
          subject = None
          html_message = None

          # Try finding a template if message/title not provided directly
          template_key_base = f"{notification_type}"
          if not final_message:
               try:
                   template = NotificationTemplate.objects.get(template_key=template_key_base+"_email") # Or logic to find appropriate template
                   subject = render_to_string(None, template.subject_template, context).strip()
                   final_message = render_to_string(None, template.body_template_txt, context)
                   if template.body_template_html:
                       html_message = render_to_string(None, template.body_template_html, context)
                   if not final_title: final_title = subject # Use subject as title if needed
               except NotificationTemplate.DoesNotExist:
                    # Fallback or error if direct message also not provided
                    if not final_message: # Ensure we have content
                         import logging
                         logger = logging.getLogger(__name__)
                         logger.warning(f"No message or template found for notification type {notification_type}")
                         return

          # 4. Create In-App Notification
          notification_instance = None
          if 'in_app' in active_channels:
               try:
                   notification_instance = Notification.objects.create(
                       recipient=recipient,
                       organization=organization,
                       level=level,
                       title=final_title or '',
                       message=final_message,
                       status=NotificationStatus.DELIVERED, # Assume delivered if created
                       action_url=action_url or '',
                       action_text=action_text or '',
                       content_object=content_object,
                       notification_type=notification_type,
                       # created_by might be system or triggering user if passed in context
                   )
               except Exception as e: # Catch DB errors etc.
                   import logging; logging.getLogger(__name__).error(f"Failed to save in-app notification: {e}", exc_info=True)


          # 5. Queue External Notifications (Email)
          if 'email' in active_channels and recipient.email:
               # Queue Celery task
               send_email_notification_task.delay(
                   recipient_pk=recipient.pk,
                   subject=subject or final_title or "Notification", # Ensure subject exists
                   text_body=final_message,
                   html_body=html_message,
                   notification_pk=getattr(notification_instance, 'pk', None) # Pass PK to update status
               )

          # 6. Queue other channels (SMS, Push) later

          return notification_instance
      ```
  [ ] Run service tests; expect pass. Refactor.

  ### 3.7 Celery Task Definition (`notifications/tasks.py`)

  [ ] **(Test First)** Write Unit Tests (`notifications/tests/unit/test_tasks.py`) for `send_email_notification_task`. Mock Django's `send_mail` function and the `Notification.objects.get/save` calls. Verify `send_mail` is called with correct args. Verify `Notification` status is updated on success/failure.
  [ ] Create `notifications/tasks.py`. Define the Celery task:
      ```python
      # notifications/tasks.py
      from celery import shared_task
      from django.core.mail import send_mail
      from django.conf import settings
      from django.contrib.auth import get_user_model
      from .models import Notification, NotificationStatus
      import logging

      logger = logging.getLogger(__name__)
      User = get_user_model()

      @shared_task(bind=True, max_retries=3, default_retry_delay=60) # Example retry config
      def send_email_notification_task(self, recipient_pk, subject, text_body, html_body=None, notification_pk=None):
          """Sends an email notification asynchronously."""
          try:
              recipient = User.objects.get(pk=recipient_pk)
              if not recipient.email:
                  logger.warning(f"Recipient User {recipient_pk} has no email address.")
                  return # Or update notification status?

              send_mail(
                  subject=subject,
                  message=text_body,
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=[recipient.email],
                  html_message=html_body,
                  fail_silently=False, # Let Celery handle retries on failure
              )

              # Optionally update Notification status if PK provided
              if notification_pk:
                  try:
                      notification = Notification.objects.get(pk=notification_pk)
                      notification.status = NotificationStatus.SENT # Or DELIVERED? Depends on email provider feedback
                      notification.save(update_fields=['status', 'updated_at'])
                  except Notification.DoesNotExist:
                      logger.warning(f"Notification {notification_pk} not found to update status after email send.")

              logger.info(f"Email notification sent successfully to user {recipient_pk}.")

          except User.DoesNotExist:
              logger.error(f"Recipient User {recipient_pk} not found for email notification.")
              # No retry if user doesn't exist
          except Exception as exc:
              logger.error(f"Error sending email notification to user {recipient_pk}: {exc}", exc_info=True)
              # Update notification status to ERROR if possible
              if notification_pk:
                   try:
                      Notification.objects.filter(pk=notification_pk).update(status=NotificationStatus.ERROR)
                   except Exception: pass # Ignore secondary error
              # Retry based on Celery task decorator settings
              raise self.retry(exc=exc)

      ```
  [ ] Ensure Celery workers discover tasks from this file.
  [ ] Run task tests; expect pass. Refactor.

  ### 3.8 API ViewSet Definition (`api/v1/notifications/views.py`)

  [ ] **(Test First)** Write API Tests (`api/v1/notifications/tests/test_endpoints.py`) for:
      *   `GET /notifications/`: List user's own notifications, test pagination, test filtering by read/unread. Verify Org Scoping implicitly via user.
      *   `POST /notifications/{id}/mark-read/`: Test marking specific notification read, check status change. Test permissions (only owner).
      *   `POST /notifications/mark-all-read/`: Test marking all read.
  [ ] Create `api/v1/notifications/views.py`. Define `NotificationViewSet`.
      ```python
      # api/v1/notifications/views.py
      from rest_framework import viewsets, permissions, status, mixins
      from rest_framework.decorators import action
      from rest_framework.response import Response
      from notifications.models import Notification # Adjust import path
      from notifications.serializers import NotificationSerializer # Need a serializer

      class NotificationViewSet(mixins.ListModelMixin,
                              mixins.RetrieveModelMixin,
                              viewsets.GenericViewSet):
          """
          API endpoint for viewing and managing user's notifications.
          """
          serializer_class = NotificationSerializer
          permission_classes = [permissions.IsAuthenticated]
          # No filter backends needed if only filtering by recipient

          def get_queryset(self):
              """Only return notifications for the current authenticated user."""
              return Notification.objects.filter(
                  recipient=self.request.user
              ).select_related('organization') # Add other selects if needed by serializer

          @action(detail=True, methods=['post'], url_path='mark-read')
          def mark_read(self, request, pk=None):
              notification = self.get_object() # Gets notification filtered by user via get_queryset
              notification.mark_as_read()
              serializer = self.get_serializer(notification)
              return Response(serializer.data)

          @action(detail=False, methods=['post'], url_path='mark-all-read')
          def mark_all_read(self, request):
              updated_count = Notification.objects.filter(
                  recipient=request.user, status=NotificationStatus.DELIVERED # Or SENT?
              ).update(status=NotificationStatus.READ, read_at=timezone.now())
              return Response({'status': 'success', 'updated_count': updated_count})

      ```
  [ ] Create `NotificationSerializer`.
  [ ] Run API tests; expect pass. Refactor.

  ### 3.9 URL Routing (`api/v1/notifications/urls.py`)

  [ ] Create `api/v1/notifications/urls.py`. Import `NotificationViewSet`. Register with router.
  [ ] Include notification URLs in main `api/v1/urls.py`.
  [ ] **(Test):** Rerun basic API tests.

  ### 3.10 Trigger Integration

  [ ] **(Test First)** In integration tests for *other* features (e.g., Workflow transitions, Comment creation), add assertions verifying that the `send_notification` service (or Celery task) was called correctly.
  [ ] Integrate calls to `notifications.services.send_notification` at appropriate points in the codebase (signal receivers, workflow actions, views).
  [ ] Run tests; expect pass.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=notifications`).
[ ] Manually trigger events that should create notifications. Check in-app list via API. Check emails (using console/mailhog locally). Check Admin UI.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs (Robust change calculation for audit logs, dynamic signal connection, M2M auditing in Audit system if needed).
[ ] Refine user preferences model/API.
[ ] Implement other delivery channels (SMS, Push) as needed.
[ ] Create Pull Request.
[ ] Update API documentation.

--- END OF FILE notification_implementation_steps.md ---