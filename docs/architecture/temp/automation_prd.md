
# Automation Rule Engine - Product Requirements Document (PRD) - Revised

## 1. Overview

*   **Purpose**: To define a system for creating, managing, and executing **configurable automation rules** within the ERP. These rules allow for automated actions (including CRUD operations on data) based on **data change events** (Create/Update/Delete) or **time-based schedules**, subject to complex, potentially cross-model **conditions**.
*   **Scope**: Definition of models to store automation rules (`AutomationRule`, `RuleCondition`, `RuleAction`), integration with Django signals and a scheduler (Celery Beat) for triggering, a condition evaluation engine supporting cross-model checks and AND/OR logic, execution of predefined actions (including CRUD) via Celery, detailed execution logging, and API endpoints for rule management by authorized users.
*   **Implementation Strategy**: Involves concrete Django Models (`AutomationRule`, `RuleCondition`, `RuleAction`, `AutomationLog`). Relies on **Django Signals** for event triggers, **Celery Beat** integration for scheduled triggers, **Celery** for asynchronous condition evaluation and action execution. Requires a robust condition evaluation engine and predefined, registered action functions.
*   **Target Users**: System Administrators, Power Users (with appropriate permissions), Developers (defining available actions, ensuring system integrity).

## 2. Business Requirements

*   **Automate Business Processes**: Trigger sequences of actions automatically based on data events or schedules to streamline workflows and reduce manual effort.
*   **Enforce Complex Business Rules**: Implement conditional logic based on data across multiple related entities to ensure policies are followed or necessary steps are taken.
*   **Cross-Module Coordination**: Enable automation that spans different parts of the ERP (e.g., confirming a Sales Order triggers Project creation).
*   **Configurability via API**: Allow authorized administrators/users to define, manage, and monitor automation rules through API endpoints.
*   **Scheduled Operations**: Automate routine tasks or checks based on time schedules (daily, weekly, monthly, etc.).
*   **Reliability & Transparency**: Ensure automations execute reliably and provide detailed logs for tracking and troubleshooting.

## 3. Functional Requirements

### 3.1 Core Models
*   **`AutomationRule` Model**:
    *   **Purpose**: Defines a single automation rule.
    *   **Inheritance**: `Timestamped`, `Auditable`, `OrganizationScoped`.
    *   **Fields**:
        *   `name`: (CharField, max_length=255) Unique name for the rule within the organization.
        *   `description`: (TextField, blank=True).
        *   `trigger_type`: (CharField with choices: 'MODEL_EVENT', 'SCHEDULED').
        *   `trigger_source_content_type`: (ForeignKey to `ContentType`, null=True, blank=True) The model whose events trigger this rule (used if `trigger_type` is 'MODEL_EVENT').
        *   `trigger_event`: (CharField with choices: 'CREATED', 'UPDATED', 'DELETED', blank=True) The type of model event (used if `trigger_type` is 'MODEL_EVENT').
        *   `schedule`: (CharField, max_length=100, blank=True) Crontab-like schedule string (e.g., '0 2 * * *' for 2 AM daily) (used if `trigger_type` is 'SCHEDULED'). Requires validation.
        *   `condition_logic`: (CharField with choices: 'ALL_MET' (AND), 'ANY_MET' (OR), default='ALL_MET') How conditions are combined. *(Advanced: Could be JSON for nested logic)*.
        *   `is_active`: (BooleanField, default=True, db_index=True) Enable/disable the rule.
        *   `execution_delay_seconds`: (PositiveIntegerField, default=0) Optional delay before executing actions (handled via Celery `countdown`).
*   **`RuleCondition` Model**:
    *   **Purpose**: Defines a condition to be evaluated. Multiple conditions linked via `AutomationRule.condition_logic`.
    *   **Inheritance**: `Timestamped`, `Auditable`.
    *   **Fields**:
        *   `rule`: (ForeignKey to `AutomationRule`, on_delete=models.CASCADE, related_name='conditions')
        *   `field_name`: (CharField) Field to check on the triggering object or a related object (using `__` notation, e.g., `status`, `order__customer__category`, `triggering_object__related_invoice__total`). **Must support related lookups**.
        *   `operator`: (CharField with choices: 'EQ', 'NEQ', 'GT', 'GTE', 'LT', 'LTE', 'CONTAINS', 'ICONTAINS', 'IN', 'NOTIN', 'ISNULL', 'ISNOTNULL', 'CHANGED_TO', 'CHANGED_FROM') Comparison operator. *(`CHANGED_TO`/`FROM` require passing old/new state)*.
        *   `value`: (JSONField) The value to compare against (stores string, number, boolean, list).
