
# Configuration Management Strategy

## 1. Overview

*   **Purpose**: To define the strategy for managing application configuration settings across different environments (development, testing, staging, production) in a consistent, secure, and maintainable manner.
*   **Scope**: Covers management of Django settings, environment variables, sensitive credentials (secrets), and feature flags.
*   **Goal**: Ensure that the application behaves correctly in each environment, secrets are handled securely, configuration is easy to manage and deploy, and environment differences are clearly defined.

## 2. Core Principles

*   **Environment Parity (Strive for):** Keep development, staging, and production environments as similar as possible regarding configuration structure and dependencies, varying only environment-specific values (like database URLs, debug flags, API keys).
*   **Configuration in Environment:** Store environment-specific configuration (especially secrets, hostnames, resource locators) in the **environment**, not in version-controlled code.
*   **Explicit Configuration:** Avoid relying on implicit defaults where explicit configuration based on the environment is safer or clearer.
*   **Security:** Treat all sensitive configuration values (passwords, API keys, `SECRET_KEY`) as secrets, managed via a secure mechanism.
*   **Consistency:** Use a consistent method for accessing configuration values within the application code.
*   **Immutability (Ideal):** Configuration ideally doesn't change frequently after deployment without a new code release or explicit configuration update process.

## 3. Configuration Layers & Tools

### 3.1. Django Settings Files (`config/settings/`)
*   **Structure:** Utilize the split settings pattern:
    *   `base.py`: Contains common settings applicable to all environments (e.g., `INSTALLED_APPS`, `MIDDLEWARE`, `TEMPLATES`, default `REST_FRAMEWORK` settings, `AUTH_USER_MODEL`, static/media URL bases). **Should not contain secrets.**
    *   `dev.py`: Imports `base.py` (`from .base import *`). Overrides settings for local development (e.g., `DEBUG = True`, `ALLOWED_HOSTS = ['*']`, `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`, potentially `FileSystemStorage`, `LocMemCache`, `CELERY_TASK_ALWAYS_EAGER = True`). Loads settings from `.env` file.
    *   `test.py`: Imports `base.py`. Overrides settings for automated testing (e.g., test database config, fast password hasher, `LocMemCache`, `CELERY_TASK_ALWAYS_EAGER = True`). Loads settings potentially from test-specific environment variables or defaults.
    *   `prod.py`: Imports `base.py`. Overrides settings for production (e.g., `DEBUG = False`, specific `ALLOWED_HOSTS`, production database URL, cache URL, Celery broker URL, production file storage, secure session/CSRF settings, production logging config). Loads settings strictly from environment variables or secrets manager.
*   **Loading:** The correct settings file is selected using the `DJANGO_SETTINGS_MODULE` environment variable (e.g., `config.settings.dev`, `config.settings.prod`).

### 3.2. Environment Variables & Secrets Management
*   **Primary Mechanism:** Environment variables are the primary method for injecting environment-specific configuration and secrets into the application via the settings files.
*   **Loading Tool (Recommended):** Use **`django-environ`**. This library simplifies reading environment variables and `.env` files, casting values to correct types (bool, int, list, dict, database URL, cache URL), and providing defaults.
    ```python
    # config/settings/base.py
    import environ
    import os
    from pathlib import Path

    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    env = environ.Env(
        # set casting, default value
        DEBUG=(bool, False)
    )

    # Read .env file for local dev if it exists
    environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

    # Example usage (replace direct os.environ.get)
    SECRET_KEY = env('DJANGO_SECRET_KEY', default='unsafe-default-key-only-for-initial-run')
    DEBUG = env('DEBUG') # Casts to bool based on 'True', 'true', '1' etc.
    DATABASE_URL = env.db('DATABASE_URL', default='postgres://user:pass@localhost/erp_dev_db')
    REDIS_URL = env.cache('REDIS_URL', default='redis://localhost:6379/1')
    ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

    DATABASES = {'default': DATABASE_URL}
    CACHES = {'default': REDIS_URL}
    # ... etc
    ```
