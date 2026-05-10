from django.shortcuts import render, redirect
from django.db.models import Count


def landing(request):
    """Homepage."""
    if request.user.is_authenticated:
        return render(request, 'core/landing.html', {})

    try:
        from apps.marketplace.models import Listing
        from apps.services.models import ServiceOffer
        from apps.rentals.models import RentalListing
        from apps.accounts.models import User

        context = {
            'listing_count': Listing.objects.filter(is_active=True).count(),
            'service_count': ServiceOffer.objects.filter(is_active=True).count(),
            'rental_count':  RentalListing.objects.filter(is_active=True).count(),
            'user_count':    User.objects.filter(is_active=True).count(),
        }
    except Exception:
        context = {}

    return render(request, 'core/landing.html', context)


def csrf_failure(request, reason=''):
    return render(request, 'core/csrf_failure.html', {'reason': reason}, status=403)


def privacy_policy(request):
    return render(request, 'core/privacy_policy.html')


def terms_of_service(request):
    return render(request, 'core/terms_of_service.html')
