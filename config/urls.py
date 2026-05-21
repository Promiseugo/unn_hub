from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core.views import landing


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /messages/",
        "Allow: /",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


admin_url = getattr(settings, 'ADMIN_URL', 'admin/')

urlpatterns = [
    path('robots.txt', robots_txt, name='robots-txt'),
    path(admin_url, admin.site.urls),

    path('', landing, name='landing'),
    path('', include('apps.core.urls')),
    path('', include('apps.marketplace.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('services/', include('apps.services.urls')),
    path('messages/', include('apps.messaging.urls')),
    path('reviews/', include('apps.reviews.urls')),
    path('accommodation/', include('apps.rentals.urls')),
    path('interactions/', include('apps.interactions.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    try:
        import debug_toolbar
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass
