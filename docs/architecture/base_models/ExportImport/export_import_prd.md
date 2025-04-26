# Data Import/Export Framework - Product Requirements Document (PRD) - Revised (with PDF Export)

## 1. Overview

*   **Purpose**: To define the standard framework, tools, and patterns for providing robust, user-driven data import and export capabilities across various key models within the ERP system.
*   **Scope**: Selection of core libraries, definition of asynchronous processing requirements, design of a job tracking model, specification of standard API patterns for initiating jobs, support for standard data formats (**CSV, XLSX, PDF** for export), and general guidelines for implementing import/export logic for specific models.
*   **Implementation Strategy**:
    *   Utilize **`django-import-export`** library for defining resource mapping and handling CSV/XLSX formats.
    *   Integrate dedicated **PDF generation libraries** (e.g., ReportLab, WeasyPrint) for PDF export functionality (implementation details specific to each report/model).
    *   Utilize **Celery** for asynchronous execution of all non-trivial import/export jobs.
    *   Implement a **`DataJob`** model for tracking asynchronous job status and results.
    *   Develop standardized **API endpoint patterns** for initiating import/export jobs and retrieving results.
*   **Target Users**: Users needing bulk data entry/extraction or formatted reports, System Administrators, Data Migration Teams, Developers implementing specific model imports/exports.

## 2. Business Requirements

*   **Bulk Data Operations**: Enable users to efficiently export large sets of data from key ERP modules (Products, Contacts, Orders, etc.) into common data formats (CSV, Excel) and formatted documents (**PDF**).
*   **Bulk Data Entry**: Enable users to import data into key ERP modules from standard file formats (CSV, Excel).
*   **Formatted Reports Export**: Allow specific views or predefined reports to be exported as PDF documents.
*   **Data Exchange**: Facilitate data exchange with external systems or for offline analysis/reporting.
*   **User Control**: Allow authorized users to initiate, configure (e.g., apply filters for export), and monitor import/export jobs.
*   **Reliability & Error Handling**: Ensure large jobs run reliably in the background, with clear reporting of success, failure, and specific row-level errors during import.

## 3. Core Framework Components

### 3.1 Core Library (`django-import-export`)
*   **Adoption**: Foundation for defining data mappings and handling **CSV/XLSX** formats.
*   **`ModelResource`**: For each model enabled for CSV/XLSX import/export, a `resources.ModelResource` subclass defines mappings, relationship handling, validation, and transformation. *(Not directly used for PDF generation)*.

### 3.2 PDF Generation Libraries (To Be Integrated Later)
*   **Requirement**: For PDF exports, a suitable Python PDF generation library (e.g., **ReportLab**, **WeasyPrint** based on HTML/CSS templates, **xhtml2pdf**) must be chosen and integrated.
*   **Implementation**: Specific logic using the chosen library will be required for each type of PDF export (e.g., generating a PDF table for a product list, formatting an Invoice PDF).

### 3.3 Asynchronous Execution (Celery)
*   **Requirement**: All import and export operations initiated via API or potentially Admin actions that handle more than a small threshold of records or involve PDF generation **must** be executed asynchronously using Celery.
*   **Tasks**: Define generic Celery tasks for:
    *   `run_export_job(job_id)`: Takes a `DataJob` ID. Retrieves export parameters (including `format`).
        *   If format is CSV/XLSX, uses the relevant `ModelResource` to generate the file data.
        *   If format is PDF, invokes the appropriate PDF generation logic/template for the target data/report.
        *   Saves the resulting file using `FileStorage`, updates the `DataJob` status and `output_file` link.
    *   `run_import_job(job_id)`: Takes a `DataJob` ID, retrieves the `input_file` and relevant `ModelResource` (for CSV/XLSX), processes the file using the resource's import logic, tracks results, updates the `DataJob`.

### 3.4 `DataJob` Model Definition (for Job Tracking)
*   **Purpose**: Track the status and outcome of asynchronous import/export tasks.
*   **Inheritance**: Inherit `Timestamped`, `Auditable`, `OrganizationScoped`.
*   **Fields**:
    *   `job_type`: (CharField with choices: 'IMPORT', 'EXPORT')
    *   `status`: (CharField with choices: 'PENDING', 'QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', default='PENDING', db_index=True)
    *   `user`: (ForeignKey to `User`, on_delete=models.SET_NULL, null=True) Initiating user.
    *   `target_model_content_type`: (ForeignKey to `ContentType`, null=True, blank=True) The primary model being imported/exported (may be less relevant for complex PDF reports).
    *   `export_format`: (CharField, max_length=10, blank=True) Requested format ('CSV', 'XLSX', 'PDF'). Relevant for export jobs.
    *   `input_params`: (JSONField, null=True, blank=True) Parameters used (e.g., filters for export, import settings).
    *   `input_file`: (ForeignKey to `FileStorage`, on_delete=models.SET_NULL, null=True, blank=True) Reference to the uploaded file for import jobs.
    *   `output_file`: (ForeignKey to `FileStorage`, on_delete=models.SET_NULL, null=True, blank=True) Reference to the generated file for export jobs.
    *   `result_log`: (JSONField, null=True, blank=True) Stores summary results and potentially row errors for imports.
    *   `celery_task_id`: (CharField, max_length=255, null=True, blank=True, db_index=True) ID of the background Celery task.
