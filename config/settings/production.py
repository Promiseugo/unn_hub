"""
Production settings.
All secrets must come from environment variables.
Set DJANGO_SETTINGS_MODULE=config.settings.production on your server.
"""

from .base import *  # noqa
from decouple import config, Csv

# ─────────────────────────────────────────────
# SECURITY
# ─────────────────────────────────────────────
DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())
SECRET_KEY = config('DJANGO_SECRET_KEY')

# HTTPS enforcement
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000          # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Secure cookies (HTTPS only)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Admin URL — obscured in production
# Change 'secret-admin-url/' to something only you know
ADMIN_URL = config('ADMIN_URL', default='admin/')


# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────
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
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@unitrax.com')


# ─────────────────────────────────────────────
# MEDIA — S3 or local
# ─────────────────────────────────────────────
USE_S3 = config('USE_S3', default=False, cast=bool)

if USE_S3:
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME')
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = 'public-read'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/'


# ─────────────────────────────────────────────
# AXES — stricter in production
# ─────────────────────────────────────────────
AXES_FAILURE_LIMIT = 3              # Only 3 attempts in production
AXES_COOLOFF_TIME = 2               # 2 hour lockout
