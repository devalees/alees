
# Logging Strategy

## 1. Overview

*   **Purpose**: To establish a standardized approach for logging events, errors, and relevant diagnostic information throughout the ERP system backend, facilitating debugging, monitoring, auditing, and analysis.
*   **Scope**: Covers logging levels, log message format (structured JSON), key information fields to include, log collection methods, and integration with a centralized logging platform.
*   **Goals**: Consistency, Searchability, Contextual Information, Performance Awareness.

## 2. Core Principles

*   **Structured Logging**: Logs **must** be emitted in a machine-parseable format, preferably **JSON**. This allows for easy filtering, aggregation, and analysis in log management tools.
*   **Standard Fields**: Every log message should contain a consistent set of core fields for context.
*   **Meaningful Messages**: Log messages should be clear, concise, and provide actionable information. Avoid overly verbose or cryptic messages.
*   **Appropriate Levels**: Use standard logging levels correctly to indicate severity and filter logs effectively.
*   **Context is Key**: Include relevant contextual information (user, organization, request ID) whenever possible.
*   **Performance**: Logging should have minimal performance impact on the application. Avoid excessive logging in performance-critical code paths. Do not log excessively large objects directly.

## 3. Logging Levels

Use standard Python `logging` levels consistently:

*   **`DEBUG`**: Fine-grained information, typically useful only when diagnosing specific problems. Include details like function entry/exit, variable values, detailed query parameters (potentially sensitive, use with care). **Should generally be disabled in production.**
*   **`INFO`**: Confirmation that things are working as expected. Log routine events like service startup, successful completion of significant background tasks, user login/logout (may also be Audit events), configuration loading.
*   **`WARNING`**: Indication of an unexpected situation or potential problem that doesn't necessarily prevent the current operation from completing, but might require attention. Examples: Deprecated feature usage, recoverable errors, minor configuration issues, high resource usage nearing limits.
*   **`ERROR`**: A serious problem occurred preventing a specific operation/request from completing successfully. Typically associated with exceptions caught in `try...except` blocks where the error couldn't be handled gracefully.
*   **`CRITICAL`**: A very serious error indicating the application itself might be unstable or unable to continue running. Examples: Cannot connect to database, essential service unavailable, unrecoverable corruption.

## 4. Standard Log Format & Key Information Fields (JSON)

Every log record emitted should ideally be a JSON object containing *at least* the following standard fields:

```json
{
  // Standard Python Logging Attributes (often added automatically by formatters)
  "timestamp": "2023-10-28T10:30:01.123Z", // ISO 8601 format in UTC (from LogRecord.asctime or formatter)
  "level": "INFO",                       // Uppercase log level name (from LogRecord.levelname)
  "logger_name": "organizations.views",  // Dotted path to logger (from LogRecord.name)
  "message": "Organization ABC created successfully.", // The primary log message (from LogRecord.getMessage())

  // Core Application Context (Add these via Filters/Formatters)
  "service_name": "erp-backend-api",     // Name of the application/service
  "environment": "production",           // Deployment environment (dev, staging, prod)
  "trace_id": "a1b2c3d4e5f6",           // Unique ID for tracing a request across services/tasks (if using distributed tracing)
  "request_id": "f6e5d4c3b2a1",           // Unique ID for the specific HTTP request (often injected by middleware)
  "user_id": 123,                        // Authenticated User ID (if available)
  "username": "admin_user",              // Authenticated Username (if available)
  "organization_id": 45,               // Organization ID context (if available, crucial for multi-tenant analysis)
  "session_id": "xyz789",                // Optional: Session Key (if using sessions)
  "client_ip": "192.168.1.100",          // Optional: Requesting client IP address (via middleware)

  // Event Specific Context (Added explicitly when logging)
  "event_type": "organization_created", // Optional: Application-specific event code/type
  "duration_ms": 55.6,                  // Optional: Duration of an operation
  "object_id": 789,                     // Optional: PK of the primary object involved
  "object_type": "organizations.Organization", // Optional: ContentType of the primary object
  // ... other relevant key-value pairs specific to the log message ...

  // Error Context (Added automatically by formatters for ERROR/CRITICAL)
  "exception_type": "ValueError",          // Type of exception if logged via logger.exception()
  "exception_message": "Invalid input provided.", // Exception message
  "stack_trace": "Traceback (most recent call last):\n..." // Stack trace (multi-line string)
}
```

**Explanation of Key Information Fields:**

