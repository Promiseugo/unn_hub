"""
Production settings.
All secrets must come from environment variables.
Set DJANGO_SETTINGS_MODULE=config.settings.production on your server.
"""

from .base import *  # noqa
from decouple import config, Csv
import dj_database_url

# ─────────────────────────────────────────────
# SECURITY
# ─────────────────────────────────────────────
DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())
SECRET_KEY = config('DJANGO_SECRET_KEY')
csrf_trusted_origins = config('CSRF_TRUSTED_ORIGINS', default='')
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in csrf_trusted_origins.split(',')
    if origin.strip()
]

# HTTPS enforcement
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000          # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = 'same-origin'

# Secure cookies (HTTPS only)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7

# Admin URL — MUST be set via env var in production
# Defaults to 'admin/' only as a fallback; always override this
ADMIN_URL = config('ADMIN_URL', default='admin/')
if ADMIN_URL == 'admin/' and not DEBUG:
    import warnings
    warnings.warn(
        "ADMIN_URL is set to the default 'admin/' in production. "
        "Set a random ADMIN_URL env var to obscure the admin panel.",
        stacklevel=2,
    )


# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────
DATABASE_URL = config('DATABASE_URL', default='')
# For Neon: set DATABASE_MIGRATE_URL to the direct (non-pooled) connection string.
# Use DATABASE_URL (pooled) for the app; DATABASE_MIGRATE_URL (direct) for migrations only.
DATABASE_MIGRATE_URL = config('DATABASE_MIGRATE_URL', default=DATABASE_URL)

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=config('DB_CONN_MAX_AGE', default=60, cast=int),
            ssl_require=config('DB_SSL_REQUIRE', default=True, cast=bool),
        )
    }
    # Override with direct URL for migrate command only
    if DATABASE_MIGRATE_URL and DATABASE_MIGRATE_URL != DATABASE_URL:
        import sys
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            DATABASES['default'] = dj_database_url.parse(
                DATABASE_MIGRATE_URL,
                conn_max_age=0,
                ssl_require=True,
            )
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
            'CONN_MAX_AGE': 60,
            'OPTIONS': {
                'sslmode': 'require',           # Encrypt DB connection
            },
        }
    }


# ─────────────────────────────────────────────
# EMAIL
# ─────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)  # Must be False when USE_TLS=True
EMAIL_TIMEOUT = 10  # Seconds before SMTP connection times out (prevents silent hangs)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@unitrax.com')

# Sanity check: if email creds are missing, fall back to console so
# the app doesn't silently fail or 500 — just logs to Railway's stdout
if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# ─────────────────────────────────────────────
# MEDIA — Cloudinary (preferred) or S3 or local
# ─────────────────────────────────────────────
USE_CLOUDINARY = config('USE_CLOUDINARY', default=False, cast=bool)
USE_S3 = config('USE_S3', default=False, cast=bool)

if USE_CLOUDINARY:
    import cloudinary
    _cloud_name = config('CLOUDINARY_CLOUD_NAME')
    _api_key    = config('CLOUDINARY_API_KEY')
    _api_secret = config('CLOUDINARY_API_SECRET')
    cloudinary.config(cloud_name=_cloud_name, api_key=_api_key, api_secret=_api_secret, secure=True)
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': _cloud_name,
        'API_KEY':    _api_key,
        'API_SECRET': _api_secret,
    }
    STORAGES['default']['BACKEND'] = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    MEDIA_ROOT = BASE_DIR / 'media'
    MEDIA_URL = f"https://res.cloudinary.com/{_cloud_name}/image/upload/"

elif USE_S3:
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME')
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = config('AWS_QUERYSTRING_AUTH', default=True, cast=bool)
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    STORAGES['default']['BACKEND'] = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_S3_CUSTOM_DOMAIN = config('AWS_S3_CUSTOM_DOMAIN', default='')
    MEDIA_URL = (
        f'https://{AWS_S3_CUSTOM_DOMAIN}/'
        if AWS_S3_CUSTOM_DOMAIN
        else f'https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/'
    )


# ─────────────────────────────────────────────
# AXES — stricter in production
# ─────────────────────────────────────────────
AXES_FAILURE_LIMIT = 3              # Only 3 attempts in production
AXES_COOLOFF_TIME = 2               # 2 hour lockout


# ─────────────────────────────────────────────
# CACHING — Redis (optional but recommended)
# Set REDIS_URL env var to enable.
# Falls back to local-memory cache if not set.
# ─────────────────────────────────────────────
REDIS_URL = config('REDIS_URL', default='')

if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'


# ─────────────────────────────────────────────
# ERROR ALERTS — email fallback if Sentry not configured
# Django emails ADMINS on every unhandled 500 error when DEBUG=False
# and an email backend is configured (see EMAIL section above).
# ─────────────────────────────────────────────
_admin_email = config('ADMIN_ALERT_EMAIL', default='')
ADMINS = [('UniTraX Admin', _admin_email)] if _admin_email else []


# ─────────────────────────────────────────────
# ERROR MONITORING — Sentry (optional)
# Set SENTRY_DSN env var to enable.
# ─────────────────────────────────────────────
SENTRY_DSN = config('SENTRY_DSN', default='')

if SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=0.1,
            environment='production',
            send_default_pii=False,
        )
    except ImportError:
        pass  # sentry-sdk not installed — install it: pip install sentry-sdk
