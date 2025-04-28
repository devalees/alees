# UserProfile API Documentation

## Table of Contents
1. [Authentication](#authentication)
2. [Base URL](#base-url)
3. [Endpoints](#endpoints)
4. [Request/Response Examples](#requestresponse-examples)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Best Practices](#best-practices)

## Authentication

All endpoints require JWT authentication. Include the token in the Authorization header:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Base URL

All endpoints are prefixed with:
```
https://api.example.com/api/v1/
```

## Endpoints

### 1. My Profile

#### GET /profiles/me/
Retrieve the authenticated user's profile.

**Example Request:**
```http
GET /api/v1/profiles/me/
Authorization: Bearer <token>
```

**Example Response (200 OK):**
```json
{
    "id": 123,
    "user": 456,
    "job_title": "Senior Developer",
    "employee_id": "EMP-12345",
    "phone_number": "+1234567890",
    "manager": 789,
    "date_of_birth": "1990-01-01",
    "employment_type": "FULL_TIME",
    "profile_picture": 101,
    "language": "en",
    "timezone": "UTC",
    "notification_preferences": {
        "email": true,
        "push": true,
        "sms": false
    },
    "custom_fields": {
        "department": "Engineering",
        "skills": ["Python", "Django", "React"]
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-02T00:00:00Z"
}
```

#### PUT /profiles/me/
Update the entire profile.

**Example Request:**
```http
PUT /api/v1/profiles/me/
Authorization: Bearer <token>
Content-Type: application/json

{
    "job_title": "Lead Developer",
    "phone_number": "+1987654321",
    "language": "en",
    "timezone": "America/New_York",
    "notification_preferences": {
        "email": true,
        "push": true,
        "sms": true
    },
    "custom_fields": {
        "department": "Engineering",
        "skills": ["Python", "Django", "React", "TypeScript"]
    }
}
```

**Example Response (200 OK):**
```json
{
    "id": 123,
    "user": 456,
    "job_title": "Lead Developer",
    "employee_id": "EMP-12345",
    "phone_number": "+1987654321",
    "manager": 789,
    "date_of_birth": "1990-01-01",
    "employment_type": "FULL_TIME",
    "profile_picture": 101,
    "language": "en",
    "timezone": "America/New_York",
    "notification_preferences": {
        "email": true,
        "push": true,
        "sms": true
    },
    "custom_fields": {
        "department": "Engineering",
        "skills": ["Python", "Django", "React", "TypeScript"]
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-03T00:00:00Z"
}
```

#### PATCH /profiles/me/
Partially update the profile.

**Example Request:**
```http
PATCH /api/v1/profiles/me/
Authorization: Bearer <token>
Content-Type: application/json

{
    "phone_number": "+1987654321",
    "timezone": "America/New_York"
}
```

**Example Response (200 OK):**
```json
{
    "id": 123,
    "user": 456,
    "job_title": "Lead Developer",
    "employee_id": "EMP-12345",
    "phone_number": "+1987654321",
    "manager": 789,
    "date_of_birth": "1990-01-01",
    "employment_type": "FULL_TIME",
    "profile_picture": 101,
    "language": "en",
    "timezone": "America/New_York",
    "notification_preferences": {
        "email": true,
        "push": true,
        "sms": true
    },
    "custom_fields": {
        "department": "Engineering",
        "skills": ["Python", "Django", "React", "TypeScript"]
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-03T00:00:00Z"
}
```

### 2. Profile List (Admin Only)

#### GET /profiles/
List all user profiles with pagination and filtering.

**Example Request:**
```http
GET /api/v1/profiles/?search=developer&ordering=-created_at&page=1&page_size=10
Authorization: Bearer <admin_token>
```

**Example Response (200 OK):**
```json
{
    "count": 100,
    "next": "https://api.example.com/api/v1/profiles/?page=2",
    "previous": null,
    "results": [
        {
            "id": 123,
            "user": 456,
            "job_title": "Senior Developer",
            "employee_id": "EMP-12345",
            "phone_number": "+1234567890",
            "manager": 789,
            "date_of_birth": "1990-01-01",
            "employment_type": "FULL_TIME",
            "profile_picture": 101,
            "language": "en",
            "timezone": "UTC",
            "notification_preferences": {
                "email": true,
                "push": true,
                "sms": false
            },
            "custom_fields": {
                "department": "Engineering",
                "skills": ["Python", "Django", "React"]
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z"
        }
    ]
}
```

#### POST /profiles/
Create a new user profile (admin only).

**Example Request:**
```http
POST /api/v1/profiles/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
    "user": 789,
    "job_title": "Junior Developer",
    "employee_id": "EMP-78901",
    "phone_number": "+1234567890",
    "manager": 456,
    "date_of_birth": "1995-01-01",
    "employment_type": "FULL_TIME",
    "language": "en",
    "timezone": "UTC",
    "notification_preferences": {
        "email": true,
        "push": true,
        "sms": false
    },
    "custom_fields": {
        "department": "Engineering",
        "skills": ["Python", "Django"]
    }
}
```

**Example Response (201 Created):**
```json
{
    "id": 124,
    "user": 789,
    "job_title": "Junior Developer",
    "employee_id": "EMP-78901",
    "phone_number": "+1234567890",
    "manager": 456,
    "date_of_birth": "1995-01-01",
    "employment_type": "FULL_TIME",
    "profile_picture": null,
    "language": "en",
    "timezone": "UTC",
    "notification_preferences": {
        "email": true,
        "push": true,
        "sms": false
    },
    "custom_fields": {
        "department": "Engineering",
        "skills": ["Python", "Django"]
    },
    "created_at": "2024-01-03T00:00:00Z",
    "updated_at": "2024-01-03T00:00:00Z"
}
```

### 3. Profile Detail (Admin Only)

#### GET /profiles/{id}/
Retrieve a specific user profile.

**Example Request:**
```http
GET /api/v1/profiles/123/
Authorization: Bearer <admin_token>
```

**Example Response (200 OK):**
```json
{
    "id": 123,
    "user": 456,
    "job_title": "Senior Developer",
    "employee_id": "EMP-12345",
    "phone_number": "+1234567890",
    "manager": 789,
    "date_of_birth": "1990-01-01",
    "employment_type": "FULL_TIME",
    "profile_picture": 101,
    "language": "en",
    "timezone": "UTC",
    "notification_preferences": {
        "email": true,
        "push": true,
        "sms": false
    },
    "custom_fields": {
        "department": "Engineering",
        "skills": ["Python", "Django", "React"]
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-02T00:00:00Z"
}
```

### 4. Profile Picture

#### PUT /profiles/{id}/picture/
Upload a new profile picture.

**Example Request:**
```http
PUT /api/v1/profiles/123/picture/
Authorization: Bearer <token>
Content-Type: multipart/form-data

picture: <binary file data>
```

**Example Response (200 OK):**
```json
{
    "picture_url": "https://api.example.com/media/profiles/123/profile.jpg"
}
```

## Error Handling

### 400 Bad Request
```json
{
    "job_title": ["This field is required."],
    "phone_number": ["Enter a valid phone number."],
    "custom_fields": ["Invalid custom fields format."]
}
```

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
    "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
    "detail": "Not found."
}
```

### 413 Payload Too Large
```json
{
    "detail": "File size exceeds maximum allowed size of 5MB."
}
```

### 415 Unsupported Media Type
```json
{
    "detail": "Unsupported media type. Only JPEG, PNG, and GIF are allowed."
}
```

## Rate Limiting

### Default Limits
- Regular users: 100 requests per minute
- Admin users: 200 requests per minute

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1625097600
```

## Best Practices

1. **Authentication**
   - Always include the JWT token in the Authorization header
   - Handle token expiration gracefully
   - Implement token refresh mechanism

2. **Request Handling**
   - Use appropriate HTTP methods (GET, POST, PUT, PATCH, DELETE)
   - Include proper Content-Type headers
   - Validate request data before processing

3. **Response Handling**
   - Check status codes
   - Handle pagination for list endpoints
   - Implement proper error handling

4. **File Uploads**
   - Compress images before upload
   - Validate file types and sizes
   - Use multipart/form-data for file uploads

5. **Rate Limiting**
   - Monitor rate limit headers
   - Implement exponential backoff for retries
   - Cache responses when appropriate

6. **Security**
   - Never expose sensitive data
   - Validate all input data
   - Use HTTPS for all requests
   - Implement proper CORS policies 