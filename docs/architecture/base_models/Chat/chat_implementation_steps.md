
# Chat System - Implementation Steps

## 1. Overview

**System Name:**
Chat System

**Corresponding PRD:**
`chat_prd.md` (Simplified version)

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `Organization`, `FileStorage`, `Notification` System, potentially `Search` System, Celery, Redis (for Channel Layer), ASGI Server (Daphne/Uvicorn). Requires `django-channels`, `channels-redis`.

**Key Features:**
Real-time direct and group messaging (`ChatRoom`, `ChatMessage` models). Uses Django Channels/WebSockets for real-time delivery. Supports basic threading, file attachments, presence, typing indicators. Integrates with notifications and search. Scoped by Organization.

**Primary Location(s):**
*   Models, Serializers, Views, Consumers, Routing: `chat/` (New dedicated app)
*   ASGI Setup: `config/asgi.py`, `config/settings/base.py`
*   API URLs: `api/v1/chat/` (New dedicated API structure)

## 2. Prerequisites

[ ] Verify all prerequisite models/mixins (`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `Organization`, `FileStorage`) are implemented and migrated.
[ ] Verify Celery & Redis infrastructure is operational.
[ ] Verify Notification system (`send_notification` service) is available.
[ ] Verify FileStorage upload API exists.
[ ] **Install Channels libraries:** `pip install django-channels channels-redis`.
[ ] **Create new Django app:** `python manage.py startapp chat`.
[ ] Add `'chat'` and `'channels'` to `INSTALLED_APPS` in `config/settings/base.py`.
[ ] Ensure `factory-boy` is set up. Factories for `User`, `Organization`, `FileStorage` exist.
[ ] Configure **ASGI Application** in `config/asgi.py`.
[ ] Configure **Channel Layer** (`CHANNEL_LAYERS`) in `config/settings/base.py` (using `channels_redis`).

## 3. Implementation Steps (TDD Workflow)

  *(Models -> Channels Setup -> API -> WebSocket Logic)*

  ### 3.1 Core Model Definitions (`chat/models.py`)

  [ ] **(Test First - ChatRoom)** Write Unit Tests (`chat/tests/unit/test_models.py`) verifying `ChatRoom` creation, fields, defaults, M2M `participants`, inheritance, `__str__`.
  [ ] Define `ChatRoom` model. Inherit `Timestamped`, `Auditable`, `OrganizationScoped`. Add `name`, `room_type`, `participants` (M2M to User), `is_active`, `custom_fields`. Define Meta.
  [ ] Run ChatRoom tests; expect pass. Refactor.
  [ ] **(Test First - ChatMessage)** Write Unit Tests verifying `ChatMessage` creation, fields, defaults, FKs (`room`, `sender`, `parent`), M2M `attachments`, inheritance, `__str__`.
  [ ] Define `ChatMessage` model. Inherit `Timestamped`, `Auditable`, `OrganizationScoped`. Add `room` (FK), `sender` (FK), `content`, `parent` (FK to self), `attachments` (M2M to FileStorage), `is_edited`, `is_deleted`, `custom_fields`. Define Meta, indexes.
  [ ] Run ChatMessage tests; expect pass. Refactor.
  [ ] *(Optional: Define `ChatParticipant` through model if per-user room state needed)*.

  ### 3.2 Factory Definitions (`chat/tests/factories.py`)

  [ ] Define `ChatRoomFactory` and `ChatMessageFactory`. Handle `participants` M2M and `attachments` M2M in factories (e.g., using post-generation). Ensure `ChatMessageFactory` links correctly to `ChatRoom` and `sender`. Handle `parent` for replies. Ensure Org scoping inherited/set.
  [ ] **(Test)** Write simple tests ensuring factories create valid instances and relationships.

  ### 3.3 Admin Registration (`chat/admin.py`)

  [ ] Create `chat/admin.py`.
  [ ] Define `ChatMessageInline` (TabularInline) showing sender, content snippet, created_at.
  [ ] Define `ChatRoomAdmin`. Use `filter_horizontal` for `participants`. Include `ChatMessageInline`. Configure `list_display`, `search_fields`, `list_filter`.
  [ ] Register models.
  [ ] **(Manual Test):** Verify Admin interface for viewing rooms, participants, and messages.

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations chat`.
  [ ] **Review generated migration file(s) carefully.** Check models, FKs, M2Ms, indexes.
  [ ] Run `python manage.py migrate` locally.

  ### 3.5 Channels Routing (`chat/routing.py` & `config/asgi.py`)

  [ ] Create `chat/routing.py`. Define `websocket_urlpatterns` using `re_path` or `path` pointing to the Chat Consumer (to be created).
      ```python
      # chat/routing.py
      from django.urls import re_path
      from . import consumers

      websocket_urlpatterns = [
          re_path(r'ws/chat/(?P<room_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
          # Add other consumers if needed (e.g., general notification socket)
      ]
      ```
  [ ] Update `config/asgi.py` to include the `chat.routing.websocket_urlpatterns`:
      ```python
      # config/asgi.py
      import os
      from django.core.asgi import get_asgi_application
      from channels.routing import ProtocolTypeRouter, URLRouter
      from channels.auth import AuthMiddlewareStack # For user auth in websockets
      import chat.routing # Import chat routing

      os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev') # Adjust

      application = ProtocolTypeRouter({
          "http": get_asgi_application(),
          "websocket": AuthMiddlewareStack( # Wrap with auth middleware
              URLRouter(
                  chat.routing.websocket_urlpatterns # Add chat patterns
                  # Add other app websocket patterns here if needed
              )
          ),
      })
      ```

  ### 3.6 Channels Consumer (`chat/consumers.py`)

  [ ] **(Test First - WebSocket Lifecycle)** Write Integration Tests (`chat/tests/integration/test_consumers.py`) using `channels.testing.WebsocketCommunicator`.
      *   Test connection attempts (unauthenticated -> reject, authenticated -> accept).
      *   Test joining/leaving a Channels group associated with a valid `room_id` on connect/disconnect. Verify user needs to be a participant.
      *   Test receiving a valid message -> verify `ChatMessage` is created, broadcast is triggered (mock broadcast call).
      *   Test receiving invalid message data -> verify error returned over WebSocket.
      *   Test handling of typing indicators.
      Run; expect failure.
  [ ] Create `chat/consumers.py`. Define `ChatConsumer` inheriting from `AsyncWebsocketConsumer`.
      ```python
      # chat/consumers.py
      import json
      from channels.generic.websocket import AsyncWebsocketConsumer
      from channels.db import database_sync_to_async # For DB operations
      from django.contrib.contenttypes.models import ContentType
      # Import models, FileStorage, serializers etc.
      from .models import ChatRoom, ChatMessage
      from api.v1.base_models.common.models import FileStorage # Adjust path

      class ChatConsumer(AsyncWebsocketConsumer):
          async def connect(self):
              self.room_id = self.scope['url_route']['kwargs']['room_id']
              self.room_group_name = f'chat_{self.room_id}'
              self.user = self.scope['user']

              if not self.user or not self.user.is_authenticated:
                  await self.close()
                  return

              # Check if user is participant (requires DB access)
              is_participant = await self.check_user_participation(self.room_id, self.user)
              if not is_participant:
                   await self.close()
                   return

              # Join room group
              await self.channel_layer.group_add(
                  self.room_group_name,
                  self.channel_name
              )
              await self.accept()
              # TODO: Broadcast user presence update?

          async def disconnect(self, close_code):
              # Leave room group
              if hasattr(self, 'room_group_name'):
                  await self.channel_layer.group_discard(
                      self.room_group_name,
                      self.channel_name
                  )
              # TODO: Broadcast user presence update?

          # Receive message from WebSocket
          async def receive(self, text_data=None, bytes_data=None):
              try:
                  text_data_json = json.loads(text_data)
                  message_type = text_data_json.get('type')
                  # Example: Simple message send
                  if message_type == 'chat_message':
                      content = text_data_json.get('message', '').strip()
                      attachment_ids = text_data_json.get('attachment_ids', [])
                      parent_id = text_data_json.get('parent_id')

                      if not content and not attachment_ids:
                          await self.send_error("Message content or attachment required.")
                          return

                      # Save message to DB (use database_sync_to_async)
                      message_obj = await self.save_message(
                          content=content,
                          attachment_ids=attachment_ids,
                          parent_id=parent_id
                      )
                      if not message_obj: # Save failed (e.g., permission)
                           await self.send_error("Failed to send message.")
                           return

                      # Broadcast message to room group (requires serialization)
                      await self.channel_layer.group_send(
                          self.room_group_name,
                          {
                              'type': 'broadcast_chat_message', # Corresponds to method below
                              'message': await self.serialize_message(message_obj) # Serialize async
                          }
                      )
                  elif message_type == 'typing_indicator':
                      # Broadcast typing status to others in the group
                      await self.channel_layer.group_send(
                           self.room_group_name,
                           {
                               'type': 'broadcast_typing_indicator',
                               'user_id': self.user.pk,
                               'username': self.user.username,
                               'is_typing': text_data_json.get('is_typing', False)
                           },
                           # Exclude sender? Sometimes needed
                           # exclude_channel=self.channel_name
                       )
                  # Handle other message types (edit, delete notifications?)

              except json.JSONDecodeError:
                  await self.send_error("Invalid JSON format.")
              except Exception as e:
                  # Log unexpected errors
                  import logging
                  logging.getLogger(__name__).error(f"ChatConsumer receive error: {e}", exc_info=True)
                  await self.send_error("An unexpected error occurred.")

          # --- Broadcasting Helpers ---
          async def broadcast_chat_message(self, event):
              """ Sends message from group down to specific websocket connection """
              message_data = event['message']
              # Send message to WebSocket client
              await self.send(text_data=json.dumps({
                  'type': 'chat_message',
                  'message': message_data
              }))

          async def broadcast_typing_indicator(self, event):
              """ Sends typing indicator to websocket connection """
              # Don't send typing indicator back to the user who is typing
              if event['user_id'] != self.user.pk:
                  await self.send(text_data=json.dumps({
                      'type': 'typing_indicator',
                      'user_id': event['user_id'],
                      'username': event['username'],
                      'is_typing': event['is_typing']
                  }))

          async def send_error(self, message):
               """ Sends an error message back to the client """
               await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': message
               }))

          # --- Database Interaction (must be async) ---
          @database_sync_to_async
          def check_user_participation(self, room_id, user):
               try:
                   room = ChatRoom.objects.get(pk=room_id, organization=user.profile.primary_organization) # Add Org scope check
                   return room.participants.filter(pk=user.pk).exists()
               except ChatRoom.DoesNotExist:
                   return False

          @database_sync_to_async
          def save_message(self, content, attachment_ids, parent_id):
               try:
                   room = ChatRoom.objects.get(pk=self.room_id)
                   # Check user can send in this room (already checked participation on connect)
                   # Check parent exists and is in same room if parent_id provided
                   parent = None
                   if parent_id:
                       parent = ChatMessage.objects.filter(pk=parent_id, room=room).first()
                       if not parent: raise ValueError("Parent comment not found or in different room.")

                   # Create message (organization scope inherited)
                   message = ChatMessage.objects.create(
                       room=room,
                       sender=self.user,
                       content=content,
                       parent=parent,
                       organization=room.organization # Explicitly set org
                       # Set created_by/updated_by automatically via Auditable mixin
                   )
                   # Handle attachments M2M
                   if attachment_ids:
                       # Validate attachment IDs belong to user/org?
                       attachments = FileStorage.objects.filter(pk__in=attachment_ids, organization=room.organization)
                       message.attachments.set(attachments)
                   return message
               except Exception as e:
                   # Log error
                   import logging
                   logging.getLogger(__name__).error(f"Failed to save chat message: {e}", exc_info=True)
                   return None

          @database_sync_to_async
          def serialize_message(self, message_obj):
              # Use DRF serializer (needs async adaptation or run_sync)
              # Simplistic dict for now:
              # TODO: Use proper DRF serializer (may need tweaking for async context)
              return {
                  'id': message_obj.pk,
                  'room_id': message_obj.room_id,
                  'sender_id': message_obj.sender_id,
                  'sender_username': getattr(message_obj.sender, 'username', 'System'),
                  'content': message_obj.content,
                  'parent_id': message_obj.parent_id,
                  'attachment_ids': list(message_obj.attachments.values_list('pk', flat=True)),
                  'is_edited': message_obj.is_edited,
                  'created_at': message_obj.created_at.isoformat(),
              }
      ```
      *(Note: This is a complex component. Error handling, detailed permission checks, serialization, presence, and read receipts need careful implementation and testing.)*
  [ ] Run consumer tests; expect pass. Refactor consumer logic.

  ### 3.7 API ViewSet/Serializer Definition (`chat/serializers.py`, `chat/views.py`, `chat/urls.py`)

  [ ] **(Test First)** Write API tests (`chat/tests/api/test_endpoints.py`) for:
      *   `GET /rooms/` (list user's rooms).
      *   `POST /rooms/` (create group room).
      *   `GET /rooms/{id}/messages/` (get history, test pagination).
      *   `POST /rooms/{id}/messages/` (send message via API - alternative to WebSocket).
      *   `PUT/DELETE /messages/{id}/` (edit/delete own message).
      *   `POST/DELETE /rooms/{id}/participants/` (add/remove users).
      *   Test permissions and Org Scoping for all endpoints.
  [ ] Define `ChatRoomSerializer`, `ChatMessageSerializer` (potentially reusing parts of consumer serialization logic). Handle nested participants/messages appropriately.
  [ ] Define `ChatRoomViewSet` and `ChatMessageViewSet` (or combined). Implement necessary actions (list rooms, get messages, create room, manage participants, edit/delete message). Use `OrganizationScopedViewSetMixin`. Apply permissions.
  [ ] Define URL routing for these API endpoints.
  [ ] Run API tests; expect pass. Refactor.

  ### 3.8 Integration with Other Systems

  [ ] **(Test First - Notifications)** Test scenario where user is offline, message sent -> verify `send_notification` task is queued.
  [ ] Integrate calls to `Notification` service (async task) from consumer/signal when offline message/mention occurs.
  [ ] **(Test First - Search)** Test scenario where message sent -> verify message content appears in Search Engine index (mock ES).
  [ ] Integrate calls to update Search index (async task) from `ChatMessage` `post_save` signal.
  [ ] **(Test First - Audit)** Test room creation, participant changes -> verify `AuditLog` created.
  [ ] Integrate calls to `AuditLogging` system for relevant events.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`), including Channels tests.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=chat`). Review uncovered consumer/signal/task logic.
[ ] Manually test core chat functionality: connecting multiple clients, sending/receiving messages, basic history, group chat, file attachments via WebSocket/API. Test Org Scoping.
[ ] Review API and WebSocket documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs (Presence implementation, read receipts, rich content, mentions, advanced error handling).
[ ] Create Pull Request.
[ ] Update API and WebSocket documentation.
[ ] Deploy ASGI server (Daphne/Uvicorn) and configure Channel Layer (Redis) in deployment strategy.

--- END OF FILE chat_implementation_steps.md ---