Okay, let's generate the implementation steps for the **Automation Rule Engine**. This is a complex system involving multiple models, signal handling, scheduled task integration (Celery Beat), asynchronous execution (Celery workers), condition evaluation, and action execution, plus management APIs. These steps outline the foundational setup.

--- START OF FILE automation_implementation_steps.md ---

# Automation Rule Engine - Implementation Steps

## 1. Overview

**System Name:**
Automation Rule Engine

**Corresponding PRD:**
`automation_prd.md` (Revised version including API management, complex conditions, scheduling, detailed logging)

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `Organization`, `ContentType`, Celery infrastructure (Workers + Beat), Redis (Broker), `django-crum` (or similar user middleware), crontab parsing library. Needs Notification system, other models for actions/conditions.

**Key Features:**
Defines and executes configurable automation rules triggered by model events or schedules. Supports complex conditions (cross-model, AND/OR) and actions (CRUD, notifications, webhooks). Includes detailed logging and API-based management for authorized users.

**Primary Location(s):**
*   Models, Tasks, Signals, Services: `automation/` (New dedicated app recommended)
*   API Views/Serializers/URLs: `api/v1/automations/` (New dedicated API structure)
*   Celery Beat Schedule Task: Defined in Celery config or `automation` app.

## 2. Prerequisites

[ ] Verify all prerequisite models/mixins (`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `Organization`, `ContentType`, `Notification` system service, target models for actions/conditions) are implemented.
[ ] Verify Celery (Workers + Beat) and Redis infrastructure is operational.
[ ] Verify user context middleware (`django-crum`) is active.
[ ] **Install Libraries:** `pip install python-crontab` (or `croniter`).
[ ] **Create new Django app:** `python manage.py startapp automation`.
[ ] Add `'automation'` to `INSTALLED_APPS`.
[ ] Ensure `factory-boy` is set up. Factories for core models exist.
[ ] Define choices for `trigger_type`, `trigger_event`, `condition_logic`, `operator`, `action_type`, `AutomationLog.status` (e.g., in `automation/choices.py`).

## 3. Implementation Steps (TDD Workflow)

  *(Models -> Actions/Conditions -> Triggers -> Task -> API)*

  ### 3.1 Core Model Definitions (`automation/models.py`)

  [ ] **(Test First - AutomationRule)** Write Unit Tests (`tests/unit/test_models.py`) verifying: `AutomationRule` creation, fields, defaults, unique name, FKs, schedule validation (if possible at model level), inheritance, `__str__`.
  [ ] Define `AutomationRule` model. Inherit `Timestamped`, `Auditable`, `OrganizationScoped`. Include fields from PRD 3.1. Add validation for `schedule` field if `trigger_type` is 'SCHEDULED'.
  [ ] Run Rule tests; expect pass. Refactor.
  [ ] **(Test First - RuleCondition)** Write Unit Tests verifying: `RuleCondition` creation, FK to Rule, fields (`field_name`, `operator`, `value`), inheritance, `__str__`.
  [ ] Define `RuleCondition` model. Inherit `Timestamped`, `Auditable`. Include fields from PRD 3.1.
  [ ] Run Condition tests; expect pass. Refactor.
  [ ] **(Test First - RuleAction)** Write Unit Tests verifying: `RuleAction` creation, FK to Rule, fields (`action_type`, `parameters`, `order`), inheritance, `__str__`.
  [ ] Define `RuleAction` model. Inherit `Timestamped`, `Auditable`. Include fields from PRD 3.1.
  [ ] Run Action tests; expect pass. Refactor.
  [ ] **(Test First - AutomationLog)** Write Unit Tests verifying: `AutomationLog` creation, fields, defaults, FKs, GFK representation, inheritance, `__str__`.
  [ ] Define `AutomationLog` model. Inherit `Timestamped`, `Auditable`, `OrganizationScoped`. Include fields from PRD 3.1, especially `action_logs` JSONField. Define Meta with indexes.
  [ ] Run Log tests; expect pass. Refactor.

  ### 3.2 Factory Definitions (`automation/tests/factories.py`)

  [ ] Define factories for `AutomationRule`, `RuleCondition`, `RuleAction`, `AutomationLog`. Handle relationships (use SubFactory, post-generation for related Conditions/Actions). Set required FKs like `organization`. Handle GFKs in `AutomationLogFactory`.
  [ ] **(Test)** Write simple tests ensuring factories create valid instances and relationships.

  ### 3.3 Action Registry & Condition Evaluator (`automation/actions.py`, `automation/conditions.py`)

  [ ] **(Test First - Actions)** Write Unit Tests for *each* planned action function (e.g., `test_update_record_action`, `test_send_notification_action`). Mock dependencies (ORM save, notification service call, webhook requests). Verify correct parameters are used and expected outcomes occur (or exceptions raised).
  [ ] Create `automation/actions.py`. Define placeholder functions for each `action_type` identified in the PRD (e.g., `update_record`, `create_record`, `delete_record`, `send_notification`, `call_webhook`). Implement the core logic for each, accepting standard arguments (`trigger_context`, `parameters`). Implement a registry dictionary mapping `action_type` strings to these functions.
  [ ] Run action tests; expect pass. Refactor actions.
  [ ] **(Test First - Conditions)** Write Unit Tests for the condition evaluation logic (`test_evaluate_conditions`). Test all operators, value types, AND/OR logic, **cross-model relationship lookups** (`__`), handling of `None` values, and error conditions (invalid field, invalid operator).
  [ ] Create `automation/conditions.py`. Implement the `evaluate_conditions(rule, instance)` function (or class). This function fetches the rule's conditions, iterates through them, performs the lookups and comparisons safely (handling potential `AttributeError`, `DoesNotExist`), combines results using `rule.condition_logic`, and returns `True` or `False`.
  [ ] Run condition tests; expect pass. Refactor evaluator.

  ### 3.4 Trigger Mechanisms (Signals, Scheduled Task)

  [ ] **(Test First - Signals)** Write Integration Tests (`tests/integration/test_triggers.py`) using `@pytest.mark.django_db`. Mock the Celery `evaluate_automation_rule.delay` task. Trigger `post_save`/`post_delete` on a sample model configured in a test `AutomationRule`. Assert the task is queued with correct arguments (rule_id, context).
  [ ] Create `automation/signals.py`. Implement generic `post_save`/`post_delete` signal receivers. Receivers query `AutomationRule` based on `sender`, `created`/event type, and `is_active`. For matching rules, queue `evaluate_automation_rule` task. Pass necessary context (PK, content_type ID, changed fields map, user ID).
  [ ] Connect signals in `automation/apps.py`.
  [ ] Run signal tests; expect pass. Refactor.
  [ ] **(Test First - Scheduler)** Write Integration Tests. Mock `evaluate_automation_rule.delay`. Use `freezegun` to simulate time. Set up a scheduled `AutomationRule`. Trigger the Celery Beat scheduler task manually or verify its configuration. Assert the evaluation task is queued at the correct time based on the rule's `schedule`.
  [ ] Create a periodic Celery task (e.g., in `automation/tasks.py`, scheduled via `django-celery-beat` or settings `CELERY_BEAT_SCHEDULE`) that runs frequently (e.g., every minute). This task queries active `AutomationRule`s with `trigger_type='SCHEDULED'`, parses their `schedule` field (using `python-crontab`), and queues `evaluate_automation_rule` for rules matching the current time.
  [ ] Configure Celery Beat to run this scheduler task.
  [ ] Run scheduler tests; expect pass. Refactor.

  ### 3.5 Core Evaluation Task (`automation/tasks.py`)

  [ ] **(Test First)** Write Unit/Integration Tests for the `evaluate_automation_rule` Celery task. Mock `AutomationLog` creation/updates, condition evaluator (`evaluate_conditions`), action function execution. Test different scenarios: conditions met/not met, action success/failure, error handling, `AutomationLog` status updates and `action_logs` population.
  [ ] Implement the `evaluate_automation_rule` task in `automation/tasks.py` following the logic outlined in PRD section 3.3 (Log start -> Fetch -> Evaluate Conditions -> Log result -> Execute Actions sequentially -> Log action details/state -> Update final log status). Use try/except blocks extensively for robustness.
  [ ] Run task tests; expect pass. Refactor task logic.

  ### 3.6 Admin Registration (`automation/admin.py`)

  [ ] Create `automation/admin.py`.
  [ ] Define Inlines for `RuleCondition`, `RuleAction` on `AutomationRuleAdmin`.
  [ ] Define `AutomationRuleAdmin`, `AutomationLogAdmin`. Configure displays, filters, search, readonly fields. Use `list_editable` for `AutomationRule.is_active`. Provide good display for `AutomationLog` fields (`changes`, `context`, `action_logs`).
  [ ] Register models.
  [ ] **(Manual Test):** Verify Admin interface for creating/managing rules, conditions, actions. View logs.

  ### 3.7 Migrations

  [ ] Run `python manage.py makemigrations automation`.
  [ ] **Review generated migration file(s) carefully.** Check all models, FKs, JSONFields, indexes.
  [ ] Run `python manage.py migrate` locally.

  ### 3.8 API Implementation (Management & Logging)

  [ ] **(Test First - Rule Management API)** Write API tests (`tests/api/test_endpoints.py`) for CRUD operations on `/api/v1/automations/rules/` (and potentially nested conditions/actions, or handle them via nested serializers). Test creating complex rules with conditions and actions. Test permissions (admin/power user only). Test Org Scoping.
  [ ] Define serializers for `AutomationRule`, `RuleCondition`, `RuleAction`. Handle nested writes carefully (e.g., using `drf-writable-nested` or custom `create`/`update`). Implement `validate_custom_fields` if applicable to these models.
  [ ] Define `AutomationRuleViewSet` (ModelViewSet). Apply appropriate permissions. Inherit `OrganizationScopedViewSetMixin`.
  [ ] Define URL routing for rule management.
  [ ] Run rule management API tests; expect pass. Refactor.
  [ ] **(Test First - Log API)** Write API tests for `GET /api/v1/automations/logs/` and `GET /api/v1/automations/logs/{id}/`. Test filtering by rule, status, date, parent object. Test permissions. Verify `action_logs` detail is present.
  [ ] Define `AutomationLogSerializer` (read-only).
  [ ] Define `AutomationLogViewSet` (ReadOnlyModelViewSet). Implement filtering. Apply appropriate permissions. Inherit `OrganizationScopedViewSetMixin`.
  [ ] Define URL routing for log viewing.
  [ ] Run log API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`), ensuring tasks run (eagerly), signals fire, conditions evaluate, actions execute (mocked), logs are created, and APIs work.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=automation`). Review uncovered areas in condition/action logic and task execution.
[ ] Manually create a simple rule (e.g., update description on Product status change) via API/Admin. Trigger the event and verify the action occurs and the `AutomationLog` is correct. Test a scheduled rule.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs (Implement all required Actions, refine condition evaluator, add more complex logic if needed, robust error handling/retries in tasks).
[ ] Create Pull Request(s).
[ ] Update API documentation (especially available actions and parameters).
[ ] Implement archiving/purging for `AutomationLog`.
[ ] Consider UI for rule building if needed in future.

--- END OF FILE automation_implementation_steps.md ---