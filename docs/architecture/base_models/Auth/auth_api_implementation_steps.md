

--- START OF FILE auth_api_implementation_steps.md (Revised for API Keys) ---

# Authentication API - Implementation Steps (Revised for API Keys)

## 1. Overview

**Feature Name:**
Authentication API (JWT + API Key + 2FA Enablement)

**Depends On:**
Django `auth` app (`User` model), `UserProfile` model, `djangorestframework-simplejwt`, `django-otp`, `djangorestframework-api-key`. Secure settings management.

**Key Features:**
Provides API endpoints for user login (username/password) via JWT, token refresh, and enables users to set up TOTP 2FA. Also integrates API Key authentication using `djangorestframework-api-key` via the `X-API-Key` header for server-to-server communication. Excludes 2FA verification during login and full password reset flow initially.

**Primary Location(s):**
*   Library Configuration: `settings.py`.
*   API Views/Serializers/URLs: Dedicated `auth` app (`api/v1/base_models/comon/auth/`) or within `user` app (`api/v1/base_models/user/`). Assume **new `auth` app**.
*   2FA Device Models: Provided by `django-otp`.
*   API Key Models: Provided by `rest_framework_api_key`.

## 2. Prerequisites

[ ] Verify `User` and `UserProfile` models are implemented and migrated.
[ ] **Install Libraries:** `pip install djangorestframework-simplejwt django-otp qrcode[pil] djangorestframework-api-key`.
[ ] Add `'rest_framework_simplejwt'`, `'django_otp'`, `'django_otp.plugins.otp_totp'`, and `'rest_framework_api_key'` to `INSTALLED_APPS`.
[ ] Add `'django_otp.middleware.OTPMiddleware'` to `MIDDLEWARE` (after `AuthenticationMiddleware`).
[ ] **Configure `simplejwt`:** Set up `SIMPLE_JWT` settings (token lifetimes, etc.) as previously defined.
[ ] **Configure `django-otp`:** Set `OTP_TOTP_ISSUER` as previously defined.
[ ] **Configure `djangorestframework-api-key`:** Specify the custom header name in `settings.py`.
    ```python
    # config/settings/base.py
    REST_FRAMEWORK_API_KEY = {
        'HEADER_NAME': 'HTTP_X_API_KEY', # DRF converts X-Api-Key header to this META key
        'CLIENT_ID_HEADER_NAME': None, # Not using Client ID header
    }
    ```
[ ] **Configure DRF Authentication Classes:** Update default authentication classes to include both JWT and API Key.
    ```python
    # config/settings/base.py
    REST_FRAMEWORK = {
        # ... other settings ...
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'rest_framework_simplejwt.authentication.JWTAuthentication',
            'rest_framework_api_key.authentication.APIKeyAuthentication', # Add API Key Auth
        ],
        # ... other settings like DEFAULT_PERMISSION_CLASSES ...
    }
    ```
[ ] Create new Django app: `python manage.py startapp auth`. Add `'api.v1.base_models.comon.auth'` to `INSTALLED_APPS`.
[ ] Ensure `factory-boy` and `UserFactory` exist.

