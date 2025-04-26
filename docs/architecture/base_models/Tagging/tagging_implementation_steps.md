Okay, let's generate the implementation steps for integrating the `Tagging` system, primarily using the `django-taggit` library. This focuses on setting up the library and adding tagging capability to other models. We will also include the *optional* steps for creating a custom `Tag` model with `custom_fields`, as requested in the PRD.

--- START OF FILE tagging_implementation_steps.md ---

# Tagging System Integration - Implementation Steps

## 1. Overview

**Model Name(s):**
`taggit.models.Tag`, `taggit.models.TaggedItem` (provided by library), potentially `CustomTag` (if custom fields needed)

**Corresponding PRD:**
`tagging_prd.md` (Simplified - Integration focus)

**Depends On:**
`django-taggit` library, Models that need to be tagged (e.g., `Product`, `Contact`, `Document`), `Timestamped`/`Auditable` (if creating custom `Tag` model).

**Key Features:**
Integrates `django-taggit` to allow applying keyword tags to various models. Provides `TaggableManager` for easy association. Supports basic tag management via Admin and potentially API. Optionally supports custom fields on Tags via a custom Tag model.

**Primary Location(s):**
*   Library integration: `settings.py`, `requirements/*.txt`.
*   `TaggableManager` field added to models in: `api/v1/*/models.py`.
*   Custom `Tag` model (if used): `core/models.py` or `common/models.py` or dedicated `tags/models.py`.
*   Admin: `tags/admin.py` (if custom model) or relies on `taggit` admin.
*   Serializers: Integration within serializers of taggable models.

## 2. Prerequisites

[ ] Install required library: `pip install django-taggit`.
[ ] Add `'taggit'` to `INSTALLED_APPS` in `config/settings/base.py`.
[ ] **Decision:** Will custom fields on Tags be required initially?
    *   If NO: Proceed using default `taggit.models.Tag`.
    *   If YES: Plan to create a custom Tag model (Step 3.2). Ensure `Timestamped`/`Auditable` exist if the custom tag model needs them.
