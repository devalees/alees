Okay, generating the implementation steps for the **Video Meeting Integration**. This focuses on setting up the ERP-side models (`Meeting`, `MeetingParticipant`) and the integration points (API calls, webhooks) assuming a third-party provider handles the actual video conferencing.

**Crucial Prerequisites/Decisions:**

*   **External Provider Choice:** A specific provider (Zoom, Vonage, Daily.co, etc.) must be selected, as API calls and webhook payloads will be specific to that provider. Steps below are generic placeholders.
*   **Recording Storage:** Decide on Option A (store URLs) or Option B (download to `FileStorage`). Steps assume **Option A (store URLs)** initially for simplicity.
*   **Calendar Integration:** Steps assume this is optional/deferred.

--- START OF FILE videomeeting_implementation_steps.md ---

# Video Meeting Integration - Implementation Steps

## 1. Overview

**Feature Name:**
Video Meeting Integration

**Corresponding PRD:**
`video_meeting_prd.md` (Simplified - Integration focus)

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `Organization`, `ContentType` (for GFKs), `FileStorage` (if downloading recordings), `Notification` System, Celery infrastructure, Secure way to store external API keys.

**Key Features:**
Integrates with a chosen third-party video conferencing provider. Implements ERP models (`Meeting`, `MeetingParticipant`) to store metadata. Provides APIs to schedule/manage meetings (proxying to provider). Handles webhooks for status updates and recording links.

**Primary Location(s):**
*   Models, Serializers, Views: `video_meetings/` (New dedicated app recommended)
*   API Client/Service: `video_meetings/services.py` or `core/integrations/`
*   Webhook View: `video_meetings/views.py`
*   Celery Tasks: `video_meetings/tasks.py` (for async API calls or recording downloads)
*   API URLs: `api/v1/meetings/` (New dedicated API structure)

## 2. Prerequisites

