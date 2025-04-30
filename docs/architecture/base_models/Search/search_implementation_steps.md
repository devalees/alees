
# Search System Integration - Implementation Steps

## 1. Overview

**Feature Name:**
Search System Integration

**Corresponding PRD:**
`search_prd.md` (Simplified - Integration focus)

**Depends On:**
Target models to be indexed (e.g., `Product`, `Organization`, `Contact`, `Document`), Celery infrastructure, Search Engine instance (Elasticsearch/OpenSearch), `django-elasticsearch-dsl` library, `elasticsearch-dsl` library.

**Key Features:**
Integrates the ERP with Elasticsearch/OpenSearch. Defines indexed documents based on Django models. Implements automatic index updates via signals/Celery. Provides a core Search API endpoint with basic filtering and permission-based result trimming.

**Primary Location(s):**
*   Search Engine Infrastructure: External (needs deployment/management).
*   Library Installation: `requirements/*.txt`, `settings.py`.
*   Index Definitions (`documents.py`): Within each app containing indexed models (e.g., `api/v1/features/products/documents.py`).
*   Signal Handlers (`signals.py`): Within each app containing indexed models OR a central location.
*   Celery Tasks (`tasks.py`): For async indexing (e.g., `core/tasks.py` or per-app).
*   Management Commands: `core/management/commands/` (for bulk indexing).
*   API View/Serializer/URL: Dedicated `search` app (`api/v1/search/`) or within `core`/`common`. Assume **new `search` app**.

## 2. Prerequisites

[ ] **Set up Search Engine:** Deploy and configure Elasticsearch or OpenSearch instance accessible from the Django application. Note connection URL(s) and any necessary credentials.
[ ] **Install Libraries:** `pip install django-elasticsearch-dsl elasticsearch-dsl elasticsearch` (or `opensearch-py opensearch-dsl`).
[ ] **Configure Connection:** Define search engine connection details in `config/settings/base.py` (loaded from environment variables):
    ```python
    # config/settings/base.py
    ELASTICSEARCH_DSL = {
        'default': {
            'hosts': env('ELASTICSEARCH_HOSTS', default='localhost:9200'), # Comma-separated for cluster
            # Add http_auth, use_ssl, ca_certs etc. if needed
            # 'http_auth': (env('ELASTICSEARCH_USER', default=None), env('ELASTICSEARCH_PASSWORD', default=None)),
        },
    }
    # Optional: django-elasticsearch-dsl specific settings
    # ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = 'django_elasticsearch_dsl.signals.RealTimeSignalProcessor' # Sync (default)
    ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = 'core.search.signals.CelerySignalProcessor' # If using async via Celery (custom class needed)
    ```
[ ] Ensure Celery infrastructure is operational (for async indexing).
[ ] Verify target models to be indexed exist and are migrated.
[ ] **Create new Django app:** `python manage.py startapp search`.
[ ] Add `'django_elasticsearch_dsl'` and `'search'` to `INSTALLED_APPS`.
[ ] Ensure `factory-boy` is set up. Factories for indexed models exist.

