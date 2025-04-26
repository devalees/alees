
# API Design & Development Strategy

## 1. Overview

This document outlines the strategy and conventions for designing, developing, and managing the RESTful API for the ERP system. Consistency, usability, security, and performance are key goals.

## 2. API Style

*   **Style:** The API will adhere to **REST (Representational State Transfer)** principles.
*   **Format:** **JSON** will be the exclusive data format for request bodies and responses. `Content-Type: application/json`, `Accept: application/json`.
*   **URL Naming:** Use plural nouns for resource collections (e.g., `/api/v1/organizations/`, `/api/v1/products/`). Use resource IDs for specific instances (e.g., `/api/v1/organizations/{id}/`). Use verbs for non-CRUD actions (e.g., `/api/v1/invoices/{id}/send/`). Use **underscores (`_`)** consistently in URL path segments for readability (e.g., `/api/v1/organization_types/`, `/api/v1/data_jobs/`).
*   **HTTP Methods:** Use standard HTTP methods correctly:
    *   `GET`: Retrieve resources (list or detail). Safe and idempotent.
    *   `POST`: Create new resources or trigger actions. Not safe or idempotent.
    *   `PUT`: Replace an existing resource entirely (requires all fields). Idempotent.
    *   `PATCH`: Partially update an existing resource (only include fields to change). Not necessarily idempotent.
    *   `DELETE`: Remove a resource. Idempotent.
*   **Statelessness:** API requests should be stateless. The server will not rely on session state between requests for core resource manipulation. Authentication state is managed via tokens/keys sent with each request.

## 3. Authentication & Authorization

*   **Authentication Methods:** The API **must** support multiple authentication methods, selectable per endpoint or configuration where appropriate:
    1.  **JWT (Primary for UI/Mobile Clients):**
        *   Clients authenticate using credentials (`username`/`password`) via a dedicated login endpoint (e.g., `/api/v1/auth/token/obtain/`) to get short-lived Access Tokens and longer-lived Refresh Tokens.
        *   Access Tokens sent in the `Authorization: Bearer <access_token>` HTTP header with subsequent requests.
        *   Refresh Tokens used via a dedicated endpoint (e.g., `/api/v1/auth/token/refresh/`) to obtain new Access Tokens without re-entering credentials.
        *   **Library:** Utilize **`djangorestframework-simplejwt`**. Configure token lifetimes (access and refresh) appropriately in settings.
    2.  **API Keys (Required for Server-to-Server/Third-Party):**
        *   **Purpose:** For programmatic access by trusted internal services, external partner systems, or specific integrations where a user login flow is not suitable or desired.
        *   **Implementation:** Utilize a dedicated library like **`djangorestframework-api-key`** or **`django-api-key`**. *(Choose one and specify)*. These libraries provide:
            *   Models to securely generate, store (hashed), and manage API Keys (`APIKey` model). Keys should have a prefix for identification and may be associated with a specific service name or a designated service `User` account.
            *   An administrative interface (e.g., Django Admin) for generating, revoking, setting expiry dates, and managing keys.
            *   Custom DRF Authentication Backend/Permission classes.
        *   **Usage:** Clients send the generated API Key via a **standardized custom HTTP header**. Choose one standard: e.g., **`Authorization: Api-Key <your_api_key>`** or **`X-API-Key: <your_api_key>`**. *(Decision required on header name)*.
        *   **Management:** Keys must be manageable by administrators. Keys must be treated as highly sensitive credentials and should not be hardcoded. Keys should have expiry dates. Keys can optionally be linked to a specific `User` account (often a dedicated service account) to inherit its permissions or scoped with specific permissions granted directly to the key via the chosen library's features.
*   **Authentication Selection:** DRF's `authentication_classes` setting (per-view or default) will list the enabled methods (e.g., `[JWTAuthentication, APIKeyAuthentication]`). DRF attempts authentication using each class in order until one succeeds.
*   **Authorization:**
    *   **Framework:** Leverage the **RBAC System** defined previously (using Django `Group` as Role, `Permission` for model-level, and custom `FieldPermission` for field-level).
    *   **Enforcement:**
        *   **Model-Level:** Use DRF `permission_classes` on ViewSets, checking standard Django permissions (`view_model`, `add_model`, `change_model`, `delete_model`) potentially combined with custom permission classes verifying organizational scope or specific roles.
        *   **Field-Level:** Enforced within Serializers (`get_fields`, `validate`, `create`, `update`) using the `has_field_permission()` check function defined in the RBAC strategy.
        *   **Object-Level:** DRF `get_object()` combined with `has_object_permission` checks within permission classes.
    *   **Scoping:** All checks must respect the `OrganizationScoped` context. Permissions for API Key authentication will be determined by the user/permissions associated with the specific key used.

## 4. Versioning

*   **Strategy:** **URL Path Versioning**.
*   **Implementation:** All API endpoints will be prefixed with the version number, e.g., `/api/v1/...`, `/api/v2/...`.
*   **Management:** Use Django URL namespaces and the chosen project structure (likely separate `urls.py` files within `api/v1/`, `api/v2/`).
*   **Deprecation:** Define a clear policy for deprecating older API versions, including communication timelines, logging usage of deprecated versions, and eventual sunset dates (returning appropriate status codes like `410 Gone`).

