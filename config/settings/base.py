import os
from pathlib import Path
from datetime import timedelta

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Initialize environment variables
env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False),
    SECRET_KEY=(str, 'your-secret-key-here'), # Replace in production!
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
    DATABASE_URL=(str, 'postgres://postgres:postgres@localhost:5432/alees'),
    REDIS_URL=(str, 'redis://localhost:6379/0'),
    CELERY_BROKER_URL=(str, 'redis://localhost:6379/1'), # Use different DB for broker
    CELERY_RESULT_BACKEND=(str, 'redis://localhost:6379/2'), # Use different DB for results
    # Add other env var defaults as needed
)

# Read .env file for local dev if it exists
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS') # Use env.list to parse comma-separated string

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    # Core API & Framework
    'rest_framework',
    'corsheaders',
    'django_filters',

    # Database & ORM Extensions
    'mptt',                     # For hierarchical data (Org, Category, StockLocation)
    'taggit',                   # For tagging (Product, Contact, Org, Doc, File)

    # Authentication & Authorization
    'rest_framework_simplejwt', # For JWT
    'django_otp',               # Core OTP library
    'django_otp.plugins.otp_totp', # TOTP plugin (must be listed)
    'rest_framework_api_key', # For API Keys

    # Async Tasks & Scheduling
    'django_celery_beat',       # DB Scheduler for Celery (Automation)
    'django_celery_results',    # Optional: To store task results in DB

    # Internationalization & Data Types
    'phonenumber_field',        # For Contact phone numbers
    'django_countries',         # For Address country field

    # Real-time
    'channels',                 # For WebSockets (Chat)

    # Data Handling & Utilities
    'import_export',            # For Data Import/Export framework (admin integration)
    'django_fsm',               # For State Machine / Workflow
    'flags',                    # For Feature Flags

    # Search Integration
    'django_elasticsearch_dsl', # For Elasticsearch integration

    # Monitoring (SDK often doesn't need to be an app, butprometheus might)
    'django_prometheus',        # For exposing Prometheus metrics

    # Helpers
    'crum',                     # For Auditable middleware
]

LOCAL_APPS = [
    # Core App
    'core.apps.CoreConfig',

    # API Apps (Adjust based on your final structure)
    'api.v1.base_models.common.auth.apps.AuthConfig', # New Auth app
    'api.v1.base_models.common.apps.CommonConfig',
    'api.v1.base_models.common.currency.apps.CurrencyConfig',  # Add Currency app
    'api.v1.base_models.common.address.apps.AddressConfig',  # Add Address app
    # 'api.v1.base_models.contact.apps.ContactConfig', # Renamed from user based on models
    'api.v1.base_models.organization.apps.OrganizationConfig',
    'api.v1.base_models.user.apps.UserConfig', # Keeps UserProfile separate
    # Add other feature/base apps as they are created
    # 'api.v1.features.products.apps.ProductsConfig',
    # 'api.v1.features.inventory.apps.InventoryConfig',
    # 'api.v1.data_jobs.apps.DataJobsConfig',
    # 'api.v1.search.apps.SearchConfig',
    # ... etc ...
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS



MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware', # Place high, before CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware', # OTP Middleware after Auth
    'crum.CurrentRequestUserMiddleware', # For Auditable
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.file_validation.FileUploadValidationMiddleware', # Your custom middleware
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')], # Add base templates dir if needed
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application' # For Channels

# Database (Using django-environ)
# DATABASES = {
#     'default': env.db('DATABASE_URL', default='postgres://postgres:postgres@localhost:5432/alees')
# }
# DATABASES['default']['ATOMIC_REQUESTS'] = True # Recommended for API atomicity

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
# LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale')] # Define if using project-level locale files

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') # For collectstatic
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')] # For local dev static files

# Media files (User Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File Storage Settings
DEFAULT_FILE_STORAGE = env('DJANGO_DEFAULT_FILE_STORAGE', default='django.core.files.storage.FileSystemStorage')

# File Upload Validation Settings
MAX_UPLOAD_SIZE = env.int('MAX_UPLOAD_SIZE', default=10 * 1024 * 1024)  # 10MB
ALLOWED_MIME_TYPES = env.list('ALLOWED_MIME_TYPES', default=[
    'image/jpeg', 'image/png', 'application/pdf', 'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/csv', 'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
])

# File Security Settings (Consider removing if relying solely on storage backend)
# FILE_UPLOAD_PERMISSIONS = 0o644
# FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Cloud Storage Settings (AWS S3 Example - Requires django-storages & boto3)
# if DEFAULT_FILE_STORAGE == 'storages.backends.s3boto3.S3Boto3Storage':
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default=None)
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default=None)
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', default=None)
AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default=None)
AWS_S3_CUSTOM_DOMAIN = env('AWS_S3_CUSTOM_DOMAIN', default=None)
AWS_DEFAULT_ACL = env('AWS_DEFAULT_ACL', default='private') # Ensure uploads are private
AWS_S3_FILE_OVERWRITE = env.bool('AWS_S3_FILE_OVERWRITE', default=False) # Prevent accidental overwrites
AWS_QUERYSTRING_AUTH = env.bool('AWS_QUERYSTRING_AUTH', default=True) # Use pre-signed URLs
AWS_S3_VERIFY = env.bool('AWS_S3_VERIFY', default=True) # Verify SSL certs

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema', # For drf-spectacular
}

