# Address Model - Architectural Decisions

## Overview

This document outlines the key architectural decisions made during the implementation of the `Address` model in the ERP system.

## 1. Nested Resource Pattern

### Decision
Addresses are implemented as nested resources within parent entities rather than as standalone endpoints.

### Rationale
1. **Data Integrity**: Addresses always belong to a parent entity (Organization, UserProfile, etc.)
2. **Simplified API**: No need for standalone CRUD endpoints
3. **Natural Relationships**: Better represents real-world relationships where addresses belong to entities
4. **Reduced Complexity**: No need to manage orphaned addresses or complex ownership rules

### Implementation Details
- No standalone ViewSet/URLs
- `AddressSerializer` designed for nested usage within parent serializers
- Parent models reference Address via ForeignKey relationships

## 2. Custom Fields Support

### Decision
Implemented a flexible but validated custom fields system using JSONField.

### Rationale
1. **Flexibility**: Different entities may need different additional address fields
2. **Validation**: Strong validation ensures data integrity
3. **Schema Control**: Predefined schema prevents arbitrary field creation

### Implementation Details
```python
CUSTOM_FIELD_SCHEMA = {
    "floor": {"type": str, "max_length": 10, "required": False},
    "building": {"type": str, "max_length": 50, "required": False},
    "unit": {"type": str, "max_length": 20, "required": False},
    "access_code": {"type": str, "max_length": 20, "required": False},
    "delivery_instructions": {"type": str, "max_length": 255, "required": False},
}
```

## 3. Country Field Implementation

### Decision
Used `django-countries` package for country field management.

### Rationale
1. **Standardization**: ISO 3166-1 country codes
2. **Built-in Validation**: Validates country codes automatically
3. **UI Support**: Provides country names, flags, and other features
4. **Internationalization**: Built-in translation support

### Implementation Details
- Uses `CountryField` from django-countries
- Serializer returns country as dict with code and name
- Indexed for performance

## 4. Indexing Strategy

### Decision
Implemented strategic database indexes for common query patterns.

### Rationale
1. **Performance**: Faster lookups for common queries
2. **Search Support**: Efficient filtering and searching
3. **Reporting**: Supports geographical aggregations

### Implementation Details
```python
class Meta:
    indexes = [
        models.Index(fields=["country", "postal_code"]),
    ]
    # Individual field indexes
    city = models.CharField(..., db_index=True)
    state_province = models.CharField(..., db_index=True)
    postal_code = models.CharField(..., db_index=True)
    country = CountryField(..., db_index=True)
```

## 5. Audit Trail

### Decision
Inherited from `Timestamped` and `Auditable` base classes.

### Rationale
1. **Tracking**: Record when addresses are created/modified
2. **Accountability**: Track who made changes
3. **Compliance**: Support for audit requirements

### Implementation Details
- Created/Updated timestamps
- Created by/Updated by user tracking
- Exposed in Admin interface (collapsed by default)

## 6. Status Management

### Decision
Included a status field with default "Active" state.

### Rationale
1. **Soft Delete**: Support for marking addresses as inactive
2. **Verification**: Can mark addresses pending verification
3. **History**: Maintain address history without deletion

### Implementation Details
```python
status = models.CharField(
    max_length=20,
    blank=True,
    default="Active",
    db_index=True
)
```

## Future Considerations

1. **Standalone Endpoints**
   - If needed, can add ViewSet/URLs later
   - Would require ownership/permission model
   - Could support address reuse across entities

2. **Geocoding Integration**
   - Could add automatic lat/long population
   - Integration with mapping services
   - Address verification services

3. **Address Normalization**
   - Could add address standardization
   - Postal format validation by country
   - Integration with postal databases

## Related Documents
- [Implementation Steps](address_implementation_steps.md)
- [PRD](address_prd.md) 