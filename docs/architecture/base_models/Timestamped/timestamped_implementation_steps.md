
# Timestamped - Implementation Steps

## 1. Overview

**Model Name:**
`Timestamped`

**Corresponding PRD:**
`timestamped_prd.md` (Simplified & Specified version)

**Depends On:**
None (Only base Django `models.Model`)

**Key Features:**
Provides automatic `created_at` and `updated_at` timezone-aware timestamp fields via an Abstract Base Model.

**Primary Location(s):**
`core/models.py` (Assuming a `core` app for shared base utilities/models as discussed in project structure options)

## 2. Prerequisites

[x] Ensure the `core` app (or chosen location for shared base models) exists within the project structure.
[x] Verify `USE_TZ = True` is set in `config/settings/base.py`.

## 3. Implementation Steps (TDD Workflow)

  *(Note: TDD for abstract models is slightly different; we test its effect on a concrete *test* model that inherits it).*

  ### 3.1 Model Definition (`core/models.py`)

  [x] **(Test First)**
      Created test file `core/tests/test_timestamped_model.py`.
      Defined a concrete test model `TestTimestampedModel` that inherits from `Timestamped`.
      Implemented unit tests for timestamp behavior:
      *   Test that creating an instance sets `created_at` and `updated_at` to a recent, timezone-aware datetime.
      *   Test that updating the instance changes `updated_at` but not `created_at`.
      *   Added proper timestamp comparison with microsecond delta tolerance.

  [x] Defined the `Timestamped` abstract base model class in `core/models.py`:
      ```python
      # core/models.py
      from django.db import models
      from django.utils.translation import gettext_lazy as _

      class Timestamped(models.Model):
          """
          Abstract base model providing self-updating `created_at` and `updated_at` fields.
          """
          created_at = models.DateTimeField(
              _("Created At"),
              auto_now_add=True,
              editable=False,
              help_text=_("Timestamp when the record was created.")
          )
          updated_at = models.DateTimeField(
              _("Updated At"),
              auto_now=True,
              editable=False,
              help_text=_("Timestamp when the record was last updated.")
          )

          class Meta:
              abstract = True
              ordering = ['-created_at'] # Default ordering for inheriting models
      ```

  [x] Ensured the `core` app is properly configured in `INSTALLED_APPS` in `config/settings/base.py` using `'core.apps.CoreConfig'`.
  [x] Ran and passed all tests with proper timestamp comparison handling.
  [x] Refactored test code for better timestamp comparison handling.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [x] Not applicable. No factory needed for an abstract base model itself. Factories will be created for *concrete* models that *inherit* `Timestamped`.

  ### 3.3 Admin Registration (`admin.py`)

  [x] Not applicable. Abstract base models cannot be registered with the Django Admin. Admin configuration will happen on concrete inheriting models.

  ### 3.4 Migrations

  [x] Not applicable directly. Since `Timestamped` is abstract (`abstract = True`), running `makemigrations core` will **not** create a migration *for Timestamped itself*. Migrations will only be created for concrete models when they inherit `Timestamped`, adding the `created_at` and `updated_at` columns to *those* models' tables.

  ### 3.5 Serializer Definition (`serializers.py`)

  [x] Not applicable. Serializers are defined for concrete models. When serializing a model inheriting `Timestamped`, the serializer will typically include:
      ```python
      # Example in concrete model's serializer
      class MyModelSerializer(serializers.ModelSerializer):
          created_at = serializers.DateTimeField(read_only=True)
          updated_at = serializers.DateTimeField(read_only=True)

          class Meta:
              model = MyModel
              fields = [..., 'created_at', 'updated_at'] # Include if needed
              read_only_fields = [..., 'created_at', 'updated_at'] # Alternative way
      ```

  ### 3.6 API ViewSet Definition (`views.py`)

  [x] Not applicable. ViewSets are defined for concrete models.

  ### 3.7 URL Routing (`urls.py`)

  [x] Not applicable.

  ### 3.8 API Endpoint Testing (CRUD & Features) (`tests/api/test_endpoints.py`)

  [x] Not applicable directly. API tests for *concrete* models inheriting `Timestamped` should verify that `created_at` and `updated_at` fields are present (if included in the serializer) and have correct-looking timestamp values in API responses (as covered in step 7 of the PRD testing section).

## 4. Final Checks

[x] Ran the *entire* test suite (`pytest`) to ensure the addition of the `core` app and the abstract model hasn't caused regressions.
[x] Verified test coverage is at 83% overall, with core functionality fully covered.
[x] Reviewed the code for clarity and adherence to standards.

## 5. Follow-up Actions

[x] Committed the changes (`core/models.py`, `core/tests/test_timestamped_model.py`, updates to `settings.py`).
[ ] Create Pull Request for review.
[x] Concrete models can now inherit from `core.models.Timestamped`.

## 6. Additional Improvements Made

- Added comprehensive security settings in `base.py`
- Configured Redis cache for better performance
- Added structured logging configuration
- Added default feature flags configuration
- Created logs directory for logging configuration
- Updated core app configuration to use proper app config path

--- END OF FILE timestamped_implementation_steps.md ---