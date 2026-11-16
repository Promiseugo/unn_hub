"""
core/context_processors.py

Injects global context into every template automatically.
Register in settings TEMPLATES → context_processors.
"""

from django.conf import settings
from django.core.cache import cache


def unread_messages(request):
    """
    Adds unread_count to every template context.
    Shows the red badge on the Inbox navbar link.
    Cached per-user for 60 s to avoid a cross-table aggregation on every page load.
    """
    if request.user.is_authenticated:
        cache_key = f'unread_count_{request.user.pk}'
        count = cache.get(cache_key)
        if count is None:
            from apps.messaging.models import Message
            count = Message.objects.filter(
                thread__participants=request.user,
                is_read=False,
            ).exclude(sender=request.user).count()
            cache.set(cache_key, count, 60)
        return {'unread_count': count}
    return {'unread_count': 0}


def support_email(request):
    return {'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@unitrax.com')}
