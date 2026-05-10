from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.http import require_POST
from .models import Listing, Category, SubCategory, ListingImage
from .forms import ListingForm, MultiImageValidator, VideoValidator

try:
    from apps.core.upload_utils import secure_video_save
except ImportError:
    def secure_video_save(instance, file, field='video'):
        if file:
            setattr(instance, field, file)

def listing_list(request):
    from django.db.models import Count, Q as DQ
    from apps.interactions.models import Reaction, Comment

    listings = Listing.objects.filter(
        is_active=True, is_sold=False
    ).select_related('seller', 'category').prefetch_related('images')

    query = request.GET.get('q', '')
    if query:
        listings = listings.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    category_slug = request.GET.get('category', '')
    subcategory_slug = request.GET.get('subcategory', '')
    if category_slug:
        listings = listings.filter(category__slug=category_slug)
    if subcategory_slug:
        listings = listings.filter(subcategory__slug=subcategory_slug)

    # Annotate like and comment counts
    ct = ContentType.objects.get_for_model(Listing)
    listings = listings.annotate(
        like_count=Count(
            'id',
            filter=DQ(
                id__in=Reaction.objects.filter(
                    content_type=ct, reaction_type='like'
                ).values('object_id')
            )
        ),
        comment_count=Count(
            'id',
            filter=DQ(
                id__in=Comment.objects.filter(
                    content_type=ct, is_active=True, parent=None
                ).values('object_id')
            )
        ),
    )

    paginator = Paginator(listings, 12)
    page = paginator.get_page(request.GET.get('page'))
    categories = Category.objects.prefetch_related('subcategories').all()

    return render(request, 'marketplace/listing_list.html', {
        'page_obj': page,
        'categories': categories,
        'query': query,
        'active_category': category_slug,
        'active_subcategory': subcategory_slug,
    })


def listing_detail(request, pk):
    from apps.reviews.models import Review
    from apps.reviews.forms import ReviewForm
    from apps.interactions.models import Reaction, Comment

    listing = get_object_or_404(
        Listing.objects.select_related(
            'seller__profile'
        ).prefetch_related('images'),
        pk=pk,
        is_active=True,
    )

    # Increment view count (skip owner's own views)
    if not request.user.is_authenticated or request.user != listing.seller:
        Listing.objects.filter(pk=pk).update(view_count=models.F('view_count') + 1)
        listing.refresh_from_db(fields=['view_count'])

    ct = ContentType.objects.get_for_model(Listing)
    reviews = Review.objects.filter(
        content_type=ct,
        object_id=str(listing.pk),
    ).select_related('reviewer').order_by('-created_at')

    user_has_reviewed = (
        request.user.is_authenticated
        and reviews.filter(reviewer=request.user).exists()
    )

    # Interactions
    likes    = Reaction.objects.filter(content_type=ct, object_id=str(listing.pk), reaction_type='like').count()
    dislikes = Reaction.objects.filter(content_type=ct, object_id=str(listing.pk), reaction_type='dislike').count()
    user_reaction = None
    if request.user.is_authenticated:
        r = Reaction.objects.filter(user=request.user, content_type=ct, object_id=str(listing.pk)).first()
        if r:
            user_reaction = r.reaction_type

    comments = Comment.objects.filter(
        content_type=ct,
        object_id=str(listing.pk),
        is_active=True,
        parent=None,
    ).select_related('user__profile').prefetch_related('replies__user__profile')

    return render(request, 'marketplace/listing_detail.html', {
        'listing': listing,
        'reviews': reviews,
        'review_form': ReviewForm(),
        'user_has_reviewed': user_has_reviewed,
        'ct_app': 'marketplace',
        'ct_model': 'listing',
        'likes': likes,
        'dislikes': dislikes,
        'user_reaction': user_reaction,
        'comments': comments,
        'app_label': 'marketplace',
        'model_name': 'listing',
    })


@login_required
def listing_create(request):
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            # Validate all uploaded images before saving anything
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
                listing = form.save(commit=False)
                listing.seller = request.user
                if video_file:
                    secure_video_save(listing, video_file, "video")
                listing.save()
                if uploaded:
                    main_idx = int(request.POST.get('main_image_index', 0))
                    main_idx = max(0, min(main_idx, len(uploaded) - 1))
                    # Reorder so chosen main comes first
                    ordered = [uploaded[main_idx]] + [f for j, f in enumerate(uploaded) if j != main_idx]
                    for i, img in enumerate(ordered[:5]):
                        ListingImage.objects.create(
                            listing=listing,
                            image=img,
                            is_primary=(i == 0),
                        )
                messages.success(request, "Listing created successfully!")
                return redirect(listing.get_absolute_url())
    else:
        form = ListingForm()

    return render(request, 'marketplace/listing_form.html', {
        'form': form,
        'action': 'Create',
    })


@login_required
def listing_edit(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES, instance=listing)
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
                listing = form.save(commit=False)
                if video_file:
                    secure_video_save(listing, video_file, "video")
                listing.save()
                if uploaded:
                    existing_count = listing.images.count()
                    slots_left = max(0, 5 - existing_count)
                    main_idx = int(request.POST.get('main_image_index', 0))
                    main_idx = max(0, min(main_idx, len(uploaded) - 1))
                    ordered = [uploaded[main_idx]] + [f for j, f in enumerate(uploaded) if j != main_idx]
                    for i, img in enumerate(ordered[:slots_left]):
                        is_primary = (existing_count == 0 and i == 0)
                        ListingImage.objects.create(
                            listing=listing,
                            image=img,
                            is_primary=is_primary,
                        )
                messages.success(request, "Listing updated.")
                return redirect(listing.get_absolute_url())
    else:
        form = ListingForm(instance=listing)

    return render(request, 'marketplace/listing_form.html', {
        'form': form,
        'listing': listing,
        'action': 'Edit',
    })


@login_required
def listing_delete(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    if request.method == 'POST':
        listing.is_active = False
        listing.save()
        messages.success(request, "Listing removed.")
        return redirect('marketplace:listing-list')
    return render(request, 'marketplace/listing_confirm_delete.html', {
        'listing': listing,
    })


@login_required
@require_POST   # Prevents GET-based CSRF attacks on state-changing action
def listing_mark_sold(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    listing.is_sold = True
    listing.save()
    messages.success(request, f'"{listing.title}" marked as sold.')
    return redirect('accounts:profile', username=request.user.username)
