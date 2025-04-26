Okay, perfect. Let's start generating the detailed implementation steps using the template we finalized. We'll begin with the `Timestamped` Abstract Base Model, based on the `timestamped_prd.md` you just provided.

--- START OF FILE timestamped_implementation_steps.md ---

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

[ ] Ensure the `core` app (or chosen location for shared base models) exists within the project structure.
[ ] Verify `USE_TZ = True` is set in `config/settings/base.py`.

## 3. Implementation Steps (TDD Workflow)

  *(Note: TDD for abstract models is slightly different; we test its effect on a concrete *test* model that inherits it).*

  ### 3.1 Model Definition (`core/models.py`)

  [ ] **(Test First)**
      Create a test file `core/tests/test_timestamped_model.py`.
      Define a simple concrete model *within the test file* that inherits from `Timestamped` (which doesn't exist yet):
      ```python
      # core/tests/test_timestamped_model.py
      from django.db import models
      from django.utils import timezone
      from django.test import TestCase
      from core.models import Timestamped # Will fail initially

      class ConcreteTimestampedModel(Timestamped):
          name = models.CharField(max_length=100)

          class Meta:
              app_label = 'core' # Important for test runner model creation
      ```
      Write **Unit Test(s)** within a `TestCase` (or using `pytest.mark.django_db` if preferred, though DB not strictly needed just to check fields exist and populate):
      *   Test that creating an instance sets `created_at` and `updated_at` to a recent, timezone-aware datetime.
      *   Test that updating the instance changes `updated_at` but not `created_at`.
      ```python
      # core/tests/test_timestamped_model.py (continued)
      class TimestampedModelTests(TestCase):

          @classmethod
          def setUpClass(cls):
              # Ensure model is registered only for tests
              super().setUpClass()
              # A way to dynamically register the model for the test run
              # This part might need adjustment based on how test runner handles dynamic models
              # Alternative: Define ConcreteTimestampedModel in a real models.py temporarily for tests

          def test_timestamps_set_on_create(self):
              """Verify created_at and updated_at are set on creation."""
              now = timezone.now()
              instance = ConcreteTimestampedModel.objects.create(name="Test")
              self.assertIsNotNone(instance.created_at)
              self.assertTrue(instance.created_at.tzinfo is not None)
              self.assertAlmostEqual(instance.created_at, now, delta=timezone.timedelta(seconds=1))
              self.assertEqual(instance.created_at, instance.updated_at)

          def test_updated_at_changes_on_update(self):
              """Verify updated_at changes on save() but created_at doesn't."""
              instance = ConcreteTimestampedModel.objects.create(name="Test Update")
              created_timestamp = instance.created_at
              # Ensure some time passes
              import time; time.sleep(0.01)
              now_before_save = timezone.now()
              instance.name = "Updated Name"
              instance.save()
              # Re-fetch to ensure DB value is checked if using DB tests
              instance.refresh_from_db()

              self.assertEqual(instance.created_at, created_timestamp) # Should not change
              self.assertNotEqual(instance.updated_at, created_timestamp)
              self.assertTrue(instance.updated_at > created_timestamp)
              self.assertTrue(instance.updated_at.tzinfo is not None)
              self.assertAlmostEqual(instance.updated_at, now_before_save, delta=timezone.timedelta(seconds=1))

      ```
      Run `pytest core/tests/test_timestamped_model.py`; expect `ImportError` or `AttributeError` because `Timestamped` doesn't exist, or test failures if it exists but is wrong. **(Red)**

  [ ] Define the `Timestamped` abstract base model class in `core/models.py`:
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
  [ ] Ensure the `core` app is in `INSTALLED_APPS` in `config/settings/base.py`.
  [ ] Run the tests again (`pytest core/tests/test_timestamped_model.py`). They should now pass. **(Green)**
  [ ] Refactor the model code (unlikely needed for this simple model) or test code for clarity. Ensure tests still pass. **(Refactor)**

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Not applicable. No factory needed for an abstract base model itself. Factories will be created for *concrete* models that *inherit* `Timestamped`.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Not applicable. Abstract base models cannot be registered with the Django Admin. Admin configuration will happen on concrete inheriting models.

  ### 3.4 Migrations

  [ ] Not applicable directly. Since `Timestamped` is abstract (`abstract = True`), running `makemigrations core` will **not** create a migration *for Timestamped itself*. Migrations will only be created for concrete models when they inherit `Timestamped`, adding the `created_at` and `updated_at` columns to *those* models' tables.

  ### 3.5 Serializer Definition (`serializers.py`)

  [ ] Not applicable. Serializers are defined for concrete models. When serializing a model inheriting `Timestamped`, the serializer will typically include:
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

  [ ] Not applicable. ViewSets are defined for concrete models.

  ### 3.7 URL Routing (`urls.py`)

  [ ] Not applicable.

  ### 3.8 API Endpoint Testing (CRUD & Features) (`tests/api/test_endpoints.py`)

  [ ] Not applicable directly. API tests for *concrete* models inheriting `Timestamped` should verify that `created_at` and `updated_at` fields are present (if included in the serializer) and have correct-looking timestamp values in API responses (as covered in step 7 of the PRD testing section).

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`) to ensure the addition of the `core` app and the abstract model hasn't caused regressions.
[ ] Run linters (`flake8`) and formatters (`black`) on `core/models.py` and `core/tests/test_timestamped_model.py`.
[ ] Review the code for clarity and adherence to standards.

## 5. Follow-up Actions

[ ] Commit the changes (`core/models.py`, `core/tests/test_timestamped_model.py`, potentially updates to `settings.py`).
[ ] Create Pull Request for review.
[ ] Concrete models implemented subsequently can now inherit from `core.models.Timestamped`.

--- END OF FILE timestamped_implementation_steps.md ---