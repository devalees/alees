import os
from pathlib import Path
from datetime import timedelta
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, 'your-secret-key-here'),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
    # Remove default DATABASE_URL parsing from here
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

DJANGO_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
]
THIRD_PARTY_APPS = [
    'rest_framework', 'corsheaders', 'django_filters', 'mptt', 'taggit',
    'rest_framework_simplejwt', 'django_otp', 'django_otp.plugins.otp_totp',
    'rest_framework_api_key', 'django_celery_beat', 'django_celery_results',
    'phonenumber_field', 'django_countries', 'channels', 'import_export',
    'django_fsm', 'flags', 'django_elasticsearch_dsl', 'django_prometheus', 'crum',
    'channels_redis', # Added channels_redis here as it's a dependency
    'drf_spectacular', # Ensure spectacular is listed for schema generation
    'django_redis', # Ensure django-redis is listed for cache
]
LOCAL_APPS = [
    'core.apps.CoreConfig',
    'core.rbac.apps.RbacConfig', # Added RBAC app
    'api.v1.base_models.common.auth.apps.AuthConfig',  # Updated auth app path
    'api.v1.base_models.common.apps.CommonConfig',
    'api.v1.base_models.common.address.apps.AddressConfig',  # Added address app
    'api.v1.base_models.common.category.apps.CategoryConfig', # Added category app
    'api.v1.base_models.common.currency.apps.CurrencyConfig',  # Added currency app
    'api.v1.base_models.common.fileStorage.apps.FileStorageConfig', # Added fileStorage app
    'api.v1.base_models.contact.apps.ContactConfig',
    'api.v1.base_models.organization.apps.OrganizationConfig',
    'api.v1.base_models.user.apps.UserConfig',
    'core.audit.apps.AuditConfig', # Added Audit app
    # Add other apps AppConfig paths here...
    # 'api.v1.features.products.apps.ProductsConfig', # Example
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'crum.CurrentRequestUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.file_validation.FileUploadValidationMiddleware',
]
ROOT_URLCONF = 'config.urls'
TEMPLATES = [ # Keep template settings simple in base
    {'BACKEND': 'django.template.backends.django.DjangoTemplates', 'APP_DIRS': True,
     'OPTIONS': { 'context_processors': [ # Basic required context processors
             'django.template.context_processors.debug', 'django.template.context_processors.request',
             'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages',
         ], }, }
]
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# --- Database Placeholder ---
# The actual configuration MUST be defined in dev.py, test.py, prod.py
DATABASES = {'default': {}} # Define empty dict to avoid import errors accessing DATABASES['default']

AUTH_PASSWORD_VALIDATORS = [ # Keep validators in base
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'en-us'; TIME_ZONE = 'UTC'; USE_I18N = True; USE_TZ = True
STATIC_URL = '/static/'; STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'; MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
DEFAULT_FILE_STORAGE = env('DJANGO_DEFAULT_FILE_STORAGE', default='django.core.files.storage.FileSystemStorage')
MAX_UPLOAD_SIZE = env.int('MAX_UPLOAD_SIZE', default=10 * 1024 * 1024)
ALLOWED_MIME_TYPES = env.list('ALLOWED_MIME_TYPES', default=[
    'image/jpeg', 'image/png', 'application/pdf', 'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/csv', 'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain', # Added plain text
])
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default='')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', default='')
AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='us-east-1')
AWS_REGION = env('AWS_REGION', default='us-east-1')  # Default to us-east-1 if not specified
AWS_S3_CUSTOM_DOMAIN = env('AWS_S3_CUSTOM_DOMAIN', default='')
AWS_DEFAULT_ACL = env('AWS_DEFAULT_ACL', default='private')
AWS_S3_FILE_OVERWRITE = env.bool('AWS_S3_FILE_OVERWRITE', default=False)
AWS_QUERYSTRING_AUTH = env.bool('AWS_QUERYSTRING_AUTH', default=True)
AWS_S3_VERIFY = env.bool('AWS_S3_VERIFY', default=True)
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_SECRETS_PREFIX = env('AWS_SECRETS_PREFIX', default='alees/')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = { # Base DRF settings
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework_api_key.permissions.HasAPIKey',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': env.int('API_PAGE_SIZE', default=20),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# API Key settings
API_KEY_CUSTOM_HEADER = "HTTP_X_API_KEY"

SIMPLE_JWT = { # Base JWT settings
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=env.int('JWT_ACCESS_TOKEN_LIFETIME', default=60)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=env.int('JWT_REFRESH_TOKEN_LIFETIME', default=1)),
    'ROTATE_REFRESH_TOKENS': env.bool('JWT_ROTATE_REFRESH_TOKENS', default=True),
    'BLACKLIST_AFTER_ROTATION': env.bool('JWT_BLACKLIST_AFTER_ROTATION', default=True),
    'UPDATE_LAST_LOGIN': env.bool('JWT_UPDATE_LAST_LOGIN', default=False),
    'ALGORITHM': 'HS256', 'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',), 'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id', 'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type', 'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    'JTI_CLAIM': 'jti',
}
OTP_TOTP_ISSUER = env('OTP_TOTP_ISSUER', default='Alees ERP')
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[]) # Define actual origins in dev/prod
CORS_ALLOW_CREDENTIALS = True
CHANNEL_LAYERS = { # Base Channels setup
    'default': {'BACKEND': 'channels_redis.core.RedisChannelLayer',
                'CONFIG': {'hosts': [env('CHANNEL_LAYERS_URL', default='redis://localhost:6379/3')]}}} # Use specific env var
