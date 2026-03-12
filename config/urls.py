"""
Root URL configuration for UNN Exchange & Services Hub.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # App routes
    path('', include('apps.marketplace.urls', namespace='marketplace')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('services/', include('apps.services.urls', namespace='services')),
    path('messages/', include('apps.messaging.urls', namespace='messaging')),
    path('reviews/', include('apps.reviews.urls', namespace='reviews')),
]

# ─────────────────────────────────────────────
# Debug Toolbar (development only)
# ─────────────────────────────────────────────
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

    # Serve media files locally during development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