*   **Standard Attributes:** Provided by Python's `logging` module.
*   **`service_name`, `environment`:** Identify the source application and deployment context. Set globally.
*   **`trace_id`, `request_id`:** Essential for correlating logs related to a single user request or transaction flow, especially in distributed systems or when using background tasks. Needs middleware to generate/propagate these.
*   **`user_id`, `username`, `organization_id`:** Provide critical application context for filtering and analysis. Needs middleware or context injection to make available to the logger.
*   **`session_id`, `client_ip`:** Useful for debugging user-specific issues or security analysis. Needs middleware.
*   **`event_type`:** Application-defined code for specific events, useful for structured analysis.
*   **`duration_ms`:** For logging performance of specific operations.
*   **`object_id`/`object_type`:** Links the log message to specific data records.
*   **Error Context:** Automatically included when using `logger.exception()` or capturing tracebacks, vital for debugging errors.

## 5. Implementation Strategy

*   **Library:** Use Python's built-in `logging` module.
*   **Configuration:** Configure logging via Django's `LOGGING` setting in `settings.py`.
*   **Formatters:** Define a `logging.JSONFormatter` (potentially using a library like `python-json-logger`) to output logs in the standard JSON format defined above.
*   **Filters:** Create custom `logging.Filter` classes to inject contextual information (like `user_id`, `organization_id`, `request_id`) into the `LogRecord`. This data can often be stored in thread-local storage by middleware during a request or passed explicitly.
*   **Handlers:** Configure appropriate handlers:
    *   **Development:** `logging.StreamHandler` writing JSON to `stdout`/`stderr` is common, especially with containers.
    *   **Production:** `logging.StreamHandler` (for container stdout/stderr collection) or potentially `logging.handlers.RotatingFileHandler` / `WatchedFileHandler` if writing to files for collection by agents like Filebeat/Fluentd. **Avoid `SysLogHandler` unless specifically required and configured.**
*   **Getting Loggers:** In application code, get loggers using `logger = logging.getLogger(__name__)`.
*   **Logging Exceptions:** Always use `logger.exception("Error during operation X")` inside `except` blocks to automatically include traceback information.

## 6. Log Collection & Centralization

*   **Collection Method:**
    *   **Containers (Recommended):** Log JSON to `stdout`/`stderr`. The container orchestration platform (e.g., Kubernetes, Docker Swarm) and a log collector agent (e.g., Fluentd, Filebeat, Vector) handle collecting these streams.
    *   **Servers (VMs/Bare Metal):** Log JSON to files. Use a log shipper agent (Fluentd, Filebeat, Vector) configured to watch these files and forward them.
*   **Centralization Platform:** Logs **must** be forwarded to a centralized log management system for aggregation, searching, analysis, and alerting. Examples:
    *   **ELK/EFK Stack:** Elasticsearch/OpenSearch + Logstash/Fluentd + Kibana
    *   **Loki + Grafana (+ Promtail):** Becoming popular, integrates well with Prometheus.
    *   **Commercial SaaS:** Datadog Logs, Splunk, Logz.io, Sumo Logic, etc.
*   **Target Platform Choice:** Select the platform that best fits infrastructure, budget, and team expertise.

## 7. Monitoring & Alerting

*   Configure the **centralized logging platform** to:
    *   Parse the JSON logs.
    *   Create dashboards to visualize log volume, error rates, specific events.
    *   Define alert rules based on log queries (e.g., alert on high frequency of `ERROR`/`CRITICAL` logs, specific error messages, security-related events). Alerts should integrate with notification channels (Slack, PagerDuty, Email).

## 8. Security & Privacy

*   **Avoid Logging Sensitive Data:** Do **not** log sensitive PII (passwords, full credit card numbers, API keys, tokens) directly in log messages unless absolutely necessary and properly masked or secured. Be mindful of GDPR/CCPA.
*   **Access Control:** Access to the centralized logging platform must be restricted to authorized personnel.

## 9. Log Retention

*   Define a log retention policy based on operational needs and compliance requirements (e.g., retain active search logs for 30 days, archive for 1 year). Implement this policy in the centralized logging platform.

## 10. Testing

*   Verify logging configuration works in different environments.
*   Test that contextual information (user, org, request ID) is correctly injected.
*   Test that exceptions are correctly logged with stack traces.
*   Test log format validity (ensure it's valid JSON).
*   Verify logs appear correctly in the chosen centralized platform during staging tests.

---