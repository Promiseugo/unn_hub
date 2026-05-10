"""
Development settings — SQLite, console email.
"""

from .base import *  # noqa
from decouple import config

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# ── Database: SQLite ───────────────────────────────────────────
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

# ── Media files ────────────────────────────────────────────────
USE_S3 = False
