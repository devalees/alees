from .base import *
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Ensure SECRET_KEY is loaded securely from environment ONLY
SECRET_KEY = env('SECRET_KEY') # No default here! Must be set in prod env.

# Ensure ALLOWED_HOSTS is loaded securely from environment ONLY
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS') # No default here! Must be set in prod env.

# Database (Ensure DATABASE_URL is set in prod env)
DATABASES = {
    'default': env.db('DATABASE_URL'),
}
DATABASES['default']['ATOMIC_REQUESTS'] = True

# File Storage Configuration (Ensure DJANGO_DEFAULT_FILE_STORAGE is set, e.g., S3)
# DEFAULT_FILE_STORAGE = env('DJANGO_DEFAULT_FILE_STORAGE') # Should be set in prod env
# MEDIA_ROOT/URL only relevant if using FileSystemStorage, usually not needed with S3
# MEDIA_ROOT = env('MEDIA_ROOT', default=os.path.join(BASE_DIR, 'media'))
# MEDIA_URL = env('MEDIA_URL', default='/media/')

# Security Headers (Enforce HTTPS and other security headers)
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True) # Default True for Prod
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=True) # Default True for Prod
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=True) # Default True for Prod
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000) # Default 1 year for Prod
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True) # Default True for Prod
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=True) # Default True for Prod
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') # If behind proxy/LB handling TLS

# Email (Ensure production Email settings are set via env vars)
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
# Ensure EMAIL_HOST, PORT, TLS, USER, PASSWORD are set in prod env

# CORS (Ensure production frontend origins are set via env vars)
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS') # No default
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS') # Add your frontend domains here

# Logging (Configure for production - e.g., INFO level, potentially JSON formatter, send to external service)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        # Consider a JSON formatter for production log aggregation
        # 'json': {
        #     '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
        #     'format': '%(asctime)s %(levelname)s %(name)s %(message)s %(pathname)s %(lineno)d',
        # },
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'console': { # Log to console for container stdout/stderr collection
            'class': 'logging.StreamHandler',
            'formatter': 'verbose', # Or 'json'
        },
        # Add Sentry handler if using Sentry
        # 'sentry': {
        #     'level': 'ERROR',
        #     'class': 'sentry_sdk.integrations.logging.EventHandler',
        # },
    },
    'root': {
        'handlers': ['console'], # Add 'sentry' if configured
        'level': env('ROOT_LOG_LEVEL', default='INFO'), # INFO level for prod often good
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'django.security.DisallowedHost': { # Reduce noise from disallowed host errors
             'handlers': ['console'],
             'level': 'WARNING',
             'propagate': False,
         },
        # Add specific app loggers if needed
    },
}

# Cache (Ensure CACHE_URL etc. point to production Redis/Memcached)
# CACHES = { ... } # Load production cache config via env.cache()

# Channels (Ensure REDIS_URL points to production Redis for channels)
# CHANNEL_LAYERS = { ... } # Load production channel config via env vars/url

# Static Files (Ensure STATIC_ROOT is set for collectstatic)
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_prod')

# Celery (Should not run eagerly in production)
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = False