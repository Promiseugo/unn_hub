from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.db.models import Count


def landing(request):
    """Homepage."""
    if request.user.is_authenticated:
        return render(request, 'core/landing.html', {})

    from django.core.cache import cache
    context = cache.get('landing_stats')
    if context is None:
        try:
            from apps.marketplace.models import Listing
            from apps.services.models import ServiceOffer
            from apps.rentals.models import RentalListing
            User = get_user_model()

            context = {
                'listing_count': Listing.objects.filter(is_active=True, approval_status='approved', deleted_at__isnull=True).count(),
                'service_count': ServiceOffer.objects.filter(is_active=True, approval_status='approved', deleted_at__isnull=True).count(),
                'rental_count':  RentalListing.objects.filter(is_active=True, approval_status='approved', deleted_at__isnull=True).count(),
                'user_count':    User.objects.filter(is_active=True).count(),
            }
            cache.set('landing_stats', context, 300)  # Cache 5 minutes
        except Exception:
            context = {}

    return render(request, 'core/landing.html', context)


def csrf_failure(request, reason=''):
    return render(request, 'core/csrf_failure.html', {'reason': reason}, status=403)


def privacy_policy(request):
    return render(request, 'core/privacy_policy.html')


def terms_of_service(request):
    return render(request, 'core/terms_of_service.html')
