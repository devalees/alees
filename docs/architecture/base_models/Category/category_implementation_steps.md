

# Category - Implementation Steps

## 1. Overview

**Model Name:**
`Category`

**Corresponding PRD:**
`category_prd.md` (Generic, Hierarchical version with Custom Fields)

**Depends On:**
`Timestamped`, `Auditable` (Abstract Base Models), `django-mptt` library.

**Key Features:**
Provides a generic, hierarchical structure for classifying various ERP entities (Products, Documents, etc.). Uses `django-mptt` for tree management. Includes type discrimination, status, and custom fields.

**Primary Location(s):**
`api/v1/base_models/common/category/` (Assuming `common` app for shared entities)

## 2. Prerequisites

[ ] Verify prerequisite models/mixins (`Timestamped`, `Auditable`) are implemented.
[ ] Ensure the `common` app structure exists (`api/v1/base_models/common/category/`).
[ ] Install required library: `pip install django-mptt`.
[ ] Add `'mptt'` to `INSTALLED_APPS` in `config/settings/base.py`.
[ ] Ensure `factory-boy` is set up. Basic User factory exists.
[ ] Define `category_type` choices (e.g., in `common/category/choices.py`).

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Model Definition (`models.py`)

  [ ] **(Test First)**
      Write **Unit Test(s)** (`tests/unit/test_models.py` in `common/category`) verifying:
      *   A `Category` instance can be created with required fields (`name`, `category_type`).
      *   `slug` is auto-generated from name if blank (requires overriding `save` or using a library like `django-autoslug`). Test unique constraint on `slug`.
      *   `parent` ForeignKey works (can assign parent category).
      *   `unique_together` constraint (`parent`, `name`, `category_type`) is enforced.
      *   Default values (`is_active`, `custom_fields`) are set.
      *   MPTT fields (`lft`, `rght`, `tree_id`, `level`) are populated after save.
      *   `__str__` method returns name.
      *   Inherited `Timestamped`/`Auditable` fields exist.
      Run; expect failure (`Category` doesn't exist).
  [ ] Define the `Category` class in `api/v1/base_models/common/category/models.py`.
  [ ] Add required inheritance: `Timestamped`, `Auditable`, `MPTTModel`.
      ```python
      # api/v1/base_models/common/category/models.py
      from django.db import models
      from django.utils.text import slugify
      from django.utils.translation import gettext_lazy as _
      from mptt.models import MPTTModel, TreeForeignKey
      from core.models import Timestamped, Auditable # Adjust import path

      # Define choices centrally if preferred
      class CategoryType:
          PRODUCT = 'PRODUCT'
          DOCUMENT_TYPE = 'DOCUMENT_TYPE'
          ASSET_TYPE = 'ASSET_TYPE'
          ORG_COST_CENTER = 'ORG_COST_CENTER'
          OTHER = 'OTHER'
          CHOICES = [
              (PRODUCT, _('Product Category')),
              (DOCUMENT_TYPE, _('Document Type')),
              (ASSET_TYPE, _('Asset Type')),
              (ORG_COST_CENTER, _('Org/Cost Center')),
              (OTHER, _('Other')),
          ]

      class Category(Timestamped, Auditable, MPTTModel):
          name = models.CharField(
              _("Name"), max_length=255, db_index=True
          )
          # Consider unique=True based on whether slugs must be globally unique
          slug = models.SlugField(
              _("Slug"), max_length=255, unique=True, blank=True,
              help_text=_("Unique URL-friendly identifier. Auto-generated if blank.")
          )
          description = models.TextField(_("Description"), blank=True)
          parent = TreeForeignKey(
              'self',
              verbose_name=_("Parent Category"),
              on_delete=models.CASCADE, # Or PROTECT if children should prevent deletion
              null=True, blank=True, related_name='children', db_index=True
          )
          category_type = models.CharField(
              _("Category Type"), max_length=50, choices=CategoryType.CHOICES, db_index=True,
              help_text=_("The type of entity this category classifies.")
          )
          is_active = models.BooleanField(
              _("Is Active"), default=True, db_index=True
          )
          custom_fields = models.JSONField(
              _("Custom Fields"), default=dict, blank=True
          )

          class MPTTMeta:
              order_insertion_by = ['name']
              parent_attr = 'parent'

          class Meta:
              verbose_name = _("Category")
              verbose_name_plural = _("Categories")
              unique_together = ('parent', 'name', 'category_type')
              ordering = ['tree_id', 'lft'] # MPTT default

          def __str__(self):
              # Example showing hierarchy in string representation
              prefix = '---' * self.get_level()
              return f"{prefix} {self.name}".strip() if prefix else self.name

          def save(self, *args, **kwargs):
              # Auto-populate slug if blank
              if not self.slug:
                  self.slug = slugify(self.name)
                  # Handle potential slug collisions if slug is unique
                  # Add logic here to append numbers if slug exists (or use django-autoslug)
              super().save(*args, **kwargs)

      ```
  [ ] Run tests; expect pass. Refactor model code (especially slug generation/uniqueness handling).

  ### 3.2 Factory Definition (`tests/factories.py`)

  [ ] Define `CategoryFactory` in `api/v1/base_models/common/category/tests/factories.py`:
      ```python
      import factory
      from factory.django import DjangoModelFactory
      from ..models import Category, CategoryType

      class CategoryFactory(DjangoModelFactory):
          class Meta:
              model = Category
              # django_get_or_create = ('slug',) # If slug is reliable unique identifier

          name = factory.Sequence(lambda n: f'Category {n}')
          # slug = factory.LazyAttribute(lambda o: slugify(o.name)) # Or let model save handle it
          parent = None # Set in tests for hierarchy
          category_type = factory.Iterator([choice[0] for choice in CategoryType.CHOICES])
          is_active = True
          custom_fields = {}
      ```
  [ ] **(Test)** Write simple tests ensuring the factory creates valid instances, including setting parents to test hierarchy creation.

  ### 3.3 Admin Registration (`admin.py`)

  [ ] Create/Update `api/v1/base_models/common/category/admin.py`.
  [ ] Define `CategoryAdmin` using `DraggableMPTTAdmin`:
      ```python
      from django.contrib import admin
      from mptt.admin import DraggableMPTTAdmin
      from .models import Category

      @admin.register(Category)
      class CategoryAdmin(DraggableMPTTAdmin):
          list_display = ('tree_actions', 'indented_title', 'slug', 'category_type', 'is_active')
          list_display_links = ('indented_title',)
          list_filter = ('category_type', 'is_active')
          search_fields = ('name', 'slug', 'description')
          prepopulated_fields = {'slug': ('name',)}
          readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
          # MPTT admin handles hierarchy display/editing
          # Add fieldsets for better layout if needed
      ```
  [ ] **(Manual Test):** Verify registration, CRUD, hierarchy management (drag-drop) in Django Admin locally.

  ### 3.4 Migrations

  [ ] Run `python manage.py makemigrations api.v1.base_models.common`.
  [ ] **Review generated migration file carefully.** Check MPTT fields, FKs, unique constraints, indexes.
  [ ] Run `python manage.py migrate` locally.
  [ ] Run `python manage.py rebuild_category` (MPTT command) if needed (unlikely for new setup).

  ### 3.5 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** Write Unit/Integration Tests (`tests/unit/test_serializers.py`, etc.) for `CategorySerializer`. Test validation (unique constraints), representation (include necessary fields, potentially parent ID/children count), custom field handling, hierarchy fields if needed.
  [ ] Define `CategorySerializer` in `api/v1/base_models/common/category/serializers.py`. Consider using `rest_framework_mptt.serializers.MPTTModelSerializer` if available/needed for easy hierarchy representation.
      ```python
      from rest_framework import serializers
      # from rest_framework_mptt.serializers import MPTTModelSerializer # Option
      from ..models import Category

      class CategorySerializer(serializers.ModelSerializer): # Or MPTTModelSerializer
          # Example: Add children count (read-only)
          # children_count = serializers.IntegerField(source='get_children.count', read_only=True)
          # Example: Represent parent by slug or ID
          parent_slug = serializers.SlugRelatedField(
              slug_field='slug', source='parent', queryset=Category.objects.all(),
              allow_null=True, required=False
          )

          class Meta:
              model = Category
              fields = [
                  'id', 'name', 'slug', 'description',
                  'parent', # Or parent_slug / parent_id
                  'category_type', 'is_active',
                  # MPTT fields if needed: 'lft', 'rght', 'tree_id', 'level'
                  # 'children_count', # Example computed field
                  'custom_fields', 'created_at', 'updated_at',
              ]
              read_only_fields = ('id', 'created_at', 'updated_at') # Slug might be read-only after creation
              # If using MPTTSerializer, configure parent/child fields as needed
      ```
  [ ] Implement `validate_custom_fields`, `validate` (e.g., ensure parent has same `category_type` if required).
  [ ] Run tests; expect pass. Refactor.

  ### 3.6 API ViewSet Definition (`views.py`)

  [ ] **(Test First)** Write basic API Tests checking URL existence, permissions for `/api/v1/categories/`.
  [ ] Define `CategoryViewSet` in `api/v1/base_models/common/category/views.py`:
      ```python
      from rest_framework import viewsets, permissions
      from rest_framework.decorators import action
      from rest_framework.response import Response
      from ..models import Category
      from ..serializers import CategorySerializer
      # Import filters, permissions etc.

      class CategoryViewSet(viewsets.ModelViewSet): # Full CRUD likely needed
          serializer_class = CategorySerializer
          permission_classes = [permissions.IsAuthenticatedOrReadOnly] # Adjust as needed
          queryset = Category.objects.filter(is_active=True) # Default to active
          lookup_field = 'slug' # Use slug for retrieval/update/delete
          filter_backends = [...] # Add filtering (django-filter, search, ordering)
          filterset_fields = ['category_type', 'parent__slug'] # Filter by type, parent slug
          search_fields = ['name', 'slug', 'description']
          ordering_fields = ['name', 'lft'] # Order by name or tree order

          # Add custom actions for hierarchy if needed beyond standard MPTT helpers
          # E.g., get full tree for a type
          @action(detail=False, methods=['get'], url_path='tree/(?P<type>[^/.]+)')
          def get_tree_by_type(self, request, type=None):
              queryset = self.get_queryset().filter(category_type=type)
              # Use serializer with recursive handling or specific tree logic
              # ... implementation needed ...
              return Response(...)
      ```
  [ ] Run basic tests; expect pass. Refactor.

  ### 3.7 URL Routing (`urls.py`)

  [ ] Import `CategoryViewSet` in `api/v1/base_models/common/category/urls.py`.
  [ ] Register with router: `router.register(r'categories', views.CategoryViewSet)`.
  [ ] **(Test):** Rerun basic API tests; expect 2xx/4xx codes.

  ### 3.8 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] **(Test First - All)** Write comprehensive API tests covering:
      *   LIST (with filters for `category_type`, `parent__slug`).
      *   CREATE (valid/invalid, setting parent).
      *   RETRIEVE (by slug).
      *   UPDATE (PUT/PATCH).
      *   DELETE (test PROTECT/CASCADE based on `on_delete` choice for `parent`).
      *   Permissions.
      *   Hierarchy actions (if any custom ones added).
      *   Saving/Validating `custom_fields`.
  [ ] Implement/Refine ViewSet/Serializer logic.
  [ ] Run all API tests; expect pass. Refactor.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=api/v1/base_models/common/ctegory`). Review uncovered lines.
[ ] Manually test via API client and Django Admin (especially hierarchy drag-drop).
[ ] Review API documentation draft.

## 5. Follow-up Actions

[ ] Address TODOs (slug collision handling, specific hierarchy API actions).
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Ensure other models (Product, Document, etc.) correctly add FK/M2M to `Category` using `limit_choices_to`.

--- END OF FILE category_implementation_steps.md ---