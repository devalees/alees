# Project Structure & Technology Stack

## 1. Overview

This document outlines the chosen directory structure and the core technologies for the ERP system API Based. The structure aims for modularity within infrastructure components and groups application logic primarily under API versions, supporting a Test-Driven Development (TDD) approach.

## 2. Project Directory Structure

The project will follow this top-level structure:

```
erp_project/
├── api/                      # API root: Contains all API versions and related app logic
│   └── v1/                  # API Version 1
│       ├── base_models/     # Foundational model applications (internal grouping)
│       │   ├── __init__.py
│       │   ├── organization/ # Example: Organization and related models
│       │   │   ├── __init__.py
│       │   │   ├── models.py
│       │   │   ├── serializers.py
│       │   │   ├── views.py
│       │   │   ├── admin.py
│       │   │   └── tests/
│       │   │       ├── __init__.py
│       │   │       ├── factories.py      # Factory-Boy factories for Organization models
│       │   │       ├── unit/             # Unit tests (isolated logic)
│       │   │       │   ├── __init__.py
│       │   │       │   └── test_serializers.py # Example
│       │   │       ├── integration/      # Integration tests (component interactions, DB access)
│       │   │       │   ├── __init__.py
│       │   │       │   └── test_signals.py   # Example
│       │   │       └── api/              # API/E2E tests (HTTP requests/responses)
│       │   │           ├── __init__.py
│       │   │           └── test_endpoints.py # Example
│       │   │
│       │   ├── user/        # Example: UserProfile model (extending Django User)
│       │   │   ├── __init__.py
│       │   │   ├── models.py
│       │   │   ├── serializers.py
│       │   │   ├── views.py
│       │   │   ├── admin.py
│       │   │   └── tests/
│       │   │       ├── __init__.py
│       │   │       ├── factories.py      # Factory-Boy factories for User/Profile models
│       │   │       ├── unit/
│       │   │       │   └── # ... unit tests ...
│       │   │       ├── integration/
│       │   │       │   └── # ... integration tests ...
│       │   │       └── api/
│       │   │           └── # ... api tests ...
│       │   │
│       │   ├── common/        # Example: Shared base models like Address, Contact, Currency, etc.
│       │   │   ├── __init__.py
│       │   │   ├── models.py
│       │   │   ├── serializers.py
│       │   │   ├── views.py
│       │   │   ├── admin.py
│       │   │   └── tests/
│       │   │       ├── __init__.py
│       │   │       ├── factories.py      # Factory-Boy factories for common models
│       │   │       ├── unit/
│       │   │       │   └── # ... unit tests ...
│       │   │       ├── integration/
│       │   │       │   └── # ... integration tests ...
│       │   │       └── api/
│       │   │           └── # ... api tests ...
│       │   │
│       │   ├── urls.py      # URL routing specific to base_models endpoints
│       │   └── apps.py      # App configuration for base_models grouping
│       │
│       ├── features/        # Business feature model applications (internal grouping)
│       │   ├── __init__.py
│       │   ├── project/     # Example: Project feature
│       │   │   ├── __init__.py
│       │   │   ├── models.py
│       │   │   ├── serializers.py
│       │   │   ├── views.py
│       │   │   ├── admin.py
│       │   │   └── tests/
│       │   │       ├── __init__.py
│       │   │       ├── factories.py      # Factory-Boy factories for Project models
│       │   │       ├── unit/
│       │   │       │   └── # ... unit tests ...
│       │   │       ├── integration/
│       │   │       │   └── # ... integration tests ...
│       │   │       └── api/
│       │   │           └── # ... api tests ...
│       │   │
│       │   ├── accounting/  # Example: Accounting feature
│       │   │   ├── __init__.py
│       │   │   ├── models.py
│       │   │   ├── serializers.py
│       │   │   ├── views.py
│       │   │   ├── admin.py
│       │   │   └── tests/
│       │   │       ├── __init__.py
│       │   │       ├── factories.py      # Factory-Boy factories for Accounting models
│       │   │       ├── unit/
│       │   │       │   └── # ... unit tests ...
│       │   │       ├── integration/
│       │   │       │   └── # ... integration tests ...
│       │   │       └── api/
│       │   │           └── # ... api tests ...
│       │   │
│       │   ├── urls.py      # URL routing specific to features endpoints
│       │   └── apps.py      # App configuration for features grouping
│       │
│       ├── urls.py         # Root URL routing for v1 API (includes base_models.urls, features.urls)
│       └── apps.py         # App configuration for api.v1
│
├── core/                   # Core infrastructure configurations and utilities
│   ├── redis/             # Redis client/cache configuration logic
│   │   ├── __init__.py
│   │   └── config.py
│   ├── elasticsearch/     # Elasticsearch client configuration logic
│   │   ├── __init__.py
│   │   └── config.py
│   ├── celery_app/        # Celery configuration and app definition
│   │   ├── __init__.py
│   │   ├── app.py
│   │   └── config.py
│   ├── logging/           # Logging configuration setup
│   │   ├── __init__.py
│   │   └── config.py
│   ├── monitoring/        # Monitoring instrumentation setup
│   │   ├── __init__.py
│   │   └── config.py
│   └── utils/             # Shared, non-domain-specific utility functions/classes
│       ├── __init__.py
│       └── helpers.py
│
├── config/               # Project-level Django configuration
│   ├── __init__.py       # Ensures celery app is loaded
│   ├── settings/        # Django settings split by environment
│   │   ├── __init__.py
│   │   ├── base.py     # Base settings (INSTALLED_APPS, MIDDLEWARE, common configs)
│   │   ├── dev.py      # Development overrides
│   │   ├── test.py     # Testing overrides (e.g., CELERY_TASK_ALWAYS_EAGER=True)
│   │   └── prod.py     # Production overrides
│   ├── urls.py         # Main project URL configuration
│   ├── asgi.py         # ASGI entry point
│   └── wsgi.py         # WSGI entry point
│
├── requirements/        # Python dependencies split by environment
│   ├── base.txt
│   ├── dev.txt
│   ├── test.txt
│   └── prod.txt
│
├── scripts/            # Operational/utility scripts
│   ├── setup/
│   ├── deployment/
│   └── maintenance/
│
├── docs/              # Project documentation
│   ├── api/
│   ├── architecture/
│   └── deployment/
│
├── .env.example
├── .gitignore
├── docker-compose.yml # For local development environment setup
├── Dockerfile        # For building production container images
├── manage.py         # Django management script
└── README.md         # Project overview and setup instructions
```

