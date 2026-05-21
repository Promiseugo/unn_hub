from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from .models import ServiceOffer, ServiceCategory, ServiceSubCategory
from .forms import ServiceOfferForm, VideoValidator

try:
    from apps.core.upload_utils import secure_video_save
except ImportError:
    def secure_video_save(instance, file, field='video'):
        if file:
            setattr(instance, field, file)

def service_list(request):
    from django.db.models import Count, Q as DQ
    from apps.interactions.models import Reaction, Comment

    services = ServiceOffer.objects.filter(is_active=True).select_related('provider', 'category')
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

    ct = ContentType.objects.get_for_model(ServiceOffer)
    services = services.annotate(
        like_count=Count('id', filter=DQ(id__in=Reaction.objects.filter(content_type=ct, reaction_type='like').values('object_id'))),
        comment_count=Count('id', filter=DQ(id__in=Comment.objects.filter(content_type=ct, is_active=True, parent=None).values('object_id'))),
    )

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

    service = get_object_or_404(
        ServiceOffer.objects.select_related('provider__profile'),
        pk=pk,
        is_active=True,
    )

    # Increment view count (skip provider's own views)
    if not request.user.is_authenticated or request.user != service.provider:
        from django.db import models as db_models
        ServiceOffer.objects.filter(pk=pk).update(view_count=db_models.F('view_count') + 1)
        service.refresh_from_db(fields=['view_count'])

    ct = ContentType.objects.get_for_model(ServiceOffer)
    reviews = Review.objects.filter(
        content_type=ct,
        object_id=str(service.pk),
    ).select_related('reviewer').order_by('-created_at')

    user_has_reviewed = False
    if request.user.is_authenticated:
        user_has_reviewed = reviews.filter(reviewer=request.user).exists()

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
def service_create(request):
    form = ServiceOfferForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        video_file = request.FILES.get('video')
        video_error = VideoValidator.validate(video_file)
        if video_error:
            form.add_error(None, f"Video: {video_error}")
        else:
            service = form.save(commit=False)
            service.provider = request.user
            if video_file:
                secure_video_save(service, video_file, "video")
            service.save()
            messages.success(request, "Service posted successfully!")
            return redirect(service.get_absolute_url())
    return render(request, 'services/service_form.html', {
        'form': form,
        'action': 'Create',
    })


@login_required
def service_edit(request, pk):
    service = get_object_or_404(ServiceOffer, pk=pk, provider=request.user)
    form = ServiceOfferForm(request.POST or None, request.FILES or None, instance=service)
    if form.is_valid():
        video_file = request.FILES.get('video')
        video_error = VideoValidator.validate(video_file)
        if video_error:
            form.add_error(None, f"Video: {video_error}")
        else:
            svc = form.save(commit=False)
            if video_file:
                secure_video_save(svc, video_file, "video")
            svc.save()
            messages.success(request, "Service updated.")
            return redirect(svc.get_absolute_url())
    return render(request, 'services/service_form.html', {
        'form': form,
        'action': 'Edit',
        'service': service,
    })


@login_required
def service_delete(request, pk):
    service = get_object_or_404(ServiceOffer, pk=pk, provider=request.user)
    if request.method == 'POST':
        service.is_active = False
        service.save()
        messages.success(request, "Service removed.")
        return redirect('services:service-list')
    return render(request, 'services/service_confirm_delete.html', {'service': service})
