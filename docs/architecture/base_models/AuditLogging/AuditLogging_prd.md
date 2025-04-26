

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
*   A dedicated concrete model (e.g., `AuditLog` likely in `core` or a dedicated `audit` app) will store individual audit records.
*   **Inheritance**: Should inherit `Timestamped` (provides `created_at` which serves as the primary event timestamp). Does *not* typically inherit `Auditable` (as it logs actions *by* users, not actions *on* the log itself) and is *not* typically `OrganizationScoped` directly (it logs events *within* orgs, identified by the `organization` FK).
*   **Required Fields for each Log Entry**:
    *   `timestamp`: (DateTimeField, default=timezone.now, db_index=True) Explicit timestamp, defaulting to now (can override if logging past events). Often `Timestamped.created_at` is sufficient and this field might be omitted if `Timestamped` is inherited. *(Decision: Use `Timestamped.created_at` or separate `timestamp` field? Using `Timestamped.created_at` is simpler)*. Let's assume use of `Timestamped.created_at`.
    *   `user`: (ForeignKey to `User` (`settings.AUTH_USER_MODEL`), on_delete=models.SET_NULL, null=True, blank=True, db_index=True) The user who performed the action. Null/blank if system-initiated or user deleted.
    *   `organization`: (ForeignKey to `Organization`, on_delete=models.SET_NULL, null=True, blank=True, db_index=True) The organization context in which the action occurred. Essential for filtering logs in a multi-tenant system.
    *   `action_type`: (CharField with choices, max_length=50, db_index=True) The type of action performed (e.g., 'CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'LOGIN_FAILED', 'PERMISSION_ASSIGN', 'PERMISSION_REVOKE', 'ROLE_CHANGE', 'SYSTEM_EVENT', 'ORDER_PLACED'). Needs a well-defined set of choices.
    *   `content_type`: (ForeignKey to `django.contrib.contenttypes.models.ContentType`, null=True, blank=True, db_index=True) The model/type of the primary resource affected by the action (if applicable).
    *   `object_id`: (CharField, max_length=255, null=True, blank=True, db_index=True) The primary key (as string to support UUIDs/Ints) of the specific resource instance affected (if applicable).
    *   `object_repr`: (CharField, max_length=255, blank=True) A human-readable representation of the affected object *at the time of the event* (e.g., Organization name, User username, Product SKU). Useful for quick identification in logs.
    *   `changes`: (JSONField, null=True, blank=True) Stores details of data changes, primarily for 'UPDATE' actions. Structure: `{"field_name": {"old": "old_value", "new": "new_value"}, ...}`. Store only changed fields. Sensitive fields should be masked or excluded based on policy.
    *   `context`: (JSONField, null=True, blank=True) Additional contextual information (e.g., `{"ip_address": "1.2.3.4", "session_key": "abc"}` for logins, `{"source": "api_v1"}` for API actions).
*   **Meta**: `verbose_name`, `plural`, `ordering = ['-created_at']`, relevant `indexes` (e.g., composite on `content_type`, `object_id`).

### 3.2 Event Categories to Audit (Action Types & Triggers)
*   The system must capture and log events for at least the following categories (defining corresponding `action_type` choices):
    *   **Data Changes (CRUD on Key Models)**: Trigger on `post_save` (distinguish CREATE/UPDATE via `created` flag), `post_delete`. Populate `changes` for UPDATEs. Key models include `Organization`, `UserProfile` (and potentially sensitive `User` fields if changed via admin), `Product`, `Category`, `Contact`, `Address`, `Warehouse`, `Document`, `Invoice`, `Order`, `Payment`, `Role`/`Group`, `Permission` assignments, `FieldPermission`, `AutomationRule`, etc. *(Maintain a list of explicitly audited models)*.
    *   **User Authentication**: Trigger on `user_logged_in`, `user_logged_out`, `user_login_failed` signals. Populate `context` with IP Address. `action_type` examples: 'LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGOUT'.
    *   **Permission/Role Changes**: Trigger on `m2m_changed` for `User.groups`, `Group.permissions`, or via explicit logging when `FieldPermission` or `UserOrganizationRole` records are changed. `action_type` examples: 'USER_ROLE_ADDED', 'USER_ROLE_REMOVED', 'ROLE_PERMISSION_CHANGED'.
    *   **Key System Events**: Explicit logging for critical actions like initiating major data imports/exports (`DataJob` status changes), running critical maintenance tasks. `action_type` examples: 'EXPORT_JOB_STARTED', 'IMPORT_JOB_COMPLETED'.

### 3.3 Event Capturing Mechanism
*   **Primary Method**: Utilize **Django Signals** (`post_save`, `post_delete`, auth signals, `m2m_changed`, potentially custom signals) connected to receiver functions.
*   **Signal Receivers**: Implement efficient receiver functions (ideally in `signals.py` per app or a central `audit/receivers.py`).
    *   Receivers extract context (user from request middleware like `django-crum`, instance data, `created`/`update_fields` flags).
    *   Determine `action_type`.
    *   For UPDATEs, calculate the `changes` dictionary (comparing `instance` fields to previous state, possibly requiring fetching the object pre-save or using a library like `django-simple-history`'s tracking). Handle related fields carefully. Mask sensitive fields.
    *   Determine `organization` context.
    *   Create and save the `AuditLog` instance.
    *   **Consider Asynchronicity:** If calculating `changes` is complex or saving the `AuditLog` adds noticeable latency to critical operations, consider queuing an asynchronous Celery task from the signal receiver to create the `AuditLog` entry. This adds complexity but improves primary request performance. *(Decision: Sync vs Async logging? Start with Sync, optimize later if needed)*.
*   **Helper Function**: Create a central helper function `log_audit_event(user, organization, action_type, content_object=None, changes=None, context=None)` to standardize log creation.

### 3.4 Log Access & Querying
*   **Admin Interface**: Provide a read-only Django Admin interface for `AuditLog`.
    *   Use `list_display` to show key fields (timestamp, user, org, action, object repr).
    *   Implement `list_filter` for filtering by `user`, `organization`, `action_type`, `content_type`, date range (`timestamp`).
    *   Implement `search_fields` for searching `object_repr`, potentially `user__username`.
    *   Display `changes` and `context` JSON nicely (perhaps using `django-json-widget`).
*   **API (Restricted)**: Provide a read-only API endpoint (e.g., `/api/v1/audit-logs/`) secured for Admin/Auditor roles.
    *   Support filtering similar to the Admin interface via query parameters.
    *   Implement pagination.

## 4. Technical Requirements

### 4.1 Data Management (`AuditLog` Model)
*   **Storage**: Standard DB storage. `JSONB` in PostgreSQL is crucial for efficient querying/indexing of `changes` and `context` fields.
*   **Indexing**: Critical indexes on fields used for filtering: `created_at` (timestamp), `user`, `organization`, `action_type`, `content_type`, `object_id`. Composite index on `(content_type, object_id)` is essential for finding history for a specific object. Consider GIN indexes on `changes` and `context` JSONB fields in PostgreSQL if querying within them is required.
*   **Data Volume & Archiving/Purging**: The `AuditLog` table **will grow very large**. A strategy for managing this size is **essential**:
    *   Define a data retention policy (e.g., keep active logs for 90 days, archive up to 1 year, purge older).
    *   Implement regular (e.g., nightly/weekly) archiving (moving data to slower/cheaper storage or separate tables) or purging (deletion) based on the retention policy. This typically requires custom management commands or database procedures.
*   **Immutability**: Design to prevent modification of log entries after creation (enforce via application logic/permissions).

### 4.2 Security
*   **Access Control**: Use Django permissions (`view_auditlog`) assigned to specific Admin/Auditor roles to strictly control who can view logs via Admin/API. No standard user access.
*   **Data Masking**: Implement logic (e.g., within the signal receiver or `log_audit_event` helper) to mask or exclude sensitive fields (passwords, tokens, PII based on policy) before saving them in the `changes` JSON field.
*   **Integrity**: Protect against tampering (standard DB security).

### 4.3 Performance
*   **Log Creation**: Minimize performance impact of signal receivers/logging calls on primary operations. Use efficient methods for detecting changes. Consider async logging if needed.
*   **Log Querying**: Ensure queries (Admin filters, API) are highly performant using appropriate indexes. Avoid slow queries on the potentially massive `AuditLog` table.

### 4.4 Integration
*   **Signal Registration**: Connect receivers to relevant signals from audited models and auth system.
*   **User/Organization Context**: Requires reliable access to the current user and organization context (e.g., via middleware like `django-crum` or passing context explicitly).
*   **ContentType Framework**: Relies heavily on `django.contrib.contenttypes`.

## 5. Non-Functional Requirements

*   **Scalability**: Handle high volume of log entries. Database performance for writes and reads must scale. Archiving/Purging essential for long-term scalability.
*   **Reliability**: Logging mechanism should be reliable; minimize loss of audit records.
*   **Availability**: Viewing interface/API should be available for authorized users.
*   **Data Consistency**: Ensure logged data (user, object refs, changes) is accurate at the time of the event.

## 6. Success Metrics

*   Comprehensive coverage of critical events as defined.
*   Ability to successfully retrieve audit history for specific objects or users.
*   Performance of log creation has negligible impact on user operations.
*   Performance of log querying meets requirements for administrators/auditors.
*   Compliance requirements related to audit trails are met.

## 7. API Documentation Requirements (If Log Query API is implemented)

*   Document the `/audit-logs/` endpoint.
*   Detail available query parameters for filtering.
*   Describe the `AuditLog` response structure, including `changes` and `context` formats.
*   Specify required Admin/Auditor permissions.

## 8. Testing Requirements

*   **Unit Tests**: Test signal receiver logic (parsing args, calculating changes, calling log creation helper - requires mocking). Test `log_audit_event` helper function. Test data masking logic.
*   **Integration Tests**:
    *   Trigger audited actions (create/update/delete models, login/logout) and verify `AuditLog` entries are created with the correct `user`, `organization`, `action_type`, `content_object`, `changes`, and `context`.
    *   Test filtering logs via Admin interface or API with various parameters.
    *   Test access control for viewing logs.
    *   Test archiving/purging scripts/commands (requires careful test setup).
*   **Performance Tests**: Measure write throughput and query performance on a large, populated `AuditLog` table in a staging environment.

## 9. Deployment Requirements

*   Migrations for `AuditLog` model and crucial indexes.
*   Ensure signal receivers are connected in production.
*   Deploy and schedule archiving/purging jobs/commands.
*   Assign `view_auditlog` permissions to appropriate roles.
*   Configure data masking rules for sensitive fields.

## 10. Maintenance Requirements

*   Monitor `AuditLog` table growth and query performance.
*   Ensure archiving/purging jobs run successfully.
*   Update audited models list and signal receivers as application evolves.
*   Regular database maintenance (indexing, vacuuming) on the `AuditLog` table.

--- END OF FILE audit_logging_system_prd.md ---