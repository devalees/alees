# config/settings/test.py

import tempfile
from .base import *  # Inherit base settings first
import os
from pathlib import Path

# BASE_DIR and env should be inherited from base.py via '*' import

# Optional: Read .env.test file AFTER base .env, overwriting if necessary
# environ.Env.read_env(os.path.join(BASE_DIR, '.env.test'), overwrite=True)

# Override SECRET_KEY for testing consistency
SECRET_KEY = env('TEST_SECRET_KEY', default='django-insecure-test-key-safe-for-tests')

# Ensure DEBUG is False unless overridden by TEST_DEBUG env var
DEBUG = env.bool('TEST_DEBUG', default=False)

# Override ALLOWED_HOSTS for testing
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# AWS Settings for testing (Inherited from base or override if needed)
# AWS_REGION = env('TEST_AWS_REGION', default='us-east-1')
# ... etc ...

# --- Database Configuration for Testing ---
# !!! THIS BLOCK MUST EXIST AND BE CORRECT IN test.py !!!
# It completely REPLACES the DATABASES definition from base.py for the test environment.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('TEST_DB_NAME'),           # Reads env var set by compose
        'USER': env('TEST_DB_USER'),           # Reads env var set by compose
        'PASSWORD': env('TEST_DB_PASSWORD'),   # Reads env var set by compose
        'HOST': env('TEST_DB_HOST'),           # Reads env var set by compose ('postgres')
        'PORT': env('TEST_DB_PORT'),           # Reads env var set by compose ('5432')
        # Inherit ATOMIC_REQUESTS from base.py's DATABASES definition if it was set there
        # Or explicitly set it:
        # 'ATOMIC_REQUESTS': True,
    }
}
# Add ATOMIC_REQUESTS if it wasn't set in base.py's DATABASES dict initially
if 'ATOMIC_REQUESTS' not in DATABASES['default']:
     DATABASES['default']['ATOMIC_REQUESTS'] = True

# --- Other Test-Specific Overrides ---
# Cache (Use LocMemCache) - This correctly overrides base.py's CACHES
CACHES = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'unique-default-test-location'},
    'permissions': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'unique-permissions-test-location'},
    'api_responses': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'unique-api-responses-test-location'},
}

# Celery (Run synchronously) - This correctly overrides base.py's CELERY settings
CELERY_TASK_ALWAYS_EAGER = env.bool('CELERY_TASK_ALWAYS_EAGER', default=True)
CELERY_TASK_EAGER_PROPAGATES = env.bool('CELERY_TASK_EAGER_PROPAGATES', default=True)
CELERY_BROKER_URL = env('TEST_CELERY_BROKER_URL', default='memory://')
CELERY_RESULT_BACKEND = env('TEST_CELERY_RESULT_BACKEND', default='cache+memory://')

# Email (Use locmem backend)
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Passwords (Use faster hasher, disable validators)
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
AUTH_PASSWORD_VALIDATORS = []

# Logging (Simplify) - This correctly overrides base.py's LOGGING
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {'class': 'logging.NullHandler'},
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {},
    'root': {
        'handlers': ['null'],
        'level': env('TEST_LOG_LEVEL', default='WARNING'),
    },
}

# Migrations (Disable for speed)
# class DisableMigrations:
#     def __contains__(self, item): return True
#     def __getitem__(self, item): return None
# MIGRATION_MODULES = DisableMigrations() # Keep Migrations ENABLED for testing

# File Storage (Use temp dir)
MEDIA_ROOT = tempfile.mkdtemp()
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Channels (Use in-memory layer)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Ensure dev tools are not installed/used in tests
# This filtering step IS IMPORTANT
_DEVS_APPS_TO_REMOVE = ['debug_toolbar', 'django_extensions']
INSTALLED_APPS = [app for app in INSTALLED_APPS if app not in _DEVS_APPS_TO_REMOVE]
MIDDLEWARE = [m for m in MIDDLEWARE if 'debug_toolbar' not in m]
