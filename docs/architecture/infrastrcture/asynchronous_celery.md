## 3. Celery Basic Setup Strategy

**(Equivalent to a focused PRD for integrating Celery)**

### 3.1. Overview

*   **Purpose**: To establish the foundational setup for using Celery within the Django project for asynchronous task execution and scheduling.
*   **Scope**: Definition of the Celery application instance, basic configuration settings, integration with Django, and conventions for defining tasks. Excludes specific task implementations.
*   **Chosen Technology**: **Celery** (Target Version: 5.x), **Redis** as the Message Broker.

### 3.2. Core Requirements

*   **Enable Asynchronous Execution**: Provide the framework to define and queue tasks that run independently of the web request cycle.
*   **Django Integration**: Ensure Celery tasks have access to the Django application context (settings, ORM).
*   **Scalability Foundation**: Allow task processing to be scaled independently by running worker processes.
*   **Scheduling Foundation**: Integrate `Celery Beat` for periodic task execution.

### 3.3. Configuration Strategy (`config/settings/`, `core/celery_app/`)

*   **Celery App Instance:** Define the Celery app instance in `core/celery_app/app.py` following standard practices (loading Django settings).
*   **Project Initialization:** Ensure the Celery app instance is loaded when Django starts (e.g., import in `config/__init__.py`).
*   **Settings (`settings/base.py` and environment specifics):**
    *   `CELERY_BROKER_URL`: Load Redis connection URL from environment variables.
    *   `CELERY_RESULT_BACKEND`: Configure if task results need to be stored (often Redis as well, load URL from env vars).
    *   `CELERY_ACCEPT_CONTENT`: Define accepted serializers (e.g., `['json']`).
    *   `CELERY_TASK_SERIALIZER`: Set to `json`.
    *   `CELERY_RESULT_SERIALIZER`: Set to `json`.
    *   `CELERY_TIMEZONE`: Set to `settings.TIME_ZONE`.
    *   `CELERY_BEAT_SCHEDULER`: Set to `django_celery_beat.schedulers:DatabaseScheduler` if using database-backed schedules (requires installing `django-celery-beat`).
*   **Task Autodiscovery:** Celery should be configured to automatically discover tasks defined in `tasks.py` files within installed apps (standard Celery practice).

### 3.4. Local Development Setup (`docker-compose.yml`)

*   Relies on the Redis service defined in `docker-compose.yml`.
*   Developers typically run worker(s) and beat (if needed) manually in separate terminals:
    *   `celery -A config.celery_app worker -l INFO`
    *   `celery -A config.celery_app beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler` (if using DB scheduler)
*   Alternatively, worker/beat services can be added to `docker-compose.yml`.
*   Recommend setting `CELERY_TASK_ALWAYS_EAGER = True` in `settings/dev.py` for simplified debugging during initial feature development (tasks run synchronously).

### 3.5. Integration Points

*   **Task Definition:** Tasks are Python functions decorated with `@shared_task` (defined typically in `app_name/tasks.py`).
*   **Task Queuing:** Application code queues tasks using `my_task.delay(...)` or `my_task.apply_async(...)`.
*   **Scheduling:** Via `CELERY_BEAT_SCHEDULE` setting, `django-celery-beat` admin/models, or triggered by the Automation Engine.
*   **Dependencies:** Requires Redis (broker), Django settings.

### 3.6. Security Considerations

*   Secure the connection to the message broker (Redis password).
*   Be mindful of data passed to tasks (serialization security).
*   Tasks running potentially sensitive operations should perform their own permission checks if not inherently safe.

### 3.7. Monitoring Considerations

*   Monitor Celery worker health and availability.
*   Monitor message queue lengths (using Redis monitoring or Celery tools like Flower).
*   Monitor Celery Beat service health.
*   Track task success/failure rates (using Flower, Sentry integration, or custom logging).

### 3.8. Backup & Recovery Strategy

*   Celery setup itself is code/configuration. Broker persistence/backups covered by Redis strategy. Task *state* is generally ephemeral or stored in the result backend (if used).

### 3.9. Testing Considerations

*   Set **`CELERY_TASK_ALWAYS_EAGER = True`** and **`CELERY_TASK_EAGER_PROPAGATES = True`** in `settings/test.py` to run tasks synchronously and raise exceptions within the test process.
*   Test that the correct tasks are queued with the correct arguments.
*   Unit/Integration test the logic *within* the task functions themselves.
*   Use `pytest-celery` plugin for more advanced testing scenarios if needed.

### 3.10. Deployment Considerations

*   Deploy Celery worker processes alongside the main application (using Supervisor, systemd, Kubernetes Deployments, etc.). Ensure they have the latest application code.
*   Deploy the Celery Beat service (usually a single instance) if scheduled tasks are used.
*   Configure workers/beat to connect to the correct broker URL for the environment.
*   Configure number of worker processes/concurrency based on expected load.

---