# API Key Settings
API_KEY_CUSTOM_HEADER = "X-Api-Key"

# JWT Settings (djangorestframework-simplejwt)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=env.int('JWT_ACCESS_TOKEN_LIFETIME', default=60)), # Increase default
    'REFRESH_TOKEN_LIFETIME': timedelta(days=env.int('JWT_REFRESH_TOKEN_LIFETIME', default=1)),
    'ROTATE_REFRESH_TOKENS': env.bool('JWT_ROTATE_REFRESH_TOKENS', default=True),
    'BLACKLIST_AFTER_ROTATION': env.bool('JWT_BLACKLIST_AFTER_ROTATION', default=True), # Needs blacklist app setup
    'UPDATE_LAST_LOGIN': env.bool('JWT_UPDATE_LAST_LOGIN', default=False),

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY, # Use Django SECRET_KEY by default
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5), # Not used unless SLIDING tokens enabled
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1), # Not used unless SLIDING tokens enabled
}

# OTP Settings
OTP_TOTP_ISSUER = env('OTP_TOTP_ISSUER', default='Alees') # Set your organization name

# CORS Settings
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    "http://localhost:3000", "http://127.0.0.1:3000" # Example Dev Frontend
])
CORS_ALLOW_CREDENTIALS = True
# CORS_ALLOW_ALL_ORIGINS = False # Explicitly False is safer

# Channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
             # Use separate Redis DB for channels if desired
            'hosts': [env('REDIS_URL', default='redis://localhost:6379/3')],
        },
    },
}

# Celery
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/1') # Use DB 1
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/2') # Use DB 2
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler' # For scheduled tasks via DB


# Elasticsearch Configuration (django-elasticsearch-dsl)
# Read hosts from environment variable defined in .env
# Format: comma-separated list of host:port, e.g., "host1:9200,host2:9200"
ELASTICSEARCH_HOSTS_LIST = env.list('ELASTICSEARCH_HOSTS', default=['localhost:9200'])

ELASTICSEARCH_DSL = {
    'default': {
        'hosts': ELASTICSEARCH_HOSTS_LIST,
        # Optional: Add authentication if your Elasticsearch requires it
        # 'http_auth': (env('ELASTICSEARCH_USER', default=None), env('ELASTICSEARCH_PASSWORD', default=null)),
        # 'timeout': env.int('ELASTICSEARCH_TIMEOUT', default=30),
    },
    # Define other clusters here if needed
    # 'other_cluster': { ... }
}

