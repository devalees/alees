
# Advanced Filtering System - Implementation Steps

## 1. Overview

**Feature Name:**
Advanced Filtering System

**Corresponding PRD:**
`advanced_filtering_prd.md` (Revised version)

**Depends On:**
Django Rest Framework, Django ORM (`Q` objects), `ContentType` framework. Potentially JSON parsing libraries if standard `json` module isn't sufficient (unlikely).

**Key Features:**
Provides complex, nested (AND/OR) filtering on API list endpoints via a structured JSON query parameter (`?filter=...`). Includes a custom DRF FilterBackend and a parser to translate JSON definitions into Django `Q` objects. Restricts filtering to configured fields.

**Primary Location(s):**
*   Filter Backend & Parser: `core/filtering/` (New directory within `core` app) or dedicated `filtering` app. Assume `core/filtering/`.
*   Configuration: `config/settings/base.py`.
*   Integration: Applied to ViewSets via `filter_backends`.

## 2. Prerequisites

[ ] Confirm **Option A (JSON in Query Parameter)** is the chosen syntax (Section 3.2 of PRD). Example: `?filter={"and": [{"field":"status", "op":"eq", "value":"active"}, ... ]}`.
[ ] Confirm **`StoredFilter` Model (Section 3.4)** is **deferred** for initial implementation.
[ ] Define initial **Configuration for Allowed Fields** (Section 3.5). Example structure in `settings.py`:
    ```python
    # config/settings/base.py
    ALLOWED_FILTER_FIELDS = {
        # Format: 'app_label.modelname': ['field1', 'related__field2', ...]
        'products.product': ['sku', 'name', 'status', 'product_type', 'category__slug', 'tags__name', 'created_at'],
        'organizations.organization': ['code', 'name', 'status', 'organization_type__name', 'tags__name'],
        # Add other models and their filterable fields
    }
    ```
