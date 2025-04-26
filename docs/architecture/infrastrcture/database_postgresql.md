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
