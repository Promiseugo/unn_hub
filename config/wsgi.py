import os
from django.core.wsgi import get_wsgi_application

# Default to production — development overrides this via $env:DJANGO_SETTINGS_MODULE
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
application = get_wsgi_application()
