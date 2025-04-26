
# Monitoring & Observability Strategy

## 1. Overview

*   **Purpose**: To define the strategy for monitoring the health, performance, and behavior of the ERP backend application and its supporting infrastructure, enabling proactive issue detection, efficient troubleshooting, and performance analysis.
*   **Scope**: Covers the selection of monitoring tools, application instrumentation (metrics, logging, tracing, error tracking), health checks, and basic alerting principles. Excludes building an internal monitoring platform.
*   **Goal**: Achieve comprehensive observability into the production and staging environments, allowing rapid detection and diagnosis of problems, and providing insights for performance optimization.
*   **Approach**: Integrate with a suite of external, specialized monitoring and observability tools. Instrument the Django application to expose necessary data to these tools.

## 2. Core Principles

*   **External Tooling**: Leverage established, best-practice external monitoring platforms rather than building monitoring capabilities natively within the ERP.
*   **The Three Pillars of Observability**: Aim to collect data covering:
    *   **Metrics**: Time-series numerical data representing system/application performance and behavior (e.g., request latency, error rates, queue lengths, CPU usage).
    *   **Logs**: Timestamped records of events occurring within the application or infrastructure (as defined in `logging_strategy.md`).
    *   **Traces**: Represent the flow of a single request as it travels through different services or components (essential for microservices, useful even in monoliths with async tasks).
*   **Actionable Data**: Monitoring should provide data that leads to actionable insights for performance improvement, debugging, or scaling.
*   **Automation**: Automate metric/log collection and alerting as much as possible.
*   **Contextualization**: Ensure metrics, logs, and traces include relevant context (environment, service, user ID, org ID, request/trace ID) for effective correlation.

## 3. Chosen Monitoring Stack (Example - Adapt as needed)

This strategy assumes a common open-source stack, but can be adapted for commercial platforms like Datadog, New Relic, etc.

*   **Metrics Collection & Storage**: **Prometheus**
    *   Application exposes metrics via an HTTP endpoint (e.g., `/metrics`).
    *   Prometheus server scrapes these endpoints periodically.
    *   Stores metrics in a time-series database.
*   **Metrics Visualization & Dashboards**: **Grafana**
    *   Connects to Prometheus (and other data sources like Loki/Elasticsearch).
    *   Used to build dashboards visualizing key metrics and logs.
*   **Log Aggregation & Querying**: **Loki** (or Elasticsearch/OpenSearch via ELK/EFK stack)
    *   Receives structured logs forwarded by collection agents (Promtail, Fluentd, Filebeat).
    *   Provides efficient storage and querying (LogQL for Loki).
*   **Log Collection Agent**: **Promtail** (for Loki) or Fluentd/Filebeat (for ELK/EFK). Runs alongside application containers/instances to collect logs (from stdout/stderr or files).
*   **Alerting**: **Alertmanager** (integrates with Prometheus)
    *   Defines alert rules based on Prometheus metrics.
    *   Handles alert silencing, grouping, and routing to notification channels (Slack, PagerDuty, Email).
*   **Error Tracking & Aggregation**: **Sentry** (Open Source or SaaS)
    *   SDK integrated into the Django application captures unhandled exceptions and explicit error reports.
    *   Groups similar errors, provides context (stack traces, user info, request data), and integrates with issue trackers.

## 4. Application Instrumentation

### 4.1. Metrics Exposure (`django-prometheus`)
*   **Library**: Utilize `django-prometheus` library.
*   **Configuration**: Add `'django_prometheus'` to `INSTALLED_APPS`. Include its middleware (`PrometheusBeforeMiddleware`, `PrometheusAfterMiddleware`) in `settings.MIDDLEWARE`. Expose the `/metrics` endpoint via `urls.py`.
*   **Default Metrics**: The library automatically exports various metrics (request counts/latency, database interaction timings, cache stats, etc.).
*   **Custom Metrics**: Define custom Prometheus metrics (Counters, Gauges, Histograms, Summaries) within application code to track specific business events or performance indicators (e.g., number of orders processed, specific API endpoint usage, queue processing time). Use `django-prometheus` utilities (`exports.ExportModelOperationsMixin` on Admin, custom collectors).

### 4.2. Structured Logging
*   **Strategy**: Follow the separate `logging_strategy.md`.
*   **Format**: JSON format with standard fields (timestamp, level, logger, message, user_id, org_id, request_id, trace_id, etc.).
*   **Collection**: Configure application to log to `stdout`/`stderr` (for containers) or files, to be collected by Promtail/Fluentd/Filebeat.

