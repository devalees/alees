# Core Strategy

## Table of Contents

1. [Configuration Management](#configuration-management)
2. [Security Strategy](#security-strategy)
3. [Secrets Management](#secrets-management)
4. [Development Setup](#development-setup)
5. [Localization Strategy](#localization-strategy)
6. [Validation Strategy](#validation-strategy)
7. [Monitoring Strategy](#monitoring-strategy)
8. [Deployment & CI/CD](#deployment--cicd)
9. [Feature Flags](#feature-flags)

---

## Configuration Management


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
*   **Add CORS/CSRF:** Explicitly list `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` as examples of environment-dependent configuration.

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
## Security Strategy

# Security Strategy

## 1. Overview

*   **Purpose**: To define the overall strategy, principles, and key practices for ensuring the security of the ERP system, protecting data confidentiality, integrity, and availability.
*   **Scope**: Covers secure development practices, dependency management, authentication/authorization reinforcement, secrets management, infrastructure security considerations, data encryption, logging, and incident response planning.
*   **Goal**: Minimize security vulnerabilities, protect sensitive data, comply with relevant regulations, and build trust with users by embedding security throughout the development lifecycle (DevSecOps principles).

## 2. Core Security Principles

*   **Defense in Depth**: Implement multiple layers of security controls, assuming no single layer is foolproof.
*   **Principle of Least Privilege**: Grant users, API keys, and system components only the minimum permissions necessary to perform their intended functions (enforced via RBAC).
*   **Secure Defaults**: Configure components and features with secure settings by default.
*   **Input Validation**: Treat all external input (API requests, user data, file uploads) as potentially malicious. Validate and sanitize input rigorously at application boundaries.
*   **Secure Coding Practices**: Follow established guidelines to avoid common web application vulnerabilities.
*   **Regular Updates & Patching**: Keep all software components (OS, database, libraries, frameworks) up-to-date with security patches.
*   **Logging & Monitoring**: Log security-relevant events and monitor for suspicious activity.
*   **Assume Breach**: Design systems with the assumption that breaches might occur and implement measures for detection, response, and recovery.

## 3. Secure Development Lifecycle (SDL)

*   **Threat Modeling (Periodic):** Identify potential threats and vulnerabilities early in the design phase for critical features or major architectural changes.
*   **Secure Coding Training:** Provide developers with training on common web vulnerabilities (OWASP Top 10) and secure coding practices specific to Python/Django.
*   **Code Reviews:** Include security checks as part of the mandatory code review process before merging code. Look for common vulnerabilities, insecure use of APIs, improper handling of sensitive data.
*   **Static Analysis (SAST):** Integrate automated SAST tools (e.g., **Bandit**, potentially linters configured for security rules) into the CI pipeline to scan code for potential security flaws on every commit/build.
*   **Dependency Scanning:** Integrate tools (e.g., **`pip-audit`**, **Snyk**, **GitHub Dependabot alerts**) into the CI pipeline and periodically scan project dependencies (`requirements/*.txt`) for known vulnerabilities (CVEs). Establish a process for patching vulnerable dependencies promptly.
*   **Dynamic Analysis (DAST):** Periodically run automated DAST tools (e.g., **OWASP ZAP**) against deployed staging environments to identify runtime vulnerabilities.
*   **Penetration Testing (Periodic):** Conduct periodic manual penetration tests (internal or external third-party) against staging or production environments, especially before major releases or significant changes.

## 4. Authentication & Authorization (Reinforcement)

*   **Authentication:** Implement strong authentication as defined in the `api_strategy.md` (JWT with secure refresh token handling, secure API Key management with expiry). Enforce strong password policies. Implement rate limiting on login attempts to prevent brute-forcing. Consider Multi-Factor Authentication (MFA/2FA) integration (e.g., via `django-otp`) for privileged users or as a user option.
*   **Authorization (RBAC):** Strictly enforce model-level and field-level permissions defined in the `rbac_prd.md` at API boundaries (Views and Serializers). Regularly audit role definitions and user assignments. Ensure API Keys have minimal necessary permissions.
*   **Session Management (if using JWT Refresh Tokens):** Securely manage refresh tokens (e.g., httpOnly cookies if applicable, short expiry for access tokens, mechanism for revocation).

## 5. Secrets Management

*   **Definition**: Secrets include database passwords, external API keys (cloud storage, email service, tax provider, video provider, etc.), Django `SECRET_KEY`, JWT signing keys, TLS certificates.
*   **Storage:**
    *   **NEVER** commit secrets directly into the Git repository.
    *   **Local Development:** Use environment variables loaded from a `.env` file (add `.env` to `.gitignore`).
    *   **Staging/Production:** Use a dedicated secrets management solution:
        *   Cloud Provider Secrets Managers (e.g., AWS Secrets Manager, GCP Secret Manager, Azure Key Vault).
        *   HashiCorp Vault.
        *   Platform-level secrets (e.g., Kubernetes Secrets).
        *   Securely injected Environment Variables (last resort, ensure platform security).
*   **Access:** Application instances retrieve secrets at runtime from the chosen manager using appropriate IAM roles or authentication tokens. Minimize human access to production secrets.
*   **Rotation:** Establish a policy for regularly rotating critical secrets (e.g., database passwords, API keys).

## 6. Data Security

*   **Encryption in Transit:** Use **HTTPS (TLS/SSL)** for all API communication. Configure web server (Nginx/Apache) or load balancer accordingly. Use TLS for connections to external services (Database, Redis, etc.) where possible/necessary.
*   **Encryption at Rest:**
    *   **Database:** Leverage database-level encryption features provided by the cloud provider (e.g., RDS encryption) or filesystem encryption on the database server.
    *   **File Storage:** Use server-side encryption features provided by the cloud storage provider (e.g., S3 SSE-S3, SSE-KMS).
    *   **Specific Fields:** For highly sensitive data within the database (e.g., certain custom fields), consider application-level encryption using libraries like `django-cryptography` (requires careful key management).
*   **Input Validation:** Rigorously validate and sanitize **all** user/API input (query parameters, path parameters, request bodies) using DRF serializers and validators (as per `validation_strategy.md`) to prevent injection attacks (XSS, SQLi - ORM helps but validate formats/types).
*   **File Uploads:** Validate file types and sizes. Consider virus scanning upon upload (async task). Serve user-uploaded files securely (avoid direct execution, use appropriate `Content-Type`, `Content-Disposition`, rely on pre-signed URLs or application-brokered access).
*   **CSRF Protection:** Ensure Django's CSRF middleware (`django.middleware.csrf.CsrfViewMiddleware`) is enabled and configured correctly, especially if session-based authentication or traditional forms are ever used alongside the API. Configure `CSRF_TRUSTED_ORIGINS` appropriately for frontend domains.
*   **CORS Policy:** Implement a secure Cross-Origin Resource Sharing (CORS) policy using `django-cors-headers` or similar. Configure `CORS_ALLOWED_ORIGINS` (or more specific settings) restrictively to only allow trusted frontend domains to interact with the API.

## 7. Infrastructure Security (Collaboration with DevOps/Platform Team)

*   **Network Security:** Implement firewalls and cloud security groups/network policies to restrict network access to servers (App, DB, Cache, Search) only from necessary sources.
*   **Operating System Hardening:** Keep OS patched. Minimize installed software. Use security best practices for server configuration.
*   **Container Security:** Use minimal base images, scan images for vulnerabilities, run containers as non-root users.
*   **Access Control:** Limit SSH/direct server access. Use bastion hosts if necessary. Implement strong authentication and authorization for infrastructure access.

## 8. Logging & Monitoring (Security Focus)

*   **Audit Logging:** Ensure the `Audit Logging System` captures security-relevant events: logins (success/failure), logouts, permission/role changes, API key creation/revocation, significant data deletions, security setting changes.
*   **Access Logs:** Log all API requests (including source IP, user agent, authenticated user/key) at the web server or load balancer level.
*   **Monitoring Platform Integration:** Forward security-relevant logs (Audit Log, web server access logs, application error logs with potentially sensitive info filtered) to the centralized monitoring/SIEM platform.
*   **Alerting:** Configure alerts in the monitoring platform for suspicious activities: high rate of failed logins, permission escalation attempts, errors from security components, critical vulnerabilities detected by scanners, potential credential leaks found in logs.

## 9. Incident Response (Planning)

*   **Plan:** Develop a basic incident response plan outlining steps to take in case of a suspected security breach:
    *   Identification (detecting the incident).
    *   Containment (isolating affected systems).
    *   Eradication (removing the threat).
    *   Recovery (restoring systems from backup, patching vulnerabilities).
    *   Post-Mortem (learning from the incident).
*   **Contacts:** Maintain contact information for security response personnel.

## 10. Compliance

*   Identify relevant data protection regulations (e.g., GDPR, CCPA, industry-specific rules) based on user base and data processed.
*   Ensure application design and data handling practices align with compliance requirements (e.g., data minimization, user consent, data subject access requests).

--- END OF FILE security_strategy.md (Updated) ---
## Secrets Management

# Secrets Management Process

## Overview

This document outlines the secrets management strategy for the Alees ERP system, using AWS Secrets Manager as the primary secrets storage solution.

## AWS Secrets Manager Integration

### Configuration

1. **AWS Credentials**
   - Set up AWS IAM user with appropriate permissions for Secrets Manager
   - Configure AWS credentials in environment variables:
     ```
     AWS_ACCESS_KEY_ID=your-access-key
     AWS_SECRET_ACCESS_KEY=your-secret-key
     AWS_REGION=your-region
     AWS_SECRETS_PREFIX=alees/
     ```

2. **Secret Naming Convention**
   - All secrets are prefixed with `alees/`
   - Format: `alees/{environment}/{service}/{secret-name}`
   - Example: `alees/prod/database/credentials`

### Secret Types

1. **Database Credentials**
   - Secret name: `database/credentials`
   - Contains: `username`, `password`, `host`, `port`, `dbname`

2. **API Keys**
   - Secret name: `api/{service-name}/key`
   - Contains: `api_key`, `api_secret`

3. **JWT Secrets**
   - Secret name: `jwt/credentials`
   - Contains: `secret_key`, `algorithm`

4. **Email Credentials**
   - Secret name: `email/credentials`
   - Contains: `host`, `port`, `username`, `password`

## Secret Rotation Process

### Automatic Rotation

1. **Database Credentials**
   - Rotate every 30 days
   - Process:
     1. Generate new credentials
     2. Update database user
     3. Update secret in AWS
     4. Update application configuration
     5. Verify connection with new credentials

2. **API Keys**
   - Rotate every 90 days
   - Process:
     1. Generate new key pair
     2. Update secret in AWS
     3. Update application configuration
     4. Verify API access

3. **JWT Secrets**
   - Rotate every 30 days
   - Process:
     1. Generate new secret
     2. Update secret in AWS
     3. Update application configuration
     4. Verify token generation

### Manual Rotation

1. **Emergency Rotation**
   - Triggered by security incidents
   - Process:
     1. Generate new credentials
     2. Update secret in AWS
     3. Update application configuration
     4. Verify functionality

2. **Scheduled Rotation**
   - Triggered by security policy
   - Process:
     1. Generate new credentials
     2. Update secret in AWS
     3. Update application configuration
     4. Verify functionality

## Implementation

### Using the Secrets Manager

```python
from core.secrets import SecretsManager

# Initialize the manager
secrets_manager = SecretsManager()

# Get a secret
database_creds = secrets_manager.get_secret('database/credentials')

# Create a new secret
secrets_manager.create_secret('api/new-service/key', {
    'api_key': 'new-key',
    'api_secret': 'new-secret'
})

# Update a secret
secrets_manager.update_secret('email/credentials', {
    'host': 'new-host',
    'port': 587,
    'username': 'new-user',
    'password': 'new-password'
})

# Rotate a secret
secrets_manager.rotate_secret('jwt/credentials')
```

### Integration with Django Settings

```python
# config/settings/prod.py
from core.secrets import SecretsManager

secrets_manager = SecretsManager()

# Load database credentials
db_creds = secrets_manager.get_secret('database/credentials')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': db_creds['dbname'],
        'USER': db_creds['username'],
        'PASSWORD': db_creds['password'],
        'HOST': db_creds['host'],
        'PORT': db_creds['port'],
    }
}
```

## Security Considerations

1. **Access Control**
   - Limit AWS IAM permissions to necessary actions
   - Use IAM roles for EC2 instances
   - Implement least privilege principle

2. **Audit Logging**
   - Enable AWS CloudTrail for Secrets Manager
   - Monitor secret access patterns
   - Alert on unusual access patterns

3. **Encryption**
   - All secrets are encrypted at rest
   - Use AWS KMS for encryption
   - Rotate KMS keys annually

4. **Backup and Recovery**
   - Regular backup of secrets
   - Document recovery procedures
   - Test recovery process quarterly

## Monitoring and Alerts

1. **Secret Access**
   - Monitor failed access attempts
   - Alert on unusual access patterns
   - Track secret usage metrics

2. **Rotation Status**
   - Monitor rotation success/failure
   - Alert on overdue rotations
   - Track rotation metrics

3. **Secret Health**
   - Monitor secret expiration
   - Alert on expiring secrets
   - Track secret lifecycle 
## Development Setup


# Local Development Environment Setup Guide

## 1. Overview

*   **Purpose**: To provide step-by-step instructions for developers to set up the ERP backend project and its dependencies on their local machine for development and testing.
*   **Goal**: Enable developers to quickly get a working, consistent development environment running that mirrors the core technologies used in staging/production where feasible.
*   **Primary Method**: Utilize **Docker** and **Docker Compose** to manage required services (PostgreSQL, Redis).

## 2. Prerequisites

*   **Git**: Must be installed ([https://git-scm.com/](https://git-scm.com/)).
*   **Docker & Docker Compose**: Must be installed and running ([https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)). Ensure sufficient resources (RAM/CPU) are allocated to Docker Desktop.
*   **Python**: A recent version compatible with the project (e.g., 3.10+) installed locally is helpful for IDE integration and running some commands outside Docker, but primary development often happens *inside* the container.
*   **Code Editor/IDE**: VS Code, PyCharm, etc.
*   **(Optional) `make`:** A `Makefile` can simplify common commands.

## 3. Initial Setup Steps

1.  **Clone Repository:**
    ```bash
    git clone https://github.com/devalees/alees.git
    cd erp_project
    ```
2.  **Environment Configuration (`.env` file):**
    *   Copy the example environment file: `cp .env.example .env`
    *   **Review and Edit `.env`:** Open the `.env` file in your editor.
    *   Fill in necessary values, especially:
        *   `DJANGO_SECRET_KEY`: Generate a new secret key (e.g., using `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`). **Do not use the example key.**
        *   `DATABASE_URL`: Verify it matches the `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `localhost:5432` defined in `docker-compose.yml`.
        *   `REDIS_URL`: Verify it matches the Redis service in `docker-compose.yml` (e.g., `redis://localhost:6379/1` for default cache, `redis://localhost:6379/0` for Celery broker).
        *   Other potential keys for local development (leave blank or use dev defaults if applicable).
    *   **Important:** The `.env` file is ignored by Git (`.gitignore`) and should **never** be committed.
3.  **Build Docker Images:**
    *   Build the necessary Docker images defined in `Dockerfile` and referenced in `docker-compose.yml`.
    *   Command: `docker-compose build`
4.  **Start Services:**
    *   Start the background services (PostgreSQL, Redis) defined in `docker-compose.yml`.
    *   Command: `docker-compose up -d postgres redis` (Replace service names with actual names from your `docker-compose.yml`). Wait a few seconds for them to initialize fully.
5.  **Run Initial Database Migrations:**
    *   Run the Django `migrate` command *inside* the application container to set up the database schema.
    *   Command: `docker-compose run --rm api python manage.py migrate` (Replace `api` with the name of your main Django application service in `docker-compose.yml`).
6.  **Create Superuser (Optional but Recommended):**
    *   Create an initial superuser for accessing the Django Admin interface.
    *   Command: `docker-compose run --rm api python manage.py createsuperuser`
    *   Follow the prompts.
7.  **Load Initial Data (If applicable):**
    *   If there are data migrations or fixtures for essential initial data (like OrganizationTypes, Statuses, Currencies), run the relevant command.
    *   Example: `docker-compose run --rm api python manage.py load_initial_data` (if a custom command exists) or run specific data migrations via `migrate`.
8.  **Start Development Server:**
    *   Start the main Django development server (running inside the container).
    *   Command: `docker-compose up api` (This will run the command specified in the `api` service's `command` or `entrypoint` in `docker-compose.yml`, typically `python manage.py runserver 0.0.0.0:8000`).
    *   Access the application at `http://localhost:8000` (or the mapped port).

## 4. Common Development Tasks

*   **Running Tests:**
    ```bash
    docker-compose run --rm api pytest
    # Or to run tests for a specific app:
    docker-compose run --rm api pytest api/v1/base_models/organization/tests/
    ```
*   **Running `makemigrations`:**
    ```bash
    docker-compose run --rm api python manage.py makemigrations <app_label>
    # Example:
    docker-compose run --rm api python manage.py makemigrations api.v1.base_models.organization
    ```
    *   *Remember to run `migrate` afterwards:* `docker-compose run --rm api python manage.py migrate`
*   **Running `manage.py` commands:**
    ```bash
    docker-compose run --rm api python manage.py <command_name> <args>
    # Example:
    docker-compose run --rm api python manage.py shell_plus
    ```
*   **Running Celery Worker (Manual):**
    ```bash
    # Ensure settings/dev.py has CELERY_TASK_ALWAYS_EAGER = False to test async
    docker-compose run --rm api celery -A config.celery_app worker -l INFO
    ```
*   **Running Celery Beat (Manual):**
    ```bash
    # Ensure settings/dev.py has CELERY_TASK_ALWAYS_EAGER = False
    docker-compose run --rm api celery -A config.celery_app beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler # If using DB scheduler
    ```
    *(Note: Running workers/beat manually is common for debugging specific tasks. For general development where async isn't the focus, `ALWAYS_EAGER=True` is simpler).*
*   **Stopping Services:**
    ```bash
    docker-compose down # Stops and removes containers
    # or
    docker-compose stop # Stops containers without removing them
    ```
*   **Accessing Database:** Use a local client (like DBeaver, pgAdmin) connecting to `localhost:5432` (or the mapped port) using the credentials from your `.env` file.
*   **Accessing Redis:** Use `redis-cli` or a GUI client connecting to `localhost:6379` (or the mapped port).

## 5. Troubleshooting Tips

*   Ensure Docker Desktop is running and has sufficient resources.
*   Verify environment variables in `.env` are correct and match `docker-compose.yml` service definitions.
*   If services fail to start, check logs using `docker-compose logs <service_name>`.
*   Run `docker-compose build --no-cache` if you suspect issues with the Docker image build cache.
*   Run `docker-compose down -v` to stop containers and remove associated volumes (use with caution, deletes DB data).

--- END OF FILE development_setup_guide.md ---

How does this look? It covers the essential steps using Docker Compose, which is a very standard and effective way to manage local development environments for projects with multiple services like this one.
## Localization Strategy


# Localization (i18n/L10n) Strategy

## 1. Overview

*   **Purpose**: To define the strategy and technical approach for implementing internationalization (i18n - supporting multiple languages) and localization (L10n - adapting to regional formats/conventions) within the ERP system.
*   **Scope**: Covers language support for UI text and potentially model data, locale-aware formatting of dates/times/numbers/currencies, timezone handling, and the chosen tools/libraries. Excludes building a custom translation management platform.
*   **Goal**: Provide a consistent user experience tailored to the user's preferred language and regional settings, and enable translation of application interfaces and potentially database content.

## 2. Core Principles

*   **Leverage Django Framework**: Utilize Django's built-in i18n and L10n capabilities as the foundation.
*   **Standard Formats**: Use industry standards for language codes (ISO 639-1, e.g., `en`, `es`, `fr-ca`) and country codes (ISO 3166-1 alpha-2, e.g., `US`, `GB`, `CA`).
*   **UTF-8 Everywhere**: Ensure all text data is handled and stored using UTF-8 encoding.
*   **UTC for Timestamps**: Store all timezone-aware datetimes in the database as UTC (as mandated by `USE_TZ=True`). Convert to user's local timezone for display only.
*   **Separation of Code and Translations**: Keep translatable strings separate from code logic using `gettext`.
*   **Model Translation Solution**: Select and consistently use a dedicated library for translating database content fields.

## 3. Internationalization (i18n) - Language Support

### 3.1. Supported Languages (`settings.LANGUAGES`)
*   Define the list of languages the application will officially support in `settings.py`.
    ```python
    from django.utils.translation import gettext_lazy as _

    LANGUAGES = [
        ('en', _('English')),
        ('es', _('Spanish')),
        ('fr', _('French')),
        # Add other required languages
    ]
    ```
*   Define the default language (`settings.LANGUAGE_CODE`, e.g., `'en'`).
*   Enable Django's i18n system (`settings.USE_I18N = True`).

### 3.2. Marking Strings for Translation
*   **Python Code (.py files):** Use `from django.utils.translation import gettext_lazy as _` and wrap translatable strings: `_("Your translatable string")`. Use `gettext` for immediate translation if needed (less common). Use `pgettext` for context and `ngettext` for pluralization.
*   **Django Templates (.html files):** Load the `i18n` tag library (`{% load i18n %}`) and use:
    *   `{% trans "Your translatable string" %}`
    *   `{% blocktrans %}String with {{ variable }}{% endblocktrans %}`
    *   `{% blocktrans count counter=my_list|length %}Singular string{% plural %}Plural string with {{ counter }} items{% endblocktrans %}`
*   **DRF Serializers/Models:** Use `gettext_lazy` for `verbose_name`, `help_text`, and potentially `choices` display values.

### 3.3. Translation File Workflow (`.po`/`.mo` files)
*   **Extraction:** Use `django-admin makemessages -l <lang_code>` (e.g., `-l es`) to extract translatable strings into `.po` files within `locale/<lang_code>/LC_MESSAGES/` directories in each app (or a project-level locale path).
*   **Translation:** Provide the generated `.po` files to translators (human or machine translation service). Translators fill in the `msgstr` entries.
*   **Compilation:** Use `django-admin compilemessages` to compile the translated `.po` files into binary `.mo` files, which Django uses at runtime.
*   **Version Control:** Commit both `.po` and `.mo` files to the Git repository.
*   **Process:** Integrate `makemessages` and `compilemessages` into development and deployment workflows.

### 3.4. Locale Detection (Middleware)
*   Enable Django's `django.middleware.locale.LocaleMiddleware` in `settings.MIDDLEWARE` (usually placed after `SessionMiddleware` and before `CommonMiddleware`).
*   This middleware determines the user's preferred language based on (in order): URL prefix, session, cookie, `Accept-Language` HTTP header, default `LANGUAGE_CODE`.

### 3.5. Translating Database Content (Model Translation)
*   **Requirement**: Specific model fields (e.g., `Product.name`, `Product.description`, `Category.name`) need to store content in multiple supported languages.
*   **Chosen Library**: **`django-parler`** (Recommended). Provides good integration with Django Admin, DRF serializers, and handles translation storage in separate tables efficiently. *(Alternative: `django-modeltranslation` modifies the original model table directly)*.
    *   *(Decision Confirmation Needed: Confirm `django-parler` is the chosen library)*.
*   **Implementation**:
    1.  Install `django-parler`.
    2.  Add `'parler'` to `INSTALLED_APPS`.
    3.  Configure `PARLER_LANGUAGES` in settings (usually mirrors `LANGUAGES`).
    4.  Modify target models to inherit `parler.models.TranslatableModel`.
    5.  Define translatable fields within a `parler.models.TranslatedFields` wrapper.
    ```python
    # Example product model
    from parler.models import TranslatableModel, TranslatedFields

    class Product(Timestamped, Auditable, OrganizationScoped, TranslatableModel):
        sku = models.CharField(...)
        # ... other non-translatable fields ...

        translations = TranslatedFields(
            name = models.CharField(max_length=255, db_index=True),
            description = models.TextField(blank=True)
        )
        # ...
    ```
    *   Run `makemigrations` and `migrate` (creates translation tables).
    *   Use `parler`'s utilities in Admin (`TranslatableAdmin`), Serializers (`TranslatableModelSerializer`), and Views/Templates to access/manage translated fields.

## 4. Localization (L10n) - Regional Formatting

### 4.1. Core Setting (`settings.py`)
*   Enable Django's L10n system: `USE_L10N = True`.

### 4.2. Date & Time Formatting
*   **Storage**: Store datetimes as timezone-aware UTC (requires `USE_TZ = True`).
*   **Display**: Use Django template tags (`{% load l10n %}`, `{{ my_datetime|localize }}`) or `django.utils.formats` functions (`formats.date_format(my_datetime, format='SHORT_DATETIME_FORMAT', use_l10n=True)`) to display dates and times according to the *active locale*. Define standard formats (`DATE_FORMAT`, `DATETIME_FORMAT`, etc.) in settings if needed.

### 4.3. Number & Currency Formatting
*   **Display**: Use Django template tags (`{{ my_number|localize }}`) or `django.utils.formats` functions (`formats.number_format(my_number, use_l10n=True)`) for locale-aware decimal/thousand separators.
*   **Currency**: Combine L10n number formatting with the `Currency` model's symbol and potentially symbol position conventions (though dedicated money formatting libraries might offer more control).

### 4.4. Timezone Handling
*   **Storage**: Store datetimes as UTC (`USE_TZ = True`).
*   **User Preference**: Store user's preferred timezone (`UserProfile.timezone`).
*   **Display**: Use Django's timezone utilities (`django.utils.timezone`) and middleware (`TimezoneMiddleware` - custom or from a package) to activate the user's preferred timezone for the duration of a request. Convert UTC datetimes to the user's timezone before display using `datetime_obj.astimezone(user_timezone)`.

## 5. Strategy Summary

1.  Enable Django's `USE_I18N`, `USE_L10N`, `USE_TZ` settings.
2.  Define supported `LANGUAGES`.
3.  Use `gettext_lazy` (`_()`) in Python and `{% trans %}`/`{% blocktrans %}` in templates for UI strings. Follow `makemessages`/`compilemessages` workflow.
4.  Use `LocaleMiddleware` for language detection.
5.  Select and integrate **`django-parler`** for translating required database model fields.
6.  Use Django's template tags/format functions (`|localize`) for locale-aware display of dates, times, and numbers.
7.  Store user timezone preferences and activate them (via middleware) for displaying times correctly.

## 6. Testing

*   Test translation string extraction (`makemessages`).
*   Test display of UI elements in different languages (requires loading `.mo` files). Use `override_settings(LANGUAGE_CODE=...)` and `translation.activate(lang_code)` in tests.
*   Test locale-aware formatting of dates/numbers.
*   Test model translation: Create/update/retrieve translated fields via API/ORM in different languages. Use `parler`'s testing utilities if needed.
*   Test timezone conversions and display.

--- END OF FILE localization_strategy.md ---
## Validation Strategy

Okay, let's create the `validation_strategy.md`. This document outlines how data validation will be handled throughout the ERP application, emphasizing the use of built-in Django and DRF features over a complex custom engine (as decided previously).

--- START OF FILE validation_strategy.md ---

# Validation Strategy

## 1. Overview

*   **Purpose**: To define the standard approach and best practices for implementing data validation across the ERP system, ensuring data integrity, enforcing business rules, and providing clear feedback to users/API consumers.
*   **Scope**: Covers validation techniques at the database, model, serializer, and potentially service layers. Excludes the implementation of a separate, generic validation rule engine.
*   **Goal**: Robust, maintainable, and consistently applied validation throughout the application.

## 2. Core Principles

*   **Validate Early, Validate Often**: Perform validation checks as close to the data entry point as possible (typically serializers for API input).
*   **Leverage Built-in Features**: Utilize Django model field options and DRF serializer validation mechanisms extensively before resorting to custom code.
*   **Clarity of Errors**: Validation errors returned via the API must be clear, specific, and follow the standard error format defined in the API Strategy (pointing to the specific field(s) in error).
*   **DRY (Don't Repeat Yourself)**: Use reusable custom validator functions for logic applied across multiple fields or models.
*   **Separation of Concerns**:
    *   **Format/Type/Presence Validation**: Primarily handled by model field definitions and serializer field types/arguments.
    *   **Business Rule/Cross-Field Validation**: Primarily handled within Serializer `validate()` methods or Model `clean()` methods.
    *   **Database Constraints**: Used for enforcing fundamental data integrity (uniqueness, foreign key existence, non-null).

## 3. Validation Layers & Techniques

Validation will be implemented at multiple layers:

### 3.1. Database Level Constraints
*   **Purpose**: Enforce absolute data integrity rules directly within the database schema.
*   **Techniques**:
    *   `NOT NULL` constraints (via `null=False` on model fields).
    *   `UNIQUE` constraints (via `unique=True` or `Meta.unique_together` on models).
    *   `FOREIGN KEY` constraints (automatically created by `models.ForeignKey`, `OneToOneField`). Ensure appropriate `on_delete` behavior is set.
    *   `(Optional)` Database `CHECK` constraints for simple value restrictions (can be added via migrations if needed, less common with Django).
*   **Note**: Database errors resulting from constraint violations are often less user-friendly than application-level validation errors. Application validation should catch most issues *before* they hit the database constraint.

### 3.2. Django Model Field Validation
*   **Purpose**: Define basic data type, format, and presence rules directly on the model fields.
*   **Techniques**:
    *   **Field Types**: Use appropriate field types (`EmailField`, `URLField`, `IntegerField`, `DecimalField`, `BooleanField`, `DateField`, `DateTimeField`, `UUIDField`, etc.) which include built-in format validation.
    *   **Field Options**:
        *   `max_length`, `min_length` (for CharField/TextField).
        *   `choices`: Restrict values to a predefined set.
        *   `unique`, `unique_for_date/month/year`.
        *   `null=False`, `blank=False` (Note: `null` is DB level, `blank` is form/serializer validation level).
        *   `validators`: Attach reusable validator functions (see below).
        *   Numeric field options (`max_digits`, `decimal_places`, `min_value`, `max_value`).
*   **Execution**: These validations are typically run automatically by Django Forms and DRF ModelSerializers.

### 3.3. Django Model `clean()` Method
*   **Purpose**: Implement model-level validation logic that requires access to multiple fields *within the same model instance*. Suitable for enforcing invariants or complex relationships between fields *before* saving to the database.
*   **Techniques**:
    *   Override the `clean()` method on the model.
    *   Perform checks involving `self.field_a`, `self.field_b`, etc.
    *   Raise `django.core.exceptions.ValidationError` if validation fails. Can target specific fields or be a non-field error.
*   **Execution**: Called automatically by `ModelForm` validation and `full_clean()` method. **Important:** DRF serializers *do not* automatically call model `clean()` by default. It must be called explicitly within the serializer's `validate()` method or by overriding `create()`/`update()` if model-level validation needs to be enforced for API input.
*   **Use Case Example:** Ensure `start_date` is always before `end_date`.

### 3.4. DRF Serializer Validation (Primary API Input Validation Point)
*   **Purpose**: Validate incoming data from API requests *before* creating or updating model instances. Handles format, business rules, cross-field dependencies, and permissions related to the *specific data being submitted*.
*   **Techniques**:
    *   **Serializer Fields**: Use appropriate serializer fields (`serializers.EmailField`, `serializers.IntegerField`, etc.) with arguments like `required=True`, `allow_null=True`, `max_length`, `min_value`, `validators`.
    *   **`validate_<field_name>(self, value)` Methods**: Implement custom validation logic for a single field. Should return the validated `value` or raise `serializers.ValidationError`.
    *   **`validate(self, data)` Method**: Implement validation logic involving multiple fields. Accesses the dictionary of validated field data (`data`). Should return the validated `data` dictionary or raise `serializers.ValidationError`. **This is the primary location for cross-field business rule validation for APIs.** Explicitly call `instance.full_clean()` from here if model-level `clean()` validation needs to be enforced for API requests involving existing instances. For creation, call model `clean` on the instance *before* saving it in the `create` method.
*   **Execution**: Run automatically by DRF when `serializer.is_valid(raise_exception=True)` is called in the view.
*   **Error Formatting**: DRF automatically collects `ValidationError`s raised during this process and formats them (usually into a dictionary mapping field names to lists of errors), which our custom exception handler will then format into the standard API error response.

### 3.5. Custom Validator Functions
*   **Purpose**: Define reusable validation logic that can be applied to multiple model fields or serializer fields.
*   **Techniques**: Create standalone functions that accept a value and raise `ValidationError` if invalid. Attach them using the `validators=[my_validator]` argument on model or serializer fields.
*   **Example:** A validator to check if a string contains only alphanumeric characters, reusable on `username`, `code`, etc.

## 4. Strategy Summary

1.  Define strict database constraints (`UNIQUE`, `NOT NULL`, FKs) for fundamental integrity.
2.  Use appropriate Django **Model Fields** and their options (`EmailField`, `max_length`, `choices`, etc.) for basic type and format validation.
3.  Implement model-level invariants (rules involving multiple fields of the *same* model) in the **Model `clean()`** method.
4.  Implement **ALL API input validation** (including business rules, cross-field checks, and *explicitly calling model `clean()` if needed*) within **DRF Serializer `validate_<field>()` and `validate()` methods**. This is the primary validation layer for the API.
5.  Create **Reusable Validator Functions** for common checks applied across different fields/models/serializers.

## 5. Integration with Other Systems

*   **RBAC System:** Validation logic within serializers/views may need to check user permissions before validating certain state transitions or field updates.
*   **Workflow System:** Transitions defined in the workflow system will have associated conditions, which act as a form of validation before allowing a status change. Serializers handling status updates might need to check if the requested transition is valid according to the workflow.
*   **Custom Fields:** Validation logic within serializers needs to retrieve the relevant `CustomFieldDefinition` schema and validate the `custom_fields` JSON data against it.

## 6. Testing

*   **Unit Tests:** Test model `clean()` methods, custom validator functions, and individual serializer `validate_<field>()` / `validate()` methods in isolation (mocking database lookups if necessary).
*   **API Tests:** Test API endpoints with various valid and invalid inputs (missing fields, incorrect formats, values violating business rules, invalid custom field data). Assert that appropriate `400 Bad Request` errors are returned with the standard error structure detailing the specific validation failures. Test that model `clean()` validations are correctly triggered for API requests.

--- END OF FILE validation_strategy.md ---
## Monitoring Strategy


# Monitoring & Observability Strategy

## 1. Overview

*   **Purpose**: To define the strategy for monitoring the health, performance, and behavior of the ERP backend application and its supporting infrastructure, enabling proactive issue detection, efficient troubleshooting, and performance analysis.
*   **Scope**: Covers the selection of monitoring tools, application instrumentation (metrics, logging, tracing, error tracking), health checks, and basic alerting principles. Excludes building an internal monitoring platform.
*   **Goal**: Achieve comprehensive observability into the production and staging environments, allowing rapid detection and diagnosis of problems, and providing insights for performance optimization.
*   **Approach**: Integrate with a suite of external, specialized monitoring and observability tools. Instrument the Django application to expose necessary data to these tools.

## 2. Core Principles

*   **External Tooling**: Leverage established, best-practice external monitoring platforms rather than building monitoring capabilities natively within the ERP.
*   **The Three Pillars of Observability**: Aim to collect data covering:
    *   **Metrics**: Time-series numerical data representing system/application performance and behavior (e.g., request latency, error rates, queue lengths, CPU usage).
    *   **Logs**: Timestamped records of events occurring within the application or infrastructure (as defined in `logging_strategy.md`).
    *   **Traces**: Represent the flow of a single request as it travels through different services or components (essential for microservices, useful even in monoliths with async tasks).
*   **Actionable Data**: Monitoring should provide data that leads to actionable insights for performance improvement, debugging, or scaling.
*   **Automation**: Automate metric/log collection and alerting as much as possible.
*   **Contextualization**: Ensure metrics, logs, and traces include relevant context (environment, service, user ID, org ID, request/trace ID) for effective correlation.

## 3. Chosen Monitoring Stack (Example - Adapt as needed)

This strategy assumes a common open-source stack, but can be adapted for commercial platforms like Datadog, New Relic, etc.

*   **Metrics Collection & Storage**: **Prometheus**
    *   Application exposes metrics via an HTTP endpoint (e.g., `/metrics`).
    *   Prometheus server scrapes these endpoints periodically.
    *   Stores metrics in a time-series database.
*   **Metrics Visualization & Dashboards**: **Grafana**
    *   Connects to Prometheus (and other data sources like Loki/Elasticsearch).
    *   Used to build dashboards visualizing key metrics and logs.
*   **Log Aggregation & Querying**: **Loki** (or Elasticsearch/OpenSearch via ELK/EFK stack)
    *   Receives structured logs forwarded by collection agents (Promtail, Fluentd, Filebeat).
    *   Provides efficient storage and querying (LogQL for Loki).
*   **Log Collection Agent**: **Promtail** (for Loki) or Fluentd/Filebeat (for ELK/EFK). Runs alongside application containers/instances to collect logs (from stdout/stderr or files).
*   **Alerting**: **Alertmanager** (integrates with Prometheus)
    *   Defines alert rules based on Prometheus metrics.
    *   Handles alert silencing, grouping, and routing to notification channels (Slack, PagerDuty, Email).
*   **Error Tracking & Aggregation**: **Sentry** (Open Source or SaaS)
    *   SDK integrated into the Django application captures unhandled exceptions and explicit error reports.
    *   Groups similar errors, provides context (stack traces, user info, request data), and integrates with issue trackers.

## 4. Application Instrumentation

### 4.1. Metrics Exposure (`django-prometheus`)
*   **Library**: Utilize `django-prometheus` library.
*   **Configuration**: Add `'django_prometheus'` to `INSTALLED_APPS`. Include its middleware (`PrometheusBeforeMiddleware`, `PrometheusAfterMiddleware`) in `settings.MIDDLEWARE`. Expose the `/metrics` endpoint via `urls.py`.
*   **Default Metrics**: The library automatically exports various metrics (request counts/latency, database interaction timings, cache stats, etc.).
*   **Custom Metrics**: Define custom Prometheus metrics (Counters, Gauges, Histograms, Summaries) within application code to track specific business events or performance indicators (e.g., number of orders processed, specific API endpoint usage, queue processing time). Use `django-prometheus` utilities (`exports.ExportModelOperationsMixin` on Admin, custom collectors).

### 4.2. Structured Logging
*   **Strategy**: Follow the separate `logging_strategy.md`.
*   **Format**: JSON format with standard fields (timestamp, level, logger, message, user_id, org_id, request_id, trace_id, etc.).
*   **Collection**: Configure application to log to `stdout`/`stderr` (for containers) or files, to be collected by Promtail/Fluentd/Filebeat.

### 4.3. Error Tracking (Sentry)
*   **Library**: Integrate the `sentry-sdk` for Python/Django.
*   **Configuration**: Configure the Sentry DSN (Data Source Name) via environment variables in `settings.py`. Initialize the SDK early in the application lifecycle (e.g., `settings.py` or `wsgi.py`/`asgi.py`).
*   **Data Capture**: The SDK automatically captures unhandled exceptions. Use `sentry_sdk.capture_message()` or `sentry_sdk.capture_exception()` for manually reporting errors or warnings.
*   **Context**: Configure the SDK to automatically include user information (`id`, `username`, `email`), request data, and potentially custom tags (like `organization_id`) with error reports.

### 4.4. Distributed Tracing (Optional - Advanced)
*   **Purpose**: Track requests across multiple services or asynchronous tasks (e.g., API request -> Celery task -> external API call).
*   **Implementation**: Requires integrating an OpenTelemetry-compatible library or platform-specific SDK (e.g., Datadog APM, Jaeger client). Involves instrumenting code (often automatically via middleware/library hooks) to propagate trace IDs and report timing spans for different operations.
*   **Initial Scope**: Likely deferred unless microservices or complex async workflows are central from the start. Basic Request ID logging provides some correlation.

### 4.5. Health Check Endpoints
*   **Requirement**: Implement standard health check endpoints for load balancers, container orchestrators (e.g., Kubernetes probes), and basic availability monitoring.
*   **Endpoints**:
    *   `/healthz` or `/livez` (Liveness probe): Simple check, returns `200 OK` if the application process is running. Should not have external dependencies (like DB).
    *   `/readyz` (Readiness probe): More comprehensive check, returns `200 OK` only if the application is ready to serve traffic (e.g., can connect to the database, cache, essential services).
*   **Implementation**: Simple Django views returning `HttpResponse("OK")`.

## 5. Alerting Strategy

*   **Tool**: Use the alerting capabilities of the chosen monitoring platform (e.g., Alertmanager, Datadog Monitors).
*   **Focus**: Define alerts for critical conditions indicating user impact or system failure:
    *   **Error Rates:** High percentage of `5xx` HTTP status codes, high rate of exceptions reported to Sentry.
    *   **Latency:** API endpoint latency (p95, p99) exceeding defined thresholds.
    *   **Resource Saturation:** High CPU/Memory/Disk utilization on application servers or database.
    *   **Queue Lengths:** Celery queue backlog exceeding thresholds for extended periods.
    *   **External Service Availability:** High error rates when calling critical external APIs.
    *   **Health Checks:** Probes failing consistently.
    *   **Critical Business Metrics:** (e.g., Order processing rate drops significantly).
*   **Configuration**: Define alert rules, thresholds, evaluation periods, and notification channels (Slack, PagerDuty, Email) within the monitoring platform.

## 6. Dashboards

*   **Tool**: Use Grafana (or the chosen platform's dashboarding feature).
*   **Purpose**: Visualize key metrics and logs to provide an overview of system health and performance.
*   **Key Dashboards**:
    *   **Application Overview:** Request rate, error rate (4xx/5xx), latency percentiles (overall and per-endpoint).
    *   **Database Performance:** Connection count, query latency, CPU/Memory/IO utilization.
    *   **Celery/Queue Performance:** Queue lengths, task execution times, worker counts, success/failure rates.
    *   **Infrastructure Resources:** CPU, Memory, Disk, Network I/O for application instances, DB, Cache, Search Engine nodes.
    *   **Business Metrics:** Key application-specific counters/gauges.

## 7. Testing

*   **Instrumentation Tests**: Verify metrics endpoints (`/metrics`) expose expected data. Verify logs are generated in the correct JSON format with context. Verify errors are sent to Sentry. Verify health check endpoints return `200 OK`.
*   **Alerting Tests**: Test alert rule configuration in the monitoring platform (often requires manual triggering or specific test environments).

## 8. Deployment & Configuration

*   Deploy chosen monitoring infrastructure (Prometheus, Grafana, Loki, Alertmanager, Sentry instance or configure SaaS).
*   Deploy log collection agents (Promtail, Fluentd, etc.) alongside application instances.
*   Configure application (`settings.py`, environment variables) with endpoints/keys for Sentry, potentially logging endpoints.
*   Configure monitoring tools (Prometheus scrape targets, Grafana data sources, Alertmanager rules).

## 9. Maintenance

*   Keep monitoring agents and libraries updated.
*   Maintain and refine dashboards and alert rules based on operational experience.
*   Manage storage retention policies for metrics and logs in the external platforms.
*   Regularly review key dashboards and alert fatigue.

--- END OF FILE monitoring_strategy.md ---
## Deployment & CI/CD


# Deployment Strategy and CI/CD Pipeline

## 1. Overview

*   **Purpose**: To define the strategy and process for reliably building, testing, and deploying the ERP backend application to various environments (Staging, Production).
*   **Scope**: Covers Continuous Integration (CI) practices, Continuous Deployment/Delivery (CD) pipeline stages, target deployment infrastructure considerations, branching strategy, and rollback procedures.
*   **Goals**: Automated testing, consistent builds, reliable deployments, reduced manual intervention, faster feedback cycles, safe production releases.

## 2. Core Principles

*   **Automate Everything Possible**: Automate testing, building, and deployment steps to ensure consistency and reduce human error.
*   **Infrastructure as Code (IaC):** Manage supporting infrastructure (servers, databases, load balancers, monitoring setup) using code (e.g., Terraform, CloudFormation, Ansible) where feasible.
*   **Immutable Infrastructure (Ideal):** Aim for deployments where servers/containers are replaced rather than updated in-place, reducing configuration drift.
*   **Environment Parity**: Keep Staging environment as close to Production as possible (infrastructure, configuration, data structure).
*   **Monitoring & Feedback**: Integrate monitoring and alerting into the deployment process to quickly detect issues post-deployment.
*   **Security Integrated**: Embed security checks (SAST, dependency scanning) into the CI/CD pipeline.
*   **Rollback Capability**: Have defined procedures to quickly revert to a previous stable version in case of critical deployment failures.

## 3. Version Control & Branching Strategy

*   **Version Control System:** **Git**. Hosted on a platform like GitHub, GitLab, or Bitbucket.
*   **Branching Model (Example: Gitflow variation):**
    *   `main`: Represents the latest stable production code. Deployments to production are tagged releases from this branch. Merges only from `release` or `hotfix` branches.
    *   `develop`: Represents the current state of development, integrating completed features. This is the target for feature branches and the source for release branches. CI runs comprehensively on this branch.
    *   `feature/<feature-name>`: Branched from `develop`. Developers work on features here. Pull Requests (PRs) are created from feature branches back into `develop`. CI runs on PRs.
    *   `release/<version-number>`: Branched from `develop` when preparing for a production release. Only bug fixes and documentation updates allowed here. Used for final testing/staging deployment. Merged into `main` (and tagged) and back into `develop` upon release.
    *   `hotfix/<issue-id>`: Branched from `main` to fix critical production bugs. Merged back into both `main` (tagged) and `develop`.

## 4. Continuous Integration (CI) Pipeline

*   **Trigger:** On every push to any branch, and especially on Pull Requests targeting `develop` or `main`.
*   **Tool:** Chosen CI/CD platform (e.g., GitHub Actions, GitLab CI, Jenkins).
*   **Key Stages:**
    1.  **Checkout Code:** Get the latest code from the relevant branch.
    2.  **Setup Environment:** Set up the correct Python version, install dependencies (`pip install -r requirements/dev.txt` or similar). Set up necessary services if needed for specific tests (e.g., Postgres, Redis via Docker).
    3.  **Linting & Code Formatting:** Run linters (`flake8`, `pylint`) and formatters (`black`, `isort`) checks to enforce code style. Fail build if checks fail.
    4.  **Static Analysis:** Run SAST tools (`bandit`) to check for common security vulnerabilities. Fail build on high-severity issues.
    5.  **Dependency Scanning:** Run vulnerability scans on `requirements/*.txt` files (`pip-audit`, Snyk, etc.). Fail build on critical vulnerabilities without approved exceptions.
    6.  **Run Tests:** Execute the full test suite (`pytest --cov ...`) using test settings (`DJANGO_SETTINGS_MODULE=config.settings.test`). Requires test database access.
    7.  **Build Artifacts (Optional):** If needed, build Docker images or other deployment artifacts. Push images to a container registry (tag with commit SHA and potentially branch name).
    8.  **Coverage Report:** Upload code coverage reports to a monitoring service (e.g., Codecov, SonarQube). Potentially fail build if coverage drops significantly.
    9.  **Notifications:** Notify developers (e.g., via Slack, email) of build success or failure.

## 5. Continuous Deployment/Delivery (CD) Pipeline

*   **Trigger:** Typically triggered automatically on successful merge to specific branches (`develop` for Staging, `main`/`release` for Production) or manually via the CI/CD platform interface.
*   **Target Environments:**
    *   **Staging:** A dedicated environment mirroring production infrastructure as closely as possible. Used for final UAT, integration testing, and performance testing before production release.
    *   **Production:** The live environment serving end-users.
*   **Key Stages (Example for Staging/Production):**
    1.  **Approval (Optional):** Manual approval step before deploying to production.
    2.  **Fetch Artifacts:** Download build artifacts (e.g., Docker image tagged from CI).
    3.  **Infrastructure Provisioning/Update (IaC):** Apply infrastructure changes using Terraform/CloudFormation/Ansible if necessary.
    4.  **Database Backup (Production):** **CRITICAL.** Trigger and verify database backup before applying changes (as defined in Migration Strategy).
    5.  **Deploy Application Code:**
        *   **(Containers/Kubernetes):** Update Kubernetes Deployments/Services with the new Docker image tag. Use rolling updates or blue-green deployment strategies.
        *   **(VMs/Servers):** Pull new code, install dependencies, collect static files (`collectstatic`).
    6.  **Run Database Migrations:** Execute `python manage.py migrate --noinput` against the target environment's database. **Monitor closely.**
    7.  **Restart Application Servers:** Restart ASGI/WSGI server processes (e.g., Gunicorn, Uvicorn/Daphne) and Celery workers/beat service to pick up new code.
    8.  **Run Post-Deployment Checks/Smoke Tests:** Execute a small suite of critical API tests or health checks against the newly deployed version.
    9.  **Traffic Shifting (Blue-Green/Canary):** If using these strategies, gradually shift traffic to the new version while monitoring health.
    10. **Notifications:** Notify relevant teams of deployment success or failure.
    **
    *   **Clarify Static Files:** Add an explicit step for `python manage.py collectstatic` *before* restarting application servers, ensuring static files are gathered correctly for serving via Nginx or cloud storage/CDN.

## 6. Deployment Infrastructure Considerations (High-Level)

*   **Target Platform (TBD):** Cloud Provider (AWS, GCP, Azure), Kubernetes, VMs.
*   **Containerization (Recommended):** Use **Docker** to package the application and its dependencies consistently.
*   **Web Server:** Use a production-grade WSGI server (like **Gunicorn**) and potentially an ASGI server (like **Daphne** or **Uvicorn**) behind a reverse proxy (like **Nginx** or cloud load balancer).
*   **Database:** Managed PostgreSQL service (e.g., AWS RDS, Google Cloud SQL) recommended for production for easier management, scaling, and backups.
*   **Redis:** Managed Redis service (e.g., AWS ElastiCache, Google Memorystore) recommended for production.
*   **Celery Workers/Beat:** Run as separate processes/containers managed by Supervisor, systemd, or Kubernetes Deployments/CronJobs.
*   **File Storage:** Cloud object storage (S3, GCS, Azure Blob).
*   **Search Engine:** Managed Elasticsearch/OpenSearch service or self-hosted cluster.
*   **Load Balancing:** Use cloud provider load balancers or Nginx/HAProxy.
*   **CDN:** Use a Content Delivery Network (CloudFront, Cloudflare, etc.) for serving static assets and potentially cached API responses.

## 7. Configuration Management Integration

*   The CD pipeline is responsible for injecting the correct environment variables and secrets (retrieved from a secure source like Vault or a cloud secrets manager) into the application runtime environment during deployment (as defined in `configuration_management_strategy.md`).

## 8. Rollback Strategy

*   **Automated Rollback (Ideal):** If post-deployment checks fail or monitoring shows critical errors, the CD pipeline should ideally automatically trigger a rollback to the previously deployed stable version (code artifact/Docker image). Database rollbacks are much harder (see below).
*   **Manual Rollback:** Define procedures for manually triggering a redeployment of the previous stable version.
*   **Database Rollback:** Reversing migrations in production is generally **not recommended** (high risk of data loss/inconsistency). The primary database rollback strategy is **restoring from the verified backup** taken immediately before the migration run. This requires downtime. Minor schema fixes might be possible via a new "forward" migration.

## 9. Monitoring Integration

*   Deployment events (start, success, failure) should be sent to the monitoring/alerting system.
*   Monitor application health and key metrics closely immediately after deployment to detect issues.

## 10. Testing

*   CI pipeline runs unit, integration, and API tests automatically.
*   Post-deployment smoke tests run against staging and production.
*   Performance and security tests run periodically against staging or dedicated environments.

--- END OF FILE deployment_strategy_and_ci_cd.md ---
## Feature Flags

# Feature Flags Management

## Overview

This document outlines the feature flags management strategy for the Alees ERP system, using `django-flags` as the primary feature flag management solution.

## Feature Flags Configuration

### Storage Options

1. **Redis Storage** (Recommended for Production)
   - Configure in settings:
     ```python
     FEATURE_FLAGS_STORAGE = 'redis'
     FEATURE_FLAGS_REDIS_URL = 'redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/4'  # Using DB 4
     ```

2. **Database Storage** (Default)
   - Configure in settings:
     ```python
     FEATURE_FLAGS_STORAGE = 'database'
     ```

3. **Cache Storage**
   - Configure in settings:
     ```python
     FEATURE_FLAGS_STORAGE = 'cache'
     ```

### Flag Naming Convention

- Format: `{module}.{feature}.{action}`
- Examples:
  - `auth.two_factor.enabled`
  - `billing.invoice_auto_generate`
  - `project.task_assignments`

## Feature Flag Types

1. **Boolean Flags**
   - Simple on/off switches
   - Example: `auth.two_factor.enabled`

2. **User-Based Flags**
   - Enabled for specific users or groups
   - Example: `project.beta_features`

3. **Percentage-Based Flags**
   - Enabled for a percentage of users
   - Example: `ui.new_dashboard`

4. **Time-Based Flags**
   - Enabled during specific time periods
   - Example: `marketing.promotion_active`

## Feature Rollout Process

### 1. Development Phase

1. **Create Feature Flag**
   ```python
   from core.flags import FeatureFlagsManager
   
   flags_manager = FeatureFlagsManager()
   flags_manager.create_flag(
       name='project.new_feature',
       description='New project management feature',
       default=False
   )
   ```

2. **Implement Feature with Flag Check**
   ```python
   from core.flags import FeatureFlagsManager
   
   flags_manager = FeatureFlagsManager()
   
   def new_feature_view(request):
       if flags_manager.is_enabled('project.new_feature', request):
           # New feature implementation
           pass
       else:
           # Old feature implementation
           pass
   ```

### 2. Testing Phase

1. **Enable for Test Environment**
   ```python
   # config/settings/test.py
   FLAGS = {
       'project.new_feature': [{'condition': 'boolean', 'value': True}]
   }
   ```

2. **Write Tests**
   ```python
   from django.test import TestCase
   from core.flags import FeatureFlagsManager
   
   class NewFeatureTests(TestCase):
       def setUp(self):
           self.flags_manager = FeatureFlagsManager()
           self.flags_manager.create_flag(
               name='project.new_feature',
               description='Test flag',
               default=True
           )
   
       def test_new_feature_enabled(self):
           self.assertTrue(self.flags_manager.is_enabled('project.new_feature'))
   ```

### 3. Staging Phase

1. **Enable for Beta Users**
   ```python
   # Enable for specific users
   FLAGS = {
       'project.new_feature': [
           {'condition': 'user', 'value': 'beta_user@example.com'}
       ]
   }
   ```

2. **Monitor Performance**
   - Track feature usage
   - Monitor error rates
   - Collect user feedback

### 4. Production Rollout

1. **Percentage-Based Rollout**
   ```python
   # Enable for 10% of users
   FLAGS = {
       'project.new_feature': [
           {'condition': 'percent', 'value': 10}
       ]
   }
   ```

2. **Gradual Increase**
   - Increase percentage weekly
   - Monitor metrics
   - Address issues

3. **Full Rollout**
   ```python
   # Enable for all users
   FLAGS = {
       'project.new_feature': [
           {'condition': 'boolean', 'value': True}
       ]
   }
   ```

## Implementation Examples

### 1. View-Level Feature Flag

```python
from django.views.generic import View
from core.flags import FeatureFlagsManager

class ProjectView(View):
    def get(self, request):
        flags_manager = FeatureFlagsManager()
        if flags_manager.is_enabled('project.new_dashboard', request):
            return self.new_dashboard(request)
        return self.old_dashboard(request)
```

### 2. Template-Level Feature Flag

```html
{% load feature_flags %}
{% flag_enabled 'ui.new_navigation' as new_nav %}
{% if new_nav %}
    {% include "new_navigation.html" %}
{% else %}
    {% include "old_navigation.html" %}
{% endif %}
```

### 3. API-Level Feature Flag

```python
from rest_framework.views import APIView
from core.flags import FeatureFlagsManager

class ProjectAPIView(APIView):
    def get_serializer_class(self):
        flags_manager = FeatureFlagsManager()
        if flags_manager.is_enabled('api.v2.serializers', self.request):
            return ProjectV2Serializer
        return ProjectV1Serializer
```

## Monitoring and Management

### 1. Flag Status Dashboard

```python
from django.contrib.admin import AdminSite
from flags.admin import FlagAdmin
from flags.models import Flag

class FeatureFlagsAdminSite(AdminSite):
    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        app_list.append({
            'name': 'Feature Flags',
            'app_label': 'flags',
            'models': [
                {
                    'name': 'Flags',
                    'object_name': 'Flag',
                    'admin_url': '/admin/flags/flag/',
                    'view_only': False,
                }
            ]
        })
        return app_list
```

### 2. Usage Tracking

```python
from django.db import models
from django.utils import timezone

class FeatureFlagUsage(models.Model):
    flag_name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    enabled = models.BooleanField()
    timestamp = models.DateTimeField(default=timezone.now)
```

## Best Practices

1. **Naming**
   - Use consistent naming conventions
   - Make names descriptive
   - Include module/feature context

2. **Documentation**
   - Document all feature flags
   - Include purpose and rollout plan
   - Update documentation with changes

3. **Cleanup**
   - Remove unused flags
   - Archive old flags
   - Update documentation

4. **Testing**
   - Test both enabled and disabled states
   - Include flag tests in CI/CD
   - Test flag combinations

5. **Monitoring**
   - Track flag usage
   - Monitor performance impact
   - Alert on issues 