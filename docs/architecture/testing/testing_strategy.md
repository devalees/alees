# Testing Strategy (TDD with Pytest)

## 1. Overview

*   **Purpose**: To define the strategy, methodologies, tools, and scope for testing the ERP backend application, ensuring its correctness, reliability, performance, and security by primarily following a **Test-Driven Development (TDD)** approach.
*   **Scope**: Covers unit testing, integration testing, API testing, performance testing, and security testing practices throughout the development lifecycle, emphasizing writing tests before implementation code.
*   **Goal**: High test coverage driven by requirements, early defect detection and prevention, confidence in deployments, maintainable test suite, improved design through testability focus.
*   **Primary Framework**: **Pytest** (`pytest` and `pytest-django`).

## 2. Testing Philosophy & Principles

*   **Test-Driven Development (TDD) First**: Development will primarily follow the Red-Green-Refactor cycle:
    1.  **Red:** Write a failing test for a small piece of desired functionality based on requirements/specifications.
    2.  **Green:** Write the *minimum* amount of production code necessary to make the test pass.
    3.  **Refactor:** Improve the production code (and potentially the test code) for clarity, efficiency, and design quality, ensuring tests still pass.
*   **Test Pyramid**: TDD applies at all levels, but the focus remains on the test pyramid:
    *   **Unit Tests (Largest Base):** Most TDD cycles occur here. Write tests for small units (functions, methods) *before* implementing them.
    *   **Integration Tests (Middle Layer):** Write tests defining the expected interaction between components *before* fully implementing the interaction logic.
    *   **API / Acceptance Tests (Smaller Top):** Write high-level tests defining the expected API behavior or user story outcome *before* implementing the underlying feature across multiple components. These often drive the development of lower-level unit/integration tests.
*   **Test Early, Test Often**: Write tests *before* code. Run tests frequently locally during development and automatically in CI.
*   **Automation**: Automate test execution via Continuous Integration (CI).
*   **Clarity & Maintainability**: Tests act as executable specifications. They must be readable, well-named, and maintainable alongside the production code. Use clear assertions.
*   **Isolation**: Design tests (and code) for isolation using fixtures and mocking where appropriate.
*   **Coverage as an Outcome**: High test coverage is a *result* of practicing TDD thoroughly, not the primary goal itself. Focus on testing requirements and behavior.

## 3. Testing Framework & Tools

*   **Core Test Runner:** **Pytest** (`pytest`).
*   **Django Integration:** **`pytest-django`**.
*   **Test Data Generation:** **`factory-boy`**. Define factories early in the TDD cycle for models being tested.
*   **API Client (for API tests):** `pytest-django`'s `client` fixture or DRF's `APIClient`.
*   **Mocking:** Python's `unittest.mock` (via `pytest-mock`'s `mocker` fixture). Crucial for isolating units during TDD.
*   **Asynchronous Task Testing:** Celery testing utilities / `pytest-celery`. Write tests for task behavior *before* implementing the task body. Use `CELERY_TASK_ALWAYS_EAGER=True` for synchronous testing during most TDD cycles.
*   **Time Manipulation:** `freezegun`.
*   **Database Interaction:** `pytest-django` test database management. Use `pytest.mark.django_db(transaction=True)` where applicable.
*   **Coverage:** `pytest-cov`. Monitor coverage as development progresses.
*   **(Optional) Fuzzing:** `hypothesis` (can complement TDD by exploring edge cases).
*   **(Optional) Performance Testing:** `locust`, `pytest-benchmark` (Separate from primary TDD cycle).
*   **(Optional) Security Testing:** SAST (`bandit`), DAST (ZAP) (Often run separately or integrated into CI checks after code is written).

## 4. Types of Tests & TDD Workflow

