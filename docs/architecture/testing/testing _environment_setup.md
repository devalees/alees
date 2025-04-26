# Testing Environment Setup & Configuration (Using Pytest with PostgreSQL)

## 1. Overview

*   **Purpose**: To define the specific setup, configuration, and dependencies required to enable the project's Testing Strategy (TDD with Pytest) for unit, integration, and API testing, utilizing **PostgreSQL** as the test database backend.
*   **Scope**: Covers required libraries, Pytest configuration, Django test settings for PostgreSQL, test data setup (Factory-Boy), fixture conventions, and basic CI integration steps related to testing.
*   **Goal**: Ensure a consistent, reliable, efficient, and production-parity testing environment for all developers and the CI/CD pipeline, particularly given the reliance on PostgreSQL-specific features like native `JSONField` support.

## 2. Core Testing Stack

*   **Test Runner:** Pytest (`pytest`)
*   **Django Integration:** `pytest-django`
*   **Test Data:** `factory-boy`
*   **Mocking:** `pytest-mock` (using `unittest.mock`)
*   **Coverage:** `pytest-cov`
*   **(Optional but Recommended):** `freezegun` (for time-sensitive tests), `pytest-celery` (for advanced Celery testing).
*   **(Optional):** `fakeredis` (if testing specific Redis interactions), `moto[s3]` (if mocking AWS S3).

## 3. Dependency Management (`requirements/`)

1.  **Create `requirements/test.txt`:** Lists dependencies needed only for running tests.
2.  **Add Core Test Dependencies:** Include the following in `requirements/test.txt`:
    ```txt
    # Database driver (needed if not in base.txt)
    psycopg2-binary>=2.9,<3.0 # Or psycopg >= 3.0

    # Base testing framework
    pytest>=7.0,<8.0
    pytest-django>=4.5,<4.6
    pytest-cov>=4.0,<5.0
    pytest-mock>=3.10,<3.11

    # Test data generation
    factory-boy>=3.2,<3.3

    # Optional (Add if explicitly needed)
    # freezegun>=1.2,<1.3
    # pytest-celery>=0.0,<0.1
    # fakeredis>=2.0,<3.0
    # moto[s3]>=4.0,<5.0
    ```
3.  **Include in Other Files:** `requirements/dev.txt` should include `-r base.txt` and `-r test.txt`. CI pipeline installs `base.txt` and `test.txt`.
4.  **Installation:** Use `pip install -r requirements/test.txt` (or `dev.txt`). Ensure PostgreSQL development headers are installed on the system if using `psycopg2` (non-binary) or `psycopg`.

## 4. Pytest Configuration (`pytest.ini` or `pyproject.toml`)

Create `pytest.ini` (or use `[tool.pytest.ini_options]` in `pyproject.toml`):

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = tests.py test_*.py *_tests.py
# Example: Configure pytest-cov options
# addopts = --cov=. --cov-report=term-missing --cov-report=xml --cov-fail-under=80
# Optional: Register custom markers
# markers =
#     slow: marks tests as slow
#     integration: marks integration tests
#     api: marks API tests
```

*   **`DJANGO_SETTINGS_MODULE`**: Points to the test-specific settings file.
*   **`addopts`**: Consider adding coverage options here for consistency.

## 5. Django Test Settings (`config/settings/test.py`)

This file configures Django specifically for the test environment using PostgreSQL.

```python
# config/settings/test.py
from .base import * # Inherit base settings
import os # For environment variables

# === General Test Settings ===
DEBUG = False
SECRET_KEY = env('DJANGO_SECRET_KEY', default='test_secret_key_unsafe_123')
TESTING = True

# === Database ===
# Configure to use PostgreSQL for tests
# Ensure separate test database credentials/name are set in environment variables
# (e.g., DATABASE_URL_TEST)
DATABASES = {
    'default': env.db('DATABASE_URL_TEST', default='postgres://test_user:test_pass@localhost:5432/erp_test_db'),
}
# Tell Django's test runner the name to use when creating/destroying the DB
# This assumes the user specified in DATABASE_URL_TEST has CREATEDB permissions
# If not, the test DB must be created manually beforehand.
DATABASES['default']['TEST'] = {'NAME': DATABASES['default']['NAME']}

