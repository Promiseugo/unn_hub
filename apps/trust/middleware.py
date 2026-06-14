from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

from .models import SafetyAcknowledgement
from .utils import user_is_restricted


class TrustSafetyMiddleware:
    """
    Enforces verification, active restrictions, and safety acknowledgement before
    high-risk marketplace actions. Public browsing remains open.
    """
    EXEMPT_PREFIXES = (
        '/accounts/login/',
        '/accounts/logout/',
        '/accounts/register/',
        '/accounts/signup/',
        '/accounts/verify-email/',
        '/trust/verify-email/',
        '/trust/safety/',
        '/admin/',
        '/static/',
        '/media/',
        '/robots.txt',
    )
    PROTECTED_PREFIXES = (
        '/listings/create/',
        '/services/create/',
        '/accommodation/create/',
        '/messages/',
        '/interactions/',
        '/reviews/add/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        path = request.path
        admin_prefix = '/' + getattr(settings, 'ADMIN_URL', 'admin/').strip('/ ') + '/'
        exempt = any(path.startswith(prefix) for prefix in self.EXEMPT_PREFIXES) or path.startswith(admin_prefix)
        if user and user.is_authenticated and not exempt:
            if user_is_restricted(user):
                messages.error(request, 'Your account is currently restricted. Contact support if this is a mistake.')
                return redirect('landing')

            if path.startswith(self.PROTECTED_PREFIXES):
                if getattr(settings, 'REQUIRE_UNIVERSITY_EMAIL_VERIFICATION', True) and not user.is_verified:
                    messages.warning(request, 'Please verify your email address before using marketplace features.')
                    return redirect(f"{reverse('trust:verify-email')}?next={path}")

                seller_paths = ('/listings/create/', '/services/create/', '/accommodation/create/')
                if path.startswith(seller_paths):
                    tier = getattr(user, 'trust_tier', 'unverified')
                    campus_tiers = {'verified_student', 'verified_staff'}
                    external_tiers = {'verified_external', 'verified_business'}
                    if tier in external_tiers:
                        if not getattr(user, 'external_seller_approved', False):
                            messages.warning(request, 'External sellers must be approved by moderation before posting.')
                            return redirect('trust:external-seller')
                    elif tier not in campus_tiers:
                        messages.warning(request, 'External sellers must be approved by moderation before posting.')
                        return redirect('trust:external-seller')

                required_safety_version = getattr(settings, 'SAFETY_ACK_VERSION', '2026-05')
                if not SafetyAcknowledgement.objects.filter(user=user, version=required_safety_version).exists():
                    messages.info(request, 'Please review the campus safety guidelines before continuing.')
                    return redirect(f"{reverse('trust:safety')}?next={path}")

        return self.get_response(request)
