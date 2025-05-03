# Status - Implementation Steps

## 1. Overview

**Model Name:**
`Status`

**Corresponding PRD:**
`status_prd.md` (Simplified version with Custom Fields)

**Depends On:**
`Timestamped`, `Auditable` (Abstract Base Models)

**Key Features:**
Defines standardized status values (e.g., 'Active', 'Pending', 'Draft') used across different ERP models. Includes slug (PK), name, description, category, color hint, and custom fields. Serves as a reference/vocabulary.

**Primary Location(s):**
`api/v1/base_models/common/status/` (Assuming `common` app for shared entities)

## 2. Prerequisites

[x] Verify prerequisite models/mixins (`Timestamped`, `Auditable`) are implemented. *(Assumed complete)*
[x] Ensure the `common` app structure exists (`api/v1/base_models/common/status/`). *(Created)*
[x] Ensure `factory-boy` is set up. Basic User factory exists. *(Assumed complete)*

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [x] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `common`) verifying:
      *   A `Status` instance can be created with required fields (`slug`, `name`).
      *   `slug` is the primary key.
      *   Unique constraints (`slug`, `name`) are present.
      *   Optional fields (`description`, `category`, `color`) can be set.
      *   `custom_fields` defaults to an empty dict.
      *   `__str__` method returns the `name`.
      *   Inherited `Timestamped`/`Auditable` fields exist.
      Run; expect failure (`Status` doesn't exist).
  [x] Define the `Status` class in `api/v1/base_models/common/status/models.py`.
  [x] Add required inheritance: `Timestamped`, `Auditable`.
      ```python
      # api/v1/base_models/common/status/models.py
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from core.models import Timestamped, Auditable # Adjust import path

      class Status(Timestamped, Auditable):
          slug = models.SlugField(
              _("Slug"),
              max_length=50,
              primary_key=True, # Use slug as the stable identifier
              help_text=_("Unique machine-readable identifier (e.g., 'pending_approval').")
          )
          name = models.CharField(
              _("Name"),
              max_length=100,
              unique=True, # Human-readable name should also be unique
              db_index=True,
              help_text=_("Human-readable status name (e.g., 'Pending Approval').")
          )
          description = models.TextField(
              _("Description"),
              blank=True,
              help_text=_("Optional description of what this status represents.")
          )
          category = models.CharField(
              _("Category"),
              max_length=50,
              blank=True,
              db_index=True,
              help_text=_("Optional category for grouping statuses (e.g., 'General', 'Order Lifecycle').")
          )
          color = models.CharField(
              _("Color"),
              max_length=7, # e.g., #RRGGBB
              blank=True,
              help_text=_("Optional HEX color code for UI representation.")
          )
          # Consider adding is_active boolean if statuses can be retired
          # is_active = models.BooleanField(default=True, db_index=True)
          custom_fields = models.JSONField(
              _("Custom Fields"),
              default=dict,
              blank=True,
              help_text=_("Custom data associated with this status definition.")
          )

          class Meta:
              verbose_name = _("Status")
              verbose_name_plural = _("Statuses")
              ordering = ['category', 'name']

          def __str__(self):
              return self.name
      ```
  [x] Run tests; expect pass. Refactor model code if needed. *(Isolated tests passed after fixes)*

  ### 3.2 Factory Definition (`tests/factories.py`)

  [x] Define `StatusFactory` in `api/v1/base_models/common/status/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from ..models import Status

      class StatusFactory(DjangoModelFactory):
          class Meta:
              model = Status
              django_get_or_create = ('slug',) # Use slug for get_or_create

          slug = factory.Sequence(lambda n: f'status_{n}')
          name = factory.Sequence(lambda n: f'Status Name {n}')
          description = factory.Faker('sentence')
          category = factory.Iterator(['General', 'Order', 'User', None])
          color = factory.Faker('hex_color')
          custom_fields = {}
      ```
  [x] **(Test)** Write a simple test ensuring `StatusFactory` creates valid instances. *(Verified indirectly via other tests)*

  ### 3.3 Admin Registration (`admin.py`)

  [x] Create/Update `api/v1/base_models/common/status/admin.py`.
  [x] Define `StatusAdmin`:
      ```python
      from django.contrib import admin
      from .models import Status

      @admin.register(Status)
      class StatusAdmin(admin.ModelAdmin):
          list_display = ('slug', 'name', 'category', 'color', 'updated_at')
          search_fields = ('slug', 'name', 'description', 'category')
          list_filter = ('category',)
          prepopulated_fields = {'slug': ('name',)} # Auto-populate slug from name
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
          fieldsets = (
              (None, {'fields': ('slug', 'name', 'description')}),
              ('Categorization', {'fields': ('category', 'color')}),
              ('Custom Data', {'fields': ('custom_fields',)}),
              ('Audit Info', {'classes': ('collapse',), 'fields': readonly_fields}),
          )
      ```
  [ ] **(Manual Test):** Verify registration, CRUD operations, and slug prepopulation in Django Admin locally.

  ### 3.4 Initial Data Population (Migration)

  [x] Create a new **Data Migration** file: `python manage.py makemigrations --empty --name populate_initial_statuses api.v1.base_models.common`.
  [x] Edit the generated migration file (`..._populate_initial_statuses.py`). Add `RunPython` operations to load essential common statuses.
      ```python
      from django.db import migrations

      INITIAL_STATUSES = [
          # Slug, Name, Category (Optional), Description (Optional), Color (Optional)
          ('draft', 'Draft', 'General', 'Record is being drafted, not yet active.', '#AAAAAA'),
          ('active', 'Active', 'General', 'Record is active and in use.', '#4CAF50'),
          ('inactive', 'Inactive', 'General', 'Record is not currently active but may be reactivated.', '#FF9800'),
          ('archived', 'Archived', 'General', 'Record is archived and typically read-only.', '#9E9E9E'),
          ('pending', 'Pending', 'Process', 'Waiting for action or approval.', '#2196F3'),
          ('pending_approval', 'Pending Approval', 'Approval', 'Waiting for approval step.', '#2196F3'),
          ('approved', 'Approved', 'Approval', 'Record has been approved.', '#4CAF50'),
          ('rejected', 'Rejected', 'Approval', 'Record has been rejected.', '#F44336'),
          ('completed', 'Completed', 'Process', 'Process or task is finished.', '#00BCD4'),
          ('cancelled', 'Cancelled', 'Process', 'Process or task was cancelled.', '#795548'),
          # Add other common statuses as needed
      ]

      def populate_statuses(apps, schema_editor):
          Status = apps.get_model('common', 'Status') # Use app_label from apps.py
          db_alias = schema_editor.connection.alias

          statuses_to_add = []
          for slug, name, category, desc, color in INITIAL_STATUSES:
              statuses_to_add.append(
                  Status(slug=slug, name=name, category=category or '', description=desc or '', color=color or '')
              )
          Status.objects.using(db_alias).bulk_create(statuses_to_add, ignore_conflicts=True)
          print(f"\nPopulated/updated {len(statuses_to_add)} statuses.")

      def remove_statuses(apps, schema_editor):
          pass # Usually safe to leave statuses in place on reversal

      class Migration(migrations.Migration):
          dependencies = [
              ('common', '000X_auto_...'), # Depends on Status model creation migration
          ]
          operations = [
              migrations.RunPython(populate_statuses, reverse_code=remove_statuses),
          ]
      ```

  ### 3.5 Migrations (Apply Initial Model & Data)

  [x] Run `python manage.py makemigrations api.v1.base_models.common`.
  [x] **Review generated migration file(s) carefully.**
  [x] Run `python manage.py migrate` locally. Verify data loaded via Admin.

  ### 3.6 Serializer Definition (`serializers.py`)

  [x] **(Test First)** Write Unit/Integration Tests (`tests/unit/test_serializers.py`, etc.) for `StatusSerializer`. Test representation, custom field handling. Validation tests likely minimal as it's mostly read-only via API.
  [x] Define `StatusSerializer` in `api/v1/base_models/common/status/serializers.py`:
      ```python
      from rest_framework import serializers
      from ..models import Status

      class StatusSerializer(serializers.ModelSerializer):
          class Meta:
              model = Status
              fields = [
                  'slug',
                  'name',
                  'description',
                  'category',
                  'color',
                  'custom_fields',
                  # Include Timestamped/Auditable fields if needed by API consumers
              ]
              # Generally read-only from an API perspective
              read_only_fields = fields
      ```
  [ ] Implement `validate_custom_fields` if needed (unlikely for read-only).
  [x] Run tests; expect pass. Refactor. *(Isolated tests passed after fixes)*

  ### 3.7 API ViewSet Definition (`views.py`)

  [x] **(Test First)** Write basic API Tests (`tests/api/test_endpoints.py`) for `/api/v1/statuses/`. Test unauthenticated access (likely allowed for read).
  [x] Define `StatusViewSet` in `api/v1/base_models/common/status/views.py`:
      ```python
      from rest_framework import viewsets, permissions
      from rest_framework import filters # Use standard filters
      from ..models import Status
      from ..serializers import StatusSerializer

      class StatusViewSet(viewsets.ReadOnlyModelViewSet):
          """
          API endpoint allowing statuses to be viewed.
          Statuses are typically managed via the Admin interface or migrations.
          """
          queryset = Status.objects.all() # Maybe filter is_active=True if added
          serializer_class = StatusSerializer
          permission_classes = [permissions.AllowAny] # Or IsAuthenticatedOrReadOnly
          lookup_field = 'slug' # Use slug for retrieval
          filter_backends = [filters.SearchFilter, filters.OrderingFilter]
          search_fields = ['slug', 'name', 'description', 'category']
          ordering_fields = ['category', 'name', 'slug']
          pagination_class = None # List is usually short
      ```
  [x] Run basic tests; expect pass. Refactor. *(Isolated tests passed after fixes)*

  ### 3.8 URL Routing (`urls.py`)

  [x] Import `StatusViewSet` in `api/v1/base_models/common/status/urls.py`.
  [x] Register with router: `router.register(r'statuses', views.StatusViewSet)`.
  [x] **(Test):** Rerun basic API tests; expect 200 OK for listing/retrieving. *(Isolated tests passed after fixes)*

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [x] **(Test First - List/Retrieve)** Write tests for `GET /api/v1/statuses/` and `GET /api/v1/statuses/{slug}/`. Assert 200, check structure, verify initial statuses present. Test search filters.
  [x] Ensure ViewSet query/filtering works.
  [x] Run list/retrieve tests; expect pass. Refactor. *(Isolated tests passed after fixes)*
  [ ] *(CRUD tests not applicable for ReadOnlyModelViewSet)*.
  [ ] *(Test custom field saving/validation via API if management endpoints were added)*.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/base_models/common/status`).
[ ] Manually test via API client and Django Admin. Verify initial statuses exist.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Ensure other models use `CharField` with choices referencing these `Status.slug` values (or `ForeignKey` if that approach was chosen).

--- END OF FILE status_implementation_steps.md ---