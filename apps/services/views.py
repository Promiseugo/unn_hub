from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import ServiceOffer, ServiceCategory
from .forms import ServiceOfferForm


def service_list(request):
    services = ServiceOffer.objects.filter(is_active=True).select_related(
        'provider', 'category'
    )
    query = request.GET.get('q', '')
    if query:
        services = services.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
    category_slug = request.GET.get('category', '')
    if category_slug:
        services = services.filter(category__slug=category_slug)

    paginator = Paginator(services, 12)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'services/service_list.html', {
        'page_obj': page,
        'categories': ServiceCategory.objects.all(),
        'query': query,
        'active_category': category_slug,
    })


def service_detail(request, pk):
    service = get_object_or_404(
        ServiceOffer.objects.select_related('provider__profile'), pk=pk, is_active=True
    )
    return render(request, 'services/service_detail.html', {'service': service})


@login_required
def service_create(request):
    form = ServiceOfferForm(request.POST or None)
    if form.is_valid():
        service = form.save(commit=False)
        service.provider = request.user
        service.save()
        messages.success(request, "Service posted successfully!")
        return redirect(service.get_absolute_url())
    return render(request, 'services/service_form.html', {'form': form, 'action': 'Create'})


@login_required
def service_edit(request, pk):
    service = get_object_or_404(ServiceOffer, pk=pk, provider=request.user)
    form = ServiceOfferForm(request.POST or None, instance=service)
    if form.is_valid():
        form.save()
        messages.success(request, "Service updated.")
        return redirect(service.get_absolute_url())
    return render(request, 'services/service_form.html', {'form': form, 'action': 'Edit', 'service': service})


@login_required
def service_delete(request, pk):
    service = get_object_or_404(ServiceOffer, pk=pk, provider=request.user)
    if request.method == 'POST':
        service.is_active = False
        service.save()
        messages.success(request, "Service removed.")
        return redirect('services:service-list')
    return render(request, 'services/service_confirm_delete.html', {'service': service})