*   **Meta**: `verbose_name`, `plural`, `ordering = ['-created_at']`.

## 4. Functional Requirements (Framework Level)

### 4.1 API Endpoint Patterns
*   **Initiate Export**:
    *   `POST /api/v1/{model_plural_name}/export/` (Or specific report endpoint)
    *   Request Body: Contains filter parameters, **`format` ('CSV', 'XLSX', 'PDF')**.
    *   Response: `202 Accepted`, returns the `job_id`.
*   **Initiate Import**:
    *   `POST /api/v1/{model_plural_name}/import/`
    *   Request Body: `multipart/form-data` file upload. Format implicitly CSV/XLSX based on endpoint/content-type. Import parameters.
    *   Response: `202 Accepted`, returns the `job_id`.
*   **Check Job Status / Get Results**:
    *   `GET /api/v1/data-jobs/{job_id}/`
    *   Response: Current `DataJob` record, including status, result_log, link to `output_file`.
*   **List Jobs**:
    *   `GET /api/v1/data-jobs/`
    *   Response: Paginated list of user's `DataJob` records.

### 4.2 Job Execution & Handling
*   API creates `DataJob`, queues Celery task.
*   Celery task (`run_export_job`) checks `export_format`:
    *   Uses `django-import-export` resource for CSV/XLSX.
    *   Uses specific PDF generation logic/library for PDF.
*   Celery task (`run_import_job`) uses `django-import-export` resource for CSV/XLSX.
*   Tasks update `DataJob` status, handle errors, link files.

### 4.3 Supported Formats
*   **Import:** CSV, XLSX.
*   **Export:** CSV, XLSX, **PDF**.

### 4.4 Validation (Import)
*   Leverage `django-import-export` resource validation for CSV/XLSX. Log errors to `DataJob.result_log`.

## 5. Technical Requirements

### 5.1 Libraries & Infrastructure
*   Requires `django-import-export`.
*   Requires **Celery** and message broker.
*   Requires `FileStorage` system.
*   Requires selected **PDF Generation Library** (e.g., ReportLab, WeasyPrint) to be installed when PDF export is implemented.

### 5.2 Resource Development
*   Developers create `ModelResource` classes for CSV/XLSX import/export per model.
*   Developers create specific PDF generation logic/templates for required PDF exports.

### 5.3 Security
*   Permissions (e.g., `can_export_product_csv`, `can_export_product_pdf`, `can_import_product`) checked by API endpoints.
*   Async tasks must respect Org Scoping.
*   Secure file handling (`FileStorage`, download URLs).

### 5.4 Performance
*   Async execution is key. Optimize DB queries for export. Handle large files/datasets. PDF generation can be resource-intensive.

### 5.5 Error Handling & Logging
*   Robust error handling in Celery tasks. Clear error reporting in `DataJob.result_log` (especially for imports). Job status updated on failure.

## 6. Non-Functional Requirements

*   Scalability (Celery workers, file storage), Reliability, Availability, Consistency, Usability (clear job status/results).

## 7. Success Metrics

*   High success rate for jobs. Accurate data/reports generated. Performant job execution. Clear error reporting. User satisfaction.

## 8. API Documentation Requirements

*   Document `DataJob` model/status.
*   Document specific export/import API endpoints per model, **including supported `format` values (CSV, XLSX, PDF)**. Detail required parameters/filters.
*   Document job status checking API.
*   Explain permission requirements.

## 9. Testing Requirements

*   Unit Tests (`ModelResource`, PDF generation logic, Celery task logic).
*   Integration Tests (Requires Celery, FileStorage):
    *   Test full API flow for CSV/XLSX export and import.
    *   Test full API flow for **PDF export** (mocking or using simple PDF generation).
    *   Verify `DataJob` status updates and results/file links.
    *   Test error handling and logging in `result_log`.
    *   Test permissions.
*   Performance Tests (large files, complex PDFs).

## 10. Deployment Requirements

*   Install `django-import-export`, Celery, broker, selected PDF library.
*   Configure `FileStorage`. Deploy Celery workers.
*   Migrations for `DataJob`.
*   Deploy `ModelResource` classes and PDF generation logic.

## 11. Maintenance Requirements

*   Monitor Celery, FileStorage, DB performance/usage.
*   Maintain `ModelResource` and PDF generation logic.
*   Manage job history/logs according to retention policies. Backups.

---