[ ] Ensure DRF is installed and configured.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Filter Parser Implementation (`core/filtering/parser.py`)

  [ ] **(Test First - Parser Logic)**
      Write extensive **Unit Test(s)** (`core/tests/unit/test_filter_parser.py`) for the parsing logic:
      *   Test parsing simple conditions (`{"field": "name", "op": "icontains", "value": "test"}`) -> generates correct `Q(name__icontains='test')`.
      *   Test all supported operators (`eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `contains`, `icontains`, `startswith`, `endswith`, `in`, `notin`, `isnull`). Test correct Django lookup generation (e.g., `eq` -> `exact` or field name directly, `isnull` -> `__isnull`).
      *   Test handling of different value types (string, int, float, boolean, list for `in`/`notin`).
      *   Test parsing nested `AND` conditions (`{"and": [...]}`) -> generates `Q(...) & Q(...)`.
      *   Test parsing nested `OR` conditions (`{"or": [...]}`) -> generates `Q(...) | Q(...)`.
      *   Test deeply nested conditions (`{"and": [..., {"or": [...]}]}`).
      *   Test handling related field lookups (`field`: `category__slug`).
      *   Test error handling: invalid JSON input, unknown operator, unknown field (should be checked later by backend), invalid value type for operator. Raise a specific custom exception (e.g., `InvalidFilterError`).
      Run; expect failure (`parse_filter_json` function/class doesn't exist).
  [ ] Create `core/filtering/parser.py`. Implement the parser function/class `parse_filter_json(filter_dict)`:
      *   Takes the parsed JSON dictionary as input.
      *   Recursively traverses the dictionary structure.
      *   Identifies logical operators (`and`, `or`) and condition objects (`field`, `op`, `value`).
      *   Maps API operators (`eq`, `icontains`, etc.) to Django ORM lookup expressions (`exact`, `icontains`, etc.). Handles `isnull` specially.
      *   Constructs corresponding Django `Q` objects.
      *   Combines `Q` objects using `&` (for `and`) and `|` (for `or`).
      *   Perform basic type validation on values based on operator (e.g., `in` requires list).
      *   Raise `InvalidFilterError` for syntax errors or unknown operators.
      ```python
      # core/filtering/parser.py (Simplified Example Structure)
      from django.db.models import Q
      from django.core.exceptions import ValidationError # Or custom exception

      class InvalidFilterError(ValidationError):
          pass

      OPERATOR_MAP = {
          'eq': 'exact', 'neq': 'exact', # Handle negation later
          'gt': 'gt', 'gte': 'gte', 'lt': 'lt', 'lte': 'lte',
          'contains': 'contains', 'icontains': 'icontains',
          'startswith': 'startswith', 'istartswith': 'istartswith',
          'endswith': 'endswith', 'iendswith': 'iendswith',
          'in': 'in', 'notin': 'in', # Handle negation later
          'isnull': 'isnull',
          # Add others like exact, iexact if needed
      }

      def parse_filter_json(filter_dict):
          if not isinstance(filter_dict, dict):
              raise InvalidFilterError("Filter definition must be an object.")

          for logic_op, conditions in filter_dict.items():
              logic_op = logic_op.lower()
              if logic_op in ('and', 'or'):
                  if not isinstance(conditions, list):
                      raise InvalidFilterError(f"'{logic_op}' value must be a list.")
                  if not conditions: return Q() # Empty AND/OR is neutral

                  q_objects = [parse_filter_json(cond) for cond in conditions]

                  combined_q = Q()
                  if q_objects:
                      combiner = Q.AND if logic_op == 'and' else Q.OR
                      combined_q = q_objects[0]
                      for i in range(1, len(q_objects)):
                           combined_q.connector = combiner
                           combined_q.add(q_objects[i], combiner)
                  return combined_q

              elif logic_op == 'not': # Optional NOT support
                   if not isinstance(conditions, dict):
                       raise InvalidFilterError("'not' value must be an object.")
                   return ~parse_filter_json(conditions) # Negate the inner Q

              elif logic_op == 'field':
                  # This is a leaf condition: {"field": "f", "op": "o", "value": "v"}
                  op = filter_dict.get('op')
                  value = filter_dict.get('value') # Value might be absent for isnull
                  field_name = conditions # The value associated with "field" key

                  if not isinstance(field_name, str) or not op:
                      raise InvalidFilterError("Condition must have 'field' and 'op'.")

                  orm_lookup = OPERATOR_MAP.get(op.lower())
                  if not orm_lookup:
                      raise InvalidFilterError(f"Unsupported operator: {op}")

                  # Basic type checks and handling isnull/in
                  is_negated = op.lower().startswith('n') or op.lower() == 'neq'
                  if orm_lookup == 'isnull':
                      if not isinstance(value, bool):
                           raise InvalidFilterError("'isnull' operator requires boolean value (true/false).")
                      orm_value = value
                  elif orm_lookup == 'in':
                       if not isinstance(value, list):
                           raise InvalidFilterError("'in'/'notin' operator requires a list value.")
                       orm_value = value
                  else:
                       # Allow basic types, further validation might be needed
                       if isinstance(value, (dict, list)):
                            raise InvalidFilterError(f"Invalid value type for operator '{op}'.")
                       orm_value = value

                  q_filter = Q(**{f"{field_name}__{orm_lookup}": orm_value})

                  if is_negated:
                      return ~q_filter
                  else:
                      return q_filter
              else:
                  raise InvalidFilterError(f"Unknown filter key: {logic_op}")

          raise InvalidFilterError("Invalid filter structure.") # Should not be reached

      ```
  [ ] Run parser tests; expect pass. Refactor parser logic for robustness and clarity.

  ### 3.2 Custom Filter Backend Implementation (`core/filtering/backends.py`)

  [ ] **(Test First - Backend Logic)**
      Write **Integration Test(s)** (`core/tests/integration/test_filter_backends.py`) using `@pytest.mark.django_db`.
      *   Simulate an HTTP request (`RequestFactory`) with a valid JSON filter string in query params (`?filter=...`).
      *   Instantiate the `AdvancedFilterBackend` (doesn't exist yet).
      *   Call `backend.filter_queryset(request, initial_queryset, view)`.
      *   Assert the returned queryset contains only the expected filtered objects.
      *   Test with invalid JSON -> expect specific exception (e.g., `InvalidFilterError`).
      *   Test filtering on a disallowed field -> expect specific exception or empty result.
      *   Test with nested AND/OR logic.
      Run; expect failure.
  [ ] Create `core/filtering/backends.py`. Implement `AdvancedFilterBackend`:
      ```python
      # core/filtering/backends.py
      import json
      from urllib.parse import unquote
      from django.conf import settings
      from django.core.exceptions import FieldDoesNotExist, ValidationError
      from rest_framework.filters import BaseFilterBackend
      from rest_framework.exceptions import ParseError
      from .parser import parse_filter_json, InvalidFilterError # Import parser

      def get_allowed_fields_for_model(model):
          """Helper to get allowed fields from settings."""
          app_label = model._meta.app_label
          model_name = model._meta.model_name
          return settings.ALLOWED_FILTER_FIELDS.get(f"{app_label}.{model_name}", [])

      def validate_filter_fields(filter_dict, allowed_fields):
          """Recursively check if all fields in the filter are allowed."""
          if not isinstance(filter_dict, dict): return True # Let parser handle basic structure error

          for key, value in filter_dict.items():
              key = key.lower()
              if key in ('and', 'or'):
                  if not isinstance(value, list): return True # Parser handles
                  for condition in value:
                      if not validate_filter_fields(condition, allowed_fields):
                          return False
              elif key == 'not':
                   if not validate_filter_fields(value, allowed_fields):
                       return False
              elif key == 'field':
                  # Check the field name (value associated with 'field' key)
                  # Basic check: ignore __ lookups for now, or split and check base field?
                  base_field = value.split('__')[0]
                  if base_field not in allowed_fields:
                       # More robust check: try getting the field from model._meta
                       # to handle relations implicitly allowed via model definition
                       try:
                           # This check might be too slow, config list is safer
                           # model_class._meta.get_field(value)
                           if value not in allowed_fields: # Check full path if needed
                               raise InvalidFilterError(f"Filtering on field '{value}' is not allowed for this resource.")
                       except (FieldDoesNotExist, InvalidFilterError) as e:
                           raise InvalidFilterError(f"Filtering on field '{value}' is not allowed or invalid: {e}")
                  # Field is allowed (or is a relation we assume is allowed)
              # Ignore 'op', 'value' keys
          return True


      class AdvancedFilterBackend(BaseFilterBackend):
          """
          Applies complex, nested filters from a 'filter' query parameter
          containing URL-encoded JSON.
          """
          query_param = 'filter'

          def filter_queryset(self, request, queryset, view):
              filter_param_json = request.query_params.get(self.query_param, None)

              if not filter_param_json:
                  return queryset

              try:
                  # URL Decode before JSON parsing
                  decoded_json_str = unquote(filter_param_json)
                  filter_definition = json.loads(decoded_json_str)
              except (json.JSONDecodeError, TypeError) as e:
                  raise ParseError(f"Invalid JSON in '{self.query_param}' parameter: {e}")

              # Validate allowed fields before parsing to Q objects
              model_class = queryset.model
              allowed_fields = get_allowed_fields_for_model(model_class)
              if not allowed_fields: # If model not configured, disallow filtering
                   # Or maybe allow if empty list means "no restrictions"? Be explicit.
                   return queryset # Or raise configuration error?

              try:
                   validate_filter_fields(filter_definition, allowed_fields)
                   q_object = parse_filter_json(filter_definition)
              except InvalidFilterError as e:
                  raise ParseError(str(e)) # Return 400
              except Exception as e:
                  # Log unexpected parser errors
                  import logging
                  logger = logging.getLogger(__name__)
                  logger.error(f"Unexpected error parsing filter: {e}", exc_info=True)
                  raise ParseError("Error processing filter definition.")

              if q_object:
                   try:
                       return queryset.filter(q_object)
                   except (FieldError, ValueError) as e: # Catch ORM errors from invalid lookups/values
                       raise ParseError(f"Invalid filter application: {e}")
              else:
                   return queryset # Empty filter definition
      ```
  [ ] Run backend tests; expect pass. Refactor backend logic (esp. `validate_filter_fields` and error handling).

  ### 3.3 Integrate Backend into ViewSets

  [ ] **(Test First)** Add API tests for specific ViewSets (e.g., `ProductViewSet`) using the `?filter={...}` query parameter with valid JSON structures relevant to that model. Verify correct filtering and error handling for disallowed fields specific to that model.
  [ ] Add the custom backend to DRF settings or base ViewSet:
      ```python
      # config/settings/base.py (Example global default)
      REST_FRAMEWORK = {
          # ... other settings
          'DEFAULT_FILTER_BACKENDS': [
              # 'django_filters.rest_framework.DjangoFilterBackend', # Keep if using both
              'core.filtering.backends.AdvancedFilterBackend', # Adjust import path
              'rest_framework.filters.SearchFilter',
              'rest_framework.filters.OrderingFilter',
          ],
          # ...
      }
      # OR add to specific ViewSets/Base classes:
      # class MyBaseViewSet(OrganizationScopedViewSetMixin, ...):
      #    filter_backends = [AdvancedFilterBackend, OrderingFilter, SearchFilter]
      ```
  [ ] Run API tests for specific ViewSets; expect pass.

  ### 3.4 Stored Filters (Deferred)

  [ ] *(Skip these steps if Stored Filters are deferred)*
  [ ] **(Test First)** Write tests for `StoredFilter` model, serializer, and API endpoints (CRUD, permissions). Write tests for applying stored filters via `?apply_filter=...` param.
  [ ] Implement `StoredFilter` model, serializer, ViewSet, URLs.
  [ ] Modify `AdvancedFilterBackend` to check for `apply_filter` param, fetch definition from `StoredFilter`, parse it, and potentially combine with ad-hoc `filter` param.
  [ ] Implement permissions for managing/using stored filters.
  [ ] Run tests; expect pass.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`). Ensure filter tests pass for multiple models.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=core/filtering`). Review parser and backend logic coverage.
[ ] Manually test complex queries via API client against various endpoints. Test URL encoding/decoding. Test error handling.
[ ] Review API documentation draft for the chosen filter syntax and allowed fields per model.

## 5. Follow-up Actions

[ ] Address TODOs (Refine field validation, parser error details).
[ ] Decide on and document the **official query parameter syntax** (Option A/B/C) clearly in API docs.
[ ] Document the `ALLOWED_FILTER_FIELDS` setting and process for adding fields/models.
[ ] Create Pull Request.
[ ] Update API documentation with detailed examples.
[ ] Implement `StoredFilter` functionality if/when required.

--- END OF FILE advanced_filtering_implementation_steps.md ---