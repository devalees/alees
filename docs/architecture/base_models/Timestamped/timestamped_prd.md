# Timestamped Abstract Base Model - Product Requirements Document (PRD) - Simplified & Specified

## 1. Overview

*   **Purpose**: To provide a standardized, automatic mechanism for tracking the creation and last modification time of model instances across the ERP system using an **Abstract Base Model**.
*   **Scope**: Definition and implementation of an **Abstract Base Model** that adds `created_at` and `updated_at` timestamp fields to inheriting models.
*   **Target Users**: Developers (inheriting the abstract model), System (automatically populating fields).

## 2. Business Requirements

*   **Basic Audit Trail**: Know when any given record was initially created.
*   **Modification Tracking**: Know when any given record was last updated.
*   **Consistency**: Ensure a uniform way of tracking these basic timestamps across all relevant models.

## 3. Functional Requirements

### 3.1 Abstract Base Model Definition (`Timestamped`)
*   **Implementation**: Defined as a Django **Abstract Base Model** (inherits from `models.Model` and includes `class Meta: abstract = True`).
*   **Location**: Defined in a shared location (e.g., `core/models.py` or `common/models.py`).
*   **Fields**:
    *   `created_at`: (`models.DateTimeField`)
        *   Automatically set to the current date and time when the record is first created.
        *   Should not be editable after creation.
        *   Implementation Detail: Use `auto_now_add=True`.
    *   `updated_at`: (`models.DateTimeField`)
        *   Automatically set to the current date and time every time the record is saved (including creation).
        *   Implementation Detail: Use `auto_now=True`.
*   **Timezone Handling**:
    *   Timestamps must be timezone-aware.
    *   Project Requirement: Django's `USE_TZ = True` setting must be enabled in `settings.py`.
    *   Storage Detail: Timestamps will be stored in the database in UTC (standard Django behavior with `USE_TZ=True`).

### 3.2 Model Inheritance
*   All concrete models requiring basic creation/update timestamps *must* inherit from this `Timestamped` **Abstract Base Model**.
*   Example Inheritance: `class MyModel(Timestamped): ...`
*   Target Models: `Organization`, `OrganizationType`, `User`, `Product`, `Contact`, `Address`, etc.

### 3.3 Data Population
*   The `created_at` and `updated_at` fields must be populated automatically by Django's ORM during the `save()` process via the `auto_now_add` and `auto_now` options. No manual setting of these fields is required in standard application code.

## 4. Technical Requirements

### 4.1 Implementation
*   Use standard Django `DateTimeField` with `auto_now_add=True` and `auto_now=True` arguments within the `Timestamped` abstract base model definition.
*   Ensure `USE_TZ = True` is set in the project's `settings.py`.

### 4.2 Database
*   Database field types used by Django for `DateTimeField` when `USE_TZ=True` must correctly store timezone-aware timestamps (e.g., `TIMESTAMP WITH TIME ZONE` in PostgreSQL).
*   Consider adding database indexes to `created_at` and `updated_at` fields on the *concrete* model tables if they are frequently used for filtering or ordering large datasets, but this is not mandatory initially for the abstract model definition itself.

### 4.3 Performance
*   Negligible performance impact, as field population is handled efficiently by the ORM.

## 5. Non-Functional Requirements

*   **Reliability**: The automatic timestamp population must work reliably for all inheriting models.
*   **Maintainability**: The abstract base model should be simple and require minimal maintenance.
*   **Consistency**: Provides a consistent way to access creation/update times across different models inheriting it.

## 6. API/Serialization

*   When concrete models inheriting `Timestamped` are serialized (e.g., via DRF serializers), the `created_at` and `updated_at` fields should typically be included as read-only fields in the serializer definition for the concrete model.
*   API responses should ideally represent these timestamps in a standard format, preferably ISO 8601 with timezone information (e.g., `2023-10-27T10:30:00Z`). Timezone conversion for display is handled outside this model's scope (e.g., serializers, frontend).

## 7. Testing Requirements

*   **Unit Tests**:
    *   Define a simple concrete test model inheriting `Timestamped`.
    *   Create an instance of the test model. Verify `created_at` and `updated_at` are set and approximately equal after initial save.
    *   Update the instance and save again. Verify `created_at` remains unchanged and `updated_at` is updated.
    *   Verify the stored values are timezone-aware (`is_aware` is True).
*   **Integration Tests**:
    *   When creating/updating concrete models (like `Organization`) via API endpoints, verify the `created_at` and `updated_at` fields are present and correctly populated in the API response and database.

## 8. Deployment Requirements

*   **Migrations**: When a concrete model inherits `Timestamped` for the first time or the abstract model itself is added/changed, Django's `makemigrations` command will generate the necessary migration(s) to add the `created_at` and `updated_at` columns to the concrete model's table. Handle default values appropriately for existing rows if adding to models with data.
*   **Settings**: Ensure `USE_TZ = True` is active in all deployment environments.

## 9. Maintenance Requirements

*   Minimal maintenance expected for the abstract base model itself. Primarily relates to standard Django and database upkeep.