*   **`.env` File:** Used *only* for local development. Contains environment variables (including secrets for local dev instances). **Must be added to `.gitignore`**. Provide a `.env.example` file in Git showing needed variables without values.
*   **Secrets Management (Staging/Production):** Environment variables containing secrets must be injected securely into the application environment using platform-specific methods:
    *   **Cloud Provider Secrets Managers:** (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault) - Recommended. Application/deployment process retrieves secrets at deploy time or runtime via IAM roles/identities.
    *   **Infrastructure-as-Code Tools:** (Terraform, CloudFormation) can provision secrets from managers.
    *   **Platform Secrets:** (Kubernetes Secrets, Docker Swarm Secrets).
    *   **Secure Environment Variables:** Injected directly by the deployment platform/CI-CD tool (less ideal for highly sensitive secrets but common). Ensure platform security.

### 3.3. Feature Flags (Optional)
*   **Purpose**: To enable/disable application features independently of code deployments.
*   **Implementation**:
    *   **Simple:** Use environment variables or Django settings (`MY_FEATURE_ENABLED = env.bool('MY_FEATURE_ENABLED', default=False)`). Check the setting in code (`if settings.MY_FEATURE_ENABLED:`).
    *   **Advanced:** Integrate a dedicated feature flag service/library (e.g., `django-flags`, LaunchDarkly, Flagsmith) for more complex rollout strategies (percentage rollouts, user targeting).

## 4. Configuration Variables (Examples)

List key configuration variables expected to differ across environments:

*   `DJANGO_SETTINGS_MODULE`
*   `DEBUG` (True/False)
*   `SECRET_KEY`
*   `ALLOWED_HOSTS`
*   `DATABASE_URL` (or individual DB components)
*   `REDIS_URL` (for Cache, Celery Broker, potentially Channels)
*   `CELERY_BROKER_URL` (often same as Redis URL but could differ)
*   `DEFAULT_FILE_STORAGE` backend setting
*   Cloud Storage Credentials (`AWS_...`, `GOOGLE_...`, `AZURE_...`) & Bucket Names
*   Search Engine Host(s) (`ELASTICSEARCH_HOSTS`)
*   External Service API Keys (Email, Tax, Video, etc.)
*   Sentry DSN (`SENTRY_DSN`)
*   CORS Allowed Origins (`CORS_ALLOWED_ORIGINS`)
*   CSRF Trusted Origins (`CSRF_TRUSTED_ORIGINS`)
*   `MEDIA_URL`, `MEDIA_ROOT` (for local dev/test file storage)
*   `STATIC_URL`, `STATIC_ROOT`

## 5. Process & Workflow

*   **Adding Config:** New environment-dependent settings are added to `settings/base.py` using `env(...)` with a sensible default (or raise an error if no default is safe).
*   **Local Dev:** Developers update their local `.env` file based on `.env.example`.
*   **CI/Testing:** CI environment variables provide necessary settings for `settings/test.py`.
*   **Staging/Production:** DevOps/Platform team configures environment variables or secrets manager injection during deployment according to `prod.py`/`staging.py` requirements.
*   **Documentation:** The `.env.example` file serves as documentation for required environment variables. `README.md` explains the settings structure and `.env` usage for local setup.

## 6. Security Considerations

*   **Secrets MUST NOT be committed to Git.** Use `.gitignore` for `.env`.
*   Use a secure method for managing and injecting secrets in staging/production.
*   Regularly rotate secrets where possible/required.
*   Limit access to production configuration and secrets.

## 7. Testing

*   `settings/test.py` overrides necessary settings for the test environment (DB, Cache, Celery, File Storage, fast password hasher, disabled external calls).
*   Tests should generally not depend on specific values from `.env` but use the defaults or overrides defined in `settings/test.py`. Mock external services.

## 8. Tooling

*   `django-environ` (Recommended for reading env vars / `.env` files).
*   Secrets Management tool (Cloud provider specific, Vault).
*   Version Control (Git) for settings code (not secrets) and `.env.example`.

--- END OF FILE configuration_management_strategy.md ---