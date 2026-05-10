"""
core/context_processors.py

Injects global context into every template automatically.
Register in settings TEMPLATES → context_processors.
"""

from django.conf import settings


def unread_messages(request):
    """
    Adds unread_count to every template context.
    Shows the red badge on the Inbox navbar link.
    """
    if request.user.is_authenticated:
        from apps.messaging.models import Message
        count = Message.objects.filter(
            thread__participants=request.user,
            is_read=False,
        ).exclude(sender=request.user).count()
        return {'unread_count': count}
    return {'unread_count': 0}


def support_email(request):
    return {'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@unitrax.com')}
