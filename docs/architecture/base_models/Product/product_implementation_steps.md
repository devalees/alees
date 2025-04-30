

# Product - Implementation Steps

## 1. Overview

**Model Name:**
`Product`

**Corresponding PRD:**
`product_prd.md` (Simplified version)

**Depends On:**
`Timestamped`, `Auditable`, `OrganizationScoped` (Abstract Base Models), `Organization`, `Category`, `UnitOfMeasure`, `Status` (model/choices), `django-taggit` library. Requires Custom Field Definition mechanism if used.

**Key Features:**
Central catalog item (good, service, etc.). Includes SKU, type, category, UoM, status, inventory tracking flag, basic attributes (JSON), custom fields (JSON). Scoped by Organization. Supports tagging.

**Primary Location(s):**
`api/v1/features/products/` (Assuming a dedicated `products` feature app/group within `features`, based on project structure examples)

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`, `OrganizationScoped`, `Organization`, `Category`, `UnitOfMeasure`, `Status`) are implemented and migrated.
[ ] Ensure `django-taggit` is installed and configured (`taggit` in `INSTALLED_APPS`, migrated).
[ ] Create the `products` app structure: `api/v1/features/products/`.
[ ] Add `'api.v1.features.products'` (adjust path) to `INSTALLED_APPS`.
[ ] Ensure `factory-boy` is set up. Factories for `Organization`, `Category`, `UnitOfMeasure`, `User` exist.
[ ] Define `ProductType` and `ProductStatus` choices (e.g., in `products/choices.py`, referencing `Status.slug` values for status).

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `products`) verifying:
      *   `Product` creation with required fields (`name`, `sku`, `organization`, `product_type`, `base_uom`).
      *   `unique_together` constraint (`organization`, `sku`) is enforced.
      *   Default values (`status`, `is_inventory_tracked`, `is_purchasable`, `is_sellable`, `attributes`, `custom_fields`) are set.
      *   FKs (`category`, `base_uom`, `organization`) work and respect `limit_choices_to` for category.
      *   `tags` manager exists and works.
      *   `__str__` method works.
      *   Inherited fields (`Timestamped`, `Auditable`, `OrganizationScoped`) exist.
      Run; expect failure (`Product` doesn't exist).
  [ ] Define the `Product` class in `api/v1/features/products/models.py`.
  [ ] Add required inheritance: `Timestamped`, `Auditable`, `OrganizationScoped`.
      ```python
      # api/v1/features/products/models.py
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from taggit.managers import TaggableManager

      # Assuming Abstract Base Models are in core
      from core.models import Timestamped, Auditable, OrganizationScoped
      # Assuming related models are in common base_models app
      from api.v1.base_models.common.models import Category, UnitOfMeasure # Adjust path
      # Import Status slugs if referencing them directly
      # from api.v1.base_models.common.models import Status

      # Define choices (or import from choices.py)
      class ProductType:
          PHYSICAL = 'PHYSICAL_GOOD'
          SERVICE = 'SERVICE'
          DIGITAL = 'DIGITAL'
          # ... add others ...
          CHOICES = [...]

      class ProductStatus: # Referencing Status slugs
          DRAFT = 'draft'
          ACTIVE = 'active'
          DISCONTINUED = 'discontinued'
          # ... add others matching Status model slugs ...
          CHOICES = [...] # Define choices tuple if needed for validation

      class Product(Timestamped, Auditable, OrganizationScoped):
          name = models.CharField(_("Name"), max_length=255, db_index=True)
          sku = models.CharField(_("SKU/Code"), max_length=100, db_index=True)
          description = models.TextField(_("Description"), blank=True)
          product_type = models.CharField(
              _("Product Type"), max_length=50, choices=ProductType.CHOICES, db_index=True
          )
          # Link to generic category, filtered by type
          category = models.ForeignKey(
              Category,
              verbose_name=_("Category"),
              related_name='products',
              on_delete=models.PROTECT,
              null=True, blank=True,
              limit_choices_to={'category_type': 'PRODUCT'} # Ensure correct category type
          )
          status = models.CharField(
              _("Status"), max_length=50, default=ProductStatus.DRAFT, db_index=True
              # choices=ProductStatus.CHOICES # Add choices for admin/serializer validation
          )
          base_uom = models.ForeignKey(
              UnitOfMeasure,
              verbose_name=_("Base Unit of Measure"),
              related_name='products_base',
              on_delete=models.PROTECT
          )
          is_inventory_tracked = models.BooleanField(_("Inventory Tracked?"), default=True)
          is_purchasable = models.BooleanField(_("Purchasable?"), default=True)
          is_sellable = models.BooleanField(_("Sellable?"), default=True)

          tags = TaggableManager(blank=True, verbose_name=_("Tags"))
          attributes = models.JSONField(
              _("Attributes"), default=dict, blank=True,
              help_text=_("Semi-structured attributes like color, size, dimensions if not using variants.")
          )
          custom_fields = models.JSONField(
              _("Custom Fields"), default=dict, blank=True
          )

          class Meta:
              verbose_name = _("Product")
              verbose_name_plural = _("Products")
              unique_together = (('organization', 'sku'),)
              ordering = ['name']
              indexes = [
                  models.Index(fields=['organization', 'sku']),
                  models.Index(fields=['organization', 'name']),
                  models.Index(fields=['status']),
                  models.Index(fields=['category']),
              ]

          def __str__(self):
              return f"{self.name} ({self.sku})"

      ```
  [ ] Run tests; expect pass. Refactor model code if needed.

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `ProductFactory` in `api/v1/features/products/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from ..models import Product, ProductType, ProductStatus
      # Import related factories
      from api.v1.base_models.organization.tests.factories import OrganizationFactory
      from api.v1.base_models.common.tests.factories import CategoryFactory, UnitOfMeasureFactory

      class ProductFactory(DjangoModelFactory):
          class Meta:
              model = Product
              # Avoid duplicate SKUs within the same org during test runs
              # django_get_or_create = ('organization', 'sku') # Careful if org changes

          name = factory.Sequence(lambda n: f'Product {n}')
          sku = factory.Sequence(lambda n: f'SKU-{n:05}')
          organization = factory.SubFactory(OrganizationFactory)
          product_type = factory.Iterator([choice[0] for choice in ProductType.CHOICES])
          # Ensure category has correct type
          category = factory.SubFactory(
              CategoryFactory,
              category_type='PRODUCT',
              # Ensure category belongs to same org if categories are scoped
              # organization=factory.SelfAttribute('..organization')
          )
          status = ProductStatus.ACTIVE
          base_uom = factory.SubFactory(UnitOfMeasureFactory, code='EA', name='Each', uom_type='Count')
          is_inventory_tracked = True
          is_purchasable = True
          is_sellable = True
          attributes = {}
          custom_fields = {}

          # Example for adding tags
          # @factory.post_generation
          # def tags(self, create, extracted, **kwargs):
          #     if not create: return
          #     if extracted: # Pass tags=['tag1', 'tag2'] to factory
          #         for tag in extracted: self.tags.add(tag)
          #     else: # Add some default tags maybe
          #         self.tags.add('test-product')
      ```
  [ ] **(Test)** Write simple tests ensuring the factory creates valid instances and sets relationships correctly.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Create `api/v1/features/products/admin.py`.
  [ ] Define `ProductAdmin`:
      ```python
      from django.contrib import admin
      from .models import Product

      @admin.register(Product)
      class ProductAdmin(admin.ModelAdmin):
          list_display = (
              'sku', 'name', 'organization', 'category', 'product_type',
              'status', 'base_uom', 'is_inventory_tracked', 'updated_at'
          )
          list_filter = ('organization', 'product_type', 'status', 'category', 'is_inventory_tracked')
          search_fields = ('sku', 'name', 'description', 'category__name')
          list_select_related = ('organization', 'category', 'base_uom')
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
          autocomplete_fields = ['category', 'base_uom'] # Assumes admin registered for Category/UoM
          fieldsets = (
              (None, {'fields': ('organization', ('sku', 'name'), 'status')}),
              ('Classification', {'fields': ('product_type', 'category', 'tags')}),
              ('Details', {'fields': ('description', 'base_uom')}),
              ('Flags', {'fields': ('is_inventory_tracked', 'is_purchasable', 'is_sellable')}),
              ('Extended Data', {'classes': ('collapse',), 'fields': ('attributes', 'custom_fields')}),
              ('Audit Info', {'classes': ('collapse',), 'fields': readonly_fields}),
          )
          # Taggit admin widget usually works automatically
          # JSONFields might need django-json-widget
      ```
  [ ] **(Manual Test):** Verify registration, CRUD, filtering, search, related field lookups in Django Admin locally. Ensure Org Scoping seems respected (though primarily enforced via API).

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations api.v1.features.products`.
  [ ] **Review generated migration file carefully.** Check FKs, `unique_together`, indexes.
  [ ] Run `python manage.py migrate` locally.

  ### 3.5 Serializer Definition (`serializers.py`)

  [ ] **(Test First - Validation/Representation)** Write Unit/Integration Tests (`tests/unit/test_serializers.py`, etc.) for `ProductSerializer`. Test validation (`unique_together`, FK existence, `limit_choices_to` for category), representation (including tags, potentially nested Category/UoM), custom field/attribute handling.
  [ ] Define `ProductSerializer` in `api/v1/features/products/serializers.py`. Integrate `TaggitSerializer`. Handle nested reads/PK writes for FKs. Include `FieldPermissionSerializerMixin`.
      ```python
      from rest_framework import serializers
      from taggit.serializers import TagListSerializerField, TaggitSerializer
      from ..models import Product
      # Import related serializers if nesting read-only representation
      # from api.v1.base_models.common.serializers import CategorySerializer, UnitOfMeasureSerializer
      # Import FieldPermission mixin
      # from core.serializers import FieldPermissionSerializerMixin

      class ProductSerializer(TaggitSerializer, serializers.ModelSerializer): # Add FieldPermissionSerializerMixin
          tags = TagListSerializerField(required=False)
          # Example: Read-only nested, write via PK
          # category_details = CategorySerializer(source='category', read_only=True)
          # base_uom_details = UnitOfMeasureSerializer(source='base_uom', read_only=True)
          category = serializers.PrimaryKeyRelatedField(
              queryset=Category.objects.filter(category_type='PRODUCT'), # Enforce type
              allow_null=True, required=False
          )
          base_uom = serializers.PrimaryKeyRelatedField(
              queryset=UnitOfMeasure.objects.all() # Or filter active
          )
          # Organization is usually set via OrgScoped mixin, make read-only here
          organization = serializers.PrimaryKeyRelatedField(read_only=True)
          organization_name = serializers.CharField(source='organization.name', read_only=True)

          class Meta:
              model = Product
              fields = [
                  'id', 'name', 'sku', 'description', 'product_type',
                  'category', #'category_details',
                  'status',
                  'base_uom', #'base_uom_details',
                  'is_inventory_tracked', 'is_purchasable', 'is_sellable',
                  'tags', 'attributes', 'custom_fields',
                  'organization', 'organization_name',
                  'created_at', 'updated_at',
              ]
              read_only_fields = ('id', 'organization', 'organization_name', 'created_at', 'updated_at')
      ```
  [ ] Implement `validate_sku` (check uniqueness within organization if DB constraint insufficient), `validate_custom_fields`.
  [ ] Run tests; expect pass. Refactor.

  ### 3.6 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests checking `/api/v1/products/` URL existence, authentication, basic permissions.
  [ ] Define `ProductViewSet` in `api/v1/features/products/views.py`. Inherit `OrganizationScopedViewSetMixin`.
      ```python
      from rest_framework import viewsets, permissions
      from core.views import OrganizationScopedViewSetMixin # Adjust import path
      from ..models import Product
      from ..serializers import ProductSerializer
      # Import filters, permissions

      class ProductViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
          serializer_class = ProductSerializer
          permission_classes = [permissions.IsAuthenticated] # Add specific Product permissions
          # queryset is automatically filtered by OrganizationScopedViewSetMixin
          queryset = Product.objects.select_related(
              'organization', 'category', 'base_uom'
          ).prefetch_related('tags').all()

          filter_backends = [...] # Advanced filtering, Search, Ordering
          # Define filterset_class pointing to a ProductFilter defined in filters.py
          # filterset_fields = ['category', 'status', 'product_type', 'tags__name']
          search_fields = ['sku', 'name', 'description', 'category__name']
          ordering_fields = ['name', 'sku', 'created_at', 'updated_at']
      ```
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.7 URL Routing (`urls.py`)

  [ ] Create `api/v1/features/products/urls.py`. Import `ProductViewSet`. Register with router: `router.register(r'products', views.ProductViewSet)`.
  [ ] Include `products.urls` in `api/v1/features/urls.py`.
  [ ] **(Test):** Rerun basic API tests; expect 2xx/4xx codes.

  ### 3.8 API Endpoint Testing (CRUD & Features) (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests covering:
      *   LIST (with filters for category, status, type, tags). **Verify Org Scoping works.**
      *   CREATE (valid/invalid data, check org auto-set). Test permission checks (model & field).
      *   RETRIEVE (check permissions, org scoping).
      *   UPDATE (PUT/PATCH, check permissions, field permissions).
      *   DELETE (check permissions).
      *   Saving/Validating `attributes` and `custom_fields`.
      *   Tag assignment and filtering via API.
  [ ] Implement/Refine ViewSet methods (`get_queryset`, potentially `perform_create` if more than org setting needed) and Serializer logic.
  [ ] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/features/products`). Review uncovered lines.
[ ] Manually test via API client and Django Admin. Pay attention to Org Scoping.
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs.
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Plan implementation for related features (Pricing, Inventory, Variants, Bundles).

--- END OF FILE product_implementation_steps.md ---