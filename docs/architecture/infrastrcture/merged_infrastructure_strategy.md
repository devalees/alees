# Infrastructure Strategy

## Table of Contents

1. [Database Management](#database-management)
   - [PostgreSQL](#postgresql)
   - [Migration Strategy](#migration-strategy)

2. [Caching & Storage](#caching--storage)
   - [Redis Caching](#redis-caching)
   - [File Storage](#file-storage)

3. [Asynchronous Processing](#asynchronous-processing)
   - [Celery Tasks](#celery-tasks)

---

## Database Management


### PostgreSQL

## 1. Database Strategy (PostgreSQL)

**(Equivalent to a focused PRD for the Database choice and setup)**

### 1.1. Overview

*   **Purpose**: To define the selection, configuration, management, and usage strategy for the primary relational database supporting the ERP application.
*   **Scope**: Choice of database system, basic configuration, local development setup, backup strategy, testing considerations, and integration with Django ORM.
*   **Chosen Technology**: **PostgreSQL** (Target Version: 14+). Selected for its robustness, ACID compliance, strong support for SQL standards, advanced features (JSONB, indexing options), scalability, and excellent integration with Django.

### 1.2. Core Requirements

*   **Data Persistence**: Reliably store all relational application data (Organizations, Users, Products, Orders, etc.).
*   **Data Integrity**: Enforce constraints (Primary Keys, Foreign Keys, Uniqueness, Not Null) defined in Django models.
*   **Transaction Support**: Provide ACID-compliant transactions for complex operations.
*   **Scalability Foundation**: Support vertical scaling and provide features (like replication) enabling future horizontal scaling if needed.
*   **JSON Support**: Efficiently store and query JSON data (for `custom_fields`, `metadata`, etc.) using the `JSONB` type.

### 1.3. Configuration Strategy (`config/settings/`)

*   Use Django's standard `settings.DATABASES` dictionary.
*   The `default` database alias will point to the primary PostgreSQL instance.
*   Connection details (`HOST`, `PORT`, `NAME`, `USER`, `PASSWORD`) **must** be loaded from environment variables (using `os.environ.get` or preferably `django-environ`) in `settings/base.py` or environment-specific files (`dev.py`, `prod.py`). **Do not commit credentials.**
*   Use distinct database names for development, testing, and production environments.

### 1.4. Local Development Setup (`docker-compose.yml`)

*   Utilize the official `postgres:<version>` Docker image in `docker-compose.yml`.
*   Configure environment variables within `docker-compose.yml` for `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.
*   Use a Docker named volume to persist database data locally between container restarts (e.g., `volumes: - postgres_data:/var/lib/postgresql/data`).

### 1.5. Integration Points

*   Primary interaction via **Django ORM**.
*   Used by **Django Migrations** system to manage schema changes.
*   May be accessed by **Celery** tasks (via Django ORM).
*   Data source for **Search Engine indexing**.
*   Data source for **Analytics/Reporting** (potentially via read replicas or ETL later).

### 1.6. Security Considerations

*   Use strong, unique passwords for database users, managed via secure environment variables/secrets management.
*   Limit network access to the database server (firewall rules, cloud security groups).
*   Use non-superuser roles for the main application connection with appropriate privileges.
*   Consider TLS/SSL encryption for database connections, especially in production/staging.

### 1.7. Monitoring Considerations

*   Monitor key database metrics via external monitoring tools: Connection count, CPU/Memory/Disk utilization, Slow query logs, Replication lag (if applicable), Transaction throughput, Index hit rates/bloat.

### 1.8. Backup & Recovery Strategy

*   **Requirement**: Implement regular, automated backups. Test restoration procedures periodically.
*   **Method**: Use `pg_dump` for logical backups and/or cloud provider snapshot capabilities (e.g., AWS RDS Snapshots). Consider Point-In-Time Recovery (PITR) using Write-Ahead Logging (WAL) archiving for production.
*   **Frequency & Retention**: Define based on RPO (Recovery Point Objective) and RTO (Recovery Time Objective) requirements (e.g., daily backups, retain for 30 days, PITR enabled).

### 1.9. Testing Considerations

*   **Test Database**: `pytest-django` will manage test database creation/destruction.
*   **Engine Choice**: **Recommend using PostgreSQL for the test database** (configured in `settings/test.py` via `settings.DATABASES`) for maximum parity with production, rather than SQLite. This ensures testing against vendor-specific features or constraints. `pytest-django` supports this.

### 1.10. Deployment Considerations

*   Ensure the target database instance exists and is accessible before application deployment.
*   Ensure database user and permissions are correctly configured.
*   Run Django migrations (`manage.py migrate`) as a standard step in the deployment process *after* code deployment but *before* releasing traffic (or during a maintenance window if needed).
*   Consider using a connection pooler (like PgBouncer) in front of the database in production.

### Migration Strategy


# Database Management and Migration Strategy

## 1. Overview

*   **Purpose**: To establish clear procedures, best practices, and tools for managing database schema changes (migrations) using Django's migration system, ensuring data integrity, minimizing deployment risks, and facilitating collaboration within the ERP project.
*   **Scope**: Covers migration creation, application, conflict resolution, testing, deployment, data migrations, database backups, and general maintenance related to Django migrations and the PostgreSQL database.
*   **Goal**: Predictable, reliable, and low-risk database schema evolution throughout the project lifecycle.

## 2. Core Principles

*   **Consistency**: All developers follow the same migration workflow.
*   **Atomicity**: Migrations should represent logical, atomic schema changes where possible. Avoid overly large, multi-purpose migrations.
*   **Reversibility**: Migrations should ideally be reversible (`manage.py migrate <app_label> <previous_migration>`), although complex data migrations might be exceptions. Always test reverse migrations where feasible.
*   **Idempotency**: Running `migrate` multiple times should have the same effect as running it once. Django handles this well, but custom `RunPython` operations need care.
*   **Testing**: Migrations *must* be tested locally and in staging environments before production deployment.
*   **Version Control**: Migration files **are code** and must be committed to version control (Git). Filenames should *not* be manually edited.
*   **Communication**: Teams need to communicate proactively about potentially conflicting schema changes, especially within the same app.
*   **Backup First**: Always ensure verified database backups are taken immediately before applying significant migrations in production.

## 3. Migration Workflow & Best Practices

1.  **Development Environment:**
    *   **Update Branch:** Ensure your feature branch is up-to-date with the main development branch (`git pull --rebase origin main` or similar). Resolve any code conflicts.
    *   **Make Model Changes:** Modify your Django models (`models.py` within the relevant `api/v1/app_name/` directory according to project structure).
    *   **Generate Migration:** Run `python manage.py makemigrations <app_label>` (e.g., `python manage.py makemigrations api.v1.base_models.organization`). **Always specify the app label**.
    *   **Review Generated File:** **CRITICAL STEP.** Carefully read the generated migration file (`XXXX_auto_....py`). Understand the `operations` list. Does it match your intent? Are there potential data loss warnings (e.g., removing a field)? Is the operation potentially slow or locking on large tables (e.g., adding a non-nullable field without a Django-level default, adding an index without `CONCURRENTLY`)?
    *   **Apply Locally:** Run `python manage.py migrate <app_label>` (or just `python manage.py migrate`) to apply the migration to your local PostgreSQL development database.
    *   **Test Locally:** Run relevant Pytest tests (`pytest path/to/app/tests/`) and manually test features related to the schema change.
    *   **Test Reversal (Recommended):** Run `python manage.py migrate <app_label> <previous_migration_number>` to test if the migration reverses cleanly. Then run `python manage.py migrate <app_label>` again to reapply.
    *   **Commit:** Add and commit **both** the `models.py` changes **and** the generated migration file(s) to Git in the *same atomic commit*. Write a clear commit message explaining the schema change.

2.  **Version Control (Git):**
    *   **Branching:** Perform schema changes on dedicated feature branches.
    *   **Pull/Rebase Frequently:** Keep feature branches updated with the main branch to catch potential migration conflicts early.
    *   **Migration Conflicts:** Occur when multiple developers generate migrations for the *same app* independently on different branches, leading to divergent migration histories (e.g., two different `0003_...` files).
        *   **Detection:** `migrate` will likely fail complaining about inconsistent history. `showmigrations` might show discrepancies. Git merge conflicts might occur in model files *before* migration generation reveals the deeper issue.
        *   **Resolution:** **COMMUNICATE!** Determine the correct sequence. Typically involves:
            1.  One developer rebases their branch onto the other (or onto the main branch after the first one is merged).
            2.  Delete the conflicting migration file(s) from the branch being rebased *before* running `makemigrations` again.
            3.  Resolve any model conflicts in `models.py`.
            4.  Run `python manage.py makemigrations <app_label>` **again** on the rebased branch. This should now generate a single new migration incorporating *both* sets of model changes relative to the now-common previous migration.
            5.  Test thoroughly.
        *   **Avoid:** Manually editing migration filenames, numbers, or `dependencies`. This is fragile and error-prone. Regenerating is usually safer.
        *   **Advanced:** `manage.py migrate --merge` exists but should be used with extreme caution and understanding.
    *   **Code Reviews:** Migration files **must** be included in Pull Requests and reviewed carefully for correctness, potential performance issues on large tables, data loss risks, and reversibility.

3.  **Staging Environment:**
    *   **Mirror Production:** Staging should ideally use the same PostgreSQL version and have a similar data structure (and representative data volume if possible) as production.
    *   **Deploy Code:** Deploy the feature branch or merged development branch containing the new migration(s).
    *   **Backup Staging DB (Optional):** Useful before testing complex or potentially destructive migrations.
    *   **Run Migrations:** Execute `python manage.py migrate`. Monitor execution time and check logs for errors.
    *   **Test Thoroughly:** Perform comprehensive functional and regression testing of features related to the schema change.

4.  **Production Deployment:**
    *   **Schedule Downtime (If Necessary):** Analyze the migration (`manage.py sqlmigrate <app_label> <migration_name>`) and assess potential locking behavior or long execution time. Schedule a maintenance window if needed, especially for operations like adding non-concurrent indexes or altering large tables. Communicate downtime to stakeholders.
    *   **BACKUP PRODUCTION DATABASE:** **Mandatory, non-negotiable step.** Ensure the backup is complete and verified *before* starting the migration process.
    *   **Deploy Code:** Deploy the new code version containing the migration files to production servers.
    *   **Run Migrations:** Execute `python manage.py migrate`. **Monitor application logs, database performance, and migration command output very closely.**
    *   **Verify:** Perform essential post-deployment checks (smoke tests) on application functionality related to the changes.
    *   **Rollback Plan:**
        *   **Immediate Failure:** If `migrate` fails critically, the primary rollback is **restoring the database from the pre-migration backup** and rolling back the code deployment.
        *   **Post-Migration Issues:** Reversing migrations in production using `migrate <app> <previous>` is **highly discouraged** for anything non-trivial due to potential data loss or inconsistent states, especially if new code relying on the migrated schema is already running. Prefer rolling forward with a fix or restoring from backup.

## 4. Handling Specific Migration Scenarios

*   **Adding Non-Nullable Fields (Large Tables):** Use the two-phase approach: 1) Add field as `null=True`, migrate. 2) Populate data (data migration/script), migrate. 3) Change field to `null=False`, migrate.
*   **Renaming Models/Fields:** Use `migrations.RenameModel` / `migrations.RenameField` operations generated by `makemigrations` (confirm when prompted) or added manually. Test carefully, especially if foreign keys are involved.
*   **Data Migrations (`migrations.RunPython`):**
    *   Use for data transformation, backfilling, etc.
    *   Use `apps.get_model()` to get historical model versions.
    *   Write separate `forward` and `reverse` functions. Make reversal safe (e.g., don't assume data deleted in forward pass can be perfectly recreated).
    *   Process large datasets in chunks using `.iterator()` to manage memory.
    *   Test data migrations thoroughly in staging with realistic data.
*   **Adding Indexes Concurrently (`db_index=True`, `Meta.indexes` on Large Tables):**
    *   Default `makemigrations` creates locking `CREATE INDEX`.
    *   **Solution:**
        1.  Generate the migration: `makemigrations`.
        2.  **Edit the migration file:** Replace `migrations.AddIndex(...)` with `migrations.AddIndex(..., concurrently=True)`.
        3.  Wrap this operation using `migrations.SeparateDatabaseAndState`: The `database_operations` list contains the concurrent index creation (which must run outside a transaction), and the `state_operations` list contains the standard `migrations.AddIndex` so Django's model state is updated correctly.
        ```python
        from django.db import migrations, models

        class Migration(migrations.Migration):
            atomic = False # Required for concurrent index creation

            dependencies = [...]

            operations = [
                migrations.SeparateDatabaseAndState(
                    state_operations=[
                        # Django model state update (no 'concurrently' here)
                        migrations.AddIndex(
                            model_name='mymodel',
                            index=models.Index(fields=['my_field'], name='myapp_mymod_my_fie_idx'),
                        ),
                    ],
                    database_operations=[
                        # Actual concurrent DB operation
                        migrations.RunSQL(
                            sql='CREATE INDEX CONCURRENTLY myapp_mymod_my_fie_idx ON myapp_mymodel (my_field);',
                            reverse_sql='DROP INDEX CONCURRENTLY IF EXISTS myapp_mymod_my_fie_idx;',
                            # Ensure atomic=False on the Migration class
                        ),
                        # Alternative using AddIndex with atomic=False (check Django version support)
                        # migrations.AddIndex(
                        #     model_name='mymodel',
                        #     index=models.Index(fields=['my_field'], name='myapp_mymod_my_fie_idx'),
                        #     concurrently=True,
                        # ),
                    ],
                ),
            ]
        ```
    *   Test this carefully, as it requires PostgreSQL and specific transactional handling. Consider the `django-add-index-concurrently` package for simplification.
*   **Complex Schema Changes:** Break down into multiple, smaller, sequential, and individually testable migrations.

## 5. Database Management & Maintenance (PostgreSQL Focus)

*   **Backup Strategy:** Defined previously. Regular, automated, tested logical (`pg_dump`) and/or physical (snapshots) backups with appropriate retention and PITR.
*   **Connection Pooling:** Use PgBouncer in production environments. Configure pool size appropriately based on application needs and database resources.
*   **Performance Monitoring:** Monitor PostgreSQL instance (CPU, RAM, IO, connections, locks), enable slow query logging (`log_min_duration_statement`), use `pg_stat_statements` extension.
*   **Index Maintenance:** Regularly run `ANALYZE` (often handled by autovacuum). Monitor index bloat and usage (`pgstattuple` extension, queries on `pg_stat_user_indexes`). Consider `REINDEX CONCURRENTLY` during maintenance windows for bloated indexes.
*   **Vacuuming:** Ensure autovacuum is enabled and properly tuned for application workload to manage table bloat and transaction ID wraparound. Monitor its activity.
*   **Version Upgrades:** Plan, test (in staging), and execute PostgreSQL major version upgrades carefully, following recommended procedures (e.g., `pg_upgrade`).

## 6. Tooling

*   **Django:** `manage.py makemigrations`, `migrate`, `showmigrations`, `sqlmigrate`.
*   **Git:** For version control of migration files.
*   **Database GUI:** pgAdmin, DBeaver, etc., for inspection.
*   **Connection Pooler:** PgBouncer.
*   **Backup:** `pg_dump`, `pg_restore`, Cloud Provider tools.
*   **(Optional):** `django-extensions` (`sqldiff`), `django-add-index-concurrently`.

## 7. Team Collaboration

*   **Communication:** Essential when multiple developers work on models within the same Django app. Announce planned schema changes.
*   **Branching Strategy:** Use feature branches for schema changes. Keep main branch clean.
*   **Conflict Resolution:** Follow defined procedures for resolving migration conflicts safely.
*   **Code Reviews:** Mandate review of migration files.
*   **Migration Squashing:** Consider `squashmigrations` periodically on stable apps after major releases to reduce the number of migration files, but test the squashed migration thoroughly.

--- END OF FILE migration_and_db_management_strategy.md ---
## Caching & Storage


### Redis Caching


## 2. Redis Strategy (Cache & Celery Broker)

**(Equivalent to a focused PRD for Redis setup and usage)**

### 2.1. Overview

*   **Purpose**: To define the setup and usage strategy for Redis as the primary backend for Django's caching framework and as the message broker for Celery task queues.
*   **Scope**: Choice of Redis, configuration within Django (`django-redis`), local setup, key usage patterns, and integration points.
*   **Chosen Technology**: **Redis** (Target Version: 6.x+). **`django-redis`** library for cache integration.

### 2.2. Core Requirements

*   **Fast In-Memory Cache**: Provide low-latency caching for frequently accessed data (permissions, configurations, API results).
*   **Reliable Message Broker**: Serve as a robust transport for Celery task messages between the Django application and Celery workers/beat.
*   **Support Required Features**: Provide necessary Redis commands/data structures used by `django-redis` and Celery.

### 2.3. Configuration Strategy (`config/settings/`, `core/redis/`)

*   Use Django's `settings.CACHES` dictionary, configured with `django_redis.cache.RedisCache` backend. Define multiple aliases (`default`, `permissions`, `api_responses`, etc.) potentially pointing to different Redis logical databases (DB numbers) or even instances if needed for isolation. Set default `TIMEOUT` per alias.
*   Configure `settings.CELERY_BROKER_URL` pointing to a specific Redis instance/database (e.g., `redis://[:password@]host:port/0`).
*   Configure `settings.CELERY_RESULT_BACKEND` (if needed) potentially also pointing to Redis.
*   Connection URLs/details **must** be loaded from environment variables.
*   The `core/redis/config.py` might contain helper functions for complex cache key generation or specific Redis interactions if needed beyond the standard cache API, but core connection setup is via settings.

### 2.4. Local Development Setup (`docker-compose.yml`)

*   Utilize the official `redis:<version>` Docker image in `docker-compose.yml`.
*   Expose the Redis port (e.g., 6379).
*   Persistence via Docker volume is optional for local dev cache/broker but can be useful.

### 2.5. Integration Points

*   **Caching**: Accessed via Django's cache framework (`from django.core.cache import caches; cache = caches['default']` or `from django.core.cache import cache`). Used by application code, RBAC permission checks, potentially DRF caching extensions.
*   **Celery Broker**: Configured via settings, used implicitly by Celery producer (e.g., `task.delay()`) and consumers (workers).
*   **Django Channels Layer (If used):** Potentially configured via `settings.CHANNEL_LAYERS` using `channels_redis.core.RedisChannelLayer`.

### 2.6. Security Considerations

*   Enable Redis password protection (`requirepass`) in production/staging, managed via secure environment variables.
*   Limit network access to the Redis server.
*   Use TLS if connecting over untrusted networks.

### 2.7. Monitoring Considerations

*   Monitor key Redis metrics: Memory usage (`used_memory_rss`, `maxmemory`), key count, connections (`connected_clients`), commands per second, latency, cache hit ratio (`keyspace_hits`/`keyspace_misses`), evictions/expirations. Use `redis-cli INFO` or external monitoring tools.

### 2.8. Backup & Recovery Strategy

*   **Cache:** Generally acceptable to lose cache data on restart. Configure Redis persistence (RDB snapshots/AOF) mainly for faster restarts, not critical data recovery.
*   **Broker:** For Celery, enabling Redis persistence (especially AOF - Append Only File) is recommended to minimize task loss if the broker restarts unexpectedly. Ensure backups of the AOF/RDB files if broker state recovery is critical.

### 2.9. Testing Considerations

*   Configure `settings.CACHES` in `settings/test.py` to use **`LocMemCache`** (`django.core.cache.backends.locmem.LocMemCache`) for most tests to avoid Redis dependency.
*   Celery tests using `CELERY_TASK_ALWAYS_EAGER=True` bypass the need for a running broker during testing.
*   For tests specifically targeting Redis features or complex cache invalidation, use `fakeredis` or integration tests requiring a running Redis instance.

### 2.10. Deployment Considerations

*   Ensure the Redis instance(s) exist and are accessible.
*   Configure application settings with correct connection details/passwords for the environment.
*   Consider Redis Sentinel or Cluster for high availability in production if required.

### File Storage

# File Storage Strategy (Local Primary, Cloud Compatible)

## 1. Overview

*   **Purpose**: To define the strategy for storing and serving user-uploaded files (`FileField`, `ImageField`) associated with ERP models, using the **local filesystem as the primary method** while ensuring **compatibility with cloud storage backends** (like AWS S3) for future scalability or specific deployment needs.
*   **Scope**: Configuration of Django's storage backend system, Django integration, security considerations for both local and potential cloud storage, local development setup, testing, and deployment considerations.
*   **Chosen Technology**:
    *   **Default/Development/Testing:** Django's built-in **`FileSystemStorage`**.
    *   **Production/Staging (Optional/Future):** Cloud Storage (AWS S3, GCS, Azure Blob) via **`django-storages`** (e.g., `storages.backends.s3boto3.S3Boto3Storage`). The system must work seamlessly with either backend based on configuration.

## 2. Core Requirements

*   **Reliable Storage**: Store uploaded files persistently.
*   **Django Integration**: Work seamlessly with Django's `FileField`, `ImageField`, and ORM.
*   **Secure Access**: Control access to files based on application permissions, preventing direct unauthorized access.
*   **Configuration Flexibility**: Allow switching between local filesystem storage and cloud storage purely through Django settings and environment variables without requiring application code changes.
*   **Scalability Foundation**: While starting local, the approach shouldn't preclude scaling to cloud storage later.

## 3. Configuration Strategy (`config/settings/`)

*   **`DEFAULT_FILE_STORAGE` Setting**: This setting controls the active storage backend.
    *   In `settings/base.py` or `settings/dev.py`: **Default to `django.core.files.storage.FileSystemStorage'`.**
        ```python
        # settings/base.py (or dev.py)
        DEFAULT_FILE_STORAGE = env('DJANGO_DEFAULT_FILE_STORAGE', default='django.core.files.storage.FileSystemStorage')
        ```
    *   In `settings/prod.py` / `settings/staging.py`: Override this setting using an environment variable if cloud storage is deployed for that environment.
        ```python
        # settings/prod.py
        DEFAULT_FILE_STORAGE = env('DJANGO_DEFAULT_FILE_STORAGE') # Must be set in prod env if using S3
        # Example value in prod .env: DJANGO_DEFAULT_FILE_STORAGE=storages.backends.s3boto3.S3Boto3Storage
        ```
*   **Local Storage Settings (`settings/base.py` or `dev.py`):**
    *   `MEDIA_URL = '/media/'` (URL prefix for serving files via Django dev server or dedicated web server).
    *   `MEDIA_ROOT = BASE_DIR / 'media'` (Filesystem path where files are stored locally). Load from `env('MEDIA_ROOT', default=...)` if customization needed.
*   **Cloud Storage Settings (`settings/prod.py` - Loaded via Env Vars):**
    *   Only required if `DEFAULT_FILE_STORAGE` is set to a cloud backend.
    *   Include `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`, `AWS_S3_CUSTOM_DOMAIN`, `AWS_DEFAULT_ACL = 'private'`, `AWS_S3_FILE_OVERWRITE = False`, `AWS_QUERYSTRING_AUTH = True`, etc. **All loaded from environment variables.**
*   **File Validation Settings (`settings/base.py`):**
    *   Define `MAX_UPLOAD_SIZE` (e.g., `10 * 1024 * 1024` for 10MB).
    *   Define `ALLOWED_MIME_TYPES` (list of strings). Load from environment if they need to be configurable per deployment.

## 4. Local Development Setup (`docker-compose.yml`)

*   **Default:** Use `FileSystemStorage`.
*   **Volume Mount:** Mount a local host directory (e.g., `./media/`) to the container's `MEDIA_ROOT` path using Docker Compose volumes to persist uploads locally.
    ```yaml
    # docker-compose.yml
    services:
      api:
        # ... other settings ...
        volumes:
          - .:/app
          - ./media:/app/media # Mount local media dir to container's MEDIA_ROOT
        environment:
          # Explicitly set FileSystemStorage for local dev via .env is also an option
          # DJANGO_DEFAULT_FILE_STORAGE: 'django.core.files.storage.FileSystemStorage'
          MEDIA_ROOT: /app/media
          MEDIA_URL: /media/
          # ... other env vars ...
    ```
*   **`.gitignore`:** Add `media/` to `.gitignore`.
*   **(Optional) S3 Compatibility:** Include a MinIO service in `docker-compose.yml` for developers who want to test S3 compatibility locally by changing their `.env` file to point `DEFAULT_FILE_STORAGE` to S3 and configuring S3 settings for MinIO.

## 5. Application Code Interaction

*   **Abstraction:** Code **must** interact with files via Django's storage abstraction layer:
    *   Model fields: `models.FileField`, `models.ImageField`.
    *   Accessing URL: Always use `instance.file.url`. This method correctly returns the local `/media/...` URL when using `FileSystemStorage` and a (potentially pre-signed) cloud URL when using `S3Boto3Storage` (if configured for query string auth).
    *   Direct Operations: Use `instance.file.save()`, `instance.file.delete()`, `instance.file.open()` or `default_storage` methods.
*   **Avoid Backend Specific Code:** Do not write code that directly imports or calls `boto3` or checks `isinstance(default_storage, S3Boto3Storage)` unless absolutely necessary for a specific, unavoidable feature (like generating upload forms with direct-to-S3 capability, which is advanced).

## 6. Security Considerations

*   **Local `FileSystemStorage`:**
    *   The Django development server (`runserver`) serves `/media/` files only if `DEBUG=True`.
    *   **Production (with Local Storage):** This is **NOT RECOMMENDED** for scalability or security if serving directly from Django. A dedicated web server (Nginx, Apache) **must** be configured to serve the `MEDIA_ROOT` directory. Access control must be carefully implemented at the web server level or by having Django views broker access (e.g., using `X-Accel-Redirect` with Nginx) which check permissions before serving the file. Direct filesystem access via `/media/` URLs is insecure without proper controls.
*   **Cloud Storage:**
    *   Configure buckets for **private** access.
    *   Rely on **pre-signed URLs** (`AWS_QUERYSTRING_AUTH = True`) generated via `instance.file.url` for secure, time-limited download access brokered by the application's permission checks.
*   **General:** Apply RBAC and Org Scoping checks within API views/serializers *before* granting access to file metadata or generating download URLs. Validate uploads (size, type). Consider virus scanning. Secure cloud credentials.

## 7. Monitoring Considerations

*   **Local Storage:** Monitor disk space usage on the server hosting `MEDIA_ROOT`. Monitor application logs for file operation errors.
*   **Cloud Storage:** Use cloud provider monitoring tools.

## 8. Backup & Recovery Strategy

*   **Local Storage:** The directory defined by `MEDIA_ROOT` **must** be included in the regular server backup strategy alongside the database.
*   **Cloud Storage:** Rely on provider durability. Enable versioning. Back up the **metadata database** (`FileStorage` model table) regularly.

## 9. Testing Considerations

*   Use `FileSystemStorage` configured with a **temporary directory** in `settings/test.py`. `pytest-django` or fixtures can manage creating/deleting this temp directory.
    ```python
    # settings/test.py
    import tempfile
    MEDIA_ROOT = tempfile.mkdtemp() # Creates a unique temp dir for test run
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    ```
*   Mock cloud storage using libraries like `moto` only for tests *specifically* verifying cloud integration aspects (e.g., signed URL generation nuances). Most tests should work against the `FileSystemStorage` mock.

## 10. Deployment Considerations

*   **Local Storage Deployment:**
    *   Ensure the `MEDIA_ROOT` directory exists and has correct write permissions for the application user.
    *   Configure Nginx/Apache (or other web server) to serve files from `MEDIA_ROOT` at the `/media/` URL path, **ideally with access control checks** (e.g., `internal` directive with `X-Accel-Redirect` handled by Django).
    *   Ensure backups include `MEDIA_ROOT`. Consider shared storage (NFS, EFS) if deploying multiple application instances that need access to the same `MEDIA_ROOT`.
*   **Cloud Storage Deployment:**
    *   Configure `DEFAULT_FILE_STORAGE` setting via environment variable.
    *   Configure all necessary cloud credentials and bucket settings via secure environment variables/secrets management.
    *   Configure bucket policies/ACLs and potentially CDN/CORS as needed.

--- END OF FILE file_storage_strategy.md ---
## Asynchronous Processing


### Celery Tasks

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