# IMPORTANT: Verify ELASTICSEARCH_HOSTS in .env
# - If ES runs in another docker-compose service named 'elasticsearch': set ELASTICSEARCH_HOSTS=elasticsearch:9200
# - If ES runs on your host machine (Mac/Win Docker Desktop): set ELASTICSEARCH_HOSTS=host.docker.internal:9200
# - If ES runs on your host machine (Linux): You might need the host's gateway IP or configure docker host networking.
# - The current default 'localhost:9200' will likely ONLY work if ES runs on the host AND you use host networking for the Django containers (not typical).



# API Documentation (drf-spectacular)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Alees ERP API',
    'DESCRIPTION': 'API documentation for the Alees ERP System',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False, # Schema available at /api/schema/
    # Optional: Useful settings
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    }
}

# Email (Set sensitive values in .env)
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default=None)
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default=None)
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default=None)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER or 'webmaster@localhost')

# Feature Flags (django-flags)
FEATURE_FLAGS_STORAGE = env('FEATURE_FLAGS_STORAGE', default='database') # Or 'redis'
FEATURE_FLAGS_REDIS_URL = env('FEATURE_FLAGS_REDIS_URL', default='redis://localhost:6379/4') # Use DB 4
# Default feature flags (can be overridden by DB/Redis storage)
FLAGS = {
    'AUTH_2FA_ENABLED': [{'condition': 'boolean', 'value': False}],
    'PROJECT_NEW_DASHBOARD': [{'condition': 'boolean', 'value': False}],
    'BILLING_INVOICE_AUTO_GENERATE': [{'condition': 'boolean', 'value': False}],
}

# Flag conditions
FLAG_CONDITIONS = {
    'boolean': 'flags.conditions.boolean',
    'user': 'flags.conditions.user',
    'percent': 'flags.conditions.percent',
    'path': 'flags.conditions.path',
}

# Flag template tags
FLAG_TEMPLATE_TAGS = [
    'flags.templatetags.flags',
]

# Security Settings (Set secure values in prod.py or via env vars)
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=False)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=False)
SECURE_BROWSER_XSS_FILTER = env.bool('SECURE_BROWSER_XSS_FILTER', default=True)
SECURE_CONTENT_TYPE_NOSNIFF = env.bool('SECURE_CONTENT_TYPE_NOSNIFF', default=True)
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=0) # Set > 0 in prod
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False) # Set True in prod
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=False) # Set True in prod

# Cache Configuration (Using django-environ's cache_url method)
# Example: CACHE_URL=rediscache://localhost:6379/0?PASSWORD=secret&COMPRESSOR=django_redis.compressors.zlib.ZlibCompressor
# Or separate env vars as before
CACHES = {
    'default': env.cache('CACHE_URL', default='locmemcache://'), # Default to LocMem if no URL
    # Define other caches like 'permissions', 'api_responses' using separate URLs or keys
    'permissions': env.cache('PERMISSIONS_CACHE_URL', default='locmemcache://permissions'),
    'api_responses': env.cache('API_RESPONSES_CACHE_URL', default='locmemcache://api_responses'),
}

# Redis Session Backend (If using redis for sessions)
# SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
# SESSION_CACHE_ALIAS = 'default' # Or a dedicated session cache alias

# Logging Configuration (Simplified - Configure handlers/loggers as needed)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': { # Example formatter
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose' # Use verbose for more info
        },
        # Add file handler, Sentry handler etc. here
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False, # Don't propagate Django logs to root
        },
        'celery': {
            'handlers': ['console'],
            'level': env('CELERY_LOG_LEVEL', default='INFO'),
            'propagate': True,
        },
        # Add loggers for your specific apps
        'core': {
            'handlers': ['console'],
            'level': env('APP_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'api': { # Catch logs from all api submodules
            'handlers': ['console'],
            'level': env('APP_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        # ... add other app loggers ...
    },
    'root': { # Catch-all logger
        'handlers': ['console'],
        'level': env('ROOT_LOG_LEVEL', default='WARNING'), # Default root to WARNING
    },
}