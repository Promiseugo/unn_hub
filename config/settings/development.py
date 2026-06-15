"""
Development settings — SQLite, console email.
"""

import sys

from .base import *  # noqa
from decouple import config
import dj_database_url

DEBUG = True
ALLOWED_HOSTS = sorted({
    'localhost',
    '127.0.0.1',
    '[::1]',
    'testserver',
    *[
        host.strip()
        for host in config('ALLOWED_HOSTS', default='').split(',')
        if host.strip()
    ],
})

# ── Database: SQLite ───────────────────────────────────────────
# Always use SQLite when running tests, regardless of DATABASE_URL.
# This avoids Neon test-database create/teardown conflicts entirely
# (PowerShell's `$env:DATABASE_URL = ""` doesn't reliably unset the
# var on Windows, so .env's Neon URL would otherwise still be picked up).
RUNNING_TESTS = 'test' in sys.argv or 'pytest' in sys.modules

DATABASE_URL = config('DATABASE_URL', default='')

if DATABASE_URL and not RUNNING_TESTS:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=config('DB_CONN_MAX_AGE', default=60, cast=int),
            ssl_require=config('DB_SSL_REQUIRE', default=False, cast=bool),
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ── Email: print to terminal ───────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ── Debug Toolbar — DISABLED ───────────────────────────────────
# Uncomment the 4 lines below ONLY if you need to debug queries.
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
# INTERNAL_IPS = ['127.0.0.1']
# DEBUG_TOOLBAR_CONFIG = {'SHOW_COLLAPSED': True}

# ── Media / Cloudinary ─────────────────────────────────────────
# BUG FIX: Do NOT import from production.py — that caused a circular
# settings import. Read USE_CLOUDINARY directly from the environment.
USE_S3 = False
USE_CLOUDINARY = config('USE_CLOUDINARY', default=False, cast=bool)

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
    # Django 5.x requires STORAGES dict — DEFAULT_FILE_STORAGE is removed and ignored
    STORAGES['default']['BACKEND'] = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    MEDIA_URL = f"https://res.cloudinary.com/{_cloud_name}/image/upload/"
    MEDIA_ROOT = BASE_DIR / 'media'
# else: local FileSystemStorage and '/media/' inherited from base.py

# ── Static files for development/testing ──────────────────────
# Override to plain StaticFilesStorage so tests don't require
# collectstatic to have been run (Manifest backend crashes tests
# with "Missing staticfiles manifest entry" otherwise)
STORAGES['staticfiles']['BACKEND'] = 'django.contrib.staticfiles.storage.StaticFilesStorage'
# Keep legacy alias in sync (see base.py) — django-cloudinary-storage
# checks settings.STATICFILES_STORAGE directly during collectstatic.
STATICFILES_STORAGE = STORAGES['staticfiles']['BACKEND']
