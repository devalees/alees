

# Data Import/Export Framework - Implementation Steps

## 1. Overview

**Framework Name:**
Data Import/Export Framework

**Corresponding PRD:**
`export_import_framework_prd.md` (Final Refined v2)

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationScoped`, `User`, `Organization`, `FileStorage`, `ContentType`, Celery infrastructure (Workers + Beat), Redis (Broker), `django-import-export`, `tablib[xlsx]`, Advanced Filtering System (parser + backend). PDF generation library required later.

**Key Features:**
Establishes framework for async import (CSV/XLSX) & export (CSV/XLSX/PDF). Uses `DataJob` model for tracking. Leverages Advanced Filtering for export datasets. Provides a generic resource factory as fallback for basic cases, uses custom `ModelResource` for specifics. Handles row errors and unmapped column warnings during import.

**Primary Location(s):**
*   Models (`DataJob`): `data_jobs/models.py` (New app).
*   Celery Tasks: `data_jobs/tasks.py`.
*   Generic Resource Factory: `core/import_export_utils.py` (Example).
*   Custom Resources (`ModelResource`): In relevant feature app (e.g., `api/v1/features/products/resources.py`).
*   API Views/URLs: `/api/v1/data-jobs/` (in `data_jobs`), plus actions in specific model ViewSets.

## 2. Prerequisites

[ ] Verify all prerequisite models/mixins and systems (Celery, Redis, FileStorage, Advanced Filtering parser) are implemented/configured.
[ ] **Install Libraries:** `pip install django-import-export tablib[xlsx]`.
[ ] **Create new Django app:** `python manage.py startapp data_jobs`.
[ ] Add `'import_export'` and `'data_jobs'` to `INSTALLED_APPS`.
[ ] Ensure `factory-boy` setup. Factories for core models exist.
[ ] Define `JobType` and `JobStatus` choices (e.g., in `data_jobs/choices.py`).

## 3. Implementation Steps (TDD Workflow)

  *(Job Model -> Generic Resource Factory -> Celery Tasks -> API Integration -> Custom Resources)*

  ### 3.1 `DataJob` Model Definition (`data_jobs/models.py`)

  [ ] **(Test First)** Write Unit Tests (`data_jobs/tests/unit/test_models.py`) verifying: `DataJob` creation, fields (type, status, FKs, GFK target, JSON params/log, task ID), defaults, inheritance, `__str__`.
  [ ] Define the `DataJob` class in `data_jobs/models.py`. Inherit `Timestamped`, `Auditable`, `OrganizationScoped`. Include fields from PRD 3.4.
  [ ] Run tests; expect pass. Refactor.

  ### 3.2 Factory Definition (`data_jobs/tests/factories.py`)

  [ ] Define `DataJobFactory` in `data_jobs/tests/factories.py`. Handle FKs.
  [ ] **(Test)** Write simple tests ensuring factory creates valid instances.

  ### 3.3 Generic Resource Factory Utility (`core/import_export_utils.py`)

  [ ] **(Test First)** Write Unit Tests (`core/tests/unit/test_import_export_utils.py`) for `get_resource_class_for_model`:
      *   Test finding a *custom* resource defined in `app.resources`.
      *   Test generating a *generic* resource when no custom one exists.
      *   Test generic resource includes expected direct fields (and excludes relations/sensitive fields).
      *   Test generic resource handles basic FK ID import/export (optional).
      *   Test generic resource sets basic `Meta` options (`model`, `import_id_fields=['id']`).
      Run; expect failure.
  [ ] Create `core/import_export_utils.py`. Implement `get_resource_class_for_model(model_class)`:
      *   Use `importlib` or convention to look for `app_label.resources.ModelNameResource`.
      *   If found, return it.
      *   If not found, use introspection (`model_class._meta.get_fields()`) to identify simple, direct, non-sensitive fields and direct `_id` FK fields.
      *   Dynamically create a `ModelResource` subclass (`type(...)`) in memory using these fields and basic `Meta` options. Handle potential naming collisions.
      *   Return the dynamically created class.
  [ ] Run tests; expect pass. Refactor.

  ### 3.4 Celery Task Definitions (`data_jobs/tasks.py`)

  [ ] **(Test First - Export)** Write Unit Tests (`data_jobs/tests/unit/test_tasks.py`) for `run_export_job`.
      *   Mock `DataJob.objects.get/save`, `FileStorage.objects.create`/`file.save`, `get_resource_class_for_model`, the resource's `export()` method, the **Advanced Filtering parser**, PDF generator calls.
      *   Test finding/using custom vs generic resource.
      *   Test parsing filter params -> applying Q object to queryset mock.
      *   Test calling resource `export()` with filtered queryset.
      *   Test handling CSV/XLSX output via resource dataset.
      *   Test placeholder/call for PDF generation logic.
      *   Test saving output file to mock storage.
      *   Test `DataJob` status updates (RUNNING, COMPLETED, FAILED) and `output_file`/`result_log` population. Test error handling.
      Run; expect failure.
  [ ] Create `data_jobs/tasks.py`. Define `run_export_job(job_id)` Celery task:
      *   Fetch `DataJob`. Set status to RUNNING.
      *   Get `model_class` from `target_model_content_type`.
      *   Parse `input_params['filters']` using Advanced Filtering parser -> `q_object`.
      *   Build initial `queryset` for the model, apply org scope, apply `q_object`. Add relevant `select/prefetch_related`.
      *   Call `get_resource_class_for_model` to get the resource class. Instantiate `resource`.
      *   If `export_format` is CSV/XLSX: call `resource.export(queryset)`, get data bytes, get content type.
      *   If `export_format` is PDF: Call specific PDF generator function `generate_pdf(queryset, job.input_params)`, get data bytes, set content type. *(Implement generator later)*.
      *   Create `FileStorage` instance, save `ContentFile` with data bytes, link to `job.output_file`.
      *   Update `DataJob` to COMPLETED with result summary.
      *   Use `try...except...finally` to catch errors, update `DataJob` to FAILED with error message in `result_log`.
  [ ] Run export task tests; expect pass. Refactor.
  [ ] **(Test First - Import)** Write Unit Tests for `run_import_job`.
      *   Mock `DataJob`, `FileStorage` (`input_file.file.read`), `get_resource_class_for_model`, resource `import_data()`, Celery retries.
      *   Test finding/using custom vs generic resource.
      *   Test calling `resource.import_data()` (mock its return `Result` object with various totals/errors/skipped rows).
      *   Test processing the `Result` object to populate `DataJob.result_log` correctly, including row errors and **unmapped column warnings**.
      *   Test `DataJob` status updates (RUNNING, COMPLETED, FAILED). Test error handling.
      Run; expect failure.
  [ ] Define `run_import_job(job_id)` Celery task:
      *   Fetch `DataJob`. Set status to RUNNING.
      *   Get `input_file` content. Determine format (CSV/XLSX).
      *   Call `get_resource_class_for_model`. Instantiate `resource`.
      *   Load data into `tablib.Dataset`.
      *   **(Optional)** Check for unmapped headers by comparing `dataset.headers` with `resource.get_export_headers()` or resource fields; store warnings.
      *   Call `resource.import_data(dataset, dry_run=False, ...)`.
      *   Process `import_result` object: extract totals, row errors. Format into `job.result_log`. Add unmapped header warnings to log.
      *   Set `DataJob` status based on `import_result.has_errors()`.
      *   Use `try...except...finally` for robust error handling.
  [ ] Run import task tests; expect pass. Refactor.

  ### 3.5 Admin Registration (`data_jobs/admin.py`)

  [ ] Create `data_jobs/admin.py`. Define `DataJobAdmin`. Make fields read-only, provide links to files/related objects, display status nicely.
  [ ] **(Manual Test):** Verify Admin interface for monitoring jobs.

  ### 3.6 Migrations

  [ ] Run `python manage.py makemigrations data_jobs`.
  [ ] **Review generated migration file carefully.** Check `DataJob` model, FKs, indexes.
  [ ] Run `python manage.py migrate` locally.

  ### 3.7 API Integration (Views, Serializers, URLs)

  [ ] **(Test First - Job Status API)** Write API tests for `/api/v1/data-jobs/` (LIST) and `/api/v1/data-jobs/{id}/` (RETRIEVE). Test filtering by user (implicit), status, type. Test permissions (user sees own jobs). Verify `output_file` link/URL generation (requires `FileStorage` serializer/logic). Verify `result_log` structure.
  [ ] Define `DataJobSerializer` (read-only) in `data_jobs/serializers.py`. Include method field for `output_file_url`.
  [ ] Define `DataJobViewSet` (ReadOnlyModelViewSet) in `data_jobs/views.py`. Filter queryset by `request.user`. Add standard filtering. Apply permissions.
  [ ] Define URL routing for `DataJobViewSet`.
  [ ] Run job status API tests; expect pass. Refactor.
  [ ] **(Test First - Trigger APIs)** Write API tests for `@action` endpoints on model ViewSets (e.g., `POST /products/export/`, `POST /products/import/`).
      *   Mock Celery `task.delay()`.
      *   Test successful request -> Assert 202 Accepted, check response body has `job_id`. Verify `DataJob` created correctly in DB. Verify task queued with correct `job_id`. Test passing filters (export) or file upload (import).
      *   Test permission failures (user lacks `can_export_model` / `can_import_model`). Test validation errors (invalid format, missing file).
  [ ] Add `@action` methods (`export_data`, `import_data`) to relevant model ViewSets (e.g., `ProductViewSet`). Logic: Check permissions, create `DataJob`, queue Celery task, return 202 response. Parse filters from request for export params. Handle file upload for import params.
  [ ] Run trigger API tests; expect pass. Refactor action views.

  ### 3.8 Model Resource Implementation (`resources.py`)

  [ ] **(Optional - Initially)** Implement *custom* `ModelResource` subclasses (e.g., `ProductResource`) only for models identified as needing complex import/export logic immediately. Test these resources thoroughly.
  [ ] **(Ongoing)** Implement custom `ModelResource` classes incrementally as needed for other models.

  ### 3.9 PDF Generation Logic (Deferred)

  [ ] Implement specific PDF generation functions/classes when required.
  [ ] Update `run_export_job` task to call the correct generator. Add tests.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`), ensuring Celery tasks run eagerly or are correctly mocked. Test with both generic and custom resources (if any).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=data_jobs --cov=core/import_export_utils`). Review uncovered areas.
[ ] Manually test end-to-end: Trigger export (CSV/XLSX) with filters via API -> check job status -> download file. Upload CSV/XLSX -> trigger import -> check job status -> check `result_log` for successes, errors, warnings -> verify data in DB.
[ ] Review API documentation draft for job management and trigger endpoints.

## 5. Follow-up Actions

[ ] Address TODOs (PDF implementation, robust error details in result_log, advanced resource features).
[ ] Create Pull Request(s).
[ ] Update API documentation.
[ ] Implement custom `ModelResource` classes for key models as needed.

--- END OF FILE exportimport_implementation_steps.md ---