### 4.3. Error Tracking (Sentry)
*   **Library**: Integrate the `sentry-sdk` for Python/Django.
*   **Configuration**: Configure the Sentry DSN (Data Source Name) via environment variables in `settings.py`. Initialize the SDK early in the application lifecycle (e.g., `settings.py` or `wsgi.py`/`asgi.py`).
*   **Data Capture**: The SDK automatically captures unhandled exceptions. Use `sentry_sdk.capture_message()` or `sentry_sdk.capture_exception()` for manually reporting errors or warnings.
*   **Context**: Configure the SDK to automatically include user information (`id`, `username`, `email`), request data, and potentially custom tags (like `organization_id`) with error reports.

### 4.4. Distributed Tracing (Optional - Advanced)
*   **Purpose**: Track requests across multiple services or asynchronous tasks (e.g., API request -> Celery task -> external API call).
*   **Implementation**: Requires integrating an OpenTelemetry-compatible library or platform-specific SDK (e.g., Datadog APM, Jaeger client). Involves instrumenting code (often automatically via middleware/library hooks) to propagate trace IDs and report timing spans for different operations.
*   **Initial Scope**: Likely deferred unless microservices or complex async workflows are central from the start. Basic Request ID logging provides some correlation.

### 4.5. Health Check Endpoints
*   **Requirement**: Implement standard health check endpoints for load balancers, container orchestrators (e.g., Kubernetes probes), and basic availability monitoring.
*   **Endpoints**:
    *   `/healthz` or `/livez` (Liveness probe): Simple check, returns `200 OK` if the application process is running. Should not have external dependencies (like DB).
    *   `/readyz` (Readiness probe): More comprehensive check, returns `200 OK` only if the application is ready to serve traffic (e.g., can connect to the database, cache, essential services).
*   **Implementation**: Simple Django views returning `HttpResponse("OK")`.

## 5. Alerting Strategy

*   **Tool**: Use the alerting capabilities of the chosen monitoring platform (e.g., Alertmanager, Datadog Monitors).
*   **Focus**: Define alerts for critical conditions indicating user impact or system failure:
    *   **Error Rates:** High percentage of `5xx` HTTP status codes, high rate of exceptions reported to Sentry.
    *   **Latency:** API endpoint latency (p95, p99) exceeding defined thresholds.
    *   **Resource Saturation:** High CPU/Memory/Disk utilization on application servers or database.
    *   **Queue Lengths:** Celery queue backlog exceeding thresholds for extended periods.
    *   **External Service Availability:** High error rates when calling critical external APIs.
    *   **Health Checks:** Probes failing consistently.
    *   **Critical Business Metrics:** (e.g., Order processing rate drops significantly).
*   **Configuration**: Define alert rules, thresholds, evaluation periods, and notification channels (Slack, PagerDuty, Email) within the monitoring platform.

## 6. Dashboards

*   **Tool**: Use Grafana (or the chosen platform's dashboarding feature).
*   **Purpose**: Visualize key metrics and logs to provide an overview of system health and performance.
*   **Key Dashboards**:
    *   **Application Overview:** Request rate, error rate (4xx/5xx), latency percentiles (overall and per-endpoint).
    *   **Database Performance:** Connection count, query latency, CPU/Memory/IO utilization.
    *   **Celery/Queue Performance:** Queue lengths, task execution times, worker counts, success/failure rates.
    *   **Infrastructure Resources:** CPU, Memory, Disk, Network I/O for application instances, DB, Cache, Search Engine nodes.
    *   **Business Metrics:** Key application-specific counters/gauges.

## 7. Testing

*   **Instrumentation Tests**: Verify metrics endpoints (`/metrics`) expose expected data. Verify logs are generated in the correct JSON format with context. Verify errors are sent to Sentry. Verify health check endpoints return `200 OK`.
*   **Alerting Tests**: Test alert rule configuration in the monitoring platform (often requires manual triggering or specific test environments).

## 8. Deployment & Configuration

*   Deploy chosen monitoring infrastructure (Prometheus, Grafana, Loki, Alertmanager, Sentry instance or configure SaaS).
*   Deploy log collection agents (Promtail, Fluentd, etc.) alongside application instances.
*   Configure application (`settings.py`, environment variables) with endpoints/keys for Sentry, potentially logging endpoints.
*   Configure monitoring tools (Prometheus scrape targets, Grafana data sources, Alertmanager rules).

## 9. Maintenance

*   Keep monitoring agents and libraries updated.
*   Maintain and refine dashboards and alert rules based on operational experience.
*   Manage storage retention policies for metrics and logs in the external platforms.
*   Regularly review key dashboards and alert fatigue.

--- END OF FILE monitoring_strategy.md ---