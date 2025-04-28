

--- START OF FILE auth_api_prd.md ---

# Authentication API - Product Requirements Document (PRD)

## 1. Overview

*   **Purpose**: To define the requirements for the API-based authentication system, enabling users to securely log in via credentials (username/password), manage authentication tokens (JWT), use API keys for programmatic access, and manage Two-Factor Authentication (2FA) settings.
*   **Scope**: Covers user login (JWT obtain/refresh), API key authentication, and initial 2FA setup/management (specifically TOTP). Excludes user self-registration, the 2FA verification step during login (deferred), and the full password reset workflow (deferred).
*   **Technical Approach**: Leverages Django's built-in `User` model, `djangorestframework-simplejwt` for JWT, `djangorestframework-api-key` for API keys, and `django-otp` (with `otp_totp`) for 2FA.
*   **Target Users**: End users (logging in, managing 2FA), API Clients (using JWT or API Keys), System Administrators (managing API Keys).

## 2. Business Requirements

*   **Secure User Login**: Provide a standard and secure method for users to authenticate using their `username` and password via the API.
*   **Session Management (API)**: Manage user sessions effectively for API clients using industry-standard JWT (Access and Refresh tokens).
*   **Programmatic Access**: Enable secure server-to-server or third-party integrations using manageable, expirable API keys.
*   **Enhanced Security (2FA)**: Allow users to optionally enable Time-based One-Time Password (TOTP) 2FA for increased account security.
*   **Basic Account Management**: Allow authenticated users to change their own password.

## 3. Functional Requirements

### 3.1 Core Authentication (Django `User` Model)
*   Utilize Django's `auth.User` model for storing user credentials (`username`, hashed `password`, `email`, etc.) and core status fields (`is_active`, `is_staff`, `is_superuser`).
*   Authentication attempts will validate against the hashed password stored in this model.
*   User creation is handled outside this scope (e.g., Admin UI). No self-registration API.

### 3.2 JWT Token Management (`djangorestframework-simplejwt`)
*   **Token Obtain Endpoint**:
    *   URL: `POST /api/v1/auth/token/obtain/`
    *   Input: `username`, `password`.
    *   Output (Success): JSON containing `access` token (short-lived) and `refresh` token (longer-lived). HTTP 200 OK.
    *   Output (Failure): Standard API error response (e.g., 401 Unauthorized for bad credentials/inactive user).
    *   *Deferred*: This endpoint will need modification later to handle the 2FA verification step if 2FA is enabled for the user. Initially, it grants tokens directly upon valid password authentication.
*   **Token Refresh Endpoint**:
    *   URL: `POST /api/v1/auth/token/refresh/`
    *   Input: `refresh` token.
    *   Output (Success): JSON containing a new `access` token. HTTP 200 OK. Optionally rotate refresh tokens.
    *   Output (Failure): Standard API error response (e.g., 401 Unauthorized for invalid/expired refresh token).
*   **Token Verification Endpoint (Optional but Recommended)**:
    *   URL: `POST /api/v1/auth/token/verify/`
    *   Input: `token` (access token).
    *   Output (Success): HTTP 200 OK (empty body).
    *   Output (Failure): Standard API error response (e.g., 401 Unauthorized for invalid/expired token).
*   **Token Usage**: Clients must send the `access` token in the `Authorization: Bearer <access_token>` header for subsequent authenticated requests.

### 3.3 API Key Authentication (`djangorestframework-api-key`)
*   **Purpose**: Authenticate non-user programmatic clients.
*   **Generation & Management**:
    *   API Keys (`APIKey` model provided by library) are generated, managed (revoked, expiry set), and permissions assigned **only** via the Django Admin interface by administrators.
    *   Keys must have an expiry date.
    *   Keys store a hashed version; the original key is shown only once upon creation.
