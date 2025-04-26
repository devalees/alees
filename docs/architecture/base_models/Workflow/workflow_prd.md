# Workflow/State Machine Integration - Product Requirements Document (PRD) - Simplified

## 1. Overview

*   **Purpose**: To define the requirements for integrating a state machine or workflow capability into the ERP system, enabling controlled transitions between defined `Status` values for specific business models (e.g., Invoice, Order, Product).
*   **Scope**: Integration of a workflow library (e.g., `django-fsm`), defining state transitions and associated logic for key business models, exposing transition triggers via API, and integrating with status/audit systems. Excludes building a workflow engine from scratch or a visual workflow designer.
*   **Implementation Strategy**: Leverage a suitable Django state machine library (Assumption: **`django-fsm`**). Workflow logic (states, transitions, conditions, actions) will be defined primarily in Python code associated with the target models.
*   **Target Users**: Developers (implementing workflows on models), Business Analysts (defining workflow rules), End Users (interacting with models whose status changes via workflow).

## 2. Business Requirements

*   **Controlled Processes**: Ensure business entities (like Invoices, Orders) move through predefined lifecycle states in a controlled manner (e.g., cannot go directly from 'Draft' to 'Paid').
*   **Process Automation**: Trigger specific actions automatically when an entity transitions between states (e.g., send notification on 'Approved', update inventory on 'Shipped').
*   **Enforce Business Rules**: Allow transitions only when specific conditions are met or required permissions are held.
*   **Visibility**: Provide clear indication of the current status of an entity and potentially the allowed next steps.

## 3. Functional Requirements

### 3.1 State Field Integration
*   **Target Models**: Identify key business models requiring workflow management (e.g., `Invoice`, `PurchaseOrder`, `Product`, `UserRequest`).
*   **Status Field**: These target models must have a `status` field (likely `CharField`) to store the current state. This field will be managed by the workflow library. (Leverages the `Status` model/system for defined values).
*   **Library Integration**: Utilize `@fsm.transition` decorator (or equivalent) from the chosen library (`django-fsm`) on model methods to define allowed transitions.

### 3.2 Transition Definition (in Code)
*   For each target model, define methods decorated with `@fsm.transition`:
    *   **`field`**: Specifies the state field being managed (e.g., `field=status`).
    *   **`source`**: The state(s) the transition is allowed *from* (e.g., `source='draft'`). Can be a list or `*` (any state).
    *   **`target`**: The state the transition moves *to* (e.g., `target='pending_approval'`).
    *   **`conditions` (Optional)**: List of helper functions/methods that must return `True` for the transition to be allowed (e.g., `conditions=[is_total_amount_valid]`).
    *   **`permission` (Optional)**: Function or permission string (`app.codename`) required by the user to execute the transition (e.g., `permission='invoices.can_approve_invoice'`). Integrates with RBAC system.
    *   **Transition Method Body**: Contains the core logic to execute *during* the transition (before the status field is updated). Can perform checks or initial actions.
    *   **Side Effects (`on_error`, Library Signals)**: Implement logic that runs *after* a successful transition (e.g., sending notifications, updating related objects) or if a transition fails. Often done via library-provided signals or hooks.

### 3.3 Triggering Transitions via API
*   **Requirement**: Need API endpoints to trigger allowed state transitions for specific object instances.
*   **Implementation**:
    *   Use DRF's `@action` decorator on the ViewSet for the target model.
    *   Define an action for each logical transition (e.g., `POST /api/v1/invoices/{id}/submit/`, `POST /api/v1/invoices/{id}/approve/`).
    *   The action view will:
        1. Retrieve the object instance.
        2. Check **model-level** permissions for the *action* itself (using standard DRF permissions).
        3. Call the corresponding transition method on the model instance (e.g., `invoice.submit(user=request.user)`). The `@fsm.transition` decorator handles the permission/condition checks defined on the transition.
        4. Handle potential `TransitionNotAllowed` exceptions from the library, returning appropriate API errors (e.g., 400 Bad Request or 403 Forbidden).
        5. Return a success response, potentially with the updated object including the new status.

