# Real-Time Chat System - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To define the requirements for a real-time chat system integrated within the ERP, enabling direct messaging, group chats, basic file sharing, and persistent message history.
*   **Scope**: Definition of core chat models (`ChatRoom`, `ChatMessage`), integration with real-time communication infrastructure (WebSockets via Django Channels), basic message/file operations, user presence indication, search integration, and permission handling. Excludes advanced features like complex threading, reactions, video calls within chat, or sophisticated moderation tools initially.
*   **Implementation Strategy**: Involves concrete Django Models (`ChatRoom`, `ChatMessage`, potentially `ChatParticipant`) inheriting base models. Relies heavily on **Django Channels** for WebSocket communication. Integrates with `FileStorage`, `Search`, `Notification`, `User`, `Organization`, `RBAC`, and `Audit` systems. Asynchronous tasks (Celery) may be used for notifications or background processing.
*   **Target Users**: All internal ERP users.

## 2. Business Requirements

*   **Instant Communication**: Facilitate real-time conversations between individuals and groups within the organizational context.
*   **Persistent History**: Store chat messages reliably for later reference and searching.
*   **Basic Collaboration**: Allow sharing relevant files directly within conversations.
*   **Contextual Chat**: Potentially link chat rooms to specific business objects (e.g., a chat about a specific Order). *(Consider as v2 feature)*.
*   **Secure Communication**: Ensure chats are scoped by organization and access is controlled by permissions.

## 3. Functional Requirements

### 3.1 Core Models
*   **`ChatRoom` Model**:
    *   **Purpose**: Represents a conversation space (DM or Group).
    *   **Inheritance**: `Timestamped`, `Auditable`, `OrganizationScoped`.
    *   **Fields**:
        *   `name`: (CharField, max_length=255, blank=True) Name of the group chat/channel. Blank for DMs.
        *   `room_type`: (CharField with choices: 'DIRECT', 'GROUP', 'CHANNEL', default='GROUP', db_index=True).
        *   `participants`: (ManyToManyField to `User`, related_name='chat_rooms') Members of the room. *(Consider a `through` model `ChatParticipant` if per-user state like `last_read_timestamp` is needed)*.
        *   `is_active`: (BooleanField, default=True).
        *   **`custom_fields`**: (JSONField, default=dict, blank=True).
    *   **Meta**: `verbose_name`, `plural`, `ordering`.
*   **`ChatMessage` Model**:
    *   **Purpose**: Represents a single message within a room.
    *   **Inheritance**: `Timestamped`, `Auditable`, `OrganizationScoped`.
    *   **Fields**:
        *   `room`: (ForeignKey to `ChatRoom`, on_delete=models.CASCADE, related_name='messages') **Required**.
        *   `sender`: (ForeignKey to `User`, on_delete=models.SET_NULL, null=True, related_name='sent_chat_messages') **Required** (except for system messages).
        *   `content`: (TextField) The message text. *(Consider JSONField for rich content later)*.
        *   `parent`: (ForeignKey to `'self'`, on_delete=models.SET_NULL, null=True, blank=True, related_name='replies') For basic threading/replies.
        *   `attachments`: (ManyToManyField to `FileStorage`, blank=True).
        *   `is_edited`: (BooleanField, default=False).
        *   `is_deleted`: (BooleanField, default=False) For soft deletes.
        *   **`custom_fields`**: (JSONField, default=dict, blank=True).
    *   **Meta**: `verbose_name`, `plural`, `ordering = ['created_at']`, index on `room`.

### 3.2 Real-Time Communication (Django Channels)
*   **WebSockets**: Implement Django Channels consumers to handle WebSocket connections (`connect`, `disconnect`, `receive`).
*   **Authentication**: Authenticate WebSocket connections using user session/token.
*   **Room Joining**: When a user connects, subscribe them to Channels groups corresponding to their active `ChatRoom`s.
*   **Message Broadcasting**: When a `ChatMessage` is saved:
    1.  Trigger a signal or task.
    2.  The handler sends the message data (or a notification) to the relevant Channels group for the message's `room`.
    3.  Consumers relay the message to connected clients in that room.
*   **Presence**: Implement basic online status tracking (users connected to the Channels chat consumer). Broadcast presence updates.
*   **Typing Indicators**: Client sends "start typing" / "stop typing" events via WebSocket; consumer broadcasts these temporary indicators to other room participants.

### 3.3 Core Chat Operations (API + WebSockets)
*   **Fetch Rooms**: API endpoint (`GET /api/v1/chat/rooms/`) to list rooms the user is a participant in.
*   **Fetch Messages**: API endpoint (`GET /api/v1/chat/rooms/{room_id}/messages/`) to retrieve historical messages for a room (paginated).
*   **Send Message**: Client sends message content (and optional attachment IDs, parent ID) via **WebSocket** `receive` handler OR a dedicated **API endpoint** (`POST /api/v1/chat/rooms/{room_id}/messages/`).
    *   Backend logic: Check permissions, create `ChatMessage`, save attachments M2M, save message, trigger broadcast (see 3.2).
*   **Edit/Delete Message**: API endpoints (`PUT/DELETE /api/v1/chat/messages/{message_id}/`). Check permissions (author only, potentially time-limited). Update `is_edited`/`is_deleted`. Broadcast update/delete event via WebSockets.
*   **Create Room**: API endpoint (`POST /api/v1/chat/rooms/`) to create new GROUP rooms, specifying initial participants. Check permissions. DMs might be created implicitly when sending the first message.
*   **Manage Participants**: API endpoints to add/remove participants from GROUP rooms (`POST/DELETE /api/v1/chat/rooms/{room_id}/participants/`). Check permissions (room admin/creator?).
*   **File Upload**: Use the existing `FileStorage` upload API. Client uploads file, gets ID, includes ID when sending message.