**Explanation of Key Structure Choices (Testing Emphasis):**

*   **Co-located Tests:** Tests reside within the specific application/feature directory they relate to (e.g., `api/v1/base_models/organization/tests/`).
*   **Test Type Subdirectories:** Each `tests/` directory is further subdivided into `unit/`, `integration/`, and `api/` directories. This clearly separates tests based on their scope and purpose, aligning with the TDD strategy and test pyramid.
*   **`factories.py`:** A dedicated file within each `tests/` directory holds `factory-boy` factories for the models defined in that application/feature, making test data generation clear and reusable within that context.
*   **`api/v1/` as Primary Container:** Remains the main container for application logic related to the V1 API.
*   **Infrastructure & Config:** Remain separate in `core/` and `config/`.

## 3. Technology Stack

*(This section remains largely the same as the previous version, but explicitly lists testing tools)*

*   **Programming Language:** Python (Specify version, e.g., 3.10+)
*   **Web Framework:** Django (Specify version, e.g., 4.x)
*   **API Framework:** Django Rest Framework (DRF)
*   **Database:** PostgreSQL (Specify version, e.g., 14+)
*   **Asynchronous Task Queue:** Celery (with Celery Beat for scheduling)
*   **Message Broker (for Celery):** Redis (Specify version)
*   **Caching Backend:** Redis (using `django-redis`)
*   **Real-time (Chat/Notifications):** Django Channels (requires ASGI server like Daphne or Uvicorn)
*   **Search Engine:** Elasticsearch or OpenSearch (Specify version)
*   **Hierarchy Management:** `django-mptt`
*   **Tagging:** `django-taggit`
*   **Import/Export:** `django-import-export`
*   **PDF Generation (for Export):** TBD (e.g., ReportLab, WeasyPrint)
*   **Testing Framework:** **Pytest**
*   **Django Test Integration:** **`pytest-django`**
*   **Test Data Generation:** **`factory-boy`**
*   **Mocking:** **`pytest-mock`** (using `unittest.mock`)
*   **Test Coverage:** **`pytest-cov`**
*   **Async Task Testing:** Celery testing utilities, **`pytest-celery`** (optional)
*   **Time Manipulation:** **`freezegun`** (optional)
*   **Containerization:** Docker, Docker Compose
*   **Environment Variables:** `python-dotenv`, OS Environment Variables, `django-environ` (optional)
*   **Authentication (API):** **JWT** (via `djangorestframework-simplejwt`) and **API Keys** (via `djangorestframework-api-key` or `django-api-key` - *specify chosen library*).
*   **Monitoring Stack (External):** TBD (e.g., Prometheus/Grafana/Loki, Datadog, Sentry). Instrumentation: `django-prometheus`, Sentry SDK.
*   **CI/CD:** TBD (e.g., GitHub Actions, GitLab CI, Jenkins).

## 4. Key Principles

*   **API First:** Design through the versioned REST API.
*   **TDD:** Follow Test-Driven Development (Red-Green-Refactor). Write tests before/alongside code.
*   **Asynchronous Operations:** Offload tasks to Celery.
*   **Configuration over Code:** Use settings/environment variables.
*   **Testing:** Comprehensive, automated testing across unit, integration, and API levels.
*   **Security:** Apply best practices.
*   **Modularity:** Group related code within feature directories under `api/v1/`. Separate infrastructure in `core/`.
