
# Data Import/Export Framework - Product Requirements Document (PRD) - Final Refined (v2)

## 1. Overview

*   **Purpose**: To define the standard framework, tools, and patterns for providing robust, user-driven data import and export capabilities across various key models within the ERP system.
*   **Scope**: Selection of core libraries, definition of asynchronous processing (Celery), design of a job tracking model (`DataJob`), specification of standard API patterns for initiating jobs, definition of a **generic resource factory** providing baseline import/export, guidelines for using **custom `ModelResource` classes**, support for standard data formats (**CSV, XLSX, PDF** for export), and refined error/warning handling for imports.
*   **Implementation Strategy**:
    *   Utilize **`django-import-export`** library for core logic and CSV/XLSX format handling via `ModelResource` classes (custom or generic).
    *   Integrate dedicated **PDF generation libraries** for PDF export.
    *   Utilize **Celery** for asynchronous job execution.
    *   Implement a **`DataJob`** model for tracking.
    *   Implement **API endpoints** for job initiation/monitoring.
    *   Leverage the **Advanced Filtering System's** JSON definition format for specifying export datasets.
    *   Implement a **Generic Resource Factory** providing baseline capabilities.
*   **Target Users**: Users needing bulk data operations/reports, Admins, Data Migration Teams, Developers.

## 2. Business Requirements

*   **Flexible Export**: Export specific data subsets based on complex filter criteria into CSV, XLSX, or PDF.
*   **Basic & Advanced Import**: Import data from CSV/XLSX. Provide automated basic import (direct fields, FK IDs) for most models. Enable robust, validated import with relationship lookups for key models via specific configurations (custom resources).
*   **Formatted Reports Export**: Allow specific views or predefined reports to be exported as PDF documents.
*   **Data Exchange**: Facilitate data transfer.
*   **User Control & Visibility**: Allow authorized users to initiate jobs, apply export filters, monitor progress, and review results/errors.
*   **Reliability & Error Handling**: Ensure jobs run reliably in the background, with clear reporting of success, failure, and specific row-level errors/warnings during import.

## 3. Core Framework Components

### 3.1 Core Library (`django-import-export`)
*   **Adoption**: Foundation for defining data mappings and handling CSV/XLSX formats via `ModelResource`.
*   **`ModelResource` (Custom)**: Developers **must** create specific `ModelResource` subclasses for models requiring:
    *   **Complex Import Logic:** Handling relationship lookups by non-PK fields (e.g., name, code), specific row validation logic, M2M field import, complex data transformations.
    *   **Custom Export Formatting:** Using `dehydrate_<field>` methods.
*   **`ModelResource` (Generic - Fallback)**: See 3.5.

### 3.2 PDF Generation Libraries (Integration)
*   Requires separate integration of libraries like ReportLab or WeasyPrint for PDF export tasks. Logic is specific per PDF report/export type.

### 3.3 Asynchronous Execution (Celery)
*   **Requirement**: All non-trivial jobs initiated via API **must** run asynchronously via Celery.
*   **Tasks**: `run_export_job(job_id)`, `run_import_job(job_id)`.

### 3.4 `DataJob` Model Definition (for Job Tracking)
*   **Purpose**: Track asynchronous import/export tasks.
*   **Inheritance**: `Timestamped`, `Auditable`, `OrganizationScoped`.
*   **Fields**:
    *   `job_type`: (Choices: 'IMPORT', 'EXPORT')
    *   `status`: (Choices: 'PENDING', 'QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', default='PENDING')
    *   `user`: (FK to User - from Auditable `created_by`)
    *   `organization`: (FK to Organization - from `OrganizationScoped`)
    *   `target_model_content_type`: (FK to `ContentType`, nullable)
    *   `export_format`: (CharField: 'CSV', 'XLSX', 'PDF', blank=True)
    *   `input_params`: (JSONField, nullable) Stores filters for export, import settings.
    *   `input_file`: (FK to `FileStorage`, nullable) For import jobs.
    *   `output_file`: (FK to `FileStorage`, nullable) For export jobs.
    *   `result_log`: (JSONField, nullable, default=dict) Stores summary results (row counts, errors, warnings).
    *   `celery_task_id`: (CharField, nullable, db_index=True).
*   **Meta**: `verbose_name`, `plural`, `ordering`, indexes.

### 3.5 Generic Resource Factory (`core/import_export_utils.py`)
*   **Requirement**: Implement `get_resource_class_for_model(model_class)` function:
    1.  Attempts to find/import a custom `ModelResource` (e.g., `app.resources.ModelResource`).
    2.  If none found, dynamically generates a basic `ModelResource`.
