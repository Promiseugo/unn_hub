import re
from decimal import Decimal

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from .models import AuditLog, Report, SuspiciousActivity, UserRestriction


CONTACT_PATTERN = re.compile(
    r'(\+?\d[\d\s().-]{7,}\d)|([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})',
    re.IGNORECASE,
)

PROHIBITED_KEYWORDS = {
    'weapon', 'gun', 'knife', 'pistol', 'rifle', 'ammunition',
    'drug', 'weed', 'cannabis', 'tramadol', 'codeine', 'exam leak',
    'stolen', 'counterfeit', 'fake id', 'id card forging',
}

DISPOSABLE_EMAIL_DOMAINS = {
    'mailinator.com', '10minutemail.com', 'tempmail.com', 'guerrillamail.com',
    'yopmail.com', 'trashmail.com', 'sharklasers.com', 'getnada.com',
}


def get_client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def get_user_agent(request):
    return request.META.get('HTTP_USER_AGENT', '')[:1000]


def official_email_domains():
    return {
        domain.strip().lower()
        for domain in getattr(settings, 'OFFICIAL_UNIVERSITY_EMAIL_DOMAINS', ['unn.edu.ng', 'student.unn.edu.ng'])
        if domain.strip()
    }


def validate_university_email(email):
    """
    Validates that an email is not from a known disposable provider.
    Any real email (Gmail, Yahoo, school, etc.) is accepted.
    Only throwaway domains are blocked.
    Use is_campus_email() to check if an email is a university address.
    """
    domain = email.rsplit('@', 1)[-1].lower() if '@' in email else ''
    if domain in DISPOSABLE_EMAIL_DOMAINS:
        return False, 'Disposable email addresses are not allowed.'
    return True, ''


def is_campus_email(email):
    """Returns True if email belongs to a configured university domain."""
    domain = email.rsplit('@', 1)[-1].lower() if '@' in email else ''
    return domain in official_email_domains()


def redact_contact_info(text):
    return CONTACT_PATTERN.sub('[contact hidden]', text or '')


def contains_contact_info(text):
    return bool(CONTACT_PATTERN.search(text or ''))


def scan_text_for_policy(text):
    lower = (text or '').lower()
    hits = sorted(keyword for keyword in PROHIBITED_KEYWORDS if keyword in lower)
    return hits


def detect_listing_risk(listing):
    reasons = []
    text = f'{getattr(listing, "title", "")} {getattr(listing, "description", "")}'
    prohibited = scan_text_for_policy(text)
    if prohibited:
        reasons.append(f"Policy keywords: {', '.join(prohibited[:5])}")
    if getattr(listing, 'price', None) and listing.price >= Decimal('5000000'):
        reasons.append('Unusually high price for campus marketplace')
    if getattr(listing, 'price', None) and listing.price <= Decimal('100'):
        reasons.append('Unrealistically low price')
    if contains_contact_info(text):
        reasons.append('Contact information in listing text')
    seller = (
        getattr(listing, 'seller', None)
        or getattr(listing, 'provider', None)
        or getattr(listing, 'landlord', None)
    )
    if seller:
        reasons.extend(detect_seller_velocity_risk(seller))
        reasons.extend(detect_duplicate_content_risk(listing, seller))
    return reasons


def detect_duplicate_content_risk(listing, seller):
    from datetime import timedelta

    title = (getattr(listing, 'title', '') or '').strip()
    if len(title) < 8:
        return []
    model = type(listing)
    owner_filter = {}
    if hasattr(listing, 'seller_id') or hasattr(listing, 'seller'):
        owner_filter['seller'] = seller
    elif hasattr(listing, 'provider_id') or hasattr(listing, 'provider'):
        owner_filter['provider'] = seller
    elif hasattr(listing, 'landlord_id') or hasattr(listing, 'landlord'):
        owner_filter['landlord'] = seller
    if not owner_filter:
        return []
    qs = model.objects.filter(
        title__iexact=title,
        created_at__gte=timezone.now() - timedelta(days=30),
        **owner_filter,
    )
    if getattr(listing, 'pk', None):
        qs = qs.exclude(pk=listing.pk)
    if qs.exists():
        return ['Duplicate or rapid re-listing pattern']
    return []


def detect_seller_velocity_risk(user):
    from datetime import timedelta

    from apps.marketplace.models import Listing
    from apps.rentals.models import RentalListing
    from apps.services.models import ServiceOffer

    since = timezone.now() - timedelta(hours=24)
    count = (
        Listing.objects.filter(seller=user, created_at__gte=since).count()
        + ServiceOffer.objects.filter(provider=user, created_at__gte=since).count()
        + RentalListing.objects.filter(landlord=user, created_at__gte=since).count()
    )
    if count >= 10:
        return ['High-volume posting pattern in the last 24 hours']
    return []


def user_is_restricted(user):
    if not user.is_authenticated:
        return False
    if getattr(user, 'is_suspended', False):
        return True
    return UserRestriction.objects.filter(user=user, is_active=True).filter(
        models_q_current_restriction()
    ).exists()


def models_q_current_restriction():
    from django.db.models import Q
    return Q(ends_at__isnull=True) | Q(ends_at__gt=timezone.now())


def log_audit(request, action, obj=None, metadata=None):
    content_type = None
    object_id = ''
    if obj is not None:
        content_type = ContentType.objects.get_for_model(obj)
        object_id = str(obj.pk)
    return AuditLog.objects.create(
        actor=request.user if getattr(request, 'user', None) and request.user.is_authenticated else None,
        action=action,
        ip_address=get_client_ip(request) or None,
        user_agent=get_user_agent(request),
        content_type=content_type,
        object_id=object_id,
        metadata=metadata or {},
    )


def log_suspicious(request, activity_type, description, *, severity='low', user=None, metadata=None):
    return SuspiciousActivity.objects.create(
        user=user or (request.user if getattr(request, 'user', None) and request.user.is_authenticated else None),
        activity_type=activity_type,
        severity=severity,
        ip_address=get_client_ip(request) or None,
        user_agent=get_user_agent(request),
        description=description,
        metadata=metadata or {},
    )


def report_count_for_user(user):
    return Report.objects.filter(
        reported_user=user,
        status=Report.STATUS_RESOLVED,
        is_actionable=True,
    ).count()
