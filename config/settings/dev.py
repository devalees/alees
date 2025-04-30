# config/settings/dev.py
from .base import * # Import base settings including DJANGO_APPS, THIRD_PARTY_APPS, LOCAL_APPS
import os

DEBUG = True
ALLOWED_HOSTS = ['*']
SECRET_KEY = env('SECRET_KEY', default='django-insecure-dev-key-placeholder-change-me')

# Use console email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Allow local frontend origins
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    "http://localhost:3000", "http://127.0.0.1:3000",
])

# Run Celery tasks eagerly
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# --- Add Development Tools ---
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
# --- End Development Tools ---


# Disable password validation complexity in development
AUTH_PASSWORD_VALIDATORS = []

# Adjust Logging for dev if needed (inherited from base by default)
# LOGGING['root']['level'] = 'DEBUG'
# LOGGING['loggers']['django']['level'] = 'DEBUG'
# ... etc ...