# === Password Hashers ===
# Use fast hasher for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# === Email ===
# Use memory backend for tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# === Caching ===
# Use in-memory cache for most tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'erp-test-cache-default',
    },
    'permissions': {
         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
         'LOCATION': 'erp-test-cache-permissions',
    },
    # Define other aliases from base.py with LocMemCache
}
# Ensure DJANGO_REDIS_CACHE_ALIAS points to a valid alias if base.py uses it
DJANGO_REDIS_CACHE_ALIAS = 'default'

# === File Storage ===
# Use temporary filesystem storage for tests
# pytest-django usually handles creating a temporary directory
MEDIA_ROOT = None # Let pytest-django handle temp dir creation for media
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
# Ensure AWS/Cloud storage settings are effectively disabled or mocked


# === Celery ===
# Run tasks synchronously and raise errors immediately
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True


# === Logging ===
# Configure simplified logging for test output
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(levelname)-8s %(name)-15s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        # Example: Reduce noise from noisy libraries during tests
        'factory': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'django.db.backends': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        # Configure other loggers as needed
        '': { # Root logger
            'handlers': ['console'],
            'level': 'INFO', # Default level for test run output
        },
    }
}

# === Third-Party Services ===
# Ensure external service integrations are disabled or use mock values/endpoints
# ELASTICSEARCH_HOSTS = None
# SENTRY_DSN = None
# AWS_ACCESS_KEY_ID = 'testing' # Provided by moto if used
# AWS_SECRET_ACCESS_KEY = 'testing' # Provided by moto if used
# etc.

```

*   **Test Database User:** The PostgreSQL user specified in `DATABASE_URL_TEST` needs `CREATEDB` privileges for `pytest-django` to automatically manage the test database lifecycle. If this isn't possible (e.g., in restrictive CI environments), the test database needs to be created manually beforehand, and the user only needs standard connect/read/write permissions on *that specific* database.
*   **Environment Variables:** Emphasize setting `DATABASE_URL_TEST` (and other `_TEST` variables if needed) in the test environment (`.env` for local, CI variables).

## 6. Factory-Boy Setup (`tests/factories.py`)

*   Follow conventions defined in the project structure document (e.g., `api/v1/app_name/tests/factories.py`).
*   Define factories inheriting `factory.django.DjangoModelFactory`. Use sequences, fuzzy data, SubFactories.

## 7. Fixture Setup (`conftest.py`)

*   Define reusable Pytest fixtures in `conftest.py` files (project root or app `tests/`).
*   **Standard Fixtures:** `api_client`, `user`, `admin_user`, `authenticated_client`, `admin_client` (as shown previously). Authenticated clients should use `client.force_authenticate` or JWT/API Key setup as appropriate for the test type.
*   Define fixtures for common setup data needed across multiple tests (e.g., `default_organization_type`, `default_currency`).

## 8. Running Tests

*   Commands remain the same: `pytest`, `pytest path/to/test`, `pytest --cov`, etc.
*   **Database Requirement:** A PostgreSQL server must be running and accessible with the connection details specified in the test environment variables (`DATABASE_URL_TEST`). `pytest-django` will connect to it to create/destroy the test database.

## 9. CI Configuration

*   The CI pipeline must:
    *   Install dependencies (including `psycopg2-binary` or `psycopg`).
    *   **Provide a PostgreSQL service** (e.g., using Docker `services:` in GitHub Actions/GitLab CI, or a dedicated test database instance).
    *   **Set the `DATABASE_URL_TEST` environment variable** (and others like Redis URL if needed for specific integration tests) for the test execution step.
    *   Execute tests using `pytest`.
    *   Execute linters/static analysis.
    *   Optionally upload coverage reports.

This setup ensures tests run against PostgreSQL, providing better parity with production and enabling reliable testing of features dependent on `JSONField` and other PostgreSQL-specific behavior.