
## Updated: `product_implementation_steps.md` (Fully Integrated with Centralized RBAC)

# Product - Implementation Steps

## 1. Overview

**Model Name:**
`Product`

**Corresponding PRD:**
`product_prd.md` (Simplified version, assuming it aligns with model-level permissions)

**Depends On:**
`Timestamped`, `Auditable`, **`OrganizationScoped`** (Abstract Base Models - Done), `Organization` (Done), `Category` (Done), `UnitOfMeasure` (Done), `Status` (Done), `django-taggit` (Done).
**Crucially depends on Centralized RBAC System:**
*   `core.rbac.permissions.has_perm_in_org`
*   `core.rbac.drf_permissions.HasModelPermissionInOrg`
*   `core.rbac.utils.get_user_request_context`
*   `core.serializers.mixins.OrganizationScopedSerializerMixin`
*   `core.viewsets.mixins.OrganizationScopedViewSetMixin`

**Key Features:**
Central catalog item. Scoped by Organization. Tagging. CRUD via API secured by Org-Aware RBAC.

**Primary Location(s):**
`api/v1/features/products/`

## 2. Prerequisites

[ ] All prerequisite models/mixins (`Timestamped`, `Auditable`, `OrganizationScoped`, `Organization`, `Category`, `UnitOfMeasure`, `Status`) are implemented and migrated.
[ ] `django-taggit` is installed, configured, and migrated.
[ ] The `products` app structure exists and is in `INSTALLED_APPS`.
[ ] Factories for `Organization`, `Category`, `UnitOfMeasure`, `User`, `Group`, `OrganizationMembership` exist.
[ ] `ProductType` and `ProductStatus` choices are defined.
[ ] **Centralized RBAC components** (helper functions, DRF permission classes, serializer/viewset mixins) are implemented and tested.
[ ] Standard Django model permissions (`add_product`, `change_product`, `view_product`, `delete_product`) are generated for the `Product` model (will happen after model definition). These permissions need to be assigned to appropriate `Group`s (Roles) by an Administrator.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)** Write Unit Tests (`tests/unit/test_models.py`) verifying:
      *   `Product` creation with required fields.
      *   `unique_together` (`organization`, `sku`).
      *   Defaults, FKs (`limit_choices_to`), `tags`, `__str__`.
      *   **Inheritance of `OrganizationScoped` is present.**
      Run; expect failure.
  [ ] Define the `Product` class in `api/v1/features/products/models.py`.
  [ ] **Ensure it inherits `OrganizationScoped`** (in addition to `Timestamped`, `Auditable`).
      ```python
      # api/v1/features/products/models.py
      # ... imports ...
      from core.models import Timestamped, Auditable, OrganizationScoped # Ensure OrganizationScoped
      # ...

      class Product(OrganizationScoped, Timestamped, Auditable): # Add OrganizationScoped
          # ... (fields as defined in the original product_implementation_steps.md) ...

          class Meta:
              # ... (as before) ...
              permissions = [ # Add any custom model-level permissions here if needed
                  # ('can_publish_product', 'Can publish product'),
              ]
      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `ProductFactory` as before, ensuring the `organization` field is set (e.g., `organization = factory.SubFactory(OrganizationFactory)`).
  [ ] **(Test)** Write simple tests for `ProductFactory`.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Define `ProductAdmin` as before.
      *   The `organization` field will be present due to `OrganizationScoped`.
      *   **Note:** Django Admin, by default, won't enforce org-aware permissions strictly like the API will. Customizing `ModelAdmin.has_add_permission`, `has_change_permission`, `save_model`, and `get_queryset` would be needed for full admin-side enforcement, which is a separate task if required.
  [ ] **(Manual Test):** Verify Admin CRUD.

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations api.v1.features.products`.
  [ ] **Review migration:** Ensure `organization_id` FK is added.
  [ ] Run `python manage.py migrate` locally.

  ### 3.5 Serializer Definition (`serializers.py`)

  [ ] **(Test First - Validation/Representation)** Write Unit/Integration Tests for `ProductSerializer`.
      *   Test validation (unique constraints, FKs, `limit_choices_to`).
      *   Test representation (tags, nested reads).
      *   Test custom field/attribute handling.
      *   **Crucially, test context passing for `OrganizationScopedSerializerMixin`**:
          *   Mock a request with a user and selected organization context.
          *   Test `create` validation succeeds when target org matches context and fails otherwise (if mixin enforces this).
          *   Test `update` validation handles organization context correctly.
  [ ] Define `ProductSerializer` in `api/v1/features/products/serializers.py`.
  [ ] **Inherit from `OrganizationScopedSerializerMixin` and `TaggitSerializer`.**
      ```python
      # api/v1/features/products/serializers.py
      from rest_framework import serializers
      from taggit.serializers import TagListSerializerField, TaggitSerializer
      # Import the RBAC mixin
      from core.serializers.mixins import OrganizationScopedSerializerMixin
      from ..models import Product
      from api.v1.base_models.common.models import Category, UnitOfMeasure # For querysets

      class ProductSerializer(OrganizationScopedSerializerMixin, TaggitSerializer, serializers.ModelSerializer):
          tags = TagListSerializerField(required=False)
          category = serializers.PrimaryKeyRelatedField(
              queryset=Category.objects.filter(category_type='PRODUCT'),
              allow_null=True, required=False
          )
          base_uom = serializers.PrimaryKeyRelatedField(
              queryset=UnitOfMeasure.objects.all()
          )
          # 'organization' field is handled by OrganizationScopedSerializerMixin
          # It will typically be read-only or set automatically based on context.

          class Meta:
              model = Product
              fields = [
                  'id', 'name', 'sku', 'description', 'product_type',
                  'category', 'status', 'base_uom',
                  'is_inventory_tracked', 'is_purchasable', 'is_sellable',
                  'tags', 'attributes', 'custom_fields',
                  'organization', # This will be included by the mixin logic
                  'created_at', 'updated_at',
              ]
              # read_only_fields primarily handled by mixin and permission checks,
              # but core fields like 'id', 'created_at', 'updated_at' remain.
              # 'organization' might be read-only depending on mixin's create/update logic.
              read_only_fields = ('id', 'created_at', 'updated_at') # Organization usually too

          # validate_sku, validate_custom_fields as before, if needed
      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.6 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests checking `/api/v1/products/` URL existence, authentication.
  [ ] Define `ProductViewSet` in `api/v1/features/products/views.py`.
  [ ] **Inherit `OrganizationScopedViewSetMixin`.**
  [ ] **Set `permission_classes` to use `HasModelPermissionInOrg`.**
      ```python
      # api/v1/features/products/views.py
      from rest_framework import viewsets, permissions
      # Import RBAC components
      from core.viewsets.mixins import OrganizationScopedViewSetMixin
      from core.rbac.drf_permissions import HasModelPermissionInOrg
      from ..models import Product
      from ..serializers import ProductSerializer
      # Import filters

      class ProductViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
          serializer_class = ProductSerializer
          # queryset is automatically filtered by OrganizationScopedViewSetMixin.get_queryset()
          queryset = Product.objects.select_related(
              'organization', 'category', 'base_uom' # organization already selected by mixin
          ).prefetch_related('tags').all()

          # Permissions handled by HasModelPermissionInOrg
          permission_classes = [permissions.IsAuthenticated, HasModelPermissionInOrg]

          # filter_backends, filterset_class, search_fields, ordering_fields as before
          # The perform_create method from OrganizationScopedViewSetMixin will be used.
          # It should call has_perm_in_org('add_product', target_org).
      ```
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.7 URL Routing (`urls.py`)

  [ ] Create `api/v1/features/products/urls.py`. Register `ProductViewSet` with router.
  [ ] Include `products.urls` in `api/v1/features/urls.py`.
  [ ] **(Test):** Rerun basic API tests.

  ### 3.8 API Endpoint Testing (CRUD & Features) (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests covering:
      *   **LIST:**
          *   Verify user only sees products from organizations they are a member of (via `OrganizationScopedViewSetMixin.get_queryset`).
          *   Verify user needs `products.view_product` permission *in their selected organization context* to list products (via `HasModelPermissionInOrg.has_permission`).
      *   **CREATE:**
          *   Verify user needs `products.add_product` permission *in their selected organization context* (or the org specified in request if allowed) to create a product (via `HasModelPermissionInOrg.has_permission` and the check in `OrganizationScopedViewSetMixin.perform_create`).
          *   Verify product is created in the correct organization.
      *   **RETRIEVE:**
          *   Verify user can only retrieve a product if it's in an organization they are a member of.
          *   Verify user needs `products.view_product` permission *in the product's organization* (via `HasModelPermissionInOrg.has_object_permission`).
      *   **UPDATE (PUT/PATCH):**
          *   Verify user needs `products.change_product` permission *in the product's organization*.
      *   **DELETE:**
          *   Verify user needs `products.delete_product` permission *in the product's organization*.
      *   Test all other standard aspects: validation, filters, tags, custom_fields, attributes.
  [ ] Implement/Refine ViewSet, Serializer (if needed), and any supporting RBAC utility functions based on tests.
  [ ] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/features/products`). Focus on ViewSet and Serializer interactions with RBAC.
[ ] Manually test API endpoints with different users assigned to different organizations and roles, using Postman or a similar client, and explicitly setting the `X-ORGANIZATION-ID` header if your `get_current_selected_organization` relies on it.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request.
[ ] Update API documentation, clearly stating the Org-Aware permission requirements for each action.
[ ] Plan implementation for related features (Pricing, Inventory, Variants, Bundles), ensuring they also integrate with the Org-Aware RBAC system.

---

This updated plan for `Product` explicitly integrates the pre-defined centralized RBAC components. The key changes are:

*   **Model:** Inherits `OrganizationScoped`.
*   **Serializer:** Inherits `OrganizationScopedSerializerMixin`.
*   **ViewSet:** Inherits `OrganizationScopedViewSetMixin` and uses `permission_classes = [permissions.IsAuthenticated, HasModelPermissionInOrg]`. The `perform_create` from the mixin will now correctly use the real `has_perm_in_org` function.
*   **Testing:** Heavily emphasizes testing the Org-Aware permission checks for all CRUD operations.