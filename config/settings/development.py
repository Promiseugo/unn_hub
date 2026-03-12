"""
Development settings.
Uses SQLite for zero-config local setup.
Set DJANGO_SETTINGS_MODULE=config.settings.development in your .env
"""

from .base import *  # noqa

from decouple import config

# ─────────────────────────────────────────────
# SECURITY
# ─────────────────────────────────────────────
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']


# ─────────────────────────────────────────────
# DATABASE
# Dev: SQLite (no setup required)
# Switch to PostgreSQL anytime by commenting
# the SQLite block and uncommenting PostgreSQL.
# ─────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# PostgreSQL (uncomment when ready)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('DB_NAME'),
#         'USER': config('DB_USER'),
#         'PASSWORD': config('DB_PASSWORD'),
#         'HOST': config('DB_HOST', default='localhost'),
#         'PORT': config('DB_PORT', default='5432'),
#     }
# }


# ─────────────────────────────────────────────
# DEBUG TOOLBAR
# ─────────────────────────────────────────────
INSTALLED_APPS += ['debug_toolbar']  # noqa: F405
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')  # noqa: F405
INTERNAL_IPS = ['127.0.0.1']


# ─────────────────────────────────────────────
# EMAIL
# Prints emails to terminal — no SMTP needed
# ─────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# ─────────────────────────────────────────────
# MEDIA
# ─────────────────────────────────────────────
USE_S3 = False
