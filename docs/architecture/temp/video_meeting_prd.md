# Video Meeting Integration - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To define the requirements for integrating a **third-party video conferencing service** into the ERP system, enabling users to schedule, manage, join, and access recordings/metadata for video meetings associated with ERP entities.
*   **Scope**: Definition of ERP-side models (`Meeting`, `MeetingParticipant`) to store meeting metadata and participant info, integration points with a chosen external video conferencing provider's API (scheduling, participant management, webhooks), embedding/linking the meeting UI, and managing recordings. **Excludes building WebRTC/media server infrastructure.**
*   **Implementation Strategy**:
    1.  **Choose External Provider**: Select a provider (e.g., Zoom, Vonage Video API, Daily.co, Twilio Video, Whereby Embedded). *(Decision Required)*
    2.  Implement ERP models (`Meeting`, `MeetingParticipant`) inheriting base models.
    3.  Integrate with the provider's REST API and potentially client SDKs.
    4.  Implement webhook handlers to receive events from the provider.
    5.  Embed the provider's UI or link to meeting URLs.
*   **Target Users**: All ERP users participating in meetings, Meeting Schedulers/Hosts, System Administrators.

## 2. Business Requirements

*   **Integrated Meetings**: Schedule and join video meetings directly from within the ERP context (e.g., linked to an Order, Project, or Contact).
*   **Simplified Scheduling**: Streamline the process of creating video meetings relevant to ERP tasks.
*   **Participant Management**: Track ERP users invited to or participating in meetings.
*   **Recording Access**: Provide links to meeting recordings within the relevant ERP context.
*   **Secure Access**: Ensure only authorized ERP users can schedule or join relevant meetings.
*   **Organization Scoping**: Meetings must be scoped by Organization.

## 3. Functional Requirements

### 3.1 Core ERP Models
*   **`Meeting` Model**:
    *   **Purpose**: Stores metadata about a scheduled meeting instance within the ERP.
    *   **Inheritance**: `Timestamped`, `Auditable`, `OrganizationScoped`.
    *   **Fields**:
        *   `topic`: (CharField, max_length=255) Meeting title/subject.
        *   `description`: (TextField, blank=True).
        *   `scheduled_start_time`: (DateTimeField, db_index=True).
        *   `scheduled_end_time`: (DateTimeField, null=True, blank=True).
        *   `actual_start_time`: (DateTimeField, null=True, blank=True) Populated via webhook.
        *   `actual_end_time`: (DateTimeField, null=True, blank=True) Populated via webhook.
        *   `status`: (CharField with choices: 'SCHEDULED', 'IN_PROGRESS', 'ENDED', 'CANCELLED', default='SCHEDULED', db_index=True). Updated via API calls or webhooks.
        *   `host`: (ForeignKey to `User`, on_delete=models.SET_NULL, null=True, related_name='hosted_meetings') The ERP user who scheduled/hosts.
        *   `provider`: (CharField, max_length=50) Identifier for the external provider used (e.g., 'zoom', 'vonage').
        *   `provider_meeting_id`: (CharField, max_length=255, unique=True, db_index=True) The unique ID assigned by the external provider.
        *   `join_url`: (URLField, max_length=1024, blank=True) The primary URL to join the meeting.
        *   `related_object_type`: (ForeignKey to `ContentType`, null=True, blank=True) Optional: Link to the type of ERP object this meeting relates to.
        *   `related_object_id`: (CharField/PositiveIntegerField, null=True, blank=True) Optional: PK of the related ERP object.
        *   **`custom_fields`**: (JSONField, default=dict, blank=True).
    *   **Meta**: `verbose_name`, `plural`, `ordering`.
*   **`MeetingParticipant` Model**:
    *   **Purpose**: Links ERP Users to a `Meeting`, tracking their role and status.
    *   **Inheritance**: `Timestamped`, `Auditable`, `OrganizationScoped`.
    *   **Fields**:
        *   `meeting`: (ForeignKey to `Meeting`, on_delete=models.CASCADE, related_name='participants').
        *   `user`: (ForeignKey to `User`, on_delete=models.CASCADE, related_name='meeting_participations').
        *   `role`: (CharField with choices: 'HOST', 'PARTICIPANT', default='PARTICIPANT').
        *   `join_time`: (DateTimeField, null=True, blank=True) Populated via webhook.
        *   `leave_time`: (DateTimeField, null=True, blank=True) Populated via webhook.
    *   **Meta**: `unique_together = ('meeting', 'user')`, `verbose_name`, `plural`.

### 3.2 Meeting Operations (via API -> Provider API)
*   **Schedule Meeting**: API endpoint (`POST /api/v1/meetings/`) receives topic, time, initial participants.
    *   Backend logic calls the **external provider's API** to create the meeting.
    *   Stores provider ID, join URL, etc., in the local `Meeting` record.
    *   Creates initial `MeetingParticipant` records.
    *   Potentially sends invites via `Notification` system.
*   **Update Meeting**: API endpoint (`PUT /api/v1/meetings/{id}/`) updates topic, time. Calls provider API.
*   **Cancel Meeting**: API endpoint (`DELETE /api/v1/meetings/{id}/` or `POST /cancel/`). Calls provider API. Updates local `status`.
*   **Get Meeting Info**: API endpoint (`GET /api/v1/meetings/{id}/`) returns local `Meeting` data (including join URL).
*   **List Meetings**: API endpoint (`GET /api/v1/meetings/`) lists meetings user is associated with (hosted or participant), filterable by date/status.

