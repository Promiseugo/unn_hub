from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/edit/', views.profile_edit_view, name='profile-edit'),
    path('profile/<str:username>/', views.profile_view, name='profile'),

    # ── Password Change (logged-in) ─────────────────────────────
    path('password-change/',
         views.PasswordChangeNotifyView.as_view(
             template_name='accounts/password_change.html',
         ),
         name='password_change'),
    path('password-change/done/',
         views.PasswordChangeDoneView.as_view(
             template_name='accounts/password_change_done.html',
         ),
         name='password_change_done'),

    # ── Password Reset ──────────────────────────────────────────
    # Step 1: User enters email
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.txt',
             subject_template_name='accounts/password_reset_subject.txt',
             # Explicitly tell Django where to go after form submit
             # because our app_name namespace breaks the default redirect
             success_url=reverse_lazy('accounts:password_reset_done'),
         ),
         name='password-reset'),

    # Step 2: "Check your email" page
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html',
         ),
         name='password_reset_done'),

    # Step 3: User sets new password via emailed link
    path('password-reset/<uidb64>/<token>/',
         views.PasswordResetConfirmNotifyView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url=reverse_lazy('accounts:password_reset_complete'),
         ),
         name='password_reset_confirm'),

    # Step 4: Success confirmation
    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html',
         ),
         name='password_reset_complete'),
]
