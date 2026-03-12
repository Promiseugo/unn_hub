from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from .models import Review
from .forms import ReviewForm


@login_required
def add_review(request, app_label, model_name, object_id):
    """
    Generic view — add a review to any object.
    URL: /reviews/add/<app_label>/<model_name>/<object_id>/
    """
    ct = get_object_or_404(ContentType, app_label=app_label, model=model_name)
    target_obj = ct.get_object_for_this_type(pk=object_id)

    # Prevent self-review
    owner_field = getattr(target_obj, 'seller', None) or getattr(target_obj, 'provider', None)
    if owner_field == request.user:
        messages.error(request, "You can't review your own listing.")
        return redirect(target_obj.get_absolute_url())

    # Prevent duplicate review
    if Review.objects.filter(
        reviewer=request.user, content_type=ct, object_id=str(object_id)
    ).exists():
        messages.warning(request, "You've already reviewed this.")
        return redirect(target_obj.get_absolute_url())

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = request.user
            review.content_type = ct
            review.object_id = str(object_id)
            review.save()
            messages.success(request, "Review submitted!")

    # Always redirect back to whatever was reviewed
    return redirect(target_obj.get_absolute_url())
