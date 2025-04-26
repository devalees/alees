
# Auditable Abstract Base Model - Product Requirements Document (PRD)

## 1. Overview

*   **Purpose**: To provide a standardized, automatic mechanism for tracking the user who created and the user who last modified model instances across the ERP system using an **Abstract Base Model**.
*   **Scope**: Definition and implementation of an **Abstract Base Model** that adds `created_by` and `updated_by` foreign key fields to inheriting models.
*   **Target Users**: System (automatically populating fields), Developers (inheriting the abstract model), Audit Log system (referencing these fields).

## 2. Business Requirements

*   **Accountability**: Know which user initially created any given record.
*   **Change Tracking**: Know which user last modified any given record.
*   **Consistency**: Ensure a uniform way of tracking basic user attribution across all relevant models.
*   **Foundation for Auditing**: Provide essential user context for more detailed audit logs.

## 3. Functional Requirements

### 3.1 Abstract Base Model Definition (`Auditable`)
*   **Implementation**: Defined as a Django **Abstract Base Model** (inherits from `models.Model` and includes `class Meta: abstract = True`).
*   **Location**: Defined in a shared location (e.g., `core/models.py` or `common/models.py`).
*   **Dependencies**: Requires the `User` model (`settings.AUTH_USER_MODEL`) to be defined.
*   **Fields**:
    *   `created_by`: (`models.ForeignKey`)
        *   Links to `settings.AUTH_USER_MODEL`.
        *   Set automatically when the record is first created to the user performing the action.
        *   Should not be editable after creation.
        *   `related_name`: Use `"+"` to avoid creating a reverse relation from User back to every auditable model, or use a pattern like `created_%(app_label)s_%(class)s_set`. `related_name="+"` is common for purely tracking fields.
        *   `on_delete=models.SET_NULL`: **Crucial**. If the creating user is deleted, we want to keep the record but set the `created_by` field to NULL, preserving the historical fact that *someone* created it without breaking referential integrity.
        *   `null=True`, `blank=True`: Necessary to allow `SET_NULL`. Also allows creation by system processes where no user is logged in (though ideally, a dedicated 'system' user is used).
        *   `editable=False`: Prevent modification via standard forms/admin.
    *   `updated_by`: (`models.ForeignKey`)
        *   Links to `settings.AUTH_USER_MODEL`.
        *   Set automatically every time the record is saved to the user performing the action.
        *   `related_name="+"`.
        *   `on_delete=models.SET_NULL`.
        *   `null=True`, `blank=True`.
        *   `editable=False`.
*   **Automation**: Requires logic (typically via overriding model `save()` method or potentially using signals, though `save()` override is common for this) to automatically populate these fields based on the currently authenticated user. This logic needs access to the user performing the request/action.

### 3.2 Model Inheritance
*   All concrete models requiring user tracking *must* inherit from this `Auditable` **Abstract Base Model**.
*   Example Inheritance: `class MyModel(Timestamped, Auditable): ...` (Often used together).
*   Target Models: `Organization`, `Product`, `Contact`, `Address`, `Invoice`, etc.

### 3.3 Data Population (Automatic)
*   **Challenge:** Unlike `auto_now*` for timestamps, Django doesn't have built-in `auto_set_user` fields. This requires custom implementation.
*   **Recommended Implementation:**
    1.  Use middleware (e.g., `django-crum` - Current Request User Middleware) or thread-local storage to make the current `request.user` globally accessible within the request cycle *in a safe way*.
    2.  Override the `save()` method in the `Auditable` abstract model (or potentially a common concrete base model that inherits the mixins).
    3.  In the overridden `save()`:
        *   Get the current user using the chosen method (e.g., `get_current_user()` from `django-crum`).
        *   If the user is authenticated:
            *   If `self.pk` is `None` (creating), set `self.created_by = current_user`.
            *   Always set `self.updated_by = current_user`.
        *   Call `super().save(*args, **kwargs)`.

## 4. Technical Requirements

### 4.1 Implementation
*   Define the `Auditable` abstract base model with the `ForeignKey` fields (`created_by`, `updated_by`) linked to `settings.AUTH_USER_MODEL` using `on_delete=models.SET_NULL`.
*   Implement the mechanism (middleware + `save()` override recommended) to automatically populate these fields. Ensure this mechanism handles unauthenticated users or system processes gracefully (leaves fields NULL or uses a designated system user).

### 4.2 Database
*   Database foreign key constraints will be created linking to the User table.
*   Indexes on `created_by_id` and `updated_by_id` might be beneficial if frequently filtering by user, but likely not essential initially.

### 4.3 Performance
*   Getting the current user on every save adds minimal overhead if using an efficient middleware/thread-local approach like `django-crum`. Avoid complex lookups in the `save()` method.

### 4.4 Integration
*   Depends on `settings.AUTH_USER_MODEL`.
*   Requires integration with the request cycle (via middleware or similar) to identify the current user.

## 5. Non-Functional Requirements

*   **Reliability**: Automatic population must work consistently for all inheriting models and handle anonymous users correctly.
*   **Maintainability**: The abstract model and user-fetching logic should be simple.
*   **Consistency**: Provides a standard way to identify creators/updaters.

## 6. API/Serialization

*   When models inheriting `Auditable` are serialized, `created_by` and `updated_by` fields might be included (read-only) and potentially nested to show user details (e.g., username). Requires careful consideration of performance and data exposure. Often just the IDs are sufficient.

## 7. Testing Requirements

*   **Unit Tests**:
    *   Define a simple concrete test model inheriting `Auditable` (and `Timestamped`).
    *   **Requires mocking the current user:** Use tools like `override_settings` (if user is stored in settings context, less common), mock the middleware function (`mock.patch`), or set thread-local storage directly within the test setup.
    *   Test creating an instance with a mocked user: Verify `created_by` and `updated_by` are set to the mocked user.
    *   Test updating the instance with a *different* mocked user: Verify `created_by` remains the same, and `updated_by` changes to the new user.
    *   Test saving without an authenticated user (if applicable): Verify fields remain NULL or are set to a system user if that pattern is used.
*   **Integration Tests**:
    *   When creating/updating models via API endpoints with an authenticated user, verify `created_by` / `updated_by` are correctly populated (though often not directly exposed in API responses, check the database record).

## 8. Deployment Requirements

*   **Migrations**: Migrations will add the `created_by_id` and `updated_by_id` columns (with foreign key constraints) when concrete models inherit `Auditable`. Handle default values/nullability correctly if adding to existing models with data (similar to `Timestamped`).
*   **Middleware**: Ensure the chosen middleware (like `django-crum`) for tracking the current user is added to `settings.MIDDLEWARE`.

## 9. Maintenance Requirements

*   Minimal maintenance for the abstract model itself. Ensure the user-fetching mechanism remains reliable.

--- END OF FILE auditable_prd.md ---

This PRD now specifically defines the `Auditable` abstract base model for `created_by`/`updated_by` fields, including the crucial implementation detail about needing a mechanism (like middleware + save override) to automatically populate them. It slots correctly into Phase 1 of our implementation plan right after `User` and `Timestamped`.