## 3. Implementation Steps (TDD Workflow)

  *(Index Definitions -> Indexing Logic -> API Endpoint)*

  ### 3.1 Index/Document Definitions (`documents.py`)

  [ ] **(Test First - Document Structure)** Write **Unit Test(s)** (`tests/unit/test_documents.py` in relevant app, e.g., `products`) verifying:
      *   The `ProductDocument` (doesn't exist yet) defines the correct index name.
      *   It includes the expected fields (`name`, `sku`, `description`, `tags`, `organization_id`).
      *   Fields have appropriate ES types (`Text`, `Keyword`, `Object`, `Integer`).
      *   The `prepare_tags` method (if needed) formats tags correctly.
      *   The `get_queryset` method returns active products.
      Run; expect failure.
  [ ] Create `documents.py` file within each app containing models to be indexed (e.g., `api/v1/features/products/documents.py`).
  [ ] Define `Document` classes inheriting from `django_elasticsearch_dsl.Document`.
      ```python
      # api/v1/features/products/documents.py
      from django_elasticsearch_dsl import Document, fields
      from django_elasticsearch_dsl.registries import registry
      from ..models import Product # Import the Django model

      @registry.register_document
      class ProductDocument(Document):
          # Include fields needed for searching AND filtering/displaying results
          organization_id = fields.IntegerField() # For filtering results by org
          category_slug = fields.KeywordField(attr='category.slug') # Example related field
          tags = fields.KeywordField() # Store tag names as keywords

          class Index:
              # Name of the Elasticsearch index
              name = 'products'
              # See Elasticsearch Indices API reference for available settings
              settings = {'number_of_shards': 1,
                          'number_of_replicas': 0}

          class Django:
              model = Product # The model associated with this Document

              # The fields of the model you want to be indexed in Elasticsearch
              fields = [
                  'name',
                  'sku',
                  'description',
                  'status', # Often keyword for filtering
                  'product_type', # Often keyword
                  'created_at', # Date field
              ]
              # Ignore auto updating of Elasticsearch when a model is saved
              # or deleted:
              # ignore_signals = True
              # Don't perform an index refresh after every update (sync setting):
              # auto_refresh = False
              # Paginate the django queryset used to populate the index with the specified size
              # (by default it uses the database driver's default setting)
              # queryset_pagination = 5000

          def prepare_tags(self, instance):
              # Convert M2M tags to list of names for indexing
              return [tag.name for tag in instance.tags.all()]

          def get_queryset(self):
              """Prevent indexing inactive products."""
              # Optimize with select/prefetch related needed for prepare methods
              return super().get_queryset().select_related('category').prefetch_related('tags').filter(is_active=True) # Example filter

          # Add prepare_organization_id if needed (if source field isn't simple FK)
          def prepare_organization_id(self, instance):
               return instance.organization_id

      ```
  [ ] Repeat for other models (`Organization`, `Contact`, `Document` etc.) in their respective app's `documents.py`.
  [ ] Run document structure tests; expect pass. Refactor.

  ### 3.2 Indexing Pipeline (Signals & Tasks)

  [ ] **(Test First - Signals/Tasks)** Write **Integration Test(s)** (`core/tests/integration/test_search_signals.py` or similar) using `@pytest.mark.django_db`.
      *   Mock the Celery task queue (`mocker.patch('core.search.tasks.update_search_index_task.delay')`).
      *   Create/Save/Delete an instance of an indexed model (e.g., `Product`).
      *   Assert that the `update_search_index_task.delay` mock was called with the correct model info (app_label, model_name, pk).
      *   Write Unit tests for the Celery task `update_search_index_task`. Mock the `django_elasticsearch_dsl` `update()` method. Verify it's called correctly for create/update/delete actions.
      Run; expect failure.
  [ ] **Option A (Sync - Default `django-elasticsearch-dsl`):** If using the default `RealTimeSignalProcessor`, signals are connected automatically. Skip defining custom signals/tasks for basic sync.
  [ ] **Option B (Async - Recommended):**
      1.  Create a custom signal processor (e.g., in `core/search/signals.py`):
          ```python
          # core/search/signals.py
          from django_elasticsearch_dsl.signals import BaseSignalProcessor
          from .tasks import update_search_index_task # Import Celery task

          class CelerySignalProcessor(BaseSignalProcessor):
              def handle_save(self, sender, instance, **kwargs):
                  # Queue task on save/update
                  update_search_index_task.delay(
                      sender._meta.app_label, sender._meta.model_name, instance.pk
                  )

              def handle_delete(self, sender, instance, **kwargs):
                  # Queue task on delete
                  update_search_index_task.delay(
                      sender._meta.app_label, sender._meta.model_name, instance.pk, action='delete'
                  )

              # Optional: Handle M2M changes if needed for indexing
              # def handle_m2m_changed(self, sender, instance, action, pk_set, **kwargs): ...
          ```
      2.  Configure settings to use it: `ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = 'core.search.signals.CelerySignalProcessor'`
      3.  Create the Celery task (`core/tasks.py` or `search/tasks.py`):
          ```python
          # core/tasks.py
          from celery import shared_task
          from django.apps import apps
          from django_elasticsearch_dsl.registries import registry
          import logging

          logger = logging.getLogger(__name__)

          @shared_task(bind=True, max_retries=3, default_retry_delay=30)
          def update_search_index_task(self, app_label, model_name, pk, action='index'):
              """Updates Elasticsearch index for a given model instance."""
              try:
                  model = apps.get_model(app_label, model_name)
                  instance = model._default_manager.get(pk=pk)

                  if action == 'index':
                      logger.info(f"Indexing {model_name} {pk}")
                      registry.update(instance)
                      registry.update_related(instance) # Update related docs if needed
                  elif action == 'delete':
                      logger.info(f"Deleting {model_name} {pk} from index")
                      registry.delete(instance, raise_on_error=False) # Don't fail task if already deleted

              except model.DoesNotExist:
                   # Object might have been deleted between signal and task execution
                   if action == 'index': # If update/create fails because it's gone, try deleting from index
                       try:
                           logger.warning(f"Object {app_label}.{model_name} {pk} not found for indexing, attempting delete from index.")
                           # Create a dummy instance with just PK for deletion signal processing
                           dummy_instance = model(pk=pk)
                           registry.delete(dummy_instance, raise_on_error=False)
                       except Exception as e:
                           logger.error(f"Error deleting non-existent object {pk} from index: {e}", exc_info=True)
                   else: # If delete fails because it's already gone, that's fine
                       logger.info(f"Object {app_label}.{model_name} {pk} not found for deletion from index (likely already deleted).")

              except Exception as exc:
                   logger.error(f"Error updating search index for {app_label}.{model_name} {pk}: {exc}", exc_info=True)
                   raise self.retry(exc=exc)

          ```
  [ ] Run signal/task tests; expect pass. Refactor.

  ### 3.3 Management Commands (Bulk Indexing)

  [ ] **(Test First)** Write tests for management commands (requires careful setup/mocking or integration test with ES). Test `populate` and `rebuild` commands.
  [ ] Create management commands (e.g., `core/management/commands/search_index.py`):
      ```python
      # core/management/commands/search_index.py
      from django.core.management.base import BaseCommand
      from django_elasticsearch_dsl.management.commands import search_index

      class Command(search_index.Command):
          help = 'Custom wrapper for Elasticsearch index management provided by django-elasticsearch-dsl'
          # Inherits create, delete, populate options from base command
          # Add custom logic or arguments if needed
      ```
  [ ] **(Manual Test)** Run `python manage.py search_index --populate -f` locally against test ES instance. Verify data appears in index using Kibana/Cerebro or ES API calls. Run `search_index --delete -f` and `search_index --create`.

  ### 3.4 Search API View/Serializer/URL (`search/`)

  [ ] **(Test First)** Write **API Test(s)** (`search/tests/api/test_endpoints.py`):
      *   Test `GET /api/v1/search/?q=...` with various query terms.
      *   Mock the search engine call initially. Verify the view constructs the correct ES Query DSL based on `q` and filters (`type`, `organization_id`, `status`).
      *   Later, integration test against a test ES instance: Seed index with data, perform search via API, verify results from mock ES match expected structure (title, snippet, score, link).
      *   **Crucially**, test the **security post-filtering**: Mock ES returning results for OrgA and OrgB. Make API call as UserA (in OrgA). Verify final API response *only* contains OrgA results. Test with superuser -> should see both.
      *   Test pagination in search results.
      *   Test error handling for invalid queries or ES connection issues.
      Run; expect failure.
  [ ] Create `search/serializers.py` (for formatting results):
      ```python
      # search/serializers.py
      from rest_framework import serializers

      class SearchResultSerializer(serializers.Serializer):
          # Represents one item in the search results list
          app_label = serializers.CharField()
          model_name = serializers.CharField()
          pk = serializers.CharField() # Use CharField for UUIDs etc.
          score = serializers.FloatField()
          title = serializers.CharField() # Primary display field
          snippet = serializers.CharField(allow_null=True) # Highlighted excerpt
          # Add other fields needed for display (e.g., timestamp, status)
          detail_url = serializers.CharField(allow_null=True) # Link to object's API detail view
      ```
  [ ] Create `search/views.py` with `SearchView(APIView)`:
      ```python
      # search/views.py
      from rest_framework.views import APIView
      from rest_framework.response import Response
      from rest_framework import permissions
      from rest_framework.exceptions import ParseError
      from django.conf import settings
      from django.apps import apps
      from django.urls import reverse
      from elasticsearch_dsl import Search, Q as ES_Q
      from elasticsearch_dsl.connections import connections
      from elasticsearch import ElasticsearchException
      from .serializers import SearchResultSerializer
      # Assuming base viewset mixin has logic or we get org from user
      # from core.views import OrganizationScopedViewSetMixin

      class SearchView(APIView):
          permission_classes = [permissions.IsAuthenticated] # Must be logged in

          def get(self, request, *args, **kwargs):
              query_term = request.query_params.get('q', '').strip()
              if not query_term:
                   return Response({"results": [], "count": 0})

              # --- Build Elasticsearch Query ---
              # Get default ES connection
              es = connections.get_connection()
              # Base search across relevant indices (e.g., products, organizations...)
              # Improve this: get index names dynamically or from settings
              s = Search(using=es, index=['products', 'organizations', 'contacts']) # TODO: Dynamic index list

              # Apply core query (e.g., multi_match across common text fields)
              # TODO: Define searchable fields per index/model more robustly
              search_fields = ["name", "description", "code", "sku", "tags", "first_name", "last_name"]
              q_query = ES_Q("multi_match", query=query_term, fields=search_fields, fuzziness="AUTO")
              s = s.query(q_query)

              # Apply Filters from query params
              filter_clauses = []
              allowed_types = request.query_params.getlist('type') # e.g., ?type=product&type=organization
              if allowed_types:
                    # Need mapping from 'product' string to index name 'products'
                    # filter_clauses.append(ES_Q('terms', _index=mapped_allowed_types)) # Filter by index
                    filter_clauses.append(ES_Q('terms', model_type_field=allowed_types)) # If using dedicated field

              # Apply Org Scoping (Crucial for pre-filtering if possible)
              user = request.user
              if not user.is_superuser:
                    user_orgs = user.get_organizations() # Assumes this exists
                    org_ids = [org.pk for org in user_orgs]
                    if not org_ids: return Response({"results": [], "count": 0}) # No access
                    # Assumes 'organization_id' field exists in ALL indexed documents
                    filter_clauses.append(ES_Q('terms', organization_id=org_ids))

              status_filter = request.query_params.get('status')
              if status_filter:
                   filter_clauses.append(ES_Q('term', status=status_filter)) # Assumes 'status' is keyword field

              date_after = request.query_params.get('created_after')
              # TODO: Add date range filters if needed (requires parsing, 'created_at' field in index)

              if filter_clauses:
                  s = s.filter(ES_Q('bool', must=filter_clauses))

              # Add Highlighting (optional)
              s = s.highlight('name', 'description', number_of_fragments=1, fragment_size=100) # Example

              # Add Sorting (e.g., by relevance score `_score` (default) or date)
              # s = s.sort('-created_at')

              # Pagination (Use ES pagination from/size)
              # TODO: Integrate with DRF pagination class? Or handle manually.
              try:
                   page_num = int(request.query_params.get('page', 1))
                   page_size = int(request.query_params.get('page_size', 20))
                   start = (page_num - 1) * page_size
                   end = start + page_size
                   s = s[start:end]
              except ValueError:
                   raise ParseError("Invalid pagination parameters.")

              # --- Execute Search ---
              try:
                  response = s.execute()
                  total_hits = response.hits.total.value
              except ElasticsearchException as e:
                  # Log error, return 500 or appropriate error
                  import logging
                  logging.getLogger(__name__).error(f"Elasticsearch query failed: {e}", exc_info=True)
                  return Response({"errors": [{"detail": "Search service unavailable."}]}, status=503)

              # --- Process Results & Post-Filter Security ---
              results_data = []
              object_ids_by_type = {} # { 'app_label.modelname': [pk1, pk2], ... }

              for hit in response.hits:
                  app_label, model_name = hit.meta.index.split('_')[-1].split('-') # Simple split, needs robust mapping
                  pk = hit.meta.id
                  model_key = f"{app_label}.{model_name}"
                  if model_key not in object_ids_by_type: object_ids_by_type[model_key] = []
                  object_ids_by_type[model_key].append(pk)
                  # Store temporary data needed for serializer
                  results_data.append({
                       'app_label': app_label, 'model_name': model_name, 'pk': pk,
                       'score': hit.meta.score,
                       'title': getattr(hit, 'name', getattr(hit, 'title', hit.meta.id)), # Get display title
                       'snippet': ' '.join(hit.meta.highlight.description) if hasattr(hit.meta, 'highlight') and 'description' in hit.meta.highlight else None # Example snippet
                  })

              # ** CRUCIAL: Post-filter based on DB permissions **
              allowed_objects = {} # { 'app_label.modelname': {pk1, pk2}, ... }
              for model_key, pks in object_ids_by_type.items():
                   try:
                        Model = apps.get_model(model_key)
                        # Apply Org Scoping and View Permissions from DB query
                        # This query MUST be efficient (uses __in lookup)
                        allowed_pks = set(Model.objects.filter(
                            pk__in=pks,
                            # Add Org Scoping filter based on user orgs HERE
                            # Add permission checks if needed (e.g., using django-guardian querysets)
                        ).values_list('pk', flat=True))
                        allowed_objects[model_key] = allowed_pks
                   except LookupError:
                        continue # Model not found

              # Filter results based on allowed objects
              final_results = []
              for res in results_data:
                   model_key = f"{res['app_label']}.{res['model_name']}"
                   if res['pk'] in allowed_objects.get(model_key, set()):
                        # Add detail URL (example)
                        try:
                            res['detail_url'] = request.build_absolute_uri(
                                reverse(f"v1:{res['app_label']}:{res['model_name']}-detail", args=[res['pk']]) # Needs URL names setup
                            )
                        except Exception:
                            res['detail_url'] = None
                        final_results.append(res)

              # Serialize results
              serializer = SearchResultSerializer(final_results, many=True)
              # TODO: Build proper paginated response structure matching DRF default
              return Response({
                  "count": total_hits, # Note: this is total found by ES, might be > len(serializer.data) after permission filter
                  "results": serializer.data
              })
      ```
  [ ] Run tests; expect pass. Refactor (especially query building, permission filtering, result formatting, pagination).

  ### 3.9 URL Routing (`search/urls.py` & `api/v1/urls.py`)

  [ ] Create `api/v1/search/urls.py`. Define URL pattern for `SearchView`.
  [ ] Include search URLs in main `api/v1/urls.py`.
  [ ] **(Test):** Rerun basic API tests.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`), mocking ES or using a test ES instance.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=search`). Ensure index/signal/task/view logic covered.
[ ] Manually test search via API client: various queries, filters, check results, check permissions by logging in as different users. Check indexing updates after model changes.
[ ] Review API documentation draft for the search endpoint.

## 5. Follow-up Actions

[ ] Address TODOs (Dynamic index list, robust searchable fields definition, robust permission post-filtering integration, document content indexing if needed, advanced search features).
[ ] Create Pull Request.
[ ] Update API documentation.
[ ] Set up Search Engine cluster and indexing pipeline in deployment environments.

--- END OF FILE search_implementation_steps.md ---