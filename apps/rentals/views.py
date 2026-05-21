from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.contrib.contenttypes.models import ContentType
from .models import RentalListing, RentalImage, RentalInquiry
from .forms import RentalListingForm, RentalInquiryForm, MultiImageValidator, VideoValidator

try:
    from apps.core.upload_utils import secure_video_save, compressed_image_file
except ImportError:
    def secure_video_save(instance, file, field='video'):
        if file:
            setattr(instance, field, file)
    def compressed_image_file(file):
        return file

def rental_list(request):
    from django.db.models import Count, Q as DQ
    from apps.interactions.models import Reaction, Comment
    from django.contrib.contenttypes.models import ContentType as CT

    rentals = RentalListing.objects.filter(
        is_active=True, is_taken=False
    ).select_related('landlord__profile').prefetch_related('images')

    # Search
    query = request.GET.get('q', '')
    if query:
        rentals = rentals.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(address__icontains=query)
            | Q(area__icontains=query)
            | Q(landlord__username__icontains=query)
        )

    # Filter by type
    rental_type = request.GET.get('type', '')
    if rental_type:
        rentals = rentals.filter(rental_type=rental_type)

    # Filter by gender preference
    gender = request.GET.get('gender', '')
    if gender:
        rentals = rentals.filter(
            Q(gender_preference=gender) | Q(gender_preference='any')
        )

    ct = CT.objects.get_for_model(RentalListing)
    rentals = rentals.annotate(
        like_count=Count('id', filter=DQ(id__in=Reaction.objects.filter(content_type=ct, reaction_type='like').values('object_id'))),
        comment_count=Count('id', filter=DQ(id__in=Comment.objects.filter(content_type=ct, is_active=True, parent=None).values('object_id'))),
    )

    rentals = rentals.order_by('-created_at')
    paginator = Paginator(rentals, 12)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'rentals/rental_list.html', {
        'page_obj': page,
        'query': query,
        'active_type': rental_type,
        'active_gender': gender,
        'rental_type_choices': RentalListing.RENTAL_TYPE_CHOICES,
        'gender_choices': RentalListing.GENDER_CHOICES,
    })


def rental_detail(request, pk):
    from apps.reviews.models import Review
    from apps.reviews.forms import ReviewForm
    from apps.interactions.models import Reaction, Comment

    rental = get_object_or_404(
        RentalListing.objects.select_related(
            'landlord__profile'
        ).prefetch_related('images'),
        pk=pk,
        is_active=True,
    )

    # Increment view count (skip landlord's own views)
    if not request.user.is_authenticated or request.user != rental.landlord:
        from django.db import models as db_models
        RentalListing.objects.filter(pk=pk).update(view_count=db_models.F('view_count') + 1)
        rental.refresh_from_db(fields=['view_count'])

    user_inquired = False
    if request.user.is_authenticated:
        user_inquired = RentalInquiry.objects.filter(
            rental=rental, inquirer=request.user
        ).exists()

    ct = ContentType.objects.get_for_model(RentalListing)
    reviews = Review.objects.filter(
        content_type=ct,
        object_id=str(rental.pk),
    ).select_related('reviewer').order_by('-created_at')

    user_has_reviewed = (
        request.user.is_authenticated
        and reviews.filter(reviewer=request.user).exists()
    )

    # Interactions
    likes    = Reaction.objects.filter(content_type=ct, object_id=str(rental.pk), reaction_type='like').count()
    dislikes = Reaction.objects.filter(content_type=ct, object_id=str(rental.pk), reaction_type='dislike').count()
    user_reaction = None
    if request.user.is_authenticated:
        r = Reaction.objects.filter(user=request.user, content_type=ct, object_id=str(rental.pk)).first()
        if r:
            user_reaction = r.reaction_type

    comments = Comment.objects.filter(
        content_type=ct,
        object_id=str(rental.pk),
        is_active=True,
        parent=None,
    ).select_related('user__profile').prefetch_related('replies__user__profile')

    return render(request, 'rentals/rental_detail.html', {
        'rental': rental,
        'inquiry_form': RentalInquiryForm(),
        'user_inquired': user_inquired,
        'reviews': reviews,
        'review_form': ReviewForm(),
        'user_has_reviewed': user_has_reviewed,
        'ct_app': 'rentals',
        'ct_model': 'rentallisting',
        'likes': likes,
        'dislikes': dislikes,
        'user_reaction': user_reaction,
        'comments': comments,
        'app_label': 'rentals',
        'model_name': 'rentallisting',
    })