*   **Usage**: API clients must send their valid, unhashed API key in the **`X-API-Key`** HTTP header.
*   **Authentication Backend**: DRF's `APIKeyAuthentication` backend (configured as default) will validate the key provided in the `X-API-Key` header against the hashed keys in the database, checking for expiry and revocation status.
*   **Authorization**: Permissions for API key requests are determined by the permissions assigned *directly to the specific `APIKey` object* in the Django Admin, enforced using the library's `HasAPIKey` permission class (or custom logic referencing key permissions).

### 3.4 Two-Factor Authentication (2FA - TOTP Setup via `django-otp`)
*   **Scope**: Initial implementation focuses only on enabling/disabling TOTP via authenticator apps. The login flow modification to *verify* the 2FA code is deferred.
*   **Device Model**: Utilizes `django_otp.plugins.otp_totp.models.TOTPDevice` to store TOTP configuration linked to a User.
*   **Enablement Flow:**
    *   **Initiate Setup Endpoint**:
        *   URL: `POST /api/v1/auth/2fa/totp/setup/`
        *   Permissions: User must be authenticated (JWT).
        *   Action: Deletes any previous *unconfirmed* TOTP devices for the user. Creates a new, *unconfirmed* `TOTPDevice`.
        *   Output: JSON containing `setup_key` (secret key for manual entry) and `qr_code` (SVG or PNG data URI for authenticator app scanning). HTTP 200 OK.
    *   **Verify Setup Endpoint**:
        *   URL: `POST /api/v1/auth/2fa/totp/verify/`
        *   Permissions: User must be authenticated (JWT).
        *   Input: `token` (the 6-digit code from the authenticator app).
        *   Action: Finds the user's *unconfirmed* `TOTPDevice`. Verifies the provided `token` against the device. If valid, marks the device as `confirmed=True`. Optionally generates and returns one-time backup codes (`StaticDevice`/`StaticToken`).
        *   Output (Success): Success message, potentially backup codes. HTTP 200 OK.
        *   Output (Failure): Standard API error (400 Bad Request for invalid token or no setup found).
*   **Disable Endpoint**:
    *   URL: `POST /api/v1/auth/2fa/totp/disable/`
    *   Permissions: User must be authenticated (JWT).
    *   Input: User's current `password` (for confirmation).
    *   Action: Verifies password. If correct, deletes all `TOTPDevice` (and potentially other OTP devices like `StaticDevice`) records associated with the user.
    *   Output (Success): Success message. HTTP 200 OK.
    *   Output (Failure): Standard API error (400 Bad Request for wrong password).

### 3.5 Password Management (Basic)
*   **Password Change Endpoint**:
    *   URL: `POST /api/v1/auth/password/change/`
    *   Permissions: User must be authenticated (JWT).
    *   Input: `old_password`, `new_password1`, `new_password2`.
    *   Action: Validates old password against user's current hash. Validates new passwords match and meet complexity requirements (via Django settings/validators). If valid, updates the user's password hash using `user.set_password()`.
    *   Output (Success): Success message. HTTP 200 OK.
    *   Output (Failure): Standard API error (400 Bad Request for validation errors).
*   **Password Reset Flow (Deferred)**: Full flow (request reset email -> confirm via token -> set new password) is not included initially.

### 3.6 Out of Scope (Initial Implementation)
*   User Self-Registration API.
*   2FA Code Verification *during* the actual login (`/token/obtain/`) flow.
*   Full Password Reset workflow.
*   Management of API Keys via API endpoints (Admin only).
*   Support for other 2FA methods (SMS, HOTP, etc.).
*   Social Login / SSO integration.
*   Token Blacklisting / Advanced Logout for JWT.

## 4. Technical Requirements