*   **`RuleAction` Model**:
    *   **Purpose**: Defines an action to perform if conditions are met. Executes sequentially based on `order`.
    *   **Inheritance**: `Timestamped`, `Auditable`.
    *   **Fields**:
        *   `rule`: (ForeignKey to `AutomationRule`, on_delete=models.CASCADE, related_name='actions')
        *   `action_type`: (CharField, db_index=True) Code identifying the registered action function (e.g., 'update_field', 'send_notification', 'create_record', 'update_related_record', 'delete_record', 'call_webhook').
        *   `parameters`: (JSONField, default=dict, blank=True) Configuration/parameters for the action (e.g., `{"target_model": "app.Model", "data": {"field1": "value1", ...}}` for create/update, `{"notification_type": "...", ...}` for notify).
        *   `order`: (PositiveSmallIntegerField, default=0) Order of execution.
*   **`AutomationLog` Model**:
    *   **Purpose**: Tracks execution history and detailed state.
    *   **Inheritance**: `Timestamped`, `Auditable`, `OrganizationScoped`.
    *   **Fields**:
        *   `rule`: (ForeignKey to `AutomationRule`, on_delete=models.SET_NULL, null=True).
        *   `trigger_type`: (CharField: 'MODEL_EVENT', 'SCHEDULED').
        *   `trigger_content_type`, `trigger_object_id`: (FK to ContentType, Char/Int Field) Triggering object details (if applicable).
        *   `status`: (CharField: 'PENDING', 'EVALUATING', 'CONDITIONS_MET', 'CONDITIONS_NOT_MET', 'ACTIONS_QUEUED', 'ACTION_RUNNING', 'ACTION_FAILED', 'COMPLETED', 'FAILED', default='PENDING').
        *   `execution_start_time`, `execution_end_time`: (DateTimeField, nullable).
        *   `condition_results`: (JSONField, null=True) Stores outcome of condition checks.
        *   **`action_logs`**: (JSONField, default=list, blank=True) **Crucial for State Tracking (#5)**. List of dicts, each detailing an action step: `{"action_order": 0, "action_type": "update_field", "parameters": {...}, "status": "SUCCESS"|"FAILURE", "timestamp": "...", "message": "...", "state_before": {...}, "state_after": {...}}`. *(Storing before/after state can be complex/verbose)*.
        *   `error_message`: (TextField, blank=True) Overall error if job failed.
        *   `celery_task_id`: (CharField, nullable).

### 3.2 Trigger Mechanisms
*   **Model Events (Signals)**: Generic signal receivers (`post_save`, `post_delete`) query active `AutomationRule`s matching the sender model and event type, then queue `evaluate_automation_rule` Celery task. Receivers must efficiently pass necessary context (instance PK, content_type ID, potentially changed fields map, user ID).
*   **Scheduled Events (Celery Beat)**:
    1.  A periodic Celery Beat task runs (e.g., every minute).
    2.  It queries `AutomationRule`s where `trigger_type='SCHEDULED'`.
    3.  For each rule whose `schedule` matches the current time (using a crontab parsing library), it queues the `evaluate_automation_rule` Celery task (passing rule ID, maybe current time as context, no specific trigger object). Conditions for scheduled tasks often check date ranges or aggregated data.

### 3.3 Rule Evaluation & Action Execution (Celery Task)
*   Implement `evaluate_automation_rule(rule_id, trigger_context)` Celery task.
*   **Context**: Contains triggering object info (if any), triggering user (if any), potentially changed fields map.
*   **Logic**:
    1.  Log start in `AutomationLog` ('PENDING'/'EVALUATING').
    2.  Fetch `AutomationRule`, `instance` (if applicable).
    3.  **Evaluate Conditions**: Iterate through `RuleCondition`s. Implement robust evaluator handling `field_name` lookups (direct and `__` related), all specified `operator`s, and type-safe comparisons against `value`. Combine results using `rule.condition_logic` (AND/OR). Log condition results to `AutomationLog.condition_results`.
    4.  If conditions fail, update `AutomationLog` ('CONDITIONS_NOT_MET'), return.
    5.  If conditions pass, update `AutomationLog` ('CONDITIONS_MET'/'ACTIONS_QUEUED').
    6.  Iterate through `RuleAction`s by `order`. For each:
        *   Update `AutomationLog` ('ACTION_RUNNING' + action details).
        *   Lookup registered action function via `action_type`.
        *   *(Optional/Complex)* Capture relevant `state_before`.
        *   Execute action function, passing `instance` (if applicable), `parameters`, `user`.
        *   Capture `state_after` (if applicable), result/message, success/failure.
        *   Log action details, status, message, state changes into `AutomationLog.action_logs`.
        *   If an action fails, stop processing further actions for this rule instance, set overall `AutomationLog` status to 'FAILED', log error.
    7.  If all actions succeed, set `AutomationLog` status to 'COMPLETED'.

### 3.4 Available Actions (Predefined & Registered)
*   Requires a registry mapping `action_type` strings to Python functions.
*   **Must include CRUD:**
    *   `create_record(parameters, trigger_context)`: Creates a new record. `parameters` specify model type and field data (can use values from trigger context).
    *   `update_record(parameters, trigger_context)`: Updates fields on the triggering record OR a related record found via lookup defined in `parameters`.
    *   `delete_record(parameters, trigger_context)`: Deletes the triggering record OR a related record.
*   **Other essential actions:**
    *   `send_notification(parameters, trigger_context)`
    *   `call_webhook(parameters, trigger_context)`
*   *Developers add new reusable actions to the registry.*

### 3.5 Management & Monitoring API (#3 In Scope)
*   Provide RESTful API endpoints for **authorized users** to perform CRUD operations on `AutomationRule`, `RuleCondition`, `RuleAction`.
*   API for listing/retrieving `AutomationLog` records (filter by rule, status, date, triggering object). Include detailed `action_logs`.
*   Endpoints should enforce permissions (e.g., only admins or specific roles can manage rules).

## 4. Technical Requirements

### 4.1 Libraries & Infrastructure
*   Requires **Celery** and message broker.
*   Requires **Celery Beat** (or other scheduler) for scheduled triggers.
*   Relies on Django Signals, `ContentType`.
*   Needs a crontab parsing library (e.g., `python-crontab`, `croniter`).

### 4.2 Condition Engine
*   Implement a robust function to evaluate conditions, safely handling field lookups (`instance.related__field`) and various operators/types defined in `RuleCondition`. Handle potential `DoesNotExist` errors during related lookups gracefully. Support AND/OR combination based on `AutomationRule.condition_logic`.

### 4.3 Action Registry & Execution
*   Implement a pattern (e.g., Python dictionary, class registry) to map `RuleAction.action_type` strings to executable Python functions.
*   Action functions must accept standard arguments (like `parameters`, `trigger_context`) and handle their own logic, including database operations or external calls. They should return success/failure status and messages.

### 4.4 Security
*   Secure the Rule Management API endpoints with appropriate permissions.
*   Action execution context: Decide if actions run with system privileges or impersonate the triggering user. Impersonation is complex but often safer. System privileges require careful validation within actions to prevent unauthorized data access/modification.
*   Validate `field_name` lookups in conditions to prevent accessing unintended data.
*   Sanitize parameters passed to actions, especially for `call_webhook`.
*   Audit logging of rule definition changes and rule executions (`AutomationLog`).

### 4.5 Performance & Scalability
*   Efficient querying for active rules upon signal triggers.
*   Condition evaluation must be performant. Avoid very complex related lookups in conditions if possible.
*   Action execution via Celery allows scaling workers.
*   `AutomationLog` table can grow large; requires indexing and potentially partitioning/archiving strategy.

## 5. Non-Functional Requirements

*   Scalability (handle many rules, frequent triggers, many actions).
*   Reliability (ensure rules trigger, conditions evaluate correctly, actions run, errors handled).
*   Availability (Engine depends on Celery, Broker, DB).
*   Maintainability (Rule definitions, action functions, engine logic).

## 6. Success Metrics

*   High success rate for rule executions.
*   Measurable reduction in manual tasks corresponding to automated rules.
*   Performance of trigger handling, condition evaluation, and action execution within acceptable limits.
*   Administrators can successfully define and manage required automations via API.

## 7. API Documentation Requirements

*   Document models (`AutomationRule`, `RuleCondition`, `RuleAction`, `AutomationLog` including `action_logs` structure).
*   Document **API endpoints for managing rules/conditions/actions**. Detail payload structure for creation/update.
*   Document API endpoint for querying `AutomationLog` history.
*   Document available `trigger_event` types, condition `operator`s, registered `action_type`s and their required `parameters`.
*   Document schedule format (e.g., standard crontab).
*   Document permissions required for management APIs.

## 8. Testing Requirements

*   **Unit Tests**: Test condition evaluation logic extensively (all operators, related lookups, AND/OR). Test individual action functions (mocking DB/external calls). Test Celery task logic (mocking rule loading, evaluation, action calls). Test crontab parsing/matching.
*   **Integration Tests**:
    *   Requires Celery worker/beat (or eager mode).
    *   Test signal-triggered rules: Modify models, verify correct task queued, conditions evaluated correctly (met/not met), actions executed (verify side effects), `AutomationLog` updated accurately (including `action_logs` detail).
    *   Test schedule-triggered rules: Advance time (using libraries like `freezegun`), verify Celery Beat queues task, verify rule execution and logging.
    *   Test API endpoints for Rule CRUD: Create complex rules with conditions/actions via API, verify they are saved correctly.
    *   Test API endpoint for querying `AutomationLog`.
    *   Test permission enforcement on management APIs.
    *   Test various failure scenarios (condition fail, action fail) and check `AutomationLog`.
*   **Performance/Load Tests**: Simulate high frequency triggers to test system throughput.

## 9. Deployment Requirements

*   Migrations for automation models & indexes.
*   Deployment of Celery workers and Celery Beat service.
*   Deployment of registered action functions.
*   Secure configuration for action parameters (e.g., webhook URLs/secrets).
*   Initial setup of any default/required automation rules.

## 10. Maintenance Requirements

*   Monitor Celery queues, Beat schedule, worker health.
*   Monitor `AutomationLog` for failures and performance issues.
*   Maintain/update rule definitions via API/Admin as business processes change.
*   Develop and register new action functions as needed.
*   Manage `AutomationLog` size (archiving/pruning). Standard backups.

---