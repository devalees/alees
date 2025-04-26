Okay, here are the implementation steps for the `OrganizationType` model, based on its PRD and using the TDD checklist format. This is a relatively simple reference data model.

--- START OF FILE organizationtype_implementation_steps.md ---

# OrganizationType - Implementation Steps

## 1. Overview

**Model Name:**
`OrganizationType`

**Corresponding PRD:**
`organization_type_prd.md`

**Depends On:**
`Timestamped`, `Auditable` (Abstract Base Models)

**Key Features:**
Defines the types or classifications for `Organization` entities (e.g., Company, Department, Customer). Provides a controlled vocabulary. Includes name and description.

**Primary Location(s):**
`api/v1/base_models/organization/` (Assuming it lives alongside the `Organization` model)

## 2. Prerequisites

[x] Verify prerequisite models/mixins (`Timestamped`, `Auditable`) are implemented.
[x] Ensure the `organization` app structure exists (`api/v1/base_models/organization/`).
[x] Ensure `factory-boy` is set up. Basic User factory exists.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [x] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `organization`) verifying:
      *   An `OrganizationType` instance can be created with a unique `name`.
      *   Saving duplicate names raises `IntegrityError`.
      *   The `description` field is optional.
      *   `__str__` method returns the `name`.
      *   Inherited `Timestamped`/`Auditable` fields exist.
      Run; expect failure (`OrganizationType` doesn't exist).
  [x] Define the `OrganizationType` class in `api/v1/base_models/organization/models.py`.
  [x] Add required inheritance: `Timestamped`, `Auditable`.
      ```python
      # api/v1/base_models/organization/models.py
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from core.models import Timestamped, Auditable # Adjust import path

      class OrganizationType(Timestamped, Auditable):
          # Consider using AutoField or UUIDField if name changes are possible
          # and name shouldn't be the logical key other models reference.
          # But using name as PK is simpler if names are stable identifiers.
          # Let's assume name is stable for now. Revisit if needed.
          # If not PK, add a slug or code field as PK.
          name = models.CharField(
              _("Name"),
              max_length=100,
              unique=True,
              db_index=True,
              primary_key=True, # Making name the PK simplifies lookups if stable
              help_text=_("Unique name for the organization type (e.g., Company, Department).")
          )
          description = models.TextField(
              _("Description"),
              blank=True,
              help_text=_("Optional description of this organization type.")
          )
          # is_internal = models.BooleanField(default=True) # Example future flag

          class Meta:
              verbose_name = _("Organization Type")
              verbose_name_plural = _("Organization Types")
              ordering = ['name']

          def __str__(self):
              return self.name

      # ... Organization model will be defined later in this file ...
      ```
      *(Note: Made `name` the primary key for simplicity, assuming names like 'Customer', 'Department' are stable identifiers. If frequent name changes are expected, use a separate AutoField/UUIDField PK and keep `name` as unique CharField).*
  [x] Run tests; expect pass. Refactor model code if needed.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [x] Define `OrganizationTypeFactory` in `api/v1/base_models/organization/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from ..models import OrganizationType

      class OrganizationTypeFactory(DjangoModelFactory):
          class Meta:
              model = OrganizationType
              # Use name as the lookup field since it's PK (or unique)
              django_get_or_create = ('name',)

          name = factory.Iterator(['Company', 'Department', 'Customer', 'Supplier', 'Branch'])
          description = factory.Faker('sentence')
      ```
  [x] **(Test)** Write a simple test ensuring `OrganizationTypeFactory` creates valid instances. Test `django_get_or_create` works.

  ### 3.3 Admin Registration (`admin.py`)

  [x] Create/Update `api/v1/base_models/organization/admin.py`.
  [x] Define `OrganizationTypeAdmin`:
      ```python
      from django.contrib import admin
      from .models import OrganizationType # Assuming OrganizationType in same models.py

      @admin.register(OrganizationType)
      class OrganizationTypeAdmin(admin.ModelAdmin):
          list_display = ('name', 'description', 'updated_at', 'updated_by')
          search_fields = ('name', 'description')
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
      ```
  [x] **(Manual Test):** Verify registration and basic CRUD in Django Admin locally.

  ### 3.4 Initial Data Population (Migration)

  [x] Create a new **Data Migration** file: `python manage.py makemigrations --empty --name populate_org_types api.v1.base_models.organization`.
  [x] Edit the generated migration file (`..._populate_org_types.py`). Add `RunPython` operations to load essential types.
      ```python
      from django.db import migrations

      INITIAL_ORG_TYPES = {
          # Name: Description
          'Company': 'Primary legal entity or top-level organization.',
          'Division': 'A major operational division within a company.',
          'Department': 'A functional department within a division or company.',
          'Team': 'A specific team within a department.',
          'Location/Branch': 'A physical office or branch location.',
          'Customer': 'An external organization that purchases goods/services.',
          'Supplier': 'An external organization that supplies goods/services.',
          'Partner': 'An external organization collaborated with.',
          'Vendor': 'Synonym for Supplier, or specific type.',
          # Add others as needed
      }

      def populate_organization_types(apps, schema_editor):
          OrganizationType = apps.get_model('organization', 'OrganizationType') # Use app_label from apps.py
          db_alias = schema_editor.connection.alias

          types_to_add = []
          for name, description in INITIAL_ORG_TYPES.items():
              types_to_add.append(
                  OrganizationType(name=name, description=description)
              )

          OrganizationType.objects.using(db_alias).bulk_create(types_to_add, ignore_conflicts=True)
          print(f"\nPopulated/updated {len(types_to_add)} organization types.")

      def remove_organization_types(apps, schema_editor):
          # Could delete specific types, but safer to often just pass in reverse
          pass

      class Migration(migrations.Migration):

          dependencies = [
              # Ensure this runs after the migration creating OrganizationType model
              ('organization', '000X_auto_...'),
          ]

          operations = [
              migrations.RunPython(populate_organization_types, reverse_code=remove_organization_types),
          ]
      ```

  ### 3.5 Migrations (Apply Initial Model & Data)

  [x] Run `python manage.py makemigrations api.v1.base_models.organization`.
  [x] **Review generated migration file(s) carefully.** (Should create `OrganizationType` table, then the data migration).
  [x] Run `python manage.py migrate` locally. Verify data loaded (e.g., via Admin).

  ### 3.6 Serializer Definition (`serializers.py`)

  [x] **(Test First - Representation)** Write Integration Tests (`tests/integration/test_serializers.py`) verifying `OrganizationTypeSerializer` output format.
  [x] Define `OrganizationTypeSerializer` in `api/v1/base_models/organization/serializers.py`:
      ```python
      from rest_framework import serializers
      from ..models import OrganizationType

      class OrganizationTypeSerializer(serializers.ModelSerializer):
          class Meta:
              model = OrganizationType
              fields = [
                  'name', # Or PK if not name
                  'description',
                  # Include Timestamped/Auditable fields if needed
              ]
              # Typically read-only for most API consumers
              read_only_fields = ['name', 'description']
      ```
  [x] Run tests; expect pass. Refactor.

  ### 3.7 API ViewSet Definition (`views.py`)

  [x] **(Test First - Permissions/Basic Structure)** Write basic API Tests (`tests/api/test_endpoints.py`) for `/api/v1/organization-types/`. Test unauthenticated/authenticated access (likely read-only allowed).
  [x] Define `OrganizationTypeViewSet` in `api/v1/base_models/organization/views.py`:
      ```python
      from rest_framework import viewsets, permissions, filters
      from django_filters.rest_framework import DjangoFilterBackend
      from .models import OrganizationType
      from .serializers import OrganizationTypeSerializer

      class OrganizationTypeViewSet(viewsets.ReadOnlyModelViewSet):
          """
          API endpoint that allows organization types to be viewed.
          Management is typically done via Admin interface.
          """
          queryset = OrganizationType.objects.all()
          serializer_class = OrganizationTypeSerializer
          permission_classes = [permissions.IsAuthenticatedOrReadOnly]
          search_fields = ['name', 'description']
          ordering_fields = ['name']
          ordering = ['name']  # Default ordering
          filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
          filterset_fields = ['name']  # Enable filtering by name
          lookup_field = 'name'  # Use name as the lookup field
      ```
  [x] Run basic structure/permission tests; expect pass. Refactor.

  ### 3.8 URL Routing (`urls.py`)

  [x] Import `OrganizationTypeViewSet` in `api/v1/base_models/organization/urls.py`.
  [x] Register the ViewSet with the router: `router.register(r'organization-types', views.OrganizationTypeViewSet)`.
  [x] Ensure `organization.urls` is included in `api/v1/base_models/urls.py`.
  [x] **(Test):** Rerun basic API tests; expect 200 OK for listing/retrieving.

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [x] **(Test First - List/Retrieve)** Write tests for `GET /api/v1/organization-types/` and `GET /api/v1/organization-types/{name}/`. Assert 200, check structure, verify initial types are present.
  [x] Ensure `queryset` and permissions are correct.
  [x] Run list/retrieve tests; expect pass. Refactor.
  [x] Implemented features:
      - Pagination with `results` in response
      - Ordering (both ascending and descending)
      - Filtering by name using DjangoFilterBackend
      - Detail view lookup by name
      - Read-only permissions
      - Search functionality
  [x] All tests passing with 100% coverage for the ViewSet.

## 4. Final Checks

[x] Run the *entire* test suite (`pytest`).
[x] Run linters (`flake8`) and formatters (`black`).
[x] Check code coverage:
   - Run pytest --cov=[app_path] (e.g., pytest --cov=api/v1/base_models/organization).
   - Review the coverage report (e.g., term-missing output).
   - Ensure coverage meets the project's agreed-upon threshold (e.g., >= 80-90%).
   - Analyze any uncovered lines, especially in critical logic sections, and add necessary tests.
[x] Manually test via API client and verify data/management in Django Admin.
[x] Review API documentation draft.

## 5. Follow-up Actions

[x] Address TODOs.
[x] Create Pull Request.
[x] Update API documentation.
[ ] Ensure `Organization` model uses `ForeignKey` to `OrganizationType`.

--- END OF FILE organizationtype_implementation_steps.md ---