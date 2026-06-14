from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django_ratelimit.decorators import ratelimit
from django.utils import timezone
from .models import ServiceOffer, ServiceCategory, ServiceSubCategory
from .forms import ServiceOfferForm, VideoValidator
from apps.core.upload_utils import secure_video_save

def service_list(request):
    from apps.interactions.utils import with_interaction_counts

    services = ServiceOffer.objects.filter(
        is_active=True,
        approval_status=ServiceOffer.APPROVAL_APPROVED,
        deleted_at__isnull=True,
    ).select_related('provider', 'category', 'subcategory')
    query = request.GET.get('q', '')
    if query:
        services = services.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
            | Q(subcategory__name__icontains=query)
            | Q(provider__username__icontains=query)
        )
    category_slug = request.GET.get('category', '')
    if category_slug:
        services = services.filter(category__slug=category_slug)
    subcategory_slug = request.GET.get('subcategory', '')
    if subcategory_slug:
        services = services.filter(subcategory__slug=subcategory_slug)

    services = with_interaction_counts(services, ServiceOffer)

    services = services.order_by('-created_at')
    paginator = Paginator(services, 12)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'services/service_list.html', {
        'page_obj': page,
        'categories': ServiceCategory.objects.prefetch_related('subcategories').all(),
        'query': query,
        'active_category': category_slug,
        'active_subcategory': subcategory_slug,
    })


def service_detail(request, pk):
    from apps.reviews.models import Review
    from apps.reviews.forms import ReviewForm
    from apps.interactions.models import Reaction, Comment
    from apps.interactions.utils import should_count_view
    from apps.trust.models import TrustTransaction

    service = get_object_or_404(
        ServiceOffer.objects.select_related('provider__profile', 'category', 'subcategory'),
        pk=pk,
        is_active=True,
        approval_status=ServiceOffer.APPROVAL_APPROVED,
        deleted_at__isnull=True,
    )

    if should_count_view(request, service):
        from django.db import models as db_models
        ServiceOffer.objects.filter(pk=pk).update(view_count=db_models.F('view_count') + 1)
        service.refresh_from_db(fields=['view_count'])

    ct = ContentType.objects.get_for_model(ServiceOffer)
    reviews = Review.objects.filter(
        content_type=ct,
        object_id=str(service.pk),
    ).select_related('reviewer').order_by('-created_at')

    user_has_reviewed = False
    user_can_review = False
    trust_transactions = []
    if request.user.is_authenticated:
        user_has_reviewed = reviews.filter(reviewer=request.user).exists()
        tx_qs = TrustTransaction.objects.filter(
            content_type=ct,
            object_id=str(service.pk),
        ).select_related('buyer', 'seller')
        if request.user == service.provider:
            trust_transactions = list(tx_qs.filter(
                seller=request.user,
            ).exclude(status__in=[
                TrustTransaction.STATUS_REVERSED,
                TrustTransaction.STATUS_CANCELLED,
            ]).order_by('-created_at')[:5])
        else:
            trust_transactions = list(tx_qs.filter(
                buyer=request.user,
                seller=service.provider,
            ).exclude(status__in=[
                TrustTransaction.STATUS_REVERSED,
                TrustTransaction.STATUS_CANCELLED,
            ]).order_by('-created_at')[:1])
            user_can_review = TrustTransaction.completed_for_review(
                reviewer=request.user,
                owner=service.provider,
                content_type=ct,
                object_id=str(service.pk),
            )

    # Interactions
    likes    = Reaction.objects.filter(content_type=ct, object_id=str(service.pk), reaction_type='like').count()
    dislikes = Reaction.objects.filter(content_type=ct, object_id=str(service.pk), reaction_type='dislike').count()
    user_reaction = None
    if request.user.is_authenticated:
        r = Reaction.objects.filter(user=request.user, content_type=ct, object_id=str(service.pk)).first()
        if r:
            user_reaction = r.reaction_type

    comments = Comment.objects.filter(
        content_type=ct,
        object_id=str(service.pk),
        is_active=True,
        parent=None,
    ).select_related('user__profile').prefetch_related('replies__user__profile')

    return render(request, 'services/service_detail.html', {
        'service': service,
        'reviews': reviews,
        'review_form': ReviewForm(),
        'user_has_reviewed': user_has_reviewed,
        'user_can_review': user_can_review,
        'trust_transactions': trust_transactions,
        'transaction_owner': service.provider,
        'transaction_app_label': 'services',
        'transaction_model_name': 'serviceoffer',
        'transaction_object_id': service.pk,
        'ct_app': 'services',
        'ct_model': 'serviceoffer',
        'likes': likes,
        'dislikes': dislikes,
        'user_reaction': user_reaction,
        'comments': comments,
        'app_label': 'services',
        'model_name': 'serviceoffer',
    })


