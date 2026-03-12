from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, LoginForm, ProfileUpdateForm, UserUpdateForm
from .models import User


def register_view(request):
    if request.user.is_authenticated:
        return redirect('marketplace:listing-list')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
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
            login(request, user)
            # Redirect to 'next' param if present (e.g., after @login_required redirect)
            next_url = request.GET.get('next', 'marketplace:listing-list')
            return redirect(next_url)
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('accounts:login')


def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    listings = profile_user.listings.filter(is_active=True).order_by('-created_at')[:6]
    services = profile_user.services.filter(is_active=True).order_by('-created_at')[:6]
    reviews = profile_user.profile.reviews.order_by('-created_at')[:5]
    
    context = {
        'profile_user': profile_user,
        'listings': listings,
        'services': services,
        'reviews': reviews,
    }
    return render(request, 'accounts/profile.html', context)


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
