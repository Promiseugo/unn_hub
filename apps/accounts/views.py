"""
accounts/views.py

Views for the accounts app.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.contrib.sessions.models import Session
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode, urlsafe_base64_encode
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit
from .forms import RegisterForm, LoginForm, ProfileUpdateForm, UserUpdateForm
from .models import Profile
from apps.trust.models import EmailOTP, UserSessionSecurityEvent
from apps.trust.utils import get_client_ip, get_user_agent, log_audit

# Logger for security events
logger = logging.getLogger('apps.accounts')
User = get_user_model()


def _build_site_context(request):
    protocol = 'https' if request.is_secure() else 'http'
    return {
        'site_name': getattr(settings, 'SITE_NAME', 'UniTraX'),
        'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@unitrax.com'),
        'domain': request.get_host(),
        'protocol': protocol,
    }


def _get_safe_next_url(request, default='marketplace:listing-list'):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return default


def _safe_send_user_email(*, request, user, subject_template, body_template, html_template=None, extra_context=None):
    if not getattr(user, 'email', None):
        return
    context = {
        'user': user,
        **_build_site_context(request),
        **(extra_context or {}),
    }
    try:
        subject = render_to_string(subject_template, context).strip().replace('\n', '')
        body = render_to_string(body_template, context)
        email = EmailMultiAlternatives(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email])
        if html_template:
            html_body = render_to_string(html_template, context)
            email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=False)
    except Exception:
        logger.exception("Failed sending transactional email", extra={'user_id': getattr(user, 'pk', None)})


def _send_verification_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    _safe_send_user_email(
        request=request,
        user=user,
        subject_template='accounts/email_verification_subject.txt',
        body_template='accounts/email_verification.txt',
        html_template='accounts/email_verification.html',
        extra_context={'uid': uid, 'token': token},
    )


def _send_verification_otp(request, user):
    otp = EmailOTP.issue(user, request_ip=get_client_ip(request), ttl_minutes=getattr(settings, 'EMAIL_OTP_TTL_MINUTES', 10))
    _safe_send_user_email(
        request=request,
        user=user,
        subject_template='accounts/email_verification_subject.txt',
        body_template='accounts/email_verification.txt',
        html_template='accounts/email_verification.html',
        extra_context={'otp_code': otp.plain_code},
    )


def _active_sessions_for_user(user):
    active = []
    for session in Session.objects.filter(expire_date__gte=timezone.now()):
        data = session.get_decoded()
        if str(data.get('_auth_user_id')) == str(user.pk):
            active.append(session)
    return active


def _record_login_security(request, user):
    ip_address = get_client_ip(request) or None
    user_agent = get_user_agent(request)
    session_key = request.session.session_key or ''

    seen_ip = UserSessionSecurityEvent.objects.filter(
        user=user,
        ip_address=ip_address,
    ).exists() if ip_address else True
    seen_agent = UserSessionSecurityEvent.objects.filter(
        user=user,
        user_agent=user_agent,
    ).exists() if user_agent else True

    event_type = UserSessionSecurityEvent.EVENT_LOGIN
    if not seen_agent:
        event_type = UserSessionSecurityEvent.EVENT_NEW_DEVICE
    elif not seen_ip:
        event_type = UserSessionSecurityEvent.EVENT_NEW_IP

    UserSessionSecurityEvent.objects.create(
        user=user,
        event_type=event_type,
        session_key=session_key,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    limit = getattr(settings, 'CONCURRENT_SESSION_LIMIT', 5)
    if limit and limit > 0:
        sessions = sorted(_active_sessions_for_user(user), key=lambda item: item.expire_date, reverse=True)
        for stale_session in sessions[limit:]:
            stale_session.delete()
        if len(sessions) > limit:
            UserSessionSecurityEvent.objects.create(
                user=user,
                event_type=UserSessionSecurityEvent.EVENT_CONCURRENT_LIMIT,
                session_key=session_key,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={'removed_sessions': len(sessions) - limit},
            )


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def register_view(request):
    if request.user.is_authenticated:
        return redirect(_get_safe_next_url(request))

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user,
                  backend='django.contrib.auth.backends.ModelBackend')
            logger.info(f"New user registered: {user.email}")
            _safe_send_user_email(
                request=request,
                user=user,
                subject_template='accounts/welcome_email_subject.txt',
                body_template='accounts/welcome_email.txt',
                html_template='accounts/welcome_email.html',
            )
            _send_verification_otp(request, user)
            log_audit(request, 'user_registered', user)
            messages.success(request, f"Welcome to UNN Hub, {user.username}!")
            return redirect('trust:verify-email')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {
        'form': form,
        'next_url': _get_safe_next_url(request, default=''),
    })


@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def login_view(request):
    if request.user.is_authenticated:
        return redirect(_get_safe_next_url(request))

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            _record_login_security(request, user)
            if getattr(settings, 'ACCOUNT_LOGIN_ALERT_EMAILS', False):
                _safe_send_user_email(
                    request=request,
                    user=user,
                    subject_template='accounts/login_alert_subject.txt',
                    body_template='accounts/login_alert.txt',
                    html_template='accounts/login_alert.html',
                    extra_context={
                        'ip_address': request.META.get('REMOTE_ADDR', 'unknown'),
                        'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown'),
                    },
                )
            return redirect(_get_safe_next_url(request))
        else:
            # Log failed login attempts for monitoring
            attempted_email = request.POST.get('username', '')
            logger.warning(
                f"Failed login attempt for email: {attempted_email} "
                f"from IP: {request.META.get('REMOTE_ADDR', 'unknown')}"
            )
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {
        'form': form,
        'next_url': _get_safe_next_url(request, default=''),
    })


@login_required
@require_http_methods(["POST"])
def logout_view(request):
    logger.info(f"User logged out: {request.user.email}")
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('accounts:login')


def verify_email_view(request, uidb64, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if not user.is_verified:
            user.is_verified = True
            if getattr(user, 'trust_tier', 'unverified') == 'unverified':
                user.trust_tier = 'verified_student'
                user.save(update_fields=['is_verified', 'trust_tier'])
            else:
                user.save(update_fields=['is_verified'])
            from apps.trust.scoring import update_trust_score
            update_trust_score(user, reason='email_verified', actor=user, source=user)
        messages.success(request, "Your email has been verified.")
    else:
        messages.error(request, "That verification link is invalid or has expired.")
    return redirect('accounts:login')


def profile_view(request, username):
    from apps.reviews.models import Review
    from apps.trust.scoring import update_trust_score

    profile_user = get_object_or_404(User, username=username)
    update_trust_score(profile_user)
    listings = profile_user.listings.filter(
        is_active=True,
        is_sold=False,
        expires_at__gt=timezone.now(),
        approval_status='approved',
        deleted_at__isnull=True,
    ).order_by('-created_at')[:6]
    services = profile_user.services.filter(
        is_active=True,
        approval_status='approved',
        deleted_at__isnull=True,
    ).order_by('-created_at')[:6]

    ct = ContentType.objects.get_for_model(Profile)
    reviews = Review.objects.filter(
        content_type=ct,
        object_id=str(profile_user.profile.pk),
    ).select_related('reviewer').order_by('-created_at')[:5]

    return render(request, 'accounts/profile.html', {
        'profile_user': profile_user,
        'listings': listings,
        'services': services,
        'reviews': reviews,
    })


@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=request.user.profile
        )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('accounts:profile', username=request.user.username)
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'accounts/profile_edit.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


class PasswordChangeNotifyView(auth_views.PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:password_change_done')

    def form_valid(self, form):
        response = super().form_valid(form)
        _safe_send_user_email(
            request=self.request,
            user=self.request.user,
            subject_template='accounts/password_changed_subject.txt',
            body_template='accounts/password_changed.txt',
            html_template='accounts/password_changed.html',
        )
        return response


class PasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    template_name = 'accounts/password_change_done.html'


@method_decorator(ratelimit(key='ip', rate='5/h', method='POST', block=True), name='dispatch')
class PasswordResetNotifyView(auth_views.PasswordResetView):
    """
    Password reset request endpoint with project-specific defaults.
    URL-level kwargs can still override these values where needed.
    """
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.txt'
    html_email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')


class PasswordResetConfirmNotifyView(auth_views.PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = getattr(self, 'user', None)
        if user is not None:
            _safe_send_user_email(
                request=self.request,
                user=user,
                subject_template='accounts/password_changed_subject.txt',
                body_template='accounts/password_changed.txt',
                html_template='accounts/password_changed.html',
                extra_context={'reason': 'password_reset'},
            )
        return response
