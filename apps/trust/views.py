from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit

from django.conf import settings

from .forms import (
    ExternalSellerApplicationForm, OTPVerificationForm, ReportForm,
    SafetyAcknowledgementForm, StudentIDVerificationForm,
)
from .models import (
    EmailOTP, ExternalSellerApplication, Report, SafetyAcknowledgement,
    StudentIDVerification, TrustTransaction,
)
from .utils import get_client_ip, log_audit
from .scoring import update_trust_score


ALLOWED_REPORT_MODELS = {
    ('marketplace', 'listing'),
    ('services', 'serviceoffer'),
    ('rentals', 'rentallisting'),
    ('messaging', 'thread'),
    ('messaging', 'message'),
    ('accounts', 'profile'),
}

ALLOWED_TRANSACTION_MODELS = {
    ('marketplace', 'listing'),
    ('services', 'serviceoffer'),
    ('rentals', 'rentallisting'),
}


def _safe_next(request, default='landing'):
    value = request.POST.get('next') or request.GET.get('next')
    return value if value and value.startswith('/') and not value.startswith('//') else reverse(default)


def _send_otp(request, user):
    otp = EmailOTP.issue(user, request_ip=get_client_ip(request), ttl_minutes=getattr(settings, 'EMAIL_OTP_TTL_MINUTES', 10))
    send_mail(
        'Your UniTraX verification code',
        f'Your UniTraX verification code is {otp.plain_code}. It expires in 10 minutes.\n\nIf you did not request this, ignore this email.',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    return otp


def _target_owner(target):
    return (
        getattr(target, 'seller', None)
        or getattr(target, 'provider', None)
        or getattr(target, 'landlord', None)
        or getattr(target, 'sender', None)
        or getattr(target, 'user', None)
    )


def _target_redirect(target):
    return getattr(target, 'get_absolute_url', lambda: reverse('landing'))()


def _get_transaction_target_or_redirect(request, app_label, model_name, object_id):
    if (app_label, model_name) not in ALLOWED_TRANSACTION_MODELS:
        messages.error(request, "Transactions are not available for this content.")
        return None, None
    content_type = get_object_or_404(ContentType, app_label=app_label, model=model_name)
    try:
        target = content_type.get_object_for_this_type(pk=object_id)
    except Exception:
        messages.error(request, "The content you selected doesn't exist.")
        return None, None
    return content_type, target


@login_required
@require_http_methods(['GET', 'POST'])
@ratelimit(key='user_or_ip', rate='5/m', method='POST', block=True)
def verify_email_otp(request):
    if request.user.is_verified:
        return redirect(_safe_next(request))

    if not EmailOTP.objects.filter(user=request.user, consumed_at__isnull=True, expires_at__gt=timezone.now()).exists():
        try:
            _send_otp(request, request.user)
            messages.info(request, 'We sent a 6-digit verification code to your email.')
        except Exception:
            messages.error(request, 'We could not send a verification code right now. Please try again.')

    form = OTPVerificationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        code = form.cleaned_data['code']
        otp = EmailOTP.objects.filter(
            user=request.user,
            purpose=EmailOTP.PURPOSE_VERIFY_EMAIL,
            consumed_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).order_by('-created_at').first()
        if otp and otp.check_code(code):
            otp.consumed_at = timezone.now()
            otp.save(update_fields=['consumed_at'])
            request.user.is_verified = True
            if getattr(request.user, 'trust_tier', 'unverified') == 'unverified':
                request.user.trust_tier = 'verified_student'
                request.user.save(update_fields=['is_verified', 'trust_tier'])
            else:
                request.user.save(update_fields=['is_verified'])
            log_audit(request, 'email_verified_otp', request.user)
            update_trust_score(request.user, reason='email_verified', actor=request.user, source=request.user)
            messages.success(request, 'Your university email has been verified.')
            return redirect(_safe_next(request))
        messages.error(request, 'Invalid or expired verification code.')

    return render(request, 'trust/verify_email.html', {'form': form, 'next_url': _safe_next(request)})


@login_required
@ratelimit(key='user_or_ip', rate='3/m', method='POST', block=True)
def resend_email_otp(request):
    try:
        _send_otp(request, request.user)
        messages.success(request, 'A new verification code has been sent.')
    except Exception:
        messages.error(request, 'We could not send a code right now.')
    return redirect(f"{reverse('trust:verify-email')}?next={_safe_next(request)}")


@login_required
@require_http_methods(['GET', 'POST'])
def safety_acknowledgement(request):
    required_version = getattr(settings, 'SAFETY_ACK_VERSION', '2026-05')
    existing = SafetyAcknowledgement.objects.filter(user=request.user, version=required_version).first()
    if existing:
        return redirect(_safe_next(request))
    form = SafetyAcknowledgementForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        SafetyAcknowledgement.objects.update_or_create(
            user=request.user,
            defaults={
                'version': required_version,
                'acknowledged_at': timezone.now(),
                'ip_address': get_client_ip(request) or None,
            },
        )
        log_audit(request, 'safety_acknowledged', request.user)
        messages.success(request, 'Thanks. Stay safe and use public campus meetup spots.')
        return redirect(_safe_next(request))
    return render(request, 'trust/safety.html', {'form': form, 'next_url': _safe_next(request)})


@login_required
@require_http_methods(['GET', 'POST'])
def student_id_verification(request):
    verification = StudentIDVerification.objects.filter(user=request.user).first()
    form = StudentIDVerificationForm(request.POST or None, request.FILES or None, instance=verification)
    if request.method == 'POST' and form.is_valid():
        verification = form.save(commit=False)
        verification.user = request.user
        verification.status = StudentIDVerification.STATUS_PENDING
        verification.save()
        log_audit(request, 'student_id_submitted', verification)
        messages.success(request, 'Student ID submitted for review.')
        return redirect('accounts:profile', username=request.user.username)
    return render(request, 'trust/student_id.html', {'form': form, 'verification': verification})


@login_required
@require_http_methods(['GET', 'POST'])
@ratelimit(key='user_or_ip', rate='3/h', method='POST', block=True)
def external_seller_application(request):
    application = ExternalSellerApplication.objects.filter(user=request.user).first()
    if application and application.status == ExternalSellerApplication.STATUS_APPROVED:
        messages.info(request, 'Your external seller application is already approved.')
        return redirect('accounts:profile', username=request.user.username)

    form = ExternalSellerApplicationForm(request.POST or None, request.FILES or None, instance=application)
    if request.method == 'POST' and form.is_valid():
        application = form.save(commit=False)
        application.user = request.user
        application.status = ExternalSellerApplication.STATUS_PENDING
        application.reviewed_at = None
        application.reviewer = None
        application.review_note = ''
        application.save()
        log_audit(request, 'external_seller_application_submitted', application)
        messages.success(request, 'Application submitted. A moderator will review it manually.')
        return redirect('accounts:profile', username=request.user.username)

    return render(request, 'trust/external_seller.html', {'form': form, 'application': application})


@login_required
@require_http_methods(['GET', 'POST'])
@ratelimit(key='user_or_ip', rate='5/m', method='POST', block=True)
def report_content(request, app_label, model_name, object_id):
    if (app_label, model_name) not in ALLOWED_REPORT_MODELS:
        messages.error(request, "This content cannot be reported.")
        return redirect('landing')
    content_type = get_object_or_404(ContentType, app_label=app_label, model=model_name)
    try:
        target = content_type.get_object_for_this_type(pk=object_id)
    except Exception:
        messages.error(request, "The content you tried to report doesn't exist.")
        return redirect('landing')
    if app_label == 'messaging' and model_name == 'thread':
        if not target.participants.filter(pk=request.user.pk).exists():
            messages.error(request, "You can't report a chat you are not part of.")
            return redirect('landing')
        reported_user = target.get_other_participant(request.user)
    else:
        reported_user = _target_owner(target)
    if reported_user == request.user:
        messages.error(request, "You can't report your own content.")
        return redirect(getattr(target, 'get_absolute_url', lambda: 'landing')())
    form = ReportForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        report = form.save(commit=False)
        report.reporter = request.user
        report.reported_user = reported_user
        report.content_type = content_type
        report.object_id = str(object_id)
        try:
            report.save()
        except IntegrityError:
            messages.warning(request, "You've already submitted an open report for this content.")
            return redirect(getattr(target, 'get_absolute_url', lambda: 'landing')())
        log_audit(request, 'report_submitted', report, metadata={'reason': report.reason})
        messages.success(request, 'Report submitted. A moderator will review it.')
        return redirect(getattr(target, 'get_absolute_url', lambda: 'landing')())
    return render(request, 'trust/report.html', {'form': form, 'target': target})


@login_required
@require_http_methods(['POST'])
@ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True)
def request_transaction(request, app_label, model_name, object_id):
    content_type, target = _get_transaction_target_or_redirect(request, app_label, model_name, object_id)
    if target is None:
        return redirect('landing')

    seller = _target_owner(target)
    if seller is None:
        messages.error(request, "We couldn't identify the seller for this item.")
        return redirect(_target_redirect(target))
    if seller == request.user:
        messages.error(request, "You can't request a transaction with yourself.")
        return redirect(_target_redirect(target))

    existing = TrustTransaction.objects.filter(
        buyer=request.user,
        seller=seller,
        content_type=content_type,
        object_id=str(object_id),
    ).exclude(status__in=[
        TrustTransaction.STATUS_REVERSED,
        TrustTransaction.STATUS_CANCELLED,
    ]).order_by('-created_at').first()

    if existing:
        messages.info(request, "A transaction confirmation is already open for this item.")
        return redirect(_target_redirect(target))

    try:
        transaction = TrustTransaction.objects.create(
            buyer=request.user,
            seller=seller,
            content_type=content_type,
            object_id=str(object_id),
        )
    except IntegrityError:
        messages.info(request, "A transaction confirmation is already open for this item.")
        return redirect(_target_redirect(target))
    log_audit(request, 'trust_transaction_requested', transaction)
    messages.success(request, "Transaction confirmation requested. Both sides need to confirm before reviews unlock.")
    return redirect(_target_redirect(target))


