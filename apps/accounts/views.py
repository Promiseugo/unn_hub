import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods
from .forms import RegisterForm, LoginForm, ProfileUpdateForm, UserUpdateForm
from .models import User, Profile

# Logger for security events
logger = logging.getLogger('apps.accounts')


def _build_site_context(request):
    protocol = 'https' if request.is_secure() else 'http'
    return {
        'site_name': getattr(settings, 'SITE_NAME', 'UniTraX'),
        'domain': request.get_host(),
        'protocol': protocol,
    }


def _safe_send_user_email(*, request, user, subject_template, body_template, extra_context=None):
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
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
    except Exception:
        logger.exception("Failed sending transactional email", extra={'user_id': getattr(user, 'pk', None)})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('marketplace:listing-list')

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
            )
            messages.success(request, f"Welcome to UNN Hub, {user.username}!")
            return redirect('marketplace:listing-list')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('marketplace:listing-list')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user,
                  backend='django.contrib.auth.backends.ModelBackend')
            next_url = request.GET.get('next', 'marketplace:listing-list')
            return redirect(next_url)
        else:
            # Log failed login attempts for monitoring
            attempted_email = request.POST.get('username', '')
            logger.warning(
                f"Failed login attempt for email: {attempted_email} "
                f"from IP: {request.META.get('REMOTE_ADDR', 'unknown')}"
            )
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
@require_http_methods(["POST"])
def logout_view(request):
    logger.info(f"User logged out: {request.user.email}")
    logout(request)
    messages.info(request, "You have been logged out.")
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
        )
        return response


class PasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    template_name = 'accounts/password_change_done.html'


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
                extra_context={'reason': 'password_reset'},
            )
        return response