### 3.4 User Experience Features
*   **Real-time Updates**: New messages, edits, deletes, typing indicators, presence updates delivered via WebSockets.
*   **Read Receipts**: *(Defer to v2 - requires tracking last read message per user per room, potentially in `ChatParticipant` model)*.

### 3.5 Integration Requirements
*   **Organization Scoping**: `ChatRoom` and `ChatMessage` inherit `OrganizationScoped`. Queries and broadcasts must respect this.
*   **User Management**: Links heavily to `User` model for participants, sender.
*   **File Storage**: Uses `FileStorage` for attachments.
*   **Notification System**: Trigger for offline users/mentions (requires parsing content for `@user` - potentially async task).
*   **Search Integration**: `ChatMessage.content` should be indexed by the Search Engine. API needs to pass search queries to the engine.
*   **Audit Logging**: Log room creation, participant changes, potentially message deletion (if required beyond `is_deleted` flag).

### 3.6 Custom Field Schema Definition (External Mechanism)
*   Requirement for separate `CustomFieldDefinition` model/mechanism if custom fields are used on `ChatRoom` or `ChatMessage`.

### 3.7 Out of Scope (Initial Implementation)
*   Advanced threading (beyond direct replies), message reactions, read receipts, rich text formatting/previews, video/audio calls, sophisticated moderation tools, bots, channel-specific features (topics, pins).

## 4. Technical Requirements

### 4.1 Infrastructure & Libraries
*   **ASGI Server**: Required for Django Channels (e.g., Daphne, Uvicorn).
*   **Channel Layers**: Backend for communication between consumers/workers (e.g., `channels_redis`).
*   **Django Channels**: Core library for WebSocket handling.
*   **(Optional) Celery**: For asynchronous notification sending or message processing.
*   **Database**: Standard Django ORM + JSONField support.

### 4.2 Data Management
*   Storage for `ChatRoom`, `ChatMessage`. Efficient querying for message history (pagination crucial). Indexing on FKs, timestamps, potentially content (if DB search needed alongside search engine). GIN index for `custom_fields`.

### 4.3 Performance
*   **Real-time Latency**: Minimize delay between message send and receipt by connected clients. Requires efficient broadcasting via Channel Layers.
*   **Database Load**: Optimize message fetching queries. Writing messages should be fast.
*   **WebSocket Connections**: Server must handle potentially large numbers of persistent connections.
*   **Async Tasks**: Ensure Celery workers (if used) can handle notification/processing load.

### 4.4 Security
*   **Authentication**: Securely authenticate WebSocket connections.
*   **Authorization**: Check permissions rigorously for joining rooms, sending messages, managing participants, editing/deleting. Ensure users can only access rooms/messages within their organization scope.
*   **Encryption**: Consider TLS/WSS for WebSocket traffic. Encryption at rest for messages/files if required by compliance.
*   **Input Sanitization**: Sanitize message content to prevent XSS attacks if displaying HTML.

### 4.5 Integration Points
*   API endpoints for history, management. WebSocket endpoint for real-time.
*   Signals/tasks for broadcasting, notifications, search indexing.
*   Integration with User/Org/File/Search/Notification systems.

## 5. Non-Functional Requirements

*   **Scalability**: Handle many concurrent users, connections, rooms, and messages. Requires scalable ASGI server, Channel Layer (Redis cluster?), and database.
*   **Availability**: Chat service (WebSocket server, API) needs high availability.
*   **Reliability**: Minimize message loss during broadcast or saving.
*   **Consistency**: Ensure messages are eventually consistent across participants' views.

## 6. Success Metrics

*   High message delivery success rate (saved and broadcast).
*   Low real-time latency.
*   High user adoption/engagement.
*   System reliability and availability meet targets.

## 7. API Documentation Requirements

*   Document `ChatRoom`, `ChatMessage` models/fields (incl. `custom_fields`).
*   Document REST API endpoints (fetching rooms/messages, creating rooms, managing participants, editing/deleting messages).
*   **Crucially**: Document the WebSocket protocol/events (connecting, authentication, expected message format for sending, message format received from server, presence/typing events).
*   Auth/Permission requirements for API and WebSocket actions.
*   Document custom field handling.

## 8. Testing Requirements

*   **Unit Tests**: Test model logic, message creation/validation. Test Channels consumer logic in isolation (mocking channel layer sends).
*   **Integration Tests**:
    *   Requires setting up Django Channels testing infrastructure (`channels.testing.WebsocketCommunicator`).
    *   Test WebSocket lifecycle: connect, auth success/fail, receive message, send message, disconnect.
    *   Test message broadcasting: Send message via API/WebSocket, verify other connected clients receive it.
    *   Test API endpoints for fetching history, managing rooms/participants.
    *   Test permissions and Org Scoping for API and WebSocket actions.
    *   Test file attachment handling.
    *   Test search integration.
    *   Test notification integration (triggering async task).
    *   Test **saving/validating `custom_fields`**.
*   **Load Tests**: Simulate many concurrent WebSocket connections and high message volume.

## 9. Deployment Requirements

*   Deployment of ASGI server (Daphne/Uvicorn).
*   Deployment of Channel Layer backend (Redis).
*   Deployment of Django application code (models, views, consumers).
*   Configuration of Channels routing.
*   Migrations for chat models, indexes (incl. JSONField).
*   Setup of Celery workers if used.
*   Deployment of `CustomFieldDefinition` mechanism if needed.

## 10. Maintenance Requirements

*   Monitor ASGI server, Channel Layer, WebSocket connections, Celery queues.
*   Standard database/model maintenance. Backups.
*   Keep Channels and related libraries updated.
*   Management of custom field schemas if applicable.

---