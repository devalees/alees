# Authentication API Documentation

## Overview

This document provides detailed information about the Authentication API endpoints, including request/response formats, authentication methods, and example usage.

## Authentication Methods

The API supports two authentication methods:

1. **JWT Authentication**: For user-based authentication
   - Use the `/api/v1/auth/token/` endpoint to obtain JWT tokens
   - Include the token in the `Authorization` header: `Bearer <token>`

2. **API Key Authentication**: For server-to-server communication
   - Include the API key in the `X-API-Key` header
   - API keys can be managed through the Django admin interface

## Endpoints

### 1. Authentication

#### 1.1 Login

```http
POST /api/v1/auth/token/
```

**Description**: Authenticate a user and obtain JWT tokens.

**Request Body**:
```json
{
    "username": "user@example.com",
    "password": "your_password"
}
```

**Response (200 OK)**:
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Error Response (401 Unauthorized)**:
```json
{
    "detail": "No active account found with the given credentials"
}
```

**Notes**:
- The access token expires after 5 minutes
- The refresh token expires after 24 hours
- Store both tokens securely
- Use the refresh token to obtain new access tokens when they expire

#### 1.2 Refresh Token

```http
POST /api/v1/auth/token/refresh/
```

**Description**: Obtain a new access token using a refresh token.

**Request Body**:
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200 OK)**:
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Error Response (401 Unauthorized)**:
```json
{
    "detail": "Token is invalid or expired"
}
```

**Notes**:
- Use this endpoint when your access token expires
- The refresh token must be valid and not expired
- You will receive a new access token but the same refresh token

### 2. Two-Factor Authentication (2FA)

#### 2.1 Setup TOTP Device

```http
POST /api/v1/auth/2fa/totp/setup/
```

**Description**: Initialize TOTP 2FA setup for the authenticated user.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response (200 OK)**:
```json
{
    "secret": "JBSWY3DPEHPK3PXP",
    "qr_code": "data:image/png;base64,...",
    "provisioning_uri": "otpauth://totp/Example:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Example"
}
```

**Error Response (401 Unauthorized)**:
```json
{
    "detail": "Authentication credentials were not provided."
}
```

#### 2.2 Verify TOTP Device

```http
POST /api/v1/auth/2fa/totp/verify/
```

**Description**: Verify and enable a TOTP device after setup.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
    "token": "123456"
}
```

**Response (200 OK)**:
```json
{
    "detail": "TOTP device verified and enabled successfully"
}
```

**Error Response (400 Bad Request)**:
```json
{
    "detail": "Invalid token"
}
```

#### 2.3 Disable TOTP

```http
POST /api/v1/auth/2fa/totp/disable/
```

**Description**: Disable 2FA for the authenticated user.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
    "password": "your_password"
}
```

**Response (200 OK)**:
```json
{
    "detail": "2FA disabled successfully"
}
```

**Error Response (400 Bad Request)**:
```json
{
    "detail": "Invalid password"
}
```

### 3. Password Management

#### 3.1 Change Password

```http
POST /api/v1/auth/password/change/
```

**Description**: Change the authenticated user's password.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
    "old_password": "current_password",
    "new_password": "new_password"
}
```

**Response (200 OK)**:
```json
{
    "detail": "Password changed successfully"
}
```

**Error Response (400 Bad Request)**:
```json
{
    "detail": "Invalid old password"
}
```

## Error Handling

The API uses standard HTTP status codes and provides detailed error messages in the response body. Common error responses include:

- **400 Bad Request**: Invalid input data
- **401 Unauthorized**: Missing or invalid authentication credentials
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server-side error

## Security Considerations

1. **JWT Tokens**:
   - Access tokens expire after 5 minutes
   - Refresh tokens expire after 24 hours
   - Store tokens securely and never share them

2. **API Keys**:
   - Generate API keys through the admin interface
   - Store API keys securely
   - Rotate API keys regularly
   - Set appropriate expiry dates

3. **2FA**:
   - Store backup codes securely
   - Use a secure authenticator app
   - Keep the QR code and secret key secure during setup

## Rate Limiting

The API implements rate limiting to prevent abuse:
- 100 requests per minute for authenticated users
- 20 requests per minute for unauthenticated users

## Example Usage

### Python Example (using requests)

```python
import requests

# Base URL
BASE_URL = "http://your-api-domain/api/v1/auth"

# 1. Obtain JWT tokens
response = requests.post(
    f"{BASE_URL}/token/",
    json={
        "username": "user@example.com",
        "password": "your_password"
    }
)
tokens = response.json()
access_token = tokens["access"]

# 2. Make authenticated request
headers = {
    "Authorization": f"Bearer {access_token}"
}
response = requests.get(
    f"{BASE_URL}/profile/",
    headers=headers
)
```

### cURL Examples

1. **Obtain JWT Token**:
```bash
curl -X POST http://your-api-domain/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com","password":"your_password"}'
```

2. **Change Password**:
```bash
curl -X POST http://your-api-domain/api/v1/auth/password/change/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"old_password":"current_password","new_password":"new_password"}'
```

## Versioning

The API is versioned through the URL path (`/api/v1/`). Future versions will maintain backward compatibility where possible.

## Support

For API support or to report issues:
- Email: support@example.com
- Documentation: https://docs.example.com/api
- Issue Tracker: https://github.com/example/repo/issues 