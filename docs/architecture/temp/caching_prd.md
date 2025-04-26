# Caching Strategy (Using Redis) - ERP System

## 1. Overview

*   **Purpose**: To define the strategy, guidelines, and best practices for implementing caching within the ERP system to improve performance, reduce database load, and enhance scalability.
*   **Scope**: Covers the choice of caching backend, key naming conventions, data candidates for caching, invalidation strategies, implementation patterns, and monitoring.
*   **Target Audience**: Developers implementing features, System Architects, DevOps managing infrastructure.

## 2. Goals of Caching

*   **Improve API Response Times**: Reduce latency for frequently accessed data or computationally expensive operations.
*   **Reduce Database Load**: Decrease the number of repetitive queries hitting the primary database.
*   **Enhance Scalability**: Allow the system to handle more concurrent users/requests by relying on faster cache lookups.
*   **Improve User Experience**: Faster load times lead to a more responsive application.

## 3. Chosen Technology: Redis via `django-redis`

*   **Backend**: **Redis** will be the primary caching backend for production and staging environments due to its speed, flexibility (data structures), persistence options, and mature ecosystem.
*   **Django Integration**: The **`django-redis`** library will be used to integrate Redis with Django's caching framework (`django.core.cache`).
*   **Development/Testing**: Django's **`LocMemCache`** (`django.core.cache.backends.locmem.LocMemCache`) can be used for local development and most unit/integration tests for simplicity, but tests specifically verifying Redis interactions or complex invalidation patterns may require a running Redis instance (or `fakeredis`).

## 4. Cache Backend Configuration (`settings.py`)

*   Multiple cache aliases **should** be configured in `settings.py` to allow for different configurations (e.g., timeouts, eviction policies) for different types of data.
*   **Example Configuration:**
    ```python
    CACHES = {
        # Default cache alias - for general purpose, shorter TTL caching
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/1', # Use different DB number
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {"max_connections": 50},
                # Consider serializers/compressors if needed
                # 'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
                # 'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            },
            'TIMEOUT': 300, # Default timeout in seconds (5 minutes)
        },
        # Cache for user sessions (if using cache-based sessions)
        'sessions': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/2', # Separate DB
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'TIMEOUT': None, # Or session-specific timeout from settings
        },
        # Cache specifically for permissions (potentially longer TTL, critical data)
        'permissions': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/3', # Separate DB
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'TIMEOUT': 3600, # Example: 1 hour TTL
        },
        # Alias for potentially expensive API responses (if doing full response caching)
        'api_responses': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/4',
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'TIMEOUT': 600, # Example: 10 minutes TTL
        },
        # Add other aliases as needed (e.g., 'reports', 'configuration')
    }

    # Define which cache alias Django uses by default
    DJANGO_REDIS_CACHE_ALIAS = 'default'
    ```
*   Use environment variables to configure `LOCATION` (Redis host, port, DB, password) for different deployment environments.

## 5. Key Naming Conventions

*   **Goal**: Avoid key collisions, allow for targeted invalidation, and make keys understandable.
*   **Standard Format**: `<app_label>:<model_name>:<identifier>:<subset_or_context>`
*   **Components**:
    *   `app_label`: Django app name (e.g., `products`, `organizations`, `rbac`).
    *   `model_name`: Lowercase model name (e.g., `product`, `organization`, `userprofile`).
    *   `identifier`: Primary key or unique slug of the specific object (e.g., `123`, `abc-widget`). Use `list` for cached lists. Use `config` for settings.
    *   `subset_or_context`: Describes *what* specific data about the object is cached (e.g., `details`, `permissions`, `full_api_v1`, `summary`). For lists, might include filter parameters (hashed or carefully constructed).
*   **Examples**:
    *   `products:product:123:details`
    *   `rbac:user:5:org_permissions`
    *   `organizations:organization:list:active_type_customer`
    *   `core:currency:list:active`
*   **Implementation**: Use helper functions to generate keys consistently. Ensure parameters used in generating keys are always in the same order. Consider hashing complex parameters if keys become too long.

