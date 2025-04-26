# Notification System - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To define a standardized system for generating, delivering, and tracking notifications related to system events and user communications within the ERP.
*   **Scope**: Definition of the core `Notification` model (primarily for in-app display and tracking), mechanisms for triggering notifications, integration with delivery channels (in-app, email, potentially others via async tasks), and respecting user preferences.
*   **Implementation**: Involves a concrete `Notification` Django Model (inheriting base models), potentially a `NotificationTemplate` model, integration with background task queues (e.g., Celery) for external channel delivery, and a notification service/function.
*   **Target Users**: All users receiving notifications, System Administrators (managing templates/settings), Developers (triggering notifications).

## 2. Business Requirements

*   **Inform Users**: Notify users promptly about relevant events, tasks, mentions, or system updates.
*   **Drive Action**: Alert users to items requiring their attention (e.g., approvals, overdue tasks).
*   **Configurable Delivery**: Allow users some control over which notifications they receive and potentially how (initially focusing on enabling/disabling types).
*   **Multi-Channel Potential**: Support delivery via in-app notifications and email initially, with architecture allowing for future channels (SMS, push).
*   **Reliable Delivery**: Ensure notifications are generated reliably and delivered efficiently (especially via background tasks).

## 3. Functional Requirements

### 3.1 `Notification` Model Definition (Primary: In-App/Tracking)
*   **Purpose**: Represents a single notification instance intended for a user.
*   **Inheritance**: Must inherit `Timestamped`, `Auditable`, and `OrganizationScoped` (notifications belong to the user's context within an org).
*   **Fields**:
    *   `recipient`: (ForeignKey to `User`, on_delete=models.CASCADE, related_name='notifications') **Required**. The user receiving the notification.
    *   `level`: (CharField with choices, e.g., 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'ACTION', default='INFO', db_index=True) Severity or type category.
    *   `title`: (CharField, max_length=255, blank=True) Optional short title/summary.
    *   `message`: (TextField) The main content/body of the notification. Can contain simple markup if needed for in-app display.
    *   `status`: (CharField with choices, e.g., 'UNSENT', 'SENT', 'DELIVERED', 'READ', 'ACTIONED', 'ERROR', default='UNSENT', db_index=True) Tracks the notification lifecycle.
    *   `read_at`: (DateTimeField, null=True, blank=True) Timestamp when the user marked the notification as read (for in-app).
    *   `action_url`: (URLField, blank=True) Optional URL for a primary action related to the notification.
    *   `action_text`: (CharField, max_length=50, blank=True) Optional text for the action button/link.
    *   **Linking Fields (Generic Relation or Specific FKs)**: Optional fields to link the notification back to the originating object (e.g., the specific Invoice that was approved). Uses `ContentType`/`object_id` or specific nullable FKs.
    *   `notification_type`: (CharField, max_length=100, blank=True, db_index=True) Application-defined code for the specific type of notification event (e.g., 'invoice_approved', 'task_assigned') used for user preferences.
*   **Meta**: `verbose_name`, `plural`, `ordering = ['-created_at']`, relevant indexes.
*   **String Representation**: Return title or truncated message.

### 3.2 `NotificationTemplate` Model (Optional but Recommended)
*   **Purpose**: Store reusable templates for notification content (especially email subjects/bodies).
*   **Fields**:
    *   `template_key`: (CharField, unique=True) Identifier used to select the template (e.g., 'invoice_approved_email').
    *   `subject_template`: (TextField) Django template syntax for the subject.
    *   `body_template_txt`: (TextField) Django template syntax for the plain text body.
    *   `body_template_html`: (TextField, blank=True) Django template syntax for the HTML body.
    *   *Inherit Timestamped/Auditable.*
*   **Management**: Via Admin UI or specific management commands/API.

### 3.3 Notification Generation & Triggering
*   **Central Service/Function**: Implement a reusable function/service (e.g., `send_notification(recipient, level, message, title=None, action_url=None, ..., notification_type=None, context=None, channels=['in_app', 'email'])`).
*   **Trigger Points**: This service will be called from various parts of the application logic:
    *   Model `save` methods (use with caution).
    *   Signal receivers (e.g., on `post_save` of an Order, on `user_logged_in`).
    *   Workflow transition actions (e.g., after an invoice is approved).
    *   Explicit calls in API views or service layers.
*   **Logic inside `send_notification`**:
    1.  Check recipient's preferences for the given `notification_type`. Abort if user opted out.
    2.  If templating used, render templates using provided `context`.
    3.  If 'in_app' in `channels`: Create and save a `Notification` model instance.
    4.  If 'email' in `channels`: Trigger an **asynchronous task** (Celery) to send the email using rendered templates.
    5.  If other channels in `channels`: Trigger corresponding async tasks.

### 3.4 Delivery Channels & Asynchronous Processing
*   **In-App**: Handled by creating the `Notification` record. Requires API endpoint for users to fetch their unread/recent notifications.
*   **Email**: Requires configuring Django's email backend. Email sending **must** be delegated to a background task queue (Celery) via dedicated tasks. Tasks should handle rendering, sending, and potentially updating the `Notification` status on success/failure.
*   **Other Channels (SMS/Push - Future)**: Require specific integrations with third-party services, also handled via asynchronous tasks.

### 3.5 User Preferences Integration
*   The `UserProfile` model needs a field (likely JSONField `notification_preferences`) to store user choices (e.g., `{"invoice_approved": {"email": true, "in_app": true}, "marketing_promo": {"email": false}}`).
*   The `send_notification` service must query these preferences before proceeding with generation/delivery for specific channels.
*   Need API endpoints/UI for users to manage their preferences.

### 3.6 Notification Interaction (In-App)
*   **API Endpoint**: `/api/v1/notifications/` (GET) - List notifications for the requesting user (paginated, filterable by status=READ/UNREAD).
*   **API Endpoint**: `/api/v1/notifications/{id}/mark-read/` (POST) - Mark a specific notification as read (updates `status`, `read_at`).
*   **API Endpoint**: `/api/v1/notifications/mark-all-read/` (POST) - Mark all unread notifications as read.

### 3.7 Out of Scope
*   Building complex channel integrations (SMS/Push) in the initial phase (focus on In-App and Email via Celery).
*   Real-time delivery using WebSockets (can be added later).
*   Detailed delivery tracking from external providers (e.g., email open/click tracking).

## 4. Technical Requirements

### 4.1 Data Management
*   Storage for `Notification` and `NotificationTemplate` models.
*   Indexing on `Notification` fields used for querying/filtering (`recipient`, `status`, `notification_type`, `organization`).
*   Efficient storage/retrieval of user preferences.

### 4.2 Asynchronous Task Queue
*   **Requirement**: A task queue system (e.g., **Celery** with Redis/RabbitMQ broker) **must** be implemented for handling external deliveries (Email, etc.).

### 4.3 Security
*   Users should only be able to access/manage their own notifications via API.
*   Secure management of templates.
*   Audit logging of notification generation (optional) and template changes.

### 4.4 Performance
*   Notification generation service should be fast (delegating slow tasks).
*   Efficient querying of user notifications.
*   Task queue must handle notification volume reliably.

### 4.5 Integration
*   Integrates with `User`, `UserProfile`, potentially `Organization` (scoping), `Audit Log`.
*   Called by various business modules/workflows.
*   Integrates with Celery (or chosen task queue).
*   Integrates with email backend/service.
*   *(Future)* Integrates with SMS/Push services.

## 5. Non-Functional Requirements

*   **Scalability**: Handle large volumes of notifications and users. Task queue scalability is key.
*   **Reliability**: Minimize notification loss. Handle delivery errors/retries (in async tasks).
*   **Availability**: Notification fetching API must be available. Delivery depends on task queue and external services.
*   **Timeliness**: While external delivery isn't instant, async tasks should process reasonably quickly.

## 6. Success Metrics

*   High delivery success rate (for triggered notifications respecting preferences).
*   Low error rate in async delivery tasks.
*   Performant fetching of user notifications via API.
*   User satisfaction with notification relevance and preference controls.

## 7. API Documentation Requirements

*   Document `Notification` model fields/states.
*   Document API endpoints for fetching notifications and marking as read.
*   Document available `notification_type` codes and their meaning (for preference management).
*   Document API for managing user notification preferences (if applicable).
*   Document any API for triggering notifications directly (if one exists beyond internal service calls).

## 8. Testing Requirements

*   **Unit Tests**: Test `Notification` model. Test notification service logic (preference checking, template rendering selection). Test template rendering. Test Celery task logic in isolation (mocking external calls).
*   **Integration Tests**:
    *   Trigger events that should generate notifications (e.g., approve an invoice). Verify `Notification` record is created and Celery task is queued.
    *   Test fetching notifications via API for different users.
    *   Test marking notifications as read via API.
    *   Test user preference logic (e.g., ensure email task isn't queued if user opted out).
    *   Mock email backend/services to test task execution.

## 9. Deployment Requirements

*   Migrations for `Notification`, `NotificationTemplate` models.
*   Setup and deployment of Celery workers and broker (Redis/RabbitMQ).
*   Configuration of email backend (API keys, etc.).
*   Initial population of essential `NotificationTemplate`s.

## 10. Maintenance Requirements

*   Monitor Celery queue length and task success/failure rates.
*   Manage notification templates.
*   Regular backups.
*   Keep email/SMS/Push service integrations updated.

---