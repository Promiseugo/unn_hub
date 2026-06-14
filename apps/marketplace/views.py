from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
from django.utils import timezone
from .models import Listing, Category, SubCategory, ListingImage
from .forms import ListingForm, MultiImageValidator, VideoValidator
from .utils import deactivate_expired_listings
from apps.core.upload_utils import secure_video_save, compressed_image_file

def listing_list(request):
    from apps.interactions.utils import with_interaction_counts

    deactivate_expired_listings()

    listings = Listing.objects.filter(
        is_active=True,
        is_sold=False,
        expires_at__gt=timezone.now(),
        approval_status=Listing.APPROVAL_APPROVED,
        deleted_at__isnull=True,
    ).select_related('seller', 'category', 'subcategory').prefetch_related('images')

    query = request.GET.get('q', '')
    if query:
        listings = listings.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(location__icontains=query)
            | Q(category__name__icontains=query)
            | Q(subcategory__name__icontains=query)
            | Q(seller__username__icontains=query)
        )

    category_slug = request.GET.get('category', '')
    subcategory_slug = request.GET.get('subcategory', '')
    condition = request.GET.get('condition', '')
    if category_slug:
        listings = listings.filter(category__slug=category_slug)
    if subcategory_slug:
        listings = listings.filter(subcategory__slug=subcategory_slug)
    if condition in dict(Listing.CONDITION_CHOICES):
        listings = listings.filter(condition=condition)

    listings = with_interaction_counts(listings, Listing)

    listings = listings.order_by('-created_at')
    paginator = Paginator(listings, 12)
    page = paginator.get_page(request.GET.get('page'))
    categories = Category.objects.prefetch_related('subcategories').all()

    return render(request, 'marketplace/listing_list.html', {
        'page_obj': page,
        'categories': categories,
        'query': query,
        'active_category': category_slug,
        'active_subcategory': subcategory_slug,
        'active_condition': condition,
        'condition_choices': Listing.CONDITION_CHOICES,
    })


def listing_detail(request, pk):
    from apps.reviews.models import Review
    from apps.reviews.forms import ReviewForm
    from apps.interactions.models import Reaction, Comment
    from apps.interactions.utils import should_count_view
    from apps.trust.models import TrustTransaction

    listing = get_object_or_404(
        Listing.objects.select_related(
            'seller__profile', 'category', 'subcategory'
        ).prefetch_related('images'),
        pk=pk,
        is_active=True,
        approval_status=Listing.APPROVAL_APPROVED,
        deleted_at__isnull=True,
        expires_at__gt=timezone.now(),
    )

    if should_count_view(request, listing):
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
    trust_transactions = []
    user_can_review = False
    if request.user.is_authenticated:
        tx_qs = TrustTransaction.objects.filter(
            content_type=ct,
            object_id=str(listing.pk),
        ).select_related('buyer', 'seller')
        if request.user == listing.seller:
            trust_transactions = list(tx_qs.filter(
                seller=request.user,
            ).exclude(status__in=[
                TrustTransaction.STATUS_REVERSED,
                TrustTransaction.STATUS_CANCELLED,
            ]).order_by('-created_at')[:5])
        else:
            trust_transactions = list(tx_qs.filter(
                buyer=request.user,
                seller=listing.seller,
            ).exclude(status__in=[
                TrustTransaction.STATUS_REVERSED,
                TrustTransaction.STATUS_CANCELLED,
            ]).order_by('-created_at')[:1])
            user_can_review = TrustTransaction.completed_for_review(
                reviewer=request.user,
                owner=listing.seller,
                content_type=ct,
                object_id=str(listing.pk),
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
        'user_can_review': user_can_review,
        'trust_transactions': trust_transactions,
        'transaction_owner': listing.seller,
        'transaction_app_label': 'marketplace',
        'transaction_model_name': 'listing',
        'transaction_object_id': listing.pk,
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
@ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True)
def listing_create(request):
    from apps.trust.utils import detect_listing_risk, log_audit, log_suspicious

    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            # Validate all uploaded images before saving anything
            uploaded = request.FILES.getlist('images')
            video_upload_disabled = bool(request.FILES.get('video')) and not getattr(settings, 'ENABLE_VIDEO_UPLOADS', False)
            video_file = request.FILES.get('video') if not video_upload_disabled else None
            if video_upload_disabled:
                form.add_error(None, "Video uploads are disabled for the MVP launch. Please use photos only.")
            img_errors = MultiImageValidator.validate(uploaded)
            video_error = VideoValidator.validate(video_file)
            if img_errors or video_error or video_upload_disabled:
                for err in img_errors:
                    form.add_error(None, err)
                if video_error:
                    form.add_error(None, f"Video: {video_error}")
            else:
                listing = form.save(commit=False)
                listing.seller = request.user
                risk_reasons = detect_listing_risk(listing)
                listing.risk_reasons = risk_reasons
                listing.risk_score = min(100, len(risk_reasons) * 35)
                if risk_reasons:
                    listing.approval_status = Listing.APPROVAL_FLAGGED
                    listing.is_active = False
                if video_file:
                    secure_video_save(listing, video_file, "video")
                listing.save()
                log_audit(request, 'listing_created', listing, metadata={'risk_reasons': risk_reasons})
                if risk_reasons:
                    log_suspicious(
                        request,
                        'listing_flagged',
                        'Listing was automatically flagged during creation.',
                        severity='medium',
                        metadata={'listing_id': str(listing.pk), 'reasons': risk_reasons},
                    )
                if uploaded:
                    main_idx = int(request.POST.get('main_image_index', 0))
                    main_idx = max(0, min(main_idx, len(uploaded) - 1))
                    # Reorder so chosen main comes first
                    ordered = [uploaded[main_idx]] + [f for j, f in enumerate(uploaded) if j != main_idx]
                    for i, img in enumerate(ordered[:5]):
                        ListingImage.objects.create(
                            listing=listing,
                            image=compressed_image_file(img),
                            is_primary=(i == 0),
                        )
                if risk_reasons:
                    messages.warning(request, "Listing submitted for moderator review before it appears publicly.")
                    return redirect('accounts:profile', username=request.user.username)
                else:
                    messages.success(request, "Listing created successfully!")
                    return redirect(listing.get_absolute_url())
    else:
        form = ListingForm()

    return render(request, 'marketplace/listing_form.html', {
        'form': form,
        'action': 'Create',
        'enable_video_uploads': getattr(settings, 'ENABLE_VIDEO_UPLOADS', False),
    })