## 6. What to Cache (Guidelines & Initial Candidates)

*   **Cache data that is read much more often than it is written.**
*   **Cache data that is expensive to compute or retrieve.**
    *   Complex database queries (multiple joins, aggregations, large offsets).
    *   Results of external API calls.
    *   Serialized data for API responses (especially for read-only or rarely changing data).
    *   Rendered template fragments (less relevant for pure API backend).
    *   Computed properties or results from complex service functions.
*   **Initial Candidates (Based on ERP models):**
    *   **User Permissions/Roles (RBAC PRD):** Cache resolved permissions per user (potentially per org). Use the `permissions` cache alias. Critical for performance. Requires careful invalidation on role/permission changes.
    *   **Frequently Accessed Configuration/Settings:** Data that rarely changes but is read often (e.g., system settings, potentially active `Status`, `UoM`, `Currency`, `OrganizationType` lists). Use `default` or a dedicated `config` alias.
    *   **Organization/User Profile Data:** Frequently accessed fields for the current user or related orgs.
    *   **API List Endpoint Results:** Consider caching results for common, non-personalized list views (e.g., list of active Products in a category), potentially using DRF caching extensions, but be wary of invalidation complexity. Use `api_responses` alias.
    *   **Reference Data Lookups:** E.g., `TaxRate` lookups based on jurisdiction/category/date.