[ ] Ensure `factory-boy` is set up.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Initial `taggit` Migration

  [ ] Run `python manage.py makemigrations taggit`. (Only needed the first time `taggit` is added).
  [ ] **Review generated migration file(s).**
  [ ] Run `python manage.py migrate taggit` locally. This creates the default `taggit_tag` and `taggit_taggeditem` tables.

  ### 3.2 Custom Tag Model Definition (Optional - Only if Custom Fields Required)

  [ ] **(Skip if not using custom fields on Tags)**
  [ ] **(Test First)** Write Unit Tests (`core/tests/test_models.py` or `tags/tests/unit/test_models.py`) verifying:
      *   `CustomTag` model inherits required fields (`name`, `slug`).
      *   `custom_fields` JSONField exists and defaults to `{}`.
      *   Inherits `Timestamped`/`Auditable` if specified in PRD.
      Run; expect failure.
  [ ] Define `CustomTag` model (e.g., in `core/models.py`):
      ```python
      # core/models.py (or tags/models.py)
      from django.db import models
      from django.utils.translation import gettext_lazy as _
      from taggit.models import TagBase, GenericTaggedItemBase
      from .models import Timestamped, Auditable # If inheriting base models

      class CustomTag(TagBase, Timestamped, Auditable): # Add Timestamped/Auditable if needed
          # Inherits name and slug fields from TagBase

          custom_fields = models.JSONField(
              _("Custom Fields"), default=dict, blank=True
          )
          # Add other fields if necessary

          class Meta:
              verbose_name = _("Tag")
              verbose_name_plural = _("Tags")
              # Add unique constraints or indexes if needed beyond name/slug
              # Ordering is often by name (handled by TagBase?)

      # If using a custom tag model, you might need a custom Through model too,
      # inheriting GenericTaggedItemBase, although TaggableManager often handles this.
      # Check taggit docs if intermediate model customization is needed.
      # class TaggedWhatever(GenericTaggedItemBase):
      #     tag = models.ForeignKey(
      #         CustomTag,
      #         on_delete=models.CASCADE,
      #         related_name="%(app_label)s_%(class)s_items",
      #     )
      ```
  [ ] Configure Django settings to use the custom model in `config/settings/base.py`:
      ```python
      TAGGIT_TAG_MODEL = "core.CustomTag" # Adjust path as needed
      # If using custom through model:
      # TAGGIT_TAGGED_ITEM_MODEL = "core.TaggedWhatever"
      ```
  [ ] Run `makemigrations core` (or `tags`).
  [ ] **Review migration:** Ensure it creates the `core_customtag` table correctly.
  [ ] Run `migrate`.
  [ ] Run tests for `CustomTag` model; expect pass. Refactor.

  ### 3.3 Factory Definition (`tests/factories.py`)

  [ ] Define `TagFactory` (or `CustomTagFactory`) in a relevant `tests/factories.py` (e.g., `core/tests/factories.py` or `common/tests/factories.py`).
      ```python
      import factory
      from factory.django import DjangoModelFactory
      # Import default Tag or CustomTag model based on decision
      # from taggit.models import Tag # Option A
      from core.models import CustomTag # Option B - Adjust import path

      # Option A: Factory for default Tag
      # class TagFactory(DjangoModelFactory):
      #     class Meta:
      #         model = Tag
      #         django_get_or_create = ('name',)
      #     name = factory.Sequence(lambda n: f'Tag {n}')

      # Option B: Factory for CustomTag
      class CustomTagFactory(DjangoModelFactory):
          class Meta:
              model = CustomTag
              django_get_or_create = ('name',) # Use name or slug

          name = factory.Sequence(lambda n: f'Tag {n}')
          # slug = factory.LazyAttribute(lambda o: slugify(o.name)) # Auto-generated by taggit usually
          custom_fields = {}
      ```
  [ ] **(Test)** Write simple tests ensuring the factory creates valid Tag instances.

  ### 3.4 Adding `TaggableManager` to Models

  [ ] **(Test First)** For *each* model requiring tagging (e.g., `Product`):
      *   Write **Integration Test(s)** (`tests/integration/test_models.py` for that model) verifying:
          *   The model instance has a `tags` attribute which is a `TaggableManager`.
          *   You can add tags using `instance.tags.add("tag1", "tag2")`.
          *   You can retrieve tags using `instance.tags.all()`.
          *   You can filter the model using `Model.objects.filter(tags__name__in=["tag1"])`.
      Run; expect failure (attribute error).
  [ ] Add the `TaggableManager` to the target model definition:
      ```python
      # api/v1/base_models/common/models.py (Example for Product)
      from taggit.managers import TaggableManager
      # ... other imports

      class Product(Timestamped, Auditable, OrganizationScoped): # Add other inheritance
          # ... other fields ...
          tags = TaggableManager(blank=True, verbose_name=_("Tags"))
          # ...
      ```
  [ ] Run `makemigrations` for the app containing the modified model(s). Taggit usually doesn't require schema changes here, but it's good practice.
  [ ] Run `migrate`.
  [ ] Run tests for the target model's tagging functionality; expect pass. Refactor.
  [ ] **Repeat Step 3.4 for all models needing tagging.**

  ### 3.5 Admin Registration (`admin.py`)

  [ ] `django-taggit` usually makes tags editable in the admin automatically for models using `TaggableManager`.
  [ ] **If using CustomTag:** Register `CustomTag` with the admin (e.g., in `core/admin.py` or `tags/admin.py`).
      ```python
      from django.contrib import admin
      from .models import CustomTag # Adjust import

      @admin.register(CustomTag)
      class CustomTagAdmin(admin.ModelAdmin):
          list_display = ('name', 'slug') # Add custom_fields if needed
          search_fields = ('name',)
          # Add fieldsets if editing custom_fields in admin
      ```
  [ ] **(Manual Test):** Verify tags can be added/edited via the admin interface for tagged models (e.g., Product admin page). Verify `CustomTag` admin works if implemented.

  ### 3.6 Serializer Definition (`serializers.py`)

  [ ] **(Test First)** For serializers of taggable models (e.g., `ProductSerializer`):
      *   Write Unit/Integration Tests verifying that the `tags` field accepts a list of strings on input (create/update) and outputs a list of strings on representation.
      *   If using custom tags with custom fields, test validation/representation of those fields.
  [ ] Integrate tag handling into relevant serializers using `taggit.serializers`:
      ```python
      # api/v1/base_models/common/serializers.py (Example for ProductSerializer)
      from rest_framework import serializers
      from taggit.serializers import TagListSerializerField, TaggitSerializer
      from ..models import Product # Assuming Product is in common

      class ProductSerializer(TaggitSerializer, serializers.ModelSerializer): # Add TaggitSerializer
          tags = TagListSerializerField(required=False) # Handles list of strings <-> tags

          class Meta:
              model = Product
              fields = [..., 'tags', ...] # Include tags field

          # TaggitSerializer handles create/update for tags if field is named 'tags'
          # If using custom tag model with custom fields, may need custom handling
      ```
  [ ] Run tests; expect pass. Refactor.

  ### 3.7 API ViewSet Definition (`views.py`)

  [ ] Ensure ViewSets for taggable models (e.g., `ProductViewSet`) use serializers that handle tags (like `ProductSerializer` above).
  [ ] Add filtering by tags using `django-filter` integration with `taggit`. Define a `FilterSet`:
      ```python
      # api/v1/base_models/common/filters.py (Example)
      import django_filters
      from taggit.forms import TagField # Use form field for filtering
      from taggit.managers import TaggableManager
      from ..models import Product

      class ProductFilter(django_filters.FilterSet):
          # Allows filtering like ?tags=tag1,tag2 (find products with ALL these tags)
          # Or potentially use a custom filter for ANY tag match (tags__name__in)
          tags = django_filters.ModelMultipleChoiceFilter(
              field_name='tags__name',
              to_field_name='name',
              lookup_expr='in', # Find products matching ANY of the tags in the list
              label='Tags (any of)',
              queryset=Product.tags.tag_model.objects.all() # Get tags from correct model
          )
          # Alternative using basic TagField for AND logic:
          # tags = TagField(required=False)

          class Meta:
              model = Product
              fields = ['tags', ...] # Add other filter fields
      ```
      ```python
      # api/v1/base_models/common/views.py (Example ProductViewSet)
      from django_filters.rest_framework import DjangoFilterBackend
      from .filters import ProductFilter # Import FilterSet

      class ProductViewSet(viewsets.ModelViewSet):
          # ... serializer_class, queryset, permissions ...
          filter_backends = [DjangoFilterBackend, ...] # Add DjangoFilterBackend
          filterset_class = ProductFilter # Use the defined filterset
          # ...
      ```
  [ ] **(Test First)** Write API tests specifically for filtering list endpoints by tags (e.g., `GET /api/v1/products/?tags__name__in=tag1,tag2` or `GET /api/v1/products/?tags=tag1,tag2`). Assert correct filtering.

  ### 3.8 URL Routing (`urls.py`)

  [ ] No specific changes usually needed for tagging itself, relies on existing model endpoints. Optionally add `/api/v1/tags/` endpoint if managing global tags via API is needed.

  ### 3.9 API Endpoint Testing (`tests/api/test_endpoints.py`)

  [ ] Test adding/updating tags via `POST`/`PUT`/`PATCH` requests to taggable model endpoints (e.g., Product). Verify the `tags` list is correctly saved and returned.
  [ ] Test filtering list endpoints using the defined tag filter parameters.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`).
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov`). Ensure tagging integration points are tested.
[ ] Manually test adding/removing tags and filtering via API client and Admin UI.
[ ] Review API documentation regarding tag handling and filtering.

## 5. Follow-up Actions

[ ] Address TODOs (e.g., custom field handling for custom tags, tag merging admin action).
[ ] Create Pull Request.
[ ] Update API documentation for relevant endpoints, showing how to use tags.
[ ] Add `TaggableManager` to other models as required in subsequent phases.

--- END OF FILE tagging_implementation_steps.md ---