### 4.1 Libraries & Configuration
*   Install and configure `djangorestframework-simplejwt`, `django-otp`, `django-otp.plugins.otp_totp`, `qrcode[pil]`, `djangorestframework-api-key`.
*   Configure required `INSTALLED_APPS`, `MIDDLEWARE`.
*   Configure `REST_FRAMEWORK` settings (`DEFAULT_AUTHENTICATION_CLASSES`).
*   Configure `SIMPLE_JWT` settings (lifetimes, etc.).
*   Configure `OTP_TOTP_ISSUER`.
*   Configure `REST_FRAMEWORK_API_KEY` setting (`HEADER_NAME`).

### 4.2 Security
*   JWT signing key must be kept secret.
*   Password hashing follows Django defaults (secure).
*   API Keys are hashed in the database.
*   TOTP secrets are stored securely by `django-otp`.
*   API endpoints must use appropriate permission classes (`IsAuthenticated`, `IsAdminUser`, potentially custom ones).
*   Rate limiting should be applied to login and potentially 2FA verification endpoints.
*   Password complexity rules enforced by Django settings.
*   Webhook validation needed if external services trigger auth events (not planned initially).

### 4.3 Integration
*   Integrates with Django `User` model.
*   Provides authentication backends for DRF.
*   Relies on secure storage for secrets/keys.
*   `django-otp` integrates with `User`.
*   `djangorestframework-api-key` integrates with DRF and Django Admin.

## 5. Non-Functional Requirements

*   **Security**: Paramount for all authentication operations.
*   **Reliability**: Login, token refresh, 2FA setup must be reliable.
*   **Performance**: Authentication checks and token generation should be fast.
*   **Usability**: API responses (especially errors) should be clear. 2FA setup flow should be understandable.

## 6. Success Metrics

*   Successful user login via JWT.
*   Successful token refresh.
*   Successful API authentication using API Keys.
*   Successful user enablement and disabling of TOTP 2FA.
*   Low rate of authentication-related errors/lockouts.
*   Security audits pass relevant authentication checks.

## 7. API Documentation Requirements

*   Document all Authentication API endpoints (`/auth/token/obtain/`, `/refresh/`, `/2fa/totp/setup/`, `/verify/`, `/disable/`, `/password/change/`).
*   Specify request methods, required headers (e.g., `Authorization: Bearer`, `X-API-Key`), request body formats, and response formats (success and error).
*   Explain the JWT obtain/refresh flow.
*   Explain how to use API Keys (header + key value).
*   Explain the TOTP setup/verify/disable flow.
*   Document permission requirements for each endpoint.

## 8. Testing Requirements

*   **Unit Tests**: Test any custom logic in views or serializers (e.g., password validation if customized). Mock external calls if any.
*   **Integration Tests / API Tests**:
    *   Test JWT obtain/refresh with valid/invalid credentials/tokens.
    *   Test API Key authentication with valid/invalid/expired/revoked keys using the `X-API-Key` header.
    *   Test full TOTP setup flow (initiate, verify with valid/invalid codes).
    *   Test TOTP disable flow (with correct/incorrect password).
    *   Test password change flow (with correct/incorrect old password, validation).
    *   Test permission enforcement on all endpoints.
*   **Security Tests**: Attempt common authentication attacks (e.g., brute force on login - check rate limiting, credential stuffing). Check for information leakage in error messages.

## 9. Deployment Requirements

*   Install required libraries in production environment.
*   Run all library migrations (`simplejwt`, `otp`, `api_key`).
*   Securely configure `SECRET_KEY`, `SIMPLE_JWT['SIGNING_KEY']`, database passwords, and external service keys (if any) via environment variables/secrets management.
*   Configure appropriate token lifetimes for production.
*   Administrators need access to Django Admin to manage API Keys.

## 10. Maintenance Requirements

*   Keep authentication libraries (`simplejwt`, `otp`, `api_key`) updated with security patches.
*   Monitor for authentication failures or suspicious activity (via logs).
*   Administrators manage API Keys lifecycle (creation, revocation, expiry). Rotate JWT signing key periodically.

--- END OF FILE auth_api_prd.md ---