
## 2. Redis Strategy (Cache & Celery Broker)

**(Equivalent to a focused PRD for Redis setup and usage)**

### 2.1. Overview

*   **Purpose**: To define the setup and usage strategy for Redis as the primary backend for Django's caching framework and as the message broker for Celery task queues.
*   **Scope**: Choice of Redis, configuration within Django (`django-redis`), local setup, key usage patterns, and integration points.
*   **Chosen Technology**: **Redis** (Target Version: 6.x+). **`django-redis`** library for cache integration.

### 2.2. Core Requirements

*   **Fast In-Memory Cache**: Provide low-latency caching for frequently accessed data (permissions, configurations, API results).
*   **Reliable Message Broker**: Serve as a robust transport for Celery task messages between the Django application and Celery workers/beat.
*   **Support Required Features**: Provide necessary Redis commands/data structures used by `django-redis` and Celery.

### 2.3. Configuration Strategy (`config/settings/`, `core/redis/`)

*   Use Django's `settings.CACHES` dictionary, configured with `django_redis.cache.RedisCache` backend. Define multiple aliases (`default`, `permissions`, `api_responses`, etc.) potentially pointing to different Redis logical databases (DB numbers) or even instances if needed for isolation. Set default `TIMEOUT` per alias.
*   Configure `settings.CELERY_BROKER_URL` pointing to a specific Redis instance/database (e.g., `redis://[:password@]host:port/0`).
*   Configure `settings.CELERY_RESULT_BACKEND` (if needed) potentially also pointing to Redis.
*   Connection URLs/details **must** be loaded from environment variables.
*   The `core/redis/config.py` might contain helper functions for complex cache key generation or specific Redis interactions if needed beyond the standard cache API, but core connection setup is via settings.

### 2.4. Local Development Setup (`docker-compose.yml`)

*   Utilize the official `redis:<version>` Docker image in `docker-compose.yml`.
*   Expose the Redis port (e.g., 6379).
*   Persistence via Docker volume is optional for local dev cache/broker but can be useful.

### 2.5. Integration Points

*   **Caching**: Accessed via Django's cache framework (`from django.core.cache import caches; cache = caches['default']` or `from django.core.cache import cache`). Used by application code, RBAC permission checks, potentially DRF caching extensions.
*   **Celery Broker**: Configured via settings, used implicitly by Celery producer (e.g., `task.delay()`) and consumers (workers).
*   **Django Channels Layer (If used):** Potentially configured via `settings.CHANNEL_LAYERS` using `channels_redis.core.RedisChannelLayer`.

### 2.6. Security Considerations

*   Enable Redis password protection (`requirepass`) in production/staging, managed via secure environment variables.
*   Limit network access to the Redis server.
*   Use TLS if connecting over untrusted networks.

### 2.7. Monitoring Considerations

*   Monitor key Redis metrics: Memory usage (`used_memory_rss`, `maxmemory`), key count, connections (`connected_clients`), commands per second, latency, cache hit ratio (`keyspace_hits`/`keyspace_misses`), evictions/expirations. Use `redis-cli INFO` or external monitoring tools.

### 2.8. Backup & Recovery Strategy

*   **Cache:** Generally acceptable to lose cache data on restart. Configure Redis persistence (RDB snapshots/AOF) mainly for faster restarts, not critical data recovery.
*   **Broker:** For Celery, enabling Redis persistence (especially AOF - Append Only File) is recommended to minimize task loss if the broker restarts unexpectedly. Ensure backups of the AOF/RDB files if broker state recovery is critical.

### 2.9. Testing Considerations

*   Configure `settings.CACHES` in `settings/test.py` to use **`LocMemCache`** (`django.core.cache.backends.locmem.LocMemCache`) for most tests to avoid Redis dependency.
*   Celery tests using `CELERY_TASK_ALWAYS_EAGER=True` bypass the need for a running broker during testing.
*   For tests specifically targeting Redis features or complex cache invalidation, use `fakeredis` or integration tests requiring a running Redis instance.

### 2.10. Deployment Considerations

*   Ensure the Redis instance(s) exist and are accessible.
*   Configure application settings with correct connection details/passwords for the environment.
*   Consider Redis Sentinel or Cluster for high availability in production if required.