## 3. Implementation Steps (TDD Workflow)

  ### 3.1 Library Migrations

  [ ] Run `python manage.py makemigrations django_otp otp_totp rest_framework_api_key`.
  [ ] **Review migrations** created by the libraries.
  [ ] Run `python manage.py migrate`.

  ### 3.2 JWT Token Endpoints (Login/Refresh)

  [ ] **(Test First)** Write **API Test(s)** (`auth/tests/api/test_token_endpoints.py`) for JWT obtain/refresh endpoints.
  [ ] Create `api/v1/base_models/comon/auth/urls.py`. Include `simplejwt` views (`TokenObtainPairView`, `TokenRefreshView`).
  [ ] Include `auth.urls` in main `api/v1/urls.py` under the `auth/` prefix.
  [ ] Run tests; expect pass. Refactor simplejwt settings if needed.

  ### 3.3 API Key Admin Management

  [ ] **(Manual Test)** Access Django Admin. Verify the "API Key Permissions" section exists (provided by `djangorestframework-api-key`).
  [ ] Create a test API Key via the Admin:
      *   Give it a Name (e.g., "Test Service Key").
      *   **Important:** Note down the **unhashed** key generated (it's only shown once).
      *   Optionally assign permissions directly to this key object if `HasAPIKey` permission class will be used later.
      *   Set an expiry date.
      *   Save the key.

  ### 3.4 API Key Authentication Testing

  [ ] **(Test First)** Write **API Test(s)** (`auth/tests/api/test_api_key.py`) for accessing a sample authenticated endpoint (e.g., `/api/v1/profiles/me/` if implemented, or create a simple test view):
      *   Test making a request **without** the `X-API-Key` header -> Assert 401/403 (depending on if JWT allows anonymous or not).
      *   Test making a request with an **invalid/incorrect** `X-API-Key` header -> Assert 401/403.
      *   Test making a request with the **correct, unhashed** `X-API-Key` header (obtained from Admin) -> Assert 200 OK (or appropriate success code for the endpoint).
      *   Test with an **expired** API Key -> Assert 401/403.
      *   Test with a **revoked** API Key -> Assert 401/403.
      Run; expect tests requiring a valid key to pass, others to fail appropriately.
  [ ] *(No code changes needed here, this tests the configuration)*.

  ### 3.5 2FA (TOTP) Device Setup Models & Admin

  [ ] *(No code changes, covered by migrations in 3.1)*.
  [ ] **(Manual Test - Optional)** Verify `TOTPDevice` admin integration if configured.

  ### 3.6 2FA (TOTP) Enablement API Endpoints

  [ ] **(Test First)** Write API Tests (`auth/tests/api/test_2fa_setup.py`) for TOTP Setup (`POST /setup/`) and Verification (`POST /verify/`) as outlined previously.
  [ ] Create `auth/views.py` and `auth/serializers.py`. Define `TOTPSetupView` and `TOTPVerifyView` as outlined previously.
  [ ] Add URLs for these views in `auth/urls.py`.
  [ ] Run setup/verification API tests; expect pass. Refactor views.

  ### 3.7 2FA Disable Endpoint (Basic)

  [ ] **(Test First)** Write API Test for `POST /api/v1/auth/2fa/totp/disable/`.
  [ ] Add `TOTPDisableView(APIView)` requiring password confirmation. Add URL.
  [ ] Run disable tests; expect pass.

  ### 3.8 Password Management API (Basic Change)

  [ ] **(Test First)** Write API Test for `POST /api/v1/auth/password/change/`.
  [ ] Add a `PasswordChangeView(GenericAPIView)` using Django's `PasswordChangeForm` or a custom serializer. Add URL.
  [ ] Run password change tests; expect pass.

## 4. Final Checks

[ ] Run the *entire* test suite (`pytest`). Verify JWT and API Key auth paths work. Verify 2FA setup flow tests.
[ ] Run linters (`flake8`) and formatters (`black`).
[ ] Check code coverage (`pytest --cov=auth`).
[ ] Manually test JWT login/refresh via API client.
[ ] Manually test API access using a generated API Key with the `X-API-Key` header.
[ ] Manually test the TOTP setup flow: Call setup -> scan QR -> call verify. Test disable. Test password change.
[ ] Review API documentation draft for auth endpoints (JWT, API Key usage, 2FA setup).

## 5. Follow-up Actions / Future Considerations

[ ] **CRITICAL:** Implement 2FA verification **during the login flow** (modifying JWT obtain view).
[ ] Implement full Password Reset flow.
[ ] Implement API endpoint for Admins to manage API Keys if needed beyond Django Admin.
[ ] Implement management of other OTP devices (Static/Backup codes).
[ ] Implement token blocklisting for JWT logout.
[ ] Define and apply specific API Key permissions using `rest_framework_api_key.permissions.HasAPIKey` where needed.
[ ] Create Pull Request.
[ ] Update API documentation.

--- END OF FILE auth_api_implementation_steps.md (Revised for API Keys) ---