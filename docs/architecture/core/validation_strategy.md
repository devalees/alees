Okay, let's create the `validation_strategy.md`. This document outlines how data validation will be handled throughout the ERP application, emphasizing the use of built-in Django and DRF features over a complex custom engine (as decided previously).

--- START OF FILE validation_strategy.md ---

# Validation Strategy

## 1. Overview

*   **Purpose**: To define the standard approach and best practices for implementing data validation across the ERP system, ensuring data integrity, enforcing business rules, and providing clear feedback to users/API consumers.
*   **Scope**: Covers validation techniques at the database, model, serializer, and potentially service layers. Excludes the implementation of a separate, generic validation rule engine.
*   **Goal**: Robust, maintainable, and consistently applied validation throughout the application.

## 2. Core Principles

*   **Validate Early, Validate Often**: Perform validation checks as close to the data entry point as possible (typically serializers for API input).
*   **Leverage Built-in Features**: Utilize Django model field options and DRF serializer validation mechanisms extensively before resorting to custom code.
*   **Clarity of Errors**: Validation errors returned via the API must be clear, specific, and follow the standard error format defined in the API Strategy (pointing to the specific field(s) in error).
*   **DRY (Don't Repeat Yourself)**: Use reusable custom validator functions for logic applied across multiple fields or models.
*   **Separation of Concerns**:
    *   **Format/Type/Presence Validation**: Primarily handled by model field definitions and serializer field types/arguments.
    *   **Business Rule/Cross-Field Validation**: Primarily handled within Serializer `validate()` methods or Model `clean()` methods.
    *   **Database Constraints**: Used for enforcing fundamental data integrity (uniqueness, foreign key existence, non-null).

## 3. Validation Layers & Techniques

Validation will be implemented at multiple layers:

### 3.1. Database Level Constraints
*   **Purpose**: Enforce absolute data integrity rules directly within the database schema.
*   **Techniques**:
    *   `NOT NULL` constraints (via `null=False` on model fields).
    *   `UNIQUE` constraints (via `unique=True` or `Meta.unique_together` on models).
    *   `FOREIGN KEY` constraints (automatically created by `models.ForeignKey`, `OneToOneField`). Ensure appropriate `on_delete` behavior is set.
    *   `(Optional)` Database `CHECK` constraints for simple value restrictions (can be added via migrations if needed, less common with Django).
*   **Note**: Database errors resulting from constraint violations are often less user-friendly than application-level validation errors. Application validation should catch most issues *before* they hit the database constraint.

### 3.2. Django Model Field Validation
*   **Purpose**: Define basic data type, format, and presence rules directly on the model fields.
*   **Techniques**:
    *   **Field Types**: Use appropriate field types (`EmailField`, `URLField`, `IntegerField`, `DecimalField`, `BooleanField`, `DateField`, `DateTimeField`, `UUIDField`, etc.) which include built-in format validation.
    *   **Field Options**:
        *   `max_length`, `min_length` (for CharField/TextField).
        *   `choices`: Restrict values to a predefined set.
        *   `unique`, `unique_for_date/month/year`.
        *   `null=False`, `blank=False` (Note: `null` is DB level, `blank` is form/serializer validation level).
        *   `validators`: Attach reusable validator functions (see below).
        *   Numeric field options (`max_digits`, `decimal_places`, `min_value`, `max_value`).
*   **Execution**: These validations are typically run automatically by Django Forms and DRF ModelSerializers.

### 3.3. Django Model `clean()` Method
*   **Purpose**: Implement model-level validation logic that requires access to multiple fields *within the same model instance*. Suitable for enforcing invariants or complex relationships between fields *before* saving to the database.
*   **Techniques**:
    *   Override the `clean()` method on the model.
    *   Perform checks involving `self.field_a`, `self.field_b`, etc.
    *   Raise `django.core.exceptions.ValidationError` if validation fails. Can target specific fields or be a non-field error.
*   **Execution**: Called automatically by `ModelForm` validation and `full_clean()` method. **Important:** DRF serializers *do not* automatically call model `clean()` by default. It must be called explicitly within the serializer's `validate()` method or by overriding `create()`/`update()` if model-level validation needs to be enforced for API input.
*   **Use Case Example:** Ensure `start_date` is always before `end_date`.

### 3.4. DRF Serializer Validation (Primary API Input Validation Point)
*   **Purpose**: Validate incoming data from API requests *before* creating or updating model instances. Handles format, business rules, cross-field dependencies, and permissions related to the *specific data being submitted*.
*   **Techniques**:
    *   **Serializer Fields**: Use appropriate serializer fields (`serializers.EmailField`, `serializers.IntegerField`, etc.) with arguments like `required=True`, `allow_null=True`, `max_length`, `min_value`, `validators`.
    *   **`validate_<field_name>(self, value)` Methods**: Implement custom validation logic for a single field. Should return the validated `value` or raise `serializers.ValidationError`.
    *   **`validate(self, data)` Method**: Implement validation logic involving multiple fields. Accesses the dictionary of validated field data (`data`). Should return the validated `data` dictionary or raise `serializers.ValidationError`. **This is the primary location for cross-field business rule validation for APIs.** Explicitly call `instance.full_clean()` from here if model-level `clean()` validation needs to be enforced for API requests involving existing instances. For creation, call model `clean` on the instance *before* saving it in the `create` method.
*   **Execution**: Run automatically by DRF when `serializer.is_valid(raise_exception=True)` is called in the view.
*   **Error Formatting**: DRF automatically collects `ValidationError`s raised during this process and formats them (usually into a dictionary mapping field names to lists of errors), which our custom exception handler will then format into the standard API error response.

### 3.5. Custom Validator Functions
*   **Purpose**: Define reusable validation logic that can be applied to multiple model fields or serializer fields.
*   **Techniques**: Create standalone functions that accept a value and raise `ValidationError` if invalid. Attach them using the `validators=[my_validator]` argument on model or serializer fields.
*   **Example:** A validator to check if a string contains only alphanumeric characters, reusable on `username`, `code`, etc.

## 4. Strategy Summary

1.  Define strict database constraints (`UNIQUE`, `NOT NULL`, FKs) for fundamental integrity.
2.  Use appropriate Django **Model Fields** and their options (`EmailField`, `max_length`, `choices`, etc.) for basic type and format validation.
3.  Implement model-level invariants (rules involving multiple fields of the *same* model) in the **Model `clean()`** method.
4.  Implement **ALL API input validation** (including business rules, cross-field checks, and *explicitly calling model `clean()` if needed*) within **DRF Serializer `validate_<field>()` and `validate()` methods**. This is the primary validation layer for the API.
5.  Create **Reusable Validator Functions** for common checks applied across different fields/models/serializers.

## 5. Integration with Other Systems

*   **RBAC System:** Validation logic within serializers/views may need to check user permissions before validating certain state transitions or field updates.
*   **Workflow System:** Transitions defined in the workflow system will have associated conditions, which act as a form of validation before allowing a status change. Serializers handling status updates might need to check if the requested transition is valid according to the workflow.
*   **Custom Fields:** Validation logic within serializers needs to retrieve the relevant `CustomFieldDefinition` schema and validate the `custom_fields` JSON data against it.

## 6. Testing

*   **Unit Tests:** Test model `clean()` methods, custom validator functions, and individual serializer `validate_<field>()` / `validate()` methods in isolation (mocking database lookups if necessary).
*   **API Tests:** Test API endpoints with various valid and invalid inputs (missing fields, incorrect formats, values violating business rules, invalid custom field data). Assert that appropriate `400 Bad Request` errors are returned with the standard error structure detailing the specific validation failures. Test that model `clean()` validations are correctly triggered for API requests.

--- END OF FILE validation_strategy.md ---