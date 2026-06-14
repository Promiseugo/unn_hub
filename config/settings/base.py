"""
Base settings for UNN Exchange & Services Hub.
All environments inherit from this file.
"""

from pathlib import Path
from decouple import config
from django.contrib.messages import constants as messages

# ---------------------------------------------
# PATHS
# ---------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------
# SECURITY
# ---------------------------------------------
SECRET_KEY = config('DJANGO_SECRET_KEY')
AUTH_USER_MODEL = 'accounts.User'

# Branding / email defaults
SITE_NAME = config('SITE_NAME', default='UniTraX')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@unitrax.com')
SERVER_EMAIL = config('SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)
SUPPORT_EMAIL = config('SUPPORT_EMAIL', default='support@unitrax.com')
ACCOUNT_LOGIN_ALERT_EMAILS = config('ACCOUNT_LOGIN_ALERT_EMAILS', default=False, cast=bool)
IMAGE_UPLOAD_MAX_DIMENSION = config('IMAGE_UPLOAD_MAX_DIMENSION', default=1600, cast=int)
IMAGE_UPLOAD_QUALITY = config('IMAGE_UPLOAD_QUALITY', default=82, cast=int)
OFFICIAL_UNIVERSITY_EMAIL_DOMAINS = [
    item.strip().lower()
    for item in config('OFFICIAL_UNIVERSITY_EMAIL_DOMAINS', default='unn.edu.ng,student.unn.edu.ng').split(',')
    if item.strip()
]
REQUIRE_UNIVERSITY_EMAIL_VERIFICATION = config('REQUIRE_UNIVERSITY_EMAIL_VERIFICATION', default=True, cast=bool)
EMAIL_OTP_TTL_MINUTES = config('EMAIL_OTP_TTL_MINUTES', default=10, cast=int)

# Password reset link expiry — Django default is 3 days (259200s), which is too long.
# Tightened to 1 hour per security best practice.
PASSWORD_RESET_TIMEOUT = config('PASSWORD_RESET_TIMEOUT', default=3600, cast=int)  # 1 hour
SAFETY_ACK_VERSION = config('SAFETY_ACK_VERSION', default='2026-05')
MVP_MANUAL_VERIFICATION_ONLY = config('MVP_MANUAL_VERIFICATION_ONLY', default=True, cast=bool)
ENABLE_VIDEO_UPLOADS = config('ENABLE_VIDEO_UPLOADS', default=False, cast=bool)

SITE_ID = config('SITE_ID', default=1, cast=int)


# ---------------------------------------------
# APPLICATIONS
# ---------------------------------------------
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    # cloudinary_storage MUST come before django.contrib.staticfiles
    'cloudinary_storage',
    'django.contrib.staticfiles',
    'cloudinary',
    'django.contrib.sites',      # Required by allauth
    'django.contrib.sitemaps',   # sitemap.xml
]

THIRD_PARTY_APPS = [
    'crispy_forms',
    'crispy_bootstrap5',
    'django_filters',
    'axes',               # Brute force protection
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

LOCAL_APPS = [
    'apps.core',
    'apps.accounts',
    'apps.marketplace',
    'apps.services',
    'apps.messaging',
    'apps.reviews',
    'apps.rentals',
    'apps.interactions',
    'apps.trust',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# ---------------------------------------------
# MIDDLEWARE
# Order matters -- axes must be after
# AuthenticationMiddleware
# ---------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'apps.core.middleware.SecurityHeadersMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',             # Brute force -- after auth
    'django.contrib.messages.middleware.MessageMiddleware',
    'apps.trust.middleware.TrustSafetyMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Required for django-allauth
]


# ---------------------------------------------
# AUTHENTICATION BACKENDS
# axes requires its backend to be listed
# ---------------------------------------------
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',        # Must be first
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',  # Enables allauth social login
]


# ---------------------------------------------
# URLS & WSGI
# ---------------------------------------------
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'


# ---------------------------------------------
# TEMPLATES
# ---------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.unread_messages',
                'apps.core.context_processors.support_email',
            ],
            'loaders': [
                # Project templates/ checked FIRST -- admin overrides work here
                'django.template.loaders.filesystem.Loader',
                # Then each installed app's templates/ folder
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]


# ---------------------------------------------
# PASSWORD HASHING
# Argon2 is the strongest -- winner of the
# Password Hashing Competition. Falls back to
# PBKDF2 for existing passwords automatically.
# ---------------------------------------------
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]


# ---------------------------------------------
# PASSWORD VALIDATION
# ---------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ---------------------------------------------
# SESSION SECURITY
# ---------------------------------------------
SESSION_COOKIE_HTTPONLY = True      # JS cannot access session cookie
SESSION_COOKIE_SAMESITE = 'Lax'    # Protects against CSRF via cross-site requests
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 1209600        # 2 weeks in seconds
CONCURRENT_SESSION_LIMIT = config('CONCURRENT_SESSION_LIMIT', default=5, cast=int)


