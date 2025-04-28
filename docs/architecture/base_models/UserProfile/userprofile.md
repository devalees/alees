# UserProfile Model Documentation

## Overview

The `UserProfile` model extends Django's built-in `User` model to provide additional fields and functionality specific to our ERP system. It follows a one-to-one relationship with the `User` model and includes various fields for user-specific information, preferences, and custom fields.

## Model Structure

### Base Inheritance
- Inherits from `Timestamped` (for created_at, updated_at fields)
- Inherits from `Auditable` (for audit trail functionality)
- One-to-one relationship with Django's `User` model

### Core Fields

#### Basic Information
- `user`: OneToOneField to Django's User model
- `job_title`: CharField (max_length=100, optional)
- `employee_id`: CharField (max_length=50, optional)
- `phone_number`: CharField (max_length=20, optional)
- `manager`: ForeignKey to User (optional)
- `date_of_birth`: DateField (optional)
- `employment_type`: CharField (max_length=50, optional)

#### Profile Media
- `profile_picture`: ForeignKey to FileStorage (optional, nullable)

#### Preferences
- `language`: CharField (max_length=10, optional)
- `timezone`: CharField (max_length=50, optional)
- `notification_preferences`: JSONField (optional)

#### Custom Fields
- `custom_fields`: JSONField (optional)

## Features

### Automatic Profile Creation
- A `UserProfile` is automatically created when a new `User` is created
- Implemented using Django signals
- Ensures every user has a profile

### Custom Fields Validation
- Custom fields are validated using a JSON schema
- Ensures data integrity for custom user attributes
- Flexible enough to accommodate different organizational needs

## API Endpoints

### Base URL
All endpoints are prefixed with `/api/v1/`

### Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <token>
```

### Endpoints

#### 1. My Profile
- **URL**: `/profiles/me/`
- **Description**: Manage the authenticated user's profile
- **Methods**:
  - **GET**
    - Description: Retrieve current user's profile
    - Response: 200 OK
    ```json
    {
        "id": "integer",
        "user": "integer",
        "job_title": "string",
        "employee_id": "string",
        "phone_number": "string",
        "manager": "integer",
        "date_of_birth": "date",
        "employment_type": "string",
        "profile_picture": "integer",
        "language": "string",
        "timezone": "string",
        "notification_preferences": "object",
        "custom_fields": "object",
        "created_at": "datetime",
        "updated_at": "datetime"
    }
    ```
  - **PUT**
    - Description: Update entire profile
    - Request Body: Complete profile object
    - Response: 200 OK (updated profile)
  - **PATCH**
    - Description: Partial profile update
    - Request Body: Partial profile object
    - Response: 200 OK (updated profile)

#### 2. Profile List (Admin Only)
- **URL**: `/profiles/`
- **Description**: List and manage all user profiles (admin only)
- **Methods**:
  - **GET**
    - Description: List all profiles
    - Query Parameters:
      - `search`: Search in job_title, employee_id, phone_number
      - `ordering`: Sort by any field (e.g., `?ordering=-created_at`)
      - `page`: Page number for pagination
      - `page_size`: Items per page
    - Response: 200 OK
    ```json
    {
        "count": "integer",
        "next": "url",
        "previous": "url",
        "results": [
            {
                "id": "integer",
                "user": "integer",
                "job_title": "string",
                // ... profile fields ...
            }
        ]
    }
    ```
  - **POST**
    - Description: Create new profile (admin only)
    - Request Body: Profile object
    - Response: 201 Created

#### 3. Profile Detail (Admin Only)
- **URL**: `/profiles/{id}/`
- **Description**: Manage specific user profile (admin only)
- **Methods**:
  - **GET**
    - Description: Retrieve specific profile
    - Response: 200 OK (profile object)
  - **PUT**
    - Description: Update entire profile
    - Request Body: Complete profile object
    - Response: 200 OK (updated profile)
  - **PATCH**
    - Description: Partial profile update
    - Request Body: Partial profile object
    - Response: 200 OK (updated profile)
  - **DELETE**
    - Description: Delete profile
    - Response: 204 No Content

#### 4. Profile Picture
- **URL**: `/profiles/{id}/picture/`
- **Description**: Manage profile picture
- **Methods**:
  - **GET**
    - Description: Get profile picture URL
    - Response: 200 OK
    ```json
    {
        "picture_url": "string"
    }
    ```
  - **PUT**
    - Description: Upload new profile picture
    - Content-Type: multipart/form-data
    - Request Body: `picture` (file)
    - Response: 200 OK
  - **DELETE**
    - Description: Remove profile picture
    - Response: 204 No Content

### Error Responses

#### 400 Bad Request
```json
{
    "field_name": ["Error message"]
}
```

#### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

#### 403 Forbidden
```json
{
    "detail": "You do not have permission to perform this action."
}
```

#### 404 Not Found
```json
{
    "detail": "Not found."
}
```

### Rate Limiting
- All endpoints are rate-limited
- Default: 100 requests per minute per user
- Admin endpoints: 200 requests per minute

## Admin Interface

### Custom User Admin
- Extends Django's default User admin
- Includes inline UserProfile configuration
- Provides easy access to manage user profiles

## Testing

### Test Coverage
- Unit tests for model, serializer, and admin
- API tests for endpoints
- Integration tests for signals
- Test coverage maintained above 90%

### Test Categories
1. Model Tests
   - Basic model creation
   - Field validation
   - String representation
   - Relationship integrity

2. Serializer Tests
   - Data validation
   - Custom fields validation
   - Read-only fields
   - Field representation

3. API Tests
   - Authentication requirements
   - CRUD operations
   - Error handling
   - Permission checks

4. Admin Tests
   - Inline configuration
   - Custom admin features
   - Interface usability

## Implementation Status

### Completed
- [x] Model definition and migrations
- [x] Factory definitions
- [x] Signal implementation
- [x] Admin registration
- [x] Serializer implementation
- [x] API ViewSet definition
- [x] URL routing
- [x] Basic test coverage

### Pending
- [ ] FileStorage integration for profile pictures
- [ ] Advanced profile picture handling
- [ ] Bulk profile operations
- [ ] Profile export/import functionality

## Dependencies

### Current
- Django User model
- Timestamped mixin
- Auditable mixin

### Future
- FileStorage model (for profile pictures)

## Security Considerations

1. Authentication
   - All API endpoints require authentication
   - JWT token-based authentication

2. Authorization
   - Users can only access their own profile
   - Admin users have full access through admin interface

3. Data Protection
   - Sensitive fields are properly validated
   - Custom fields schema validation
   - Audit trail for changes

## Best Practices

1. Profile Creation
   - Always use signals for automatic profile creation
   - Never create profiles manually

2. Data Updates
   - Use PUT for complete updates
   - Use PATCH for partial updates
   - Validate all custom fields

3. Testing
   - Maintain high test coverage
   - Test both success and failure cases
   - Include integration tests for signals

## Future Enhancements

1. Profile Picture
   - Implement image optimization
   - Add multiple size variants
   - Add CDN integration

2. Custom Fields
   - Add field type validation
   - Implement field templates
   - Add field-level permissions

3. API Features
   - Add bulk operations
   - Implement profile search
   - Add profile export/import

## Related Documentation

- [Implementation Steps](userprofile_implementation_steps.md)
- [API Documentation](api.md)
- [Testing Strategy](testing.md) 