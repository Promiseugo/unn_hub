from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
from .models import Review
from .forms import ReviewForm


ALLOWED_REVIEW_MODELS = {
    ('marketplace', 'listing'),
    ('services', 'serviceoffer'),
    ('rentals', 'rentallisting'),
    ('accounts', 'profile'),
}


@login_required
@require_POST
@ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True)
def add_review(request, app_label, model_name, object_id):
    """
    Generic review view — handles any reviewable object.
    Only accepts POST. Redirects back to the object on GET.

    URL pattern:
      /reviews/add/marketplace/listing/<uuid>/
      /reviews/add/services/serviceoffer/<uuid>/
      /reviews/add/accounts/profile/<int>/
    """
    if (app_label, model_name) not in ALLOWED_REVIEW_MODELS:
        messages.error(request, "This content cannot be reviewed.")
        return redirect('marketplace:listing-list')

    ct = get_object_or_404(ContentType, app_label=app_label, model=model_name)

    try:
        target_obj = ct.get_object_for_this_type(pk=object_id)
    except Exception:
        messages.error(request, "The item you tried to review doesn't exist.")
        return redirect('marketplace:listing-list')

    # Build the redirect URL — every reviewable object has get_absolute_url()
    # Profile doesn't, so fall back to the profile page
    if hasattr(target_obj, 'get_absolute_url'):
        redirect_url = target_obj.get_absolute_url()
    else:
        # It's a Profile — redirect to the user's profile page
        redirect_url = f"/accounts/profile/{target_obj.user.username}/"

    # Block self-reviews
    owner = (
        getattr(target_obj, 'seller', None)
        or getattr(target_obj, 'provider', None)
        or getattr(target_obj, 'user', None)  # Profile
    )
    if owner == request.user:
        messages.error(request, "You can't review your own content.")
        return redirect(redirect_url)

    # Block duplicate reviews
    if Review.objects.filter(
        reviewer=request.user,
        content_type=ct,
        object_id=str(object_id),
    ).exists():
        messages.warning(request, "You've already reviewed this.")
        return redirect(redirect_url)

    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.reviewer = request.user
        review.content_type = ct
        review.object_id = str(object_id)
        review.save()
        messages.success(request, "Review submitted — thank you!")
    else:
        messages.error(request, "Please select a rating before submitting.")

    return redirect(redirect_url)
