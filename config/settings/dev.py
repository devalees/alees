# config/settings/dev.py
from .base import * # Inherit base settings first
import os

DEBUG = True
ALLOWED_HOSTS = ['*']
SECRET_KEY = env('SECRET_KEY', default='django-insecure-dev-key-placeholder-change-me')

# --- Development Specific Overrides ---

# Database: Explicitly parse DATABASE_URL for dev
DATABASES = {
    'default': env.db('DATABASE_URL', default='postgres://postgres:postgres@localhost:5432/alees')
}
if 'default' in DATABASES: DATABASES['default']['ATOMIC_REQUESTS'] = True

# Email: Use console backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS: Allow local frontend origins
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    "http://localhost:3000", "http://127.0.0.1:3000",
])

# Celery: Run tasks eagerly for easier debugging
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True # Raise task exceptions directly

# --- Add Development Tools ---
try:
    # Add to the lists inherited from base.py
    THIRD_PARTY_APPS += [
        'debug_toolbar',
        'django_extensions',
    ]
    # IMPORTANT: Reconstruct the final INSTALLED_APPS list
    INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

    MIDDLEWARE += [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ]
    INTERNAL_IPS = ['127.0.0.1']
except NameError: # Handle case where base lists aren't defined (shouldn't happen with import *)
    print("Warning: Could not add debug_toolbar/django_extensions. Base settings lists might be missing.")
# --- End Development Tools ---


# Passwords: Disable complexity validation for easier testing
AUTH_PASSWORD_VALIDATORS = []

# Logging: Increase level for dev
LOGGING['root']['level'] = 'DEBUG'
if 'loggers' in LOGGING:
    LOGGING['loggers']['django']['level'] = 'DEBUG'
    LOGGING['loggers']['api']['level'] = 'DEBUG'
    LOGGING['loggers']['core']['level'] = 'DEBUG'
    LOGGING['loggers']['celery']['level'] = 'DEBUG'

# Use LocMemCache if no specific CACHE_URLs are set in .env
CACHES['default'] = env.cache('CACHE_URL', default='locmemcache://')
CACHES['permissions'] = env.cache('PERMISSIONS_CACHE_URL', default='locmemcache://permissions')
CACHES['api_responses'] = env.cache('API_RESPONSES_CACHE_URL', default='locmemcache://api_responses')

# File Storage: Use FileSystemStorage if not set in .env
DEFAULT_FILE_STORAGE = env('DJANGO_DEFAULT_FILE_STORAGE', default='django.core.files.storage.FileSystemStorage')