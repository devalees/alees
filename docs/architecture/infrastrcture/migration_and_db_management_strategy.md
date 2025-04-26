
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