@login_required
@ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True)
def service_create(request):
    from apps.trust.utils import detect_listing_risk, log_audit, log_suspicious

    form = ServiceOfferForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        video_upload_disabled = bool(request.FILES.get('video')) and not getattr(settings, 'ENABLE_VIDEO_UPLOADS', False)
        video_file = request.FILES.get('video') if not video_upload_disabled else None
        if video_upload_disabled:
            form.add_error(None, "Video uploads are disabled for the MVP launch. Please use photos only.")
        video_error = VideoValidator.validate(video_file)
        if video_error or video_upload_disabled:
            if video_error:
                form.add_error(None, f"Video: {video_error}")
        else:
            service = form.save(commit=False)
            service.provider = request.user
            risk_reasons = detect_listing_risk(service)
            service.risk_reasons = risk_reasons
            service.risk_score = min(100, len(risk_reasons) * 35)
            if risk_reasons:
                service.approval_status = ServiceOffer.APPROVAL_FLAGGED
                service.is_active = False
            if video_file:
                secure_video_save(service, video_file, "video")
            service.save()
            log_audit(request, 'service_created', service, metadata={'risk_reasons': risk_reasons})
            if risk_reasons:
                log_suspicious(
                    request,
                    'service_flagged',
                    'Service was automatically flagged during creation.',
                    severity='medium',
                    metadata={'service_id': str(service.pk), 'reasons': risk_reasons},
                )
                messages.warning(request, "Service submitted for moderator review before it appears publicly.")
                return redirect('accounts:profile', username=request.user.username)
            messages.success(request, "Service posted successfully!")
            return redirect(service.get_absolute_url())
    return render(request, 'services/service_form.html', {
        'form': form,
        'action': 'Create',
        'enable_video_uploads': getattr(settings, 'ENABLE_VIDEO_UPLOADS', False),
    })


@login_required
@ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True)
def service_edit(request, pk):
    from apps.trust.utils import detect_listing_risk, log_audit, log_suspicious

    service = get_object_or_404(ServiceOffer, pk=pk, provider=request.user, deleted_at__isnull=True)
    form = ServiceOfferForm(request.POST or None, request.FILES or None, instance=service)
    if form.is_valid():
        video_upload_disabled = bool(request.FILES.get('video')) and not getattr(settings, 'ENABLE_VIDEO_UPLOADS', False)
        video_file = request.FILES.get('video') if not video_upload_disabled else None
        if video_upload_disabled:
            form.add_error(None, "Video uploads are disabled for the MVP launch. Please use photos only.")
        video_error = VideoValidator.validate(video_file)
        if video_error or video_upload_disabled:
            if video_error:
                form.add_error(None, f"Video: {video_error}")
        else:
            svc = form.save(commit=False)
            risk_reasons = detect_listing_risk(svc)
            svc.risk_reasons = risk_reasons
            svc.risk_score = min(100, len(risk_reasons) * 35)
            if risk_reasons:
                svc.approval_status = ServiceOffer.APPROVAL_FLAGGED
                svc.is_active = False
            if video_file:
                secure_video_save(svc, video_file, "video")
            svc.save()
            log_audit(request, 'service_updated', svc, metadata={'risk_reasons': risk_reasons})
            if risk_reasons:
                log_suspicious(
                    request,
                    'service_flagged_on_edit',
                    'Service was automatically flagged during edit.',
                    severity='medium',
                    metadata={'service_id': str(svc.pk), 'reasons': risk_reasons},
                )
            messages.success(request, "Service updated.")
            return redirect(svc.get_absolute_url())
    return render(request, 'services/service_form.html', {
        'form': form,
        'action': 'Edit',
        'service': service,
        'enable_video_uploads': getattr(settings, 'ENABLE_VIDEO_UPLOADS', False),
    })


@login_required
def service_delete(request, pk):
    from apps.trust.utils import log_audit

    service = get_object_or_404(ServiceOffer, pk=pk, provider=request.user)
    if request.method == 'POST':
        service.is_active = False
        service.deleted_at = timezone.now()
        service.save(update_fields=['is_active', 'deleted_at', 'updated_at'])
        log_audit(request, 'service_soft_deleted', service)
        messages.success(request, "Service removed.")
        return redirect('services:service-list')
    return render(request, 'services/service_confirm_delete.html', {'service': service})