@login_required
@require_http_methods(['POST'])
def confirm_transaction(request, pk):
    transaction = get_object_or_404(
        TrustTransaction.objects.select_related('buyer', 'seller', 'content_type'),
        pk=pk,
    )
    if request.user not in (transaction.buyer, transaction.seller):
        messages.error(request, "You can't confirm this transaction.")
        return redirect('landing')
    if transaction.status != TrustTransaction.STATUS_PENDING:
        messages.info(request, "This transaction is no longer pending.")
        return redirect(_target_redirect(transaction.content_object) if transaction.content_object else 'landing')

    changed = transaction.confirm_for(request.user)
    if changed:
        transaction.save(update_fields=[
            'buyer_confirmed_at',
            'seller_confirmed_at',
            'status',
            'completed_at',
            'confirmed_by',
            'updated_at',
        ])
        log_audit(request, 'trust_transaction_confirmed', transaction)
        if transaction.status == TrustTransaction.STATUS_COMPLETED:
            update_trust_score(
                transaction.seller,
                reason='trust_transaction_completed',
                actor=request.user,
                source=transaction,
            )
            messages.success(request, "Transaction completed. Reviews are now unlocked.")
        else:
            messages.success(request, "Confirmation saved. Waiting for the other side.")
    else:
        messages.info(request, "You've already confirmed this transaction.")
    return redirect(_target_redirect(transaction.content_object) if transaction.content_object else 'landing')


@login_required
@require_http_methods(['POST'])
def dispute_transaction(request, pk):
    transaction = get_object_or_404(
        TrustTransaction.objects.select_related('buyer', 'seller', 'content_type'),
        pk=pk,
    )
    if request.user not in (transaction.buyer, transaction.seller):
        messages.error(request, "You can't dispute this transaction.")
        return redirect('landing')

    was_completed = transaction.status == TrustTransaction.STATUS_COMPLETED
    changed = transaction.dispute(request.user)
    if changed:
        transaction.save(update_fields=['status', 'disputed_at', 'disputed_by', 'updated_at'])
        log_audit(request, 'trust_transaction_disputed', transaction)
        if was_completed:
            update_trust_score(
                transaction.seller,
                reason='trust_transaction_disputed',
                actor=request.user,
                source=transaction,
            )
        messages.warning(request, "Transaction disputed. A moderator can review it before it counts toward trust.")
    else:
        messages.info(request, "This transaction can't be disputed.")
    return redirect(_target_redirect(transaction.content_object) if transaction.content_object else 'landing')
