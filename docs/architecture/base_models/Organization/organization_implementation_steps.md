# Organization - Implementation Steps

## 1. Overview

**Model Name:**
`Organization`

**Corresponding PRD:**
`organization_prd.md` (Revised Post-Prerequisites & RBAC Simplification)

**Depends On:**
`Timestamped` (Done), `Auditable` (Done), `OrganizationType` (Done), `Currency` (Done), `Contact` (Done - Initial Version), `Address` (Done). Requires libraries `django-mptt` and `django-taggit`.

**Key Features:**
Core ERP entity representing internal/external org units. Supports hierarchy (MPTT), tagging (Taggit), custom fields (JSONField), status, localization settings, links to Type, Contact, Address, Currency. Foundation for `OrganizationScoped`.

**Primary Location(s):**
`api/v1/base_models/organization/`

## 2. Prerequisites

[x] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `OrganizationType`, `Currency`, `Contact`, `Address`) are implemented and migrated.
[x] Ensure the `organization` app structure exists (`api/v1/base_models/organization/`). Add `'api.v1.base_models.organization'` to `INSTALLED_APPS`.
[x] Install required libraries: `pip install django-mptt django-taggit`.
[x] Add `'mptt'` and `'taggit'` to `INSTALLED_APPS` in `config/settings/base.py`. Run `python manage.py migrate taggit` if needed.
[x] Ensure `factory-boy` is set up. Factories for `OrganizationType`, `Currency`, `Contact`, `Address`, and `User` exist.

**Note**: All prerequisites are now in place. The next step is to run the taggit migration if it hasn't been run yet:
```bash
python manage.py migrate taggit
```

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [x] **(Test First)** Write **Unit Test(s)** verifying model structure, constraints, defaults, FKs, MPTT fields, `tags`, `__str__`, inheritance.
  [x] Define the `Organization` class in `api/v1/base_models/organization/models.py` (as shown in previous example, using correct FKs to existing models like `Contact`, `Address`, `Currency`, `OrganizationType`).
  [x] Add required inheritance: `Timestamped`, `Auditable`, `MPTTModel`.
  [ ] Run tests; expect pass. Refactor model code if needed.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `OrganizationFactory` in `api/v1/base_models/organization/tests/factories.py` (as shown previously, ensuring `SubFactory` calls point to existing factories like `ContactFactory`, `AddressFactory`, etc.).
  [ ] **(Test)** Write tests ensuring `OrganizationFactory` creates valid instances and links related factories correctly. Test hierarchy creation.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Create/Update `api/v1/base_models/organization/admin.py`.
  [ ] Define `OrganizationAdmin` using `DraggableMPTTAdmin`. Use `raw_id_fields` for FKs (Contact, Address, Currency, OrgType, Parent).
  [ ] **(Manual Test):** Verify Admin operations, hierarchy management, related field selection.

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations api.v1.base_models.organization`.
  [ ] **Review generated migration file carefully.** Check MPTT setup, FKs, unique constraints, indexes.
  [ ] Run `python manage.py migrate` locally.
  [ ] Run `python manage.py rebuild_organization` (MPTT command) if needed.

  ### 3.5 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write Tests for `OrganizationSerializer`. Test validation (unique code), representation (fields, tags, maybe nested reads), custom/metadata field handling. **No need to test field-level permissions.**
  [ ] Create `api/v1/base_models/organization/serializers.py`.
  [ ] Define `OrganizationSerializer`. Use `TaggitSerializer`. Handle FKs with `PrimaryKeyRelatedField` for writing (using correct querysets like `Contact.objects.all()`, `Address.objects.all()` which are now available). Optionally add nested serializers for reading.
  [ ] Implement `validate_code` uniqueness check, `validate_custom_fields` if needed.
  [ ] Run tests; expect pass. Refactor.

  ### 3.6 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests checking `/api/v1/organizations/` URL, authentication. Test basic **model-level permission** checking setup (e.g., requiring `IsAuthenticated` initially).
  [ ] Create `api/v1/base_models/organization/views.py`. Define `OrganizationViewSet`. Select/Prefetch related fields. Add filtering/search/ordering. Add MPTT actions. Ensure standard `permission_classes` are set (e.g., `[permissions.IsAuthenticated]`). Org-Aware RBAC checks will be enforced later via mixin or decorator if needed per object.
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.7 URL Routing (`urls.py`)

  [ ] Create `api/v1/base_models/organization/urls.py`. Import `OrganizationViewSet`. Register with router.
  [ ] Include `organization.urls` in `api/v1/base_models/urls.py`.
  [ ] **(Test):** Rerun basic API tests; expect 2xx/4xx codes.

  ### 3.8 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests for `/api/v1/organizations/` CRUD & Features.
      *   LIST (with filters for type, status, parent, tags). **(Org Scoping tests added later)**.
      *   CREATE (valid/invalid, check FK links). Test **model-level** permissions (e.g., user needs `organization.add_organization` globally for now, Org-Aware checks added later).
      *   RETRIEVE (check **model-level** `view_organization` permission).
      *   UPDATE/PATCH (check **model-level** `change_organization` permission).
      *   DELETE (check **model-level** `delete_organization` permission, check PROTECT constraints).
      *   Test creating/updating organizations with `primary_contact`, `primary_address`, and `currency` set to valid IDs and also set to `null` to verify nullability.
      *   Hierarchy actions (`/descendants/` etc.).
      *   Saving/Validating `metadata`, `custom_fields`.
      *   Tag assignment/filtering.
      *   **Remove any tests checking for field-level permission responses.**
  [ ] Implement/Refine ViewSet methods and Serializer logic.
  [ ] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/base_models/organization`).
[ ] Manually test via API client and Django Admin (hierarchy, FK links, tags).
[ ] Review API documentation draft.

## 5. Follow-up Actions / Post-Requisites

[ ] Address TODOs.
[ ] **CRITICAL:** Immediately refactor `ContactSerializer` to use `PrimaryKeyRelatedField(queryset=Organization.objects.all(), ...)` now that `Organization` is implemented. Update tests for `Contact` API to reflect this.
[ ] Create Pull Request for Organization (and potentially the Contact refactor).
[ ] Update API documentation.
[ ] Ensure `OrganizationScoped` implementation uses this model.
[ ] Ensure `OrganizationMembership` uses this model.
