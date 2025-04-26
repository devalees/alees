# Audit Logging System - Product Requirements Document (PRD) - Refined

## 1. Overview

*   **Purpose**: To define the requirements for a standardized **Audit Logging System** responsible for creating and storing an immutable trail of significant activities and data changes within the ERP system.
*   **Scope**: Definition of the central `AuditLog` model, the mechanisms for capturing auditable events, basic requirements for accessing/querying the logs, and related technical considerations. This system provides historical tracking and accountability.
*   **Target Users**: System Administrators, Auditors, Compliance Officers, potentially Support Staff (with specific, limited query permissions).

## 2. Business Requirements

*   **Accountability**: Track user actions and system events to determine who did what, when.
*   **Change History**: Provide a historical record of modifications to critical data entities.
*   **Compliance**: Support internal and external audit requirements by providing verifiable logs.
*   **Security Monitoring**: Aid in detecting suspicious activities or unauthorized changes.
*   **Troubleshooting**: Assist in diagnosing issues by reviewing the sequence of events leading up to a problem.

## 3. Functional Requirements

### 3.1 Audit Log Entry (`AuditLog` Model Definition)
*   A dedicated model (e.g., `AuditLog`) will store individual audit records.
*   **Required Fields for each Log Entry**:
    *   `timestamp`: (DateTimeField, auto_now_add=True, db_index=True) When the event occurred.
    *   `user`: (ForeignKey to `User`, on_delete=models.SET_NULL, null=True, blank=True, db_index=True) The user who performed the action. Null/blank if system-initiated.
    *   `action_type`: (CharField with choices, db_index=True) The type of action performed (e.g., 'CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'PERMISSION_CHANGE', 'SYSTEM_EVENT').
    *   `content_type`: (ForeignKey to `django.contrib.contenttypes.models.ContentType`, null=True, blank=True, db_index=True) The model/type of the resource affected (if applicable).
    *   `object_id`: (PositiveIntegerField or CharField, null=True, blank=True, db_index=True) The primary key of the specific resource instance affected (if applicable). *Use CharField if UUIDs are used.*
    *   `object_repr`: (CharField, max_length=255, blank=True) A human-readable representation of the object at the time of the event (e.g., Organization name, User username).
    *   `changes`: (JSONField, null=True, blank=True) Stores details of data changes, especially for 'UPDATE' actions. Structure could be `{"field_name": {"old": "old_value", "new": "new_value"}, ...}`. Only store if `action_type` is relevant (e.g., UPDATE).
    *   `context`: (JSONField, null=True, blank=True) Additional contextual information (e.g., IP address for logins, session ID, source system).
    *   `organization`: (ForeignKey to `Organization`, on_delete=models.SET_NULL, null=True, blank=True, db_index=True) The organization context in which the action occurred (important for multi-tenant filtering of logs).

### 3.2 Event Categories to Audit (Action Types & Triggers)
*   The system must capture and log events for at least the following categories:
    *   **Data Changes (CRUD on Key Models)**: Record 'CREATE', 'UPDATE', 'DELETE' actions on core models (e.g., `Organization`, `User`, `Product`, `Permission`, `Role`, `Order`, `Invoice`, etc. - *list to be maintained*). `changes` field should be populated for UPDATES.
    *   **User Authentication**: Record 'LOGIN', 'LOGOUT', 'LOGIN_FAILED' events. Include IP address in `context`.
    *   **Permission/Role Changes**: Record changes to user roles or permissions ('PERMISSION_ASSIGN', 'PERMISSION_REVOKE', 'ROLE_CHANGE').
    *   **Key Configuration Changes**: Record changes to critical system settings (specifics TBD).
    *   *(Optional)* Specific Business Operations (e.g., 'ORDER_PLACED', 'PAYMENT_PROCESSED') if detailed business process auditing is required beyond simple CRUD.

### 3.3 Event Capturing Mechanism
*   **Primary Method**: Utilize **Django Signals** (`post_save`, `post_delete`, `user_logged_in`, `user_logged_out`, `user_login_failed`, potentially custom signals) to trigger the creation of `AuditLog` entries asynchronously or synchronously as appropriate.
*   **Signal Receivers**: Implement signal receiver functions that:
    *   Receive the signal arguments (e.g., `sender`, `instance`, `created`, `update_fields`, `user`, `request`).
    *   Extract necessary information (User, Action Type, Resource details, Changes, Context).
    *   Create and save an `AuditLog` instance.
    *   Handle potential errors gracefully.
*   **Alternative**: Middleware (for request-level context) or explicit function calls within critical service layers might supplement signals.

### 3.4 Log Access & Querying
*   **Admin Interface**: Provide an interface in the Django Admin site for viewing `AuditLog` records.
    *   Read-only display.
    *   Include filtering capabilities (by user, date range, action type, content type/object, organization).
    *   Include search capabilities.
*   **API (Optional/Restricted)**: Consider a read-only API endpoint (e.g., `/api/v1/audit-logs/`) for querying logs, secured for specific administrative/auditor roles. This API should support filtering similar to the Admin interface.

## 4. Technical Requirements

### 4.1 Data Management (`AuditLog` Model)
*   **Storage**: Choose appropriate database types (e.g., `TIMESTAMP WITH TIME ZONE`, `JSONB` for PostgreSQL).
*   **Indexing**: Implement database indexes on key query fields: `timestamp`, `user`, `action_type`, `content_type`, `object_id`, `organization`. Composite indexes might be beneficial.
*   **Data Volume & Archiving**: Plan for large data volumes. Implement a strategy for archiving or purging old audit logs after a defined retention period (e.g., move to cold storage, delete after X years based on compliance needs).
*   **Immutability**: Log entries, once written, should not be modifiable by standard application logic or users (enforced via permissions and potentially database triggers if required).

### 4.2 Security
*   **Access Control**: Access to view audit logs (via Admin or API) must be strictly controlled using the `Permission` system. Define specific roles (e.g., `Auditor`, `SuperAdmin`) with `view_auditlog` permission. Standard users should *not* have access.
*   **Integrity**: Protect against unauthorized modification or deletion of log entries (database-level permissions, application logic).

### 4.3 Performance
*   **Log Creation**: The process of creating log entries (e.g., signal receivers) should have minimal performance impact on the primary user action. Consider asynchronous logging (e.g., via Celery) for high-frequency events if synchronous logging causes delays, but weigh against the risk of losing logs if the async task fails.
*   **Log Querying**: Queries against the `AuditLog` table must be efficient, supported by proper indexing. Avoid inefficient queries (e.g., full text search on JSON without specific indexing).

### 4.4 Integration
*   **Signal Registration**: Ensure signal receivers are correctly registered to listen to events from all designated auditable models and authentication signals.
*   **User Context**: Reliably capture the correct `request.user` performing the action. Handle system-initiated actions where no user is present.
*   **Organization Context**: Reliably capture the `Organization` context for the event, potentially from the affected object or the user's session/request.

## 5. Non-Functional Requirements

*   **Scalability**: System must handle a high volume of audit event generation without impacting overall application performance. Database and query performance must scale.
*   **Reliability**: The logging mechanism should be highly reliable. Minimize log loss.
*   **Availability**: The audit log viewing interface/API should be available to authorized personnel.
*   **Data Consistency**: Timestamps should be accurate (UTC). Relationships (User, ContentType, Organization) should be consistent.
*   **Maintainability**: Signal receivers and logging logic should be well-organized and maintainable.

## 6. Success Metrics

*   **Audit Coverage**: Percentage of critical actions/models successfully generating audit logs.
*   **Log Integrity**: Absence of unauthorized modifications to log data.
*   **Query Performance**: Audit log query times meet defined performance targets for common filter combinations.
*   **Compliance Fulfillment**: Ability to generate reports or provide data satisfying audit/compliance requests.

## 7. API Documentation Requirements (If Log Query API is implemented)

*   OpenAPI/Swagger documentation for the `/audit-logs/` endpoint.
*   Detailed description of query parameters (filtering by date, user, action, resource, organization).
*   Request/response examples, including the structure of the `changes` and `context` fields.
*   Authentication/Authorization documentation (Admin/Auditor roles required).
*   Error code documentation.

## 8. Testing Requirements

*   **Unit Tests**: Test signal receiver logic in isolation (e.g., given signal args, does it create the correct `AuditLog` structure?).
*   **Integration Tests**:
    *   Perform CRUD operations on auditable models and verify the corresponding `AuditLog` entries are created correctly with accurate data (user, action, object, changes, organization).
    *   Test user login/logout/failed login signal handling.
    *   Test permission change logging.
    *   Test querying logs via Admin UI/API with various filters.
    *   Test access control – ensure unauthorized users cannot view logs.
*   **Performance Tests**: Simulate high event volume to measure impact on application performance and log write times. Test query performance on a large `AuditLog` table.

## 9. Deployment Requirements

*   **Migrations**: Standard Django migration for creating the `AuditLog` table and its indexes.
*   **Signal Registration**: Ensure signals are connected in production environment (e.g., via `AppConfig.ready()`).
*   **Archiving/Purging**: Deploy scripts or configure scheduled tasks for managing old log data according to the defined retention policy.
*   **Permissions Setup**: Ensure appropriate roles/groups have `view_auditlog` permissions assigned in production.

## 10. Maintenance Requirements

*   Regular database maintenance (index rebuilding, vacuuming) for the `AuditLog` table.
*   Execution and monitoring of archiving/purging jobs.
*   Review and potentially update the list of auditable models/actions as the application evolves.
*   Monitor log volume and storage usage.

