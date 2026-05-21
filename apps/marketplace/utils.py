from django.utils import timezone

from .models import Listing


def deactivate_expired_listings():
    """
    Hide marketplace listings whose 30-day window has elapsed.
    Returns the number of rows updated.
    """
    return Listing.objects.filter(
        is_active=True,
        is_sold=False,
        expires_at__lte=timezone.now(),
    ).update(is_active=False)