*   **Generic Resource Capabilities:**
    *   **Export:** Includes non-relational, non-sensitive fields. Optionally includes simple FK fields (exporting PK). Basic dehydration.
    *   **Import:**
        *   Maps columns to direct model fields or `fk_field_id` based on header match.
        *   Imports direct ForeignKey fields using provided **PKs** (checks existence).
        *   **Ignores** M2M fields, GFKs, and columns requiring relationship lookups by non-PK fields (e.g., `category_name`).
        *   Generates **row errors** if values for **required** direct model fields (`blank=False`) are missing/empty in the file.
        *   Generates **row errors** if values for **required** ForeignKey fields (`fk_field_id` column) are missing, invalid, or the referenced object doesn't exist.
        *   Calls model's `full_clean()` after populating direct/FK-by-ID fields. Rows failing model validation generate errors.
*   **Purpose**: Provide baseline import/export, focusing on direct field mapping and FKs by ID, without needing custom code for every model.

## 4. Functional Requirements (Framework Level)

### 4.1 API Endpoint Patterns
*   **Initiate Export**: `POST /api/v1/{model_plural_name}/export/` (Body: `{ "format": "...", "filters": { ... Advanced Filter JSON ... } }`). Returns `202 Accepted` with `job_id`.
*   **Initiate Import**: `POST /api/v1/{model_plural_name}/import/` (Body: `multipart/form-data` file + optional params). Returns `202 Accepted` with `job_id`.
*   **Job Status/Results**: `GET /api/v1/data-jobs/{job_id}/`.
*   **List Jobs**: `GET /api/v1/data-jobs/`.

### 4.2 Job Execution & Handling
*   API creates `DataJob`, queues Celery task.
*   `run_export_job` task: Parses filters, gets queryset, gets resource (custom or generic), generates file (CSV/XLSX via resource, PDF via custom logic), saves to `FileStorage`, updates `DataJob`.
*   `run_import_job` task: Gets file, gets resource (custom or generic), uses resource `import_data()`, handles results/errors, updates `DataJob` status and `result_log`.

### 4.3 Supported Formats
*   **Import:** CSV, XLSX.
*   **Export:** CSV, XLSX, PDF.

### 4.4 Validation & Error Handling (Import)
*   Validation performed by the chosen `ModelResource` (custom or generic).
*   **Row Errors:** Specific validation failures (required field missing, invalid FK ID, model `full_clean` fail) are logged per row in `DataJob.result_log['row_errors']`.
*   **Unmapped Columns:** Any columns in the import file header not used by the `ModelResource` are ignored. A **warning** listing these ignored columns **must** be added to `DataJob.result_log['summary']` or a similar key.
*   Job proceeds or fails based on `skip_errors` setting and severity of errors. Final status and summary counts updated in `DataJob`.

## 5. Technical Requirements

### 5.1 Libraries & Infrastructure
*   Requires `django-import-export`, `tablib[xlsx]`, Celery, Broker, `FileStorage`, PDF library (later). Requires Advanced Filtering parser logic for export.

### 5.2 Resource Development
*   Implement generic resource factory. Developers create custom `ModelResource` classes for advanced needs. Developers create specific PDF generators.

### 5.3 Security
*   API endpoints check specific import/export permissions. Async tasks respect Org Scoping. Secure file handling. Generic resource avoids sensitive fields by default.

### 5.4 Performance
*   Async execution. Optimize export queries. Optimize import batching (`use_transactions`). Handle large files. Efficient resource finding.

### 5.5 Error Handling & Logging
*   Robust Celery task error handling. Clear, structured logging of import row errors and unmapped column warnings in `DataJob.result_log`.

## 6. Non-Functional Requirements

*   Scalability, Reliability, Availability, Consistency, Usability (Job feedback).

## 7. Success Metrics

*   High job success rate. Accurate data/reports. Performant execution. Clear error/warning reporting. User satisfaction. Baseline import/export works for simple models without custom code.

## 8. API Documentation Requirements

*   Document `DataJob` model/status/`result_log` structure (including `row_errors` and `summary` for warnings).
*   Document export/import API endpoints per model: supported `format`s, `filters` JSON structure for export.
*   Document job status API. Explain permissions.

## 9. Testing Requirements

*   Unit Tests (Generic resource factory, Celery tasks - mocked, `ModelResource` classes).
*   Integration Tests (Requires Celery, FileStorage):
    *   Test full API flow for export/import (CSV/XLSX/PDF). Verify `DataJob` lifecycle and results/files.
    *   **Test generic import:** Use a model *without* a custom resource. Import file with direct fields, valid FK IDs, invalid FK IDs (for required/optional fields), missing required direct fields, and extra unmapped columns. Verify correct data import, expected row errors, and unmapped column warnings in `result_log`.
    *   Test import/export with custom resources.
    *   Test error handling scenarios. Test permissions.
*   Performance Tests (Large files).

## 10. Deployment Requirements

*   Install libraries. Deploy Celery. Configure FileStorage.
*   Migrations for `DataJob`. Deploy generic resource factory. Deploy initial custom `ModelResource` classes/PDF logic as needed.

## 11. Maintenance Requirements

*   Monitor Celery jobs & `DataJob` records/logs. Maintain resources/PDF logic. Manage job history/logs. Backups.

--- END OF FILE export_import_framework_prd.md ---