from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Listing, Category
from .forms import ListingForm, ListingImageForm


def listing_list(request):
    listings = Listing.objects.filter(is_active=True, is_sold=False).select_related(
        'seller', 'category'
    ).prefetch_related('images')

    # Search
    query = request.GET.get('q', '')
    if query:
        listings = listings.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    # Category filter
    category_slug = request.GET.get('category', '')
    if category_slug:
        listings = listings.filter(category__slug=category_slug)

    paginator = Paginator(listings, 12)
    page = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page,
        'categories': Category.objects.all(),
        'query': query,
        'active_category': category_slug,
    }
    return render(request, 'marketplace/listing_list.html', context)


def listing_detail(request, pk):
    listing = get_object_or_404(
        Listing.objects.select_related('seller__profile').prefetch_related('images'),
        pk=pk,
        is_active=True,
    )
    return render(request, 'marketplace/listing_detail.html', {'listing': listing})


@login_required
def listing_create(request):
    if request.method == 'POST':
        form = ListingForm(request.POST)
        image_form = ListingImageForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.seller = request.user
            listing.save()
            # Handle multiple image uploads
            images = request.FILES.getlist('images')
            for i, img in enumerate(images[:5]):     # Max 5 images
                ListingImage.objects.create(
                    listing=listing,
                    image=img,
                    is_primary=(i == 0),             # First image is primary
                )
            messages.success(request, "Listing created successfully!")
            return redirect(listing.get_absolute_url())
    else:
        form = ListingForm()
        image_form = ListingImageForm()

    return render(request, 'marketplace/listing_form.html', {
        'form': form,
        'image_form': image_form,
        'action': 'Create',
    })


@login_required
def listing_edit(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    if request.method == 'POST':
        form = ListingForm(request.POST, instance=listing)
        if form.is_valid():
            form.save()
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
    return render(request, 'marketplace/listing_confirm_delete.html', {'listing': listing})


@login_required
def listing_mark_sold(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    listing.is_sold = True
    listing.save()
    messages.success(request, f'"{listing.title}" marked as sold.')
    return redirect('accounts:profile', username=request.user.username)