@login_required
@ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True)
def listing_edit(request, pk):
    from apps.trust.utils import detect_listing_risk, log_audit, log_suspicious

    listing = get_object_or_404(Listing, pk=pk, seller=request.user, deleted_at__isnull=True)
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES, instance=listing)
        if form.is_valid():
            uploaded = request.FILES.getlist('images')
            video_upload_disabled = bool(request.FILES.get('video')) and not getattr(settings, 'ENABLE_VIDEO_UPLOADS', False)
            video_file = request.FILES.get('video') if not video_upload_disabled else None
            if video_upload_disabled:
                form.add_error(None, "Video uploads are disabled for the MVP launch. Please use photos only.")
            img_errors = MultiImageValidator.validate(uploaded)
            video_error = VideoValidator.validate(video_file)
            if img_errors or video_error or video_upload_disabled:
                for err in img_errors:
                    form.add_error(None, err)
                if video_error:
                    form.add_error(None, f"Video: {video_error}")
            else:
                listing = form.save(commit=False)
                risk_reasons = detect_listing_risk(listing)
                listing.risk_reasons = risk_reasons
                listing.risk_score = min(100, len(risk_reasons) * 35)
                if risk_reasons:
                    listing.approval_status = Listing.APPROVAL_FLAGGED
                    listing.is_active = False
                if video_file:
                    secure_video_save(listing, video_file, "video")
                listing.save()
                log_audit(request, 'listing_updated', listing, metadata={'risk_reasons': risk_reasons})
                if risk_reasons:
                    log_suspicious(
                        request,
                        'listing_flagged_on_edit',
                        'Listing was automatically flagged during edit.',
                        severity='medium',
                        metadata={'listing_id': str(listing.pk), 'reasons': risk_reasons},
                    )
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
                            image=compressed_image_file(img),
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
        'enable_video_uploads': getattr(settings, 'ENABLE_VIDEO_UPLOADS', False),
    })


@login_required
def listing_delete(request, pk):
    from apps.trust.utils import log_audit

    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    if request.method == 'POST':
        listing.is_active = False
        listing.deleted_at = timezone.now()
        listing.save(update_fields=['is_active', 'deleted_at', 'updated_at'])
        log_audit(request, 'listing_soft_deleted', listing)
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
