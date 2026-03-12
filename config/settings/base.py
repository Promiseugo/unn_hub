"""
Base settings for UNN Exchange & Services Hub.
All environments inherit from this file.
"""

from pathlib import Path
from decouple import config

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
# Build paths like: BASE_DIR / 'subdir'
# BASE_DIR points to the project root (where manage.py lives)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# ─────────────────────────────────────────────
# SECURITY
# ─────────────────────────────────────────────
SECRET_KEY = config('DJANGO_SECRET_KEY')

# ─────────────────────────────────────────────
# CUSTOM USER MODEL
# This MUST be set before the first migration.
# Changing this after migrations requires a full DB reset.
# ─────────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.User'


# ─────────────────────────────────────────────
# APPLICATIONS
# ─────────────────────────────────────────────
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',   # Required by reviews (GenericForeignKey)
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'crispy_forms',
    'crispy_bootstrap5',
    'django_filters',
]

LOCAL_APPS = [
    'apps.core',
    'apps.accounts',
    'apps.marketplace',
    'apps.services',
    'apps.messaging',
    'apps.reviews',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# ─────────────────────────────────────────────
# MIDDLEWARE
# ─────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # Serve static files in prod
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ─────────────────────────────────────────────
# URLS & WSGI
# ─────────────────────────────────────────────
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'


# ─────────────────────────────────────────────
# TEMPLATES
# ─────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # Project-level templates
        'APP_DIRS': True,                   # Also finds app-level templates/
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


# ─────────────────────────────────────────────
# PASSWORD VALIDATION
# ─────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ─────────────────────────────────────────────
# INTERNATIONALISATION
# ─────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True


# ─────────────────────────────────────────────
# STATIC FILES
# ─────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'   # collectstatic writes here
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# ─────────────────────────────────────────────
# MEDIA FILES (user uploads)
# ─────────────────────────────────────────────
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ─────────────────────────────────────────────
# DEFAULT PRIMARY KEY
# ─────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ─────────────────────────────────────────────
# AUTH REDIRECTS
# ─────────────────────────────────────────────
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'marketplace:listing-list'
LOGOUT_REDIRECT_URL = 'accounts:login'


# ─────────────────────────────────────────────
# CRISPY FORMS
# ─────────────────────────────────────────────
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'


# ─────────────────────────────────────────────
# MESSAGES FRAMEWORK
# Map Django message levels to Bootstrap alert classes
# ─────────────────────────────────────────────
from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}