CELERY_BROKER_URL = env('CELERY_BROKER_URL') # Read directly from env
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND') # Read directly from env
CELERY_ACCEPT_CONTENT = ['json']; CELERY_TASK_SERIALIZER = 'json'; CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE; CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
ELASTICSEARCH_HOSTS_LIST = env.list('ELASTICSEARCH_HOSTS', default=['localhost:9200'])
ELASTICSEARCH_DSL = {'default': {'hosts': ELASTICSEARCH_HOSTS_LIST}}
SPECTACULAR_SETTINGS = { # API Doc settings
    'TITLE': 'Alees ERP API', 'DESCRIPTION': 'API documentation for the Alees ERP System',
    'VERSION': '1.0.0', 'SERVE_INCLUDE_SCHEMA': False, 'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {'deepLinking': True, 'persistAuthorization': True, 'displayOperationId': True}
}
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend') # Default to console
EMAIL_HOST = env('EMAIL_HOST', default=None); EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default=None); EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default=None)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER or 'webmaster@localhost')
FEATURE_FLAGS_STORAGE = env('FEATURE_FLAGS_STORAGE', default='database')
FEATURE_FLAGS_REDIS_URL = env('FEATURE_FLAGS_REDIS_URL', default='redis://localhost:6379/4')
FLAGS = { # Default Flags
    'AUTH_2FA_ENABLED': [{'condition': 'boolean', 'value': False}],
    'PROJECT_NEW_DASHBOARD': [{'condition': 'boolean', 'value': False}],
    'BILLING_INVOICE_AUTO_GENERATE': [{'condition': 'boolean', 'value': False}],
}
FLAG_CONDITIONS = {'boolean': 'flags.conditions.boolean', 'user': 'flags.conditions.user', 'percent': 'flags.conditions.percent', 'path': 'flags.conditions.path'}
FLAG_TEMPLATE_TAGS = ['flags.templatetags.flags']
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=False)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=False)
SECURE_BROWSER_XSS_FILTER = env.bool('SECURE_BROWSER_XSS_FILTER', default=True)
SECURE_CONTENT_TYPE_NOSNIFF = env.bool('SECURE_CONTENT_TYPE_NOSNIFF', default=True)
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=False)
CACHES = { # Base Cache setup (default uses env var or LocMem)
    'default': env.cache('CACHE_URL', default='locmemcache://'),
    'permissions': env.cache('PERMISSIONS_CACHE_URL', default='locmemcache://permissions'),
    'api_responses': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-api-responses',
    },
    # Add RBAC cache definition
    'rbac': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-rbac', # Unique location
        'TIMEOUT': 3600, # Default timeout (e.g., 1 hour)
    }
}
LOGGING = { # Base Logging config
    'version': 1, 'disable_existing_loggers': False,
    'formatters': {'verbose': {'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s", 'datefmt': "%d/%b/%Y %H:%M:%S"}},
    'handlers': {'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'}},
    'loggers': {'django': {'handlers': ['console'], 'level': env('DJANGO_LOG_LEVEL', default='INFO'), 'propagate': False},
                'celery': {'handlers': ['console'], 'level': env('CELERY_LOG_LEVEL', default='INFO'), 'propagate': True},
                'core': {'handlers': ['console'], 'level': env('APP_LOG_LEVEL', default='INFO'), 'propagate': False},
                'api': {'handlers': ['console'], 'level': env('APP_LOG_LEVEL', default='INFO'), 'propagate': False},},
    'root': {'handlers': ['console'], 'level': env('ROOT_LOG_LEVEL', default='WARNING')},
}

# Phone Number Field Settings
PHONENUMBER_DEFAULT_REGION = 'US'  # Default region for phone number parsing
PHONENUMBER_DB_FORMAT = 'E164'  # Store phone numbers in E.164 format
PHONENUMBER_DEFAULT_FORMAT = 'INTERNATIONAL'  # Display format

# Organization Scoped Settings
DISABLE_PERMISSIONS_CHECK = env.bool('DISABLE_PERMISSIONS_CHECK', default=False)