[ ] Verify all prerequisite models/mixins (`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `Organization`, `ContentType`, `FileStorage` - if downloading recordings) are implemented.
[ ] Verify Celery infrastructure is operational.
[ ] Verify Notification system is available.
[ ] **Select External Video Provider:** Choose the specific provider (e.g., Zoom, Daily.co, Vonage).
[ ] **Obtain Provider Credentials:** Get API Keys/Secrets/Credentials from the chosen provider's developer portal.
[ ] **Store Credentials Securely:** Configure environment variables or secrets manager for storing provider API keys (as per `security_strategy.md`).
[ ] **Create new Django app:** `python manage.py startapp video_meetings`.
[ ] Add `'video_meetings'` to `INSTALLED_APPS`.
[ ] Ensure `factory-boy` is set up. Factories for `User`, `Organization` exist.
[ ] Define `MeetingStatus` choices.

## 3. Implementation Steps (TDD Workflow)

  *(Models -> Provider Service -> API -> Webhooks)*

  ### 3.1 Core Model Definitions (`video_meetings/models.py`)

  [ ] **(Test First - Meeting)** Write Unit Tests (`tests/unit/test_models.py`) verifying `Meeting` creation, fields (topic, times, status, provider, provider_id, join_url, GFK, custom fields), defaults, inheritance, `__str__`.
  [ ] Define `Meeting` model. Inherit `Timestamped`, `Auditable`, `OrganizationScoped`. Include fields from PRD 3.1 (topic, times, status, host FK, provider, provider_id, join_url, GFK fields, `custom_fields`). Define `Meta`. Add `recording_links` (JSONField, default=list) if storing URLs (Option A). Add `recording_files` (M2M to FileStorage) if downloading (Option B).
  [ ] Run Meeting tests; expect pass. Refactor.
  [ ] **(Test First - Participant)** Write Unit Tests verifying `MeetingParticipant` creation, fields (meeting FK, user FK, role), `unique_together`, inheritance, `__str__`.
  [ ] Define `MeetingParticipant` model. Inherit `Timestamped`, `Auditable`, `OrganizationScoped`. Include fields from PRD 3.1 (meeting FK, user FK, role, join/leave times). Define `Meta`.
  [ ] Run Participant tests; expect pass. Refactor.

  ### 3.2 Factory Definitions (`video_meetings/tests/factories.py`)

  [ ] Define `MeetingFactory` and `MeetingParticipantFactory`. Handle FKs, GFKs (potentially passing a target object to MeetingFactory). Set default provider name.
  [ ] **(Test)** Write simple tests ensuring factories create valid instances.

  ### 3.3 Provider API Client/Service (`video_meetings/services.py`)

  [ ] **(Test First)** Write Unit Tests for the service functions. **Mock external HTTP requests** (using `requests-mock` or `unittest.mock.patch`).
      *   Test `create_provider_meeting(topic, start_time, ...)`: Verify it makes the correct API call (URL, method, headers, payload) to the *mocked* provider endpoint and returns expected data (provider ID, join URL). Test error handling for provider API failures.
      *   Test `update_provider_meeting(provider_meeting_id, ...)`: Verify correct mock API call.
      *   Test `cancel_provider_meeting(provider_meeting_id)`: Verify correct mock API call.
      *   Test functions for adding/removing participants via provider API if applicable.
  [ ] Create `video_meetings/services.py`. Implement functions that encapsulate calls to the chosen external provider's API using a library like `requests` or the provider's official SDK.
      *   Load API keys/secrets securely from settings/environment.
      *   Handle request formatting, authentication headers, and response parsing specific to the provider.
      *   Include error handling and logging for API calls.
  [ ] Run service tests; expect pass. Refactor.

  ### 3.4 Admin Registration (`video_meetings/admin.py`)

  [ ] Create `video_meetings/admin.py`.
  [ ] Define `MeetingParticipantInline`.
  [ ] Define `MeetingAdmin`. Make provider fields read-only. Add participant inline. Configure display/filters.
  [ ] Register models.
  [ ] **(Manual Test):** Verify basic viewing/metadata editing in Admin.

  ### 3.5 Migrations

  [ ] Run `python manage.py makemigrations video_meetings`.
  [ ] **Review generated migration file(s) carefully.** Check models, FKs, GFKs, indexes.
  [ ] Run `python manage.py migrate` locally.

  ### 3.6 Serializer Definition (`video_meetings/serializers.py`)

  [ ] **(Test First)** Write Unit/Integration Tests for `MeetingSerializer` and `MeetingParticipantSerializer`. Test representation, validation, `custom_fields`, read-only fields. Test nested participant representation (if needed).
  [ ] Define serializers. Handle read-only provider fields, GFK representation, `custom_fields`. Inherit `FieldPermissionSerializerMixin` if needed.
  [ ] Implement `validate_custom_fields` if applicable.
  [ ] Run tests; expect pass. Refactor.

  ### 3.7 API ViewSet Definition (`video_meetings/views.py`)

  [ ] **(Test First)** Write basic API Tests checking `/api/v1/meetings/` URL, authentication, Org Scoping, basic permissions.
  [ ] Define `MeetingViewSet` in `video_meetings/views.py`. Inherit `OrganizationScopedViewSetMixin`, `viewsets.ModelViewSet`.
  [ ] Implement `perform_create`:
      1.  Call `create_provider_meeting` service function.
      2.  Save `Meeting` instance with provider data.
      3.  Create `MeetingParticipant` records for host and initial invitees.
      4.  **(Async)** Queue notification task for invites.
  [ ] Implement `perform_update`: Call `update_provider_meeting` service. Save local changes.
  [ ] Implement `perform_destroy`: Call `cancel_provider_meeting` service. Update local status to `CANCELLED` (or delete).
  [ ] Override `get_queryset` to filter meetings accessible to the user (hosted or participant). Apply `select/prefetch_related`.
  [ ] Add filtering/search/ordering backends.
  [ ] Secure endpoints with appropriate permissions (`IsAuthenticated` + custom permission checks).
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.8 Webhook Handler View (`video_meetings/views.py`)

  [ ] **(Test First)** Write Integration Tests for the webhook endpoint (`POST /api/v1/webhooks/video-provider/`).
      *   **Requires mocking request signature verification.**
      *   Send mock payloads simulating `meeting.started`, `meeting.ended`, `participant.joined`, `participant.left`, `recording.completed` events.
      *   Verify the handler correctly identifies the `Meeting` via `provider_meeting_id`.
      *   Verify `Meeting` status and `actual_start/end_time` are updated.
      *   Verify `MeetingParticipant` join/leave times are updated.
      *   Verify recording links/files are processed correctly (check `Meeting.recording_links` or queued Celery task for download).
      *   Test invalid signatures/payloads -> Assert appropriate error response (e.g., 400, 403).
      Run; expect failure.
  [ ] Create a new Django View (e.g., `VideoProviderWebhookView(APIView)`) for handling incoming webhooks.
  [ ] Implement webhook signature verification specific to the provider.
  [ ] Implement logic within the `post` method to parse the payload, identify the event type, find the corresponding `Meeting`/`Participant`, and update records accordingly.
  [ ] For potentially slow operations (like recording downloads - Option B), queue a Celery task from the webhook handler.
  [ ] Return appropriate HTTP status codes (e.g., 200 OK on success, 400 on bad payload, 403 on bad signature).
  [ ] Run webhook tests; expect pass. Refactor.

  ### 3.9 URL Routing (`video_meetings/urls.py` & `api/v1/urls.py`)

  [ ] Create `api/v1/video_meetings/urls.py`. Import `MeetingViewSet`. Register with router: `router.register(r'meetings', views.MeetingViewSet)`.
  [ ] Define URL pattern for the webhook handler view. Ensure this URL is *not* included in standard API auth/prefixing if the provider requires a simple public endpoint (security handled by signature).
  [ ] Include `video_meetings.urls` in main `api/v1/urls.py`.
  [ ] **(Test):** Rerun basic API tests; expect 2xx/4xx codes.

  ### 3.10 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests for `MeetingViewSet` CRUD operations (List, Create, Retrieve, Update, Delete/Cancel).
      *   **Mock the provider service calls** (`create_provider_meeting`, etc.) to avoid external dependencies. Verify the service functions are called with correct arguments.
      *   Verify local `Meeting` and `MeetingParticipant` records are created/updated correctly.
      *   Verify responses match the API spec.
      *   Test permissions and Org Scoping rigorously.
      *   Test filtering/pagination on LIST endpoint.
      *   Test saving/validating `custom_fields`.
  [ ] Implement/Refine ViewSet methods and Serializer logic.
  [ ] Run all API tests; expect pass. Refactor.

  ### 3.11 Recording Download Task (Optional - If using Option B)

  [ ] **(Test First)** Write Unit Tests for Celery task `download_meeting_recording`. Mock `FileStorage` save and external download call.
  [ ] Implement Celery task `download_meeting_recording(meeting_id, recording_url)`. Fetches recording, saves using `FileStorage`, links `FileStorage` object to `Meeting.recording_files` M2M. Handles errors.
  [ ] Ensure webhook handler queues this task.
  [ ] Run tests; expect pass.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`), ensuring external services are mocked appropriately.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=video_meetings`).
[ ] Manually test the end-to-end flow in staging with the *actual* video provider: Schedule via API/UI -> Join Meeting -> Record -> End Meeting -> Verify webhook updates status and recording link/file appears.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs (Refine error handling, implement optional calendar sync).
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Securely deploy webhook endpoint and configure provider settings.

--- END OF FILE videomeeting_implementation_steps.md ---