@login_required
def rental_create(request):
    if request.method == 'POST':
        form = RentalListingForm(request.POST)
        if form.is_valid():
            uploaded = request.FILES.getlist('images')
            video_file = request.FILES.get('video')
            img_errors = MultiImageValidator.validate(uploaded)
            video_error = VideoValidator.validate(video_file)
            if img_errors or video_error:
                for err in img_errors:
                    form.add_error(None, err)
                if video_error:
                    form.add_error(None, f"Video: {video_error}")
            else:
                rental = form.save(commit=False)
                rental.landlord = request.user
                if video_file:
                    secure_video_save(rental, video_file, "video")
                rental.save()
                if uploaded:
                    main_idx = int(request.POST.get('main_image_index', 0))
                    main_idx = max(0, min(main_idx, len(uploaded) - 1))
                    ordered = [uploaded[main_idx]] + [f for j, f in enumerate(uploaded) if j != main_idx]
                    for i, img in enumerate(ordered[:5]):
                        RentalImage.objects.create(
                            rental=rental,
                            image=compressed_image_file(img),
                            is_primary=(i == 0),
                        )
                messages.success(request, "Rental listing posted successfully!")
                return redirect(rental.get_absolute_url())
    else:
        form = RentalListingForm()

    return render(request, 'rentals/rental_form.html', {
        'form': form,
        'action': 'Post',
    })


@login_required
def rental_edit(request, pk):
    rental = get_object_or_404(RentalListing, pk=pk, landlord=request.user)
    if request.method == 'POST':
        form = RentalListingForm(request.POST, request.FILES, instance=rental)
        if form.is_valid():
            uploaded = request.FILES.getlist('images')
            video_file = request.FILES.get('video')
            img_errors = MultiImageValidator.validate(uploaded)
            video_error = VideoValidator.validate(video_file)
            if img_errors or video_error:
                for err in img_errors:
                    form.add_error(None, err)
                if video_error:
                    form.add_error(None, f"Video: {video_error}")
            else:
                rental = form.save(commit=False)
                if video_file:
                    secure_video_save(rental, video_file, "video")
                rental.save()
                if uploaded:
                    existing_count = rental.images.count()
                    slots_left = max(0, 5 - existing_count)
                    main_idx = int(request.POST.get('main_image_index', 0))
                    main_idx = max(0, min(main_idx, len(uploaded) - 1))
                    ordered = [uploaded[main_idx]] + [f for j, f in enumerate(uploaded) if j != main_idx]
                    for i, img in enumerate(ordered[:slots_left]):
                        is_primary = (existing_count == 0 and i == 0)
                        RentalImage.objects.create(
                            rental=rental,
                            image=compressed_image_file(img),
                            is_primary=is_primary,
                        )
                messages.success(request, "Rental listing updated.")
                return redirect(rental.get_absolute_url())
    else:
        form = RentalListingForm(instance=rental)

    return render(request, 'rentals/rental_form.html', {
        'form': form,
        'rental': rental,
        'action': 'Edit',
    })


@login_required
def rental_delete(request, pk):
    rental = get_object_or_404(RentalListing, pk=pk, landlord=request.user)
    if request.method == 'POST':
        rental.is_active = False
        rental.save()
        messages.success(request, "Rental listing removed.")
        return redirect('rentals:rental-list')
    return render(request, 'rentals/rental_confirm_delete.html', {'rental': rental})


@login_required
@require_POST
def rental_mark_taken(request, pk):
    rental = get_object_or_404(RentalListing, pk=pk, landlord=request.user)
    rental.is_taken = True
    rental.save()
    messages.success(request, f'"{rental.title}" marked as taken.')
    return redirect('accounts:profile', username=request.user.username)


@login_required
def rental_inquire(request, pk):
    """Submit a rental inquiry — sends message to landlord."""
    rental = get_object_or_404(RentalListing, pk=pk, is_active=True)

    if rental.landlord == request.user:
        messages.error(request, "You can't inquire about your own listing.")
        return redirect(rental.get_absolute_url())

    if RentalInquiry.objects.filter(rental=rental, inquirer=request.user).exists():
        messages.warning(request, "You've already sent an inquiry for this listing.")
        return redirect(rental.get_absolute_url())

    if request.method == 'POST':
        form = RentalInquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.rental = rental
            inquiry.inquirer = request.user
            inquiry.save()

            # Also create a messaging thread so landlord can reply
            from apps.messaging.models import Thread, Message
            existing = Thread.objects.filter(
                participants=request.user
            ).filter(participants=rental.landlord).first()

            if not existing:
                thread = Thread.objects.create(
                    subject=f"Re: {rental.title}"
                )
                thread.participants.add(request.user, rental.landlord)
            else:
                thread = existing

            Message.objects.create(
                thread=thread,
                sender=request.user,
                body=form.cleaned_data['message'],
            )
            thread.save()

            messages.success(
                request,
                "Inquiry sent! The landlord will reply via your inbox."
            )
            return redirect(rental.get_absolute_url())

    return redirect(rental.get_absolute_url())


@login_required
def my_rentals(request):
    """Landlord dashboard — their listings and inquiries."""
    rentals = RentalListing.objects.filter(
        landlord=request.user, is_active=True
    ).prefetch_related('images', 'inquiries')

    return render(request, 'rentals/my_rentals.html', {'rentals': rentals})