### 3.3 Joining Meetings
*   Users retrieve the `join_url` via the ERP API/UI.
*   Clicking the URL either launches the provider's app or loads an embedded experience (depending on provider and implementation). Authentication within the meeting is handled by the provider (potentially using tokens generated via ERP backend).

### 3.4 Real-Time Features (Handled by Provider)
*   Video/Audio Streaming, Screen Sharing, In-Meeting Chat, Reactions, Participant List within the meeting UI are provided by the external service.

### 3.5 Recording Management
*   **Webhook Handler**: Implement an endpoint to receive webhook events from the provider (e.g., `recording.completed`).
*   **Logic**: When a recording is ready, the webhook handler:
    1.  Finds the corresponding `Meeting` record using the `provider_meeting_id`.
    2.  Gets the recording URL(s) or download link(s) from the webhook payload.
    3.  **(Option A)** Stores the URL(s) directly on the `Meeting` record (e.g., in a JSONField `recording_links`).
    4.  **(Option B)** Downloads the recording file asynchronously (Celery task), saves it via the `FileStorage` system, and links the `FileStorage` record to the `Meeting` record (e.g., `Meeting.recording_files = ManyToManyField(FileStorage)`). *Option B provides more control but uses more storage.*

### 3.6 Integration Requirements
*   **External Provider API**: Requires secure storage and use of API keys/credentials for the chosen provider.
*   **Webhook Handling**: Requires a publicly accessible endpoint for provider webhooks with security verification (e.g., signature validation).
*   **User Interface**: Requires embedding the provider's meeting UI (e.g., via iFrame or SDK) or linking out to meeting URLs.
*   **Notification System**: Send meeting invitations and reminders.
*   **Calendar Integration (Optional)**: API calls to create/update events in users' external calendars (Google Calendar, Outlook) when meetings are scheduled/updated. Requires OAuth integration.
*   **Audit Logging**: Log creation, cancellation, participant changes (via webhooks) for `Meeting` records.

### 3.7 Custom Field Schema Definition (External Mechanism)
*   Requirement for separate `CustomFieldDefinition` model/mechanism if custom fields are used on the `Meeting` model.

### 3.8 Out of Scope
*   Building custom WebRTC/media server infrastructure.
*   Implementing in-meeting features (chat, screen share, recording) - rely on provider.

## 4. Technical Requirements

### 4.1 External API Integration
*   Robust client for interacting with the chosen provider's API (error handling, retries).
*   Secure storage for provider API credentials (`django-environ`, Vault, etc.).

### 4.2 Webhook Handling
*   Reliable webhook endpoint capable of handling provider events. Security validation is essential. Asynchronous processing (Celery) recommended for webhook payloads.

### 4.3 Security
*   Secure API key management. Webhook signature validation.
*   Permissions (RBAC) control who can schedule meetings, view recordings, manage participants.
*   Organization scoping ensures users only interact with meetings within their org.
*   Rely on provider's security for in-meeting encryption and access.

### 4.4 Performance
*   API calls to the external provider should ideally be asynchronous (Celery) if they might be slow.
*   Efficient querying of local `Meeting` / `MeetingParticipant` data.

### 4.5 Integration Points
*   ERP Models (`Meeting`, `MeetingParticipant`).
*   Provider API client. Webhook handler.
*   UI embedding/linking logic.
*   Notification System, Audit Log, RBAC, Org Scoping, File Storage (for recordings).
*   Optional Calendar API integration.

## 5. Non-Functional Requirements

*   **Reliability**: Depends heavily on the chosen external provider's reliability. Webhook handling must be reliable.
*   **Availability**: Depends on provider's availability. ERP endpoints for scheduling/viewing must be available.
*   **Scalability**: Provider handles media scalability. ERP must handle metadata/scheduling load.

## 6. Success Metrics

*   Successful scheduling and joining of meetings via ERP interface.
*   Reliable retrieval of meeting metadata and recording links.
*   High user satisfaction with the integrated meeting experience.
*   Provider service uptime and quality meet expectations.

## 7. API Documentation Requirements

*   Document ERP API endpoints for managing `Meeting` metadata (CRUD, list, get join URL).
*   Document webhook endpoint requirements (if applicable for external configuration).
*   Explain the relationship with the external provider and how joining works.
*   Auth/Permission requirements for meeting APIs.
*   Document `custom_fields` handling.

## 8. Testing Requirements

*   **Unit Tests**: Test `Meeting`, `MeetingParticipant` models. Test logic within API views/webhook handlers (mocking external API calls).
*   **Integration Tests**:
    *   **Requires mocking the external provider's API**.
    *   Test scheduling API call -> verify mock provider API called correctly -> verify local `Meeting` created.
    *   Test webhook handler -> send mock webhook payload -> verify local `Meeting`/`Participant`/`FileStorage` records are updated correctly.
    *   Test fetching meeting lists/details and join URLs.
    *   Test permissions and org scoping.
    *   Test **saving/validating `custom_fields`**.
*   **Manual/E2E Tests**: Test the full flow with the actual external provider in a staging environment.

## 9. Deployment Requirements

*   Migrations for `Meeting`, `MeetingParticipant` models, indexes (incl. JSONField).
*   Secure configuration of external provider API keys/secrets for each environment.
*   Deployment of webhook handler endpoint.
*   Setup of Celery workers for async tasks (provider calls, recording downloads).
*   Deployment of `CustomFieldDefinition` mechanism if needed.

## 10. Maintenance Requirements

*   Keep provider API client/SDK updated.
*   Monitor provider API usage and webhook success/failure rates.
*   Manage provider API keys/secrets securely.
*   Standard backups.
*   Manage custom field schemas if applicable.

---