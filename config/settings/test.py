# config/settings/test.py
import tempfile
from .base import *  # Inherit base settings first
import os
from pathlib import Path

# --- Explicitly Define DATABASES for Test ---
# Uses TEST_DB_* environment variables set by docker-compose
# This definition REPLACES the one from base.py entirely for this scope
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('TEST_DB_NAME'),
        'USER': env('TEST_DB_USER'),
        'PASSWORD': env('TEST_DB_PASSWORD'),
        'HOST': env('TEST_DB_HOST'), # Should be 'postgres' service name
        'PORT': env('TEST_DB_PORT'), # Should be '5432'
        'ATOMIC_REQUESTS': True,
    }
}
# --- End Database Override ---

# BASE_DIR and env inherited

# Optional: Read .env.test file AFTER base .env, overwriting OTHER vars
# environ.Env.read_env(os.path.join(BASE_DIR, '.env.test'), overwrite=True)

# Test-specific overrides
SECRET_KEY = env('TEST_SECRET_KEY', default='django-insecure-test-key-safe-for-tests')
DEBUG = env.bool('TEST_DEBUG', default=False)
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# AWS Settings for testing (Optional: Override base if needed)
# AWS_ACCESS_KEY_ID = 'testing' ... etc.

# Cache (Use LocMemCache for test isolation)
CACHES = {
    'default': { # Keep default as is (likely memory or dummy)
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'default-test-cache',
    },
    'rbac': { # Define the rbac cache needed by core.rbac.permissions
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', # Use in-memory for tests
        'LOCATION': 'rbac-test-cache', # Unique location name
        'TIMEOUT': 300, # Optional: Shorter timeout for tests
    },
    'permissions': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'unique-permissions-test'},
    'api_responses': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'unique-api-responses-test'},
}

# Celery - Run tasks synchronously for testing
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True # Propagate exceptions raised in tasks
CELERY_BROKER_URL = env('TEST_CELERY_BROKER_URL', default='memory://')
CELERY_RESULT_BACKEND = env('TEST_CELERY_RESULT_BACKEND', default='cache+memory://')

# Email (Use locmem backend)
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Passwords (Use faster hasher, disable validators)
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
AUTH_PASSWORD_VALIDATORS = []

# Logging (Simplify for tests)
LOGGING = {
    'version': 1, 'disable_existing_loggers': True,
    'handlers': { 'null': {'class': 'logging.NullHandler'} },
    'loggers': {}, 'root': { 'handlers': ['null'], 'level': env('TEST_LOG_LEVEL', default='WARNING')},
}

# Migrations (Disable for speed - Usually OK, re-enable if needed)
# class DisableMigrations:
#     def __contains__(self, item): return True
#     def __getitem__(self, item): return None
# MIGRATION_MODULES = DisableMigrations()

# File Storage (Use temp dir)
MEDIA_ROOT = tempfile.mkdtemp()
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Channels (Use in-memory layer)
CHANNEL_LAYERS = { 'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'} }

# Ensure dev tools are not installed/used in tests
# These filters run on the lists inherited from base.py
_DEVS_APPS_TO_REMOVE = ['debug_toolbar', 'django_extensions']
# Add the new test utility app
INSTALLED_APPS = ['core.tests_app.apps.CoreTestsAppConfig'] + \
                 [app for app in INSTALLED_APPS if app not in _DEVS_APPS_TO_REMOVE]
MIDDLEWARE = [m for m in MIDDLEWARE if 'debug_toolbar' not in m]

# Remove the dynamic test app config path
# INSTALLED_APPS += [
#     'core.rbac.tests.integration.apps.RBACIntegrationTestAppConfig',
# ]

# Remove the dynamically added app path that caused issues
# INSTALLED_APPS += [
#     'core.rbac.tests.integration.test_viewset_integration',
# ]