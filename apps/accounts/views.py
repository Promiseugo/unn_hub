"""
accounts/views.py

Views for the accounts app.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode, urlsafe_base64_encode
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit
from django.utils.encoding import force_bytes
from .forms import RegisterForm, LoginForm, ProfileUpdateForm, UserUpdateForm
from .models import User, Profile

# Logger for security events
logger = logging.getLogger('apps.accounts')


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
            _send_verification_email(request, user)
            messages.success(request, f"Welcome to UNN Hub, {user.username}!")
            return redirect(_get_safe_next_url(request))
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
            user.save(update_fields=['is_verified'])
        messages.success(request, "Your email has been verified.")
    else:
        messages.error(request, "That verification link is invalid or has expired.")
    return redirect('accounts:login')


def profile_view(request, username):
    from apps.reviews.models import Review

    profile_user = get_object_or_404(User, username=username)
    listings = profile_user.listings.filter(
        is_active=True
    ).order_by('-created_at')[:6]
    services = profile_user.services.filter(
        is_active=True
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
    pass


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