# ---------------------------------------------
# CSRF SECURITY
# ---------------------------------------------
CSRF_COOKIE_HTTPONLY = False        # Must be False -- JS needs to read it for AJAX
CSRF_COOKIE_SAMESITE = 'Lax'


# ---------------------------------------------
# SECURITY HEADERS (non-HTTPS ones -- safe in dev)
# ---------------------------------------------
SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevents MIME-type sniffing attacks
SECURE_BROWSER_XSS_FILTER = True    # Enables browser XSS filter
X_FRAME_OPTIONS = 'DENY'            # Prevents clickjacking


# ---------------------------------------------
# BRUTE FORCE PROTECTION -- django-axes
# Locks account after AXES_FAILURE_LIMIT
# consecutive failed login attempts
# ---------------------------------------------
AXES_FAILURE_LIMIT = 5              # Lock after 5 failed attempts
AXES_COOLOFF_TIME = 1               # Lockout for 1 hour
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address']  # Lock by both
AXES_RESET_ON_SUCCESS = True        # Reset counter on successful login
AXES_ENABLE_ADMIN = True            # Show lockouts in Django Admin
AXES_VERBOSE = True                 # Log to console so you can see attempts
AXES_LOCKOUT_TEMPLATE = 'axes/lockout.html'  # Our custom lockout page
# Ensure axes reads IP correctly in dev (no proxy)
AXES_IPWARE_PROXY_COUNT = 0
# Record attempts even for non-existent usernames
# AXES_ONLY_USER_FAILURES = False


# ---------------------------------------------
# INTERNATIONALISATION
# ---------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True


# ---------------------------------------------
# STATIC FILES
# ---------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Django 4.2+ replaced DEFAULT_FILE_STORAGE and STATICFILES_STORAGE
# with a unified STORAGES dict. DEFAULT_FILE_STORAGE is fully removed in Django 5.
# Always configure storage here; override 'default' backend in settings that use Cloudinary/S3.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# ---------------------------------------------
# MEDIA FILES
# ---------------------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ---------------------------------------------
# DEFAULT PRIMARY KEY
# ---------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------------------------------------------
# FILE UPLOAD SECURITY
# ---------------------------------------------
# Maximum upload size enforced by Django before hitting view logic
# 55MB = 50MB video + 5MB overhead for form data
DATA_UPLOAD_MAX_MEMORY_SIZE = 55 * 1024 * 1024   # 55MB total form data
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440            # 2.5MB in-memory threshold (larger = temp disk)

# Only allow these handlers -- prevents bypass via alternative upload mechanisms
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

# ---------------------------------------------
# CSRF
# ---------------------------------------------
# Custom CSRF failure page — replaces Django's yellow debug screen
# Shown when a security token is stale (e.g. session timeout, back button)
CSRF_FAILURE_VIEW = 'apps.core.views.csrf_failure'

# ---------------------------------------------
# AUTH REDIRECTS
# ---------------------------------------------
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = 'accounts:login'


# ---------------------------------------------
# CRISPY FORMS
# ---------------------------------------------
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'


# ---------------------------------------------
# MESSAGES -> Bootstrap classes
# ---------------------------------------------
MESSAGE_TAGS = {
    messages.DEBUG:   'secondary',
    messages.INFO:    'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR:   'danger',
}


# ---------------------------------------------
# LOGGING
# Logs WARNING+ to console always.
# Logs security events (failed logins etc.)
# to a dedicated security.log file.
# Auto-creates logs/ directory if missing (e.g. fresh server deploy).
# ---------------------------------------------
import os as _os
_os.makedirs(BASE_DIR / 'logs', exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 1024 * 1024 * 5,   # 5MB per file
            'backupCount': 5,               # Keep 5 old files
            'formatter': 'verbose',
        },
        'app_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'app.log',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 3,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['console', 'security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'axes': {
            'handlers': ['console', 'security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'app_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# --- django-allauth settings ---
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_LOGOUT_REDIRECT_URL = '/accounts/login/'
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}

GOOGLE_CLIENT_ID = config('SOCIAL_AUTH_GOOGLE_CLIENT_ID', default='')
GOOGLE_CLIENT_SECRET = config('SOCIAL_AUTH_GOOGLE_CLIENT_SECRET', default='')

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    SOCIALACCOUNT_PROVIDERS['google']['APP'] = {
        'client_id': GOOGLE_CLIENT_ID,
        'secret': GOOGLE_CLIENT_SECRET,
        'key': '',
        'settings': {'hidden': True},
    }