### 3.4 Status Information API
*   The standard GET endpoint for the target model (`/api/v1/invoices/{id}/`) should return the current `status`.
*   *(Optional)* Consider an API action (`/api/v1/invoices/{id}/available-transitions/`) that inspects the object's current state and uses library helpers (like `get_available_user_transitions`) to return a list of transitions the *current user* is permitted to trigger. Useful for driving UI buttons.

### 3.5 Audit Logging Integration
*   **Requirement**: Log successful state transitions.
*   **Implementation**: Implement a signal receiver (e.g., for `django-fsm`'s `post_transition` signal) that creates an `AuditLog` entry recording the user, object, `from_state`, `to_state`, and timestamp.

### 3.6 Out of Scope
*   Building a visual workflow designer/editor.
*   Database storage of workflow *definitions* (definitions primarily live in Python code with `django-fsm`). More complex libraries like `django-viewflow` might store definitions differently.
*   Complex BPMN features (gateways, timers, etc.) unless supported by the chosen library and explicitly required.

## 4. Technical Requirements

### 4.1 Library Integration
*   Install and configure the chosen workflow library (e.g., `pip install django-fsm`).
*   Follow library documentation for model integration (`FSMField` or decorators) and signal handling.

### 4.2 Performance
*   Transition logic (conditions, actions, side effects) should be reasonably efficient.
*   Permission checks within transitions should leverage the cached RBAC system.
*   Fetching available transitions should be performant.

### 4.3 Security
*   Transition methods must reliably check permissions using the integrated RBAC system.
*   Ensure API actions triggering transitions are properly protected.
*   Audit logging of transitions is essential.

### 4.4 Data Consistency
*   State transitions should ideally occur within database transactions if they involve multiple model updates as side effects. `django-fsm` typically updates the state field within the transition method's transaction.

## 5. Non-Functional Requirements

*   **Reliability**: State transitions should execute reliably and consistently.
*   **Maintainability**: Workflow definitions (transitions, conditions, actions in code) should be clear and maintainable.
*   **Testability**: Workflows must be easily testable.

## 6. Success Metrics

*   Successful enforcement of defined state transition rules.
*   Successful execution of automated actions triggered by transitions.
*   Correct logging of status changes in the Audit Log.
*   Developer/Admin satisfaction with defining and managing workflows for models.

## 7. API Documentation Requirements

*   Document the `status` field on relevant models and its possible values.
*   Document the specific API `@action` endpoints used to trigger transitions (e.g., `POST /submit/`, `POST /approve/`).
*   Specify required permissions for each transition endpoint.
*   Document the optional `/available-transitions/` endpoint if implemented.
*   Document error responses related to forbidden or invalid transitions.

## 8. Testing Requirements

*   **Unit Tests**:
    *   Test individual transition methods on models: mock conditions/permissions, verify state changes, check for `TransitionNotAllowed` exceptions when conditions/permissions fail.
    *   Test condition functions.
    *   Test side-effect/action logic.
*   **Integration Tests / API Tests**:
    *   Test calling the API transition actions (`POST /submit/`, etc.) with users having correct/incorrect permissions. Verify state changes and appropriate HTTP responses (2xx, 400, 403).
    *   Test sequences of transitions.
    *   Test that transitions fail if prerequisite conditions are not met.
    *   Verify Audit Log entries are created for successful transitions.
    *   Test the `/available-transitions/` endpoint if implemented.

## 9. Deployment Requirements

*   Ensure chosen workflow library is installed in all environments.
*   Migrations for any changes to models (e.g., adding the `status` field).
*   Ensure initial states for existing data are set correctly if applying workflows retrospectively.

## 10. Maintenance Requirements

*   Update workflow definitions (code) as business processes evolve.
*   Keep the workflow library updated.
*   Monitor Audit Logs related to transitions.

---