*   **What NOT to Cache (Generally):**
    *   Highly volatile data where real-time accuracy is paramount (unless TTL is extremely short).
    *   Sensitive data *unless* properly secured/encrypted within the cache (Redis itself doesn't encrypt data at rest by default).
    *   Large objects that consume excessive memory without significant benefit.

## 7. Cache Timeouts (TTL - Time To Live)

*   **Default Strategy**: Use relatively short-to-medium TTLs by default (e.g., 5-15 minutes via `default` alias `TIMEOUT`). Rely on TTL expiration as the primary invalidation mechanism for non-critical data.
*   **Longer TTLs**: Use longer TTLs (e.g., 1 hour, 1 day via dedicated aliases like `permissions` or `config`) only for data that changes very infrequently AND has a robust event-based invalidation mechanism in place.
*   **`TIMEOUT=None` (Forever):** Use **EXTREMELY SPARINGLY**. Only suitable for data that *never* changes or where invalidation is guaranteed and foolproof. Prone to causing stale data issues.
*   **Overrides**: Allow developers to specify custom timeouts when calling `cache.set(key, value, timeout=...)`.

## 8. Cache Invalidation Strategies

*   **Goal**: Ensure cached data is removed or updated when the underlying source data changes. This is critical to prevent serving stale data.
*   **Primary Methods**:
    1.  **Time-Based (TTL):** (Default) Let entries expire automatically. Simplest, but introduces potential latency window for staleness.
    2.  **Explicit Deletion on Update (Event-Based):**
        *   **Mechanism:** Use Django signals (`post_save`, `post_delete`, `m2m_changed`) on relevant models.
        *   **Implementation:** Signal receivers identify the changed object and construct the corresponding cache key(s) that need invalidation, then call `cache.delete(key)` or `cache.delete_many([keys...])`.
        *   **Targeting:** Be specific. Invalidate only the keys related to the changed object (e.g., saving Product 123 should invalidate `products:product:123:details`, not the entire product list cache).
        *   **Example:**
            ```python
            # models.py (or signals.py)
            from django.db.models.signals import post_save
            from django.dispatch import receiver
            from django.core.cache import caches
            from .models import Product

            permission_cache = caches['permissions'] # Example: Use specific alias

            def _invalidate_product_cache(instance):
                # Use helper to generate keys
                keys_to_delete = [
                    f'products:product:{instance.pk}:details',
                    f'products:product:{instance.pk}:api_v1'
                ]
                caches['default'].delete_many(keys_to_delete) # Invalidate on default cache
                # Invalidate potentially related list caches (harder)
                # caches['default'].delete_pattern('products:product:list:*') # Use pattern deletion cautiously

            @receiver(post_save, sender=Product)
            def invalidate_product_on_save(sender, instance, **kwargs):
                _invalidate_product_cache(instance)

            # Similar receiver for post_delete needed
            ```
    3.  **Pattern Deletion (`django-redis`):** Use `cache.delete_pattern('prefix:*')`.
        *   **Use Case:** Useful for invalidating groups of related keys (e.g., all cached list views for products).
        *   **Warning:** Can be **slow and resource-intensive** on Redis instances with many keys. Use judiciously, prefer deleting specific keys when possible.
    4.  **Key Versioning (Advanced):** Include a version number in cache keys (e.g., `product:123:details:v2`). When data changes, increment the version number associated with the object. New requests will generate keys with the new version (cache miss), effectively invalidating old entries without explicit deletion. Requires managing the version number.

*   **Chosen Strategy**: Prioritize **TTL** for general caching and **Event-Based Explicit Deletion via Signals** for critical data or where longer TTLs are used. Use `delete_pattern` sparingly.

## 9. Implementation Patterns

*   **Direct API Usage**:
    ```python
    from django.core.cache import cache # Uses 'default' alias

    def get_product_details(product_id):
        cache_key = f'products:product:{product_id}:details'
        data = cache.get(cache_key)
        if data is None:
            # Data not in cache, fetch from DB
            try:
                product = Product.objects.select_related(...).get(pk=product_id)
                data = {'name': product.name, 'sku': product.sku, ...} # Prepare data
                cache.set(cache_key, data, timeout=600) # Cache for 10 mins
            except Product.DoesNotExist:
                return None # Or raise error
        return data
    ```
*   **Decorators**: Use built-in (`@cached_property` on models) or custom decorators to simplify caching logic for functions/methods.
*   **Cache Aliases**: Use `caches['alias_name']` to interact with specific configured backends.

## 10. Advanced Considerations

*   **Cache Stampede (Dogpile Effect):** When a popular cached item expires, multiple requests might try to regenerate it simultaneously, overloading the database.
    *   **Mitigation:** Use techniques provided by `django-redis` (locking within `cache.get_or_set`) or simple probabilistic checks. Shorter TTLs reduce the window.
*   **Thundering Herd:** Similar issue when invalidating many keys at once triggers regeneration storms. Staggered invalidation or probabilistic regeneration can help.

## 11. Monitoring

*   **Redis Monitoring**: Use Redis-specific tools (`redis-cli MONITOR`, `INFO`, external monitoring services like Datadog, Prometheus exporters) to track memory usage, hit rate, evictions, latency, connections.
*   **Application Monitoring**: Log cache hits/misses within the application (potentially sampled) to understand cache effectiveness. Monitor performance of signal handlers/invalidation tasks. Track cache-related errors.

## 12. Testing

*   **Unit/Integration Tests**:
    *   Configure `CACHES` setting in test environment, often using `LocMemCache` for simplicity.
    *   Test functions/methods that use caching: verify data is retrieved from cache on subsequent calls, verify cache is populated correctly.
    *   **Test Invalidation:** This is critical. Trigger signals (e.g., save a model instance) and verify that the relevant cache keys *are* deleted or updated. Requires careful mocking or specific cache setup for tests. Use `cache.clear()` in test `setUp/tearDown` to ensure clean state.
*   **Redis-Specific Tests**: If relying on specific Redis features or complex invalidation, integration tests against a real Redis instance (or `fakeredis`) might be necessary.

## 13. Gotchas / Best Practices

*   **Invalidation is the Hardest Part:** Prioritize simple, reliable invalidation (TTL, explicit delete via signals) over complex strategies initially.
*   **Key Naming Consistency:** Strictly enforce key naming conventions.
*   **Cache Selectively:** Don't cache everything. Profile the application to find actual bottlenecks.
*   **Test Thoroughly:** Especially invalidation logic. Stale cache data can cause subtle and hard-to-debug issues.
*   **Monitor:** Keep an eye on cache performance, memory usage, and hit rates.
*   **Security:** Don't cache sensitive, unencrypted user data directly unless the cache backend itself is appropriately secured.

---