## 5. Standard Response & Error Formats

*   **Goal:** Provide consistent, predictable, and informative responses for both success and error conditions.

*   **Successful Responses (`2xx` Status Codes):**
    *   **`GET /resource/` (List):** Standard DRF paginated response structure.
        ```json
        {
          "count": 123,
          "next": "url_to_next_page_or_null",
          "previous": "url_to_previous_page_or_null",
          "results": [ /* Array of serialized objects */ ]
        }
        ```
    *   **`GET /resource/{id}/` (Detail):** Full serialized object.
        ```json
        { /* Serialized object fields */ }
        ```
    *   **`POST /resource/` (Create):** Status `201 Created`. Body is the full representation of the newly created resource.
        ```json
        { /* Serialized object fields, including new ID */ }
        ```
    *   **`PUT /resource/{id}/`, `PATCH /resource/{id}/` (Update):** Status `200 OK`. Body is the full representation of the updated resource.
        ```json
        { /* Updated serialized object fields */ }
        ```
    *   **`DELETE /resource/{id}/` (Delete):** Status `204 No Content`. Empty body.
    *   **`POST /resource/{id}/action/` (Action):** Status `200 OK` (sync) or `202 Accepted` (async). Body includes status message, optionally relevant data or `job_id`.
        ```json
        {
          "status": "success" | "accepted",
          "message": "Action completed/queued successfully.",
          "job_id": "abc-123" // If async
        }
        ```

*   **Error Responses (`4xx` & `5xx` Status Codes):**
    *   **Standard Structure:** Use a list containing one or more error objects.
        ```json
        {
          "errors": [
            {
              "status": "4xx or 5xx", // String representation of HTTP status code
              "code": "application_specific_code", // Unique code, e.g., validation_error
              "detail": "Human-readable explanation.", // General error message
              "source": { // Optional: Pointer to error origin
                "pointer": "/data/attributes/email", // JSON Pointer (RFC 6901) for request body field
                // "parameter": "filter_param_name" // For query parameter errors
              },
              "meta": { // Optional: Additional details
                 "field_errors": { /* DRF field validation errors */ },
                 "allowed_methods": ["GET", "POST"] // For 405 errors
              }
            }
          ]
        }
        ```
    *   **Key Components Defined:** `errors` (list), `status` (string), `code` (string, defined list), `detail` (string), `source` (optional object), `meta` (optional object with `field_errors` for validation).
    *   **Common Codes:** `invalid_request`, `validation_error`, `authentication_failed`, `permission_denied`, `not_found`, `method_not_allowed`, `rate_limit_exceeded`, `internal_server_error`.
    *   **Implementation:** Utilize DRF Exception Handling with a custom exception handler to enforce this structure consistently.

## 6. Serialization Strategy

*   **Tool:** Use **Django Rest Framework Serializers** (`serializers.Serializer`, `serializers.ModelSerializer`).
*   **Field Exposure:** Use `fields = [...]` or `exclude = [...]` explicitly. Default to exposing only necessary fields.
*   **Read/Write Control:** Use `read_only=True`, `write_only=True` appropriately. Field-level RBAC provides dynamic control.
*   **Relationships:**
    *   **Read:** Default to Primary Keys. Use nested serializers selectively (with `read_only=True`) for detail views or simple embeds, managing depth. Use `StringRelatedField` for simple names.
    *   **Write:** Accept Primary Keys. Implement natural key lookups (e.g., using `SlugRelatedField` or custom logic) for user-friendliness where appropriate.
*   **Performance:** **Crucially use `select_related` and `prefetch_related` in ViewSet `get_queryset()`** to optimize database queries based on serializer fields, especially nested ones.
*   **Validation:** Implement all input validation within serializers (`validate_<field>`, `validate`).
*   **Custom Fields (`JSONField`):**
    *   **Read:** Include as `serializers.JSONField(read_only=True)`.
    *   **Write:** Implement `validate_custom_fields` method in relevant serializers to validate against external schemas.
*   **Data Transformation:** Use `SerializerMethodField`, `to_representation`, `to_internal_value` for API-specific formatting.

## 7. Rate Limiting

*   **Strategy:** Implement rate limiting using DRF throttling.
*   **Implementation:** Use `AnonRateThrottle`, `UserRateThrottle`. Consider `ScopedRateThrottle` for different limits on specific endpoints or user tiers.
*   **Configuration:** Define rates (e.g., `'user': '1000/hour'`, `'anon': '100/hour'`) in `settings.py` (`REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']`).
*   **Response:** Return `429 Too Many Requests` with `Retry-After` header.

## 8. Development Guidelines

*   Follow the chosen project structure (API code within `api/vX/` directories).
*   Write comprehensive tests (Unit for serializers, Integration/API for views/endpoints).
*   Document endpoints using OpenAPI/Swagger (`drf-spectacular` recommended).
*   Adhere strictly to standard response/error formats via custom exception handler.
*   Prioritize security: validate input, check permissions thoroughly.

--- END OF FILE api_strategy.md ---