### 4.1 Unit Tests
*   **TDD Cycle:**
    1.  Identify a small unit of behavior (e.g., a specific validation rule in a serializer, a calculation in a model method).
    2.  Write a test function (`test_...`) asserting the expected outcome or raised exception for that behavior. Run it; it should fail (Red).
    3.  Implement the minimal code in the model method, serializer validation, or utility function to make the test pass (Green). Use `mocker` to isolate from dependencies.
    4.  Refactor the implementation code and the test for clarity and quality. Rerun tests (Green).
*   **Scope:** Model methods, Serializer validation, Utility functions, Service logic, Condition/Action logic (Automation).

### 4.2 Integration Tests
*   **TDD Cycle:**
    1.  Identify an interaction between components (e.g., saving a model should trigger a signal handler that updates another model).
    2.  Write an integration test (using `@pytest.mark.django_db`) that sets up the initial state (using factories), performs the action (e.g., `model_instance.save()`), and asserts the expected outcome on the interacting components (e.g., the other model was updated correctly, a Celery task was queued). Run it; it should fail (Red).
    3.  Implement the interaction logic (e.g., the signal handler code, the Celery task call) needed to make the test pass (Green). Mock external systems if necessary.
    4.  Refactor the interaction code and test. Rerun tests (Green).
*   **Scope:** Database interactions, Service layer integration, Signal handlers, Celery task queuing/execution involving DB, Cache interaction/invalidation logic, Permission logic involving DB checks.

### 4.3 API / Acceptance Tests
*   **TDD Cycle (BDD Influence):**
    1.  Define the desired API behavior based on a user story or requirement (e.g., "As an admin, I should be able to POST to `/api/v1/products/` and get a 201 Created response with the new product data if the input is valid").
    2.  Write an API test using the `client` fixture that makes the request (e.g., `client.post('/api/v1/products/', data=...)`) and asserts the expected status code and response structure/content. Run it; it should fail (likely 404 or error) (Red).
    3.  Implement the minimal ViewSet, Serializer, URL routing, and underlying model logic required to make the API test pass (Green). This often involves driving out lower-level unit/integration tests via TDD along the way.
    4.  Refactor the API implementation (views, serializers, models) and the test. Rerun tests (Green).
*   **Scope:** CRUD operations via API, Authentication/Authorization flows via API, Filtering/Sorting/Pagination via API, Error handling/responses, High-level business workflows via API calls.

### 4.4 Performance & Security Tests
*   These are typically **not** part of the core TDD cycle but are applied *after* functionality is implemented and passes other tests, often in dedicated environments or CI stages. They validate non-functional requirements.

## 5. Test Execution & CI/CD

*   **Local Execution:** Developers run `pytest` frequently while implementing features following the Red-Green-Refactor cycle.
*   **Continuous Integration (CI):**
    *   CI pipeline runs the **full test suite** automatically on every push/merge request.
    *   Includes linting, static analysis (`bandit`).
    *   Generates coverage reports (`pytest --cov`). Coverage trends should be monitored.
    *   **Build fails if any tests fail.**
*   **Staging Environment:** Run relevant API/E2E tests against deployed staging environment.

## 6. Test Data Management

*   **Primary Tool:** **`factory-boy`**. Define factories alongside or before model implementation during TDD.
*   **Data Creation:** Create only the necessary data within each test function or fixture using factories.
*   **Avoid Static Fixtures:** Minimize use of `manage.py loaddata`.

## 7. Test Organization

*   Place tests in `tests/` directory within each relevant app (or the centralized `api/vX/tests/` if using that structure).
*   Use descriptive filenames and test function names reflecting the tested behavior.
*   Use Pytest markers (`@pytest.mark.django_db`, etc.).

## 8. Responsibilities

*   **Developers:** Primarily responsible for writing unit, integration, and often API/acceptance tests *before or alongside* implementation code, following the TDD workflow. Maintain tests as code evolves. Fix failing tests.
*   **QA Team (if applicable):** May contribute to API/E2E tests, exploratory testing, performance/security testing coordination.
*   **All:** Foster a culture where testing is integral to development, not an afterthought. Participate in test code reviews.

--- END OF FILE testing_strategy_tdd.md ---