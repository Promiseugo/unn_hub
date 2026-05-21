from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('signup/', views.register_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('signin/', views.login_view, name='signin'),
    path('sign-in/', views.login_view, name='sign-in'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/<uidb64>/<token>/', views.verify_email_view, name='verify-email'),
    path('profile/edit/', views.profile_edit_view, name='profile-edit'),
    path('profile/<str:username>/', views.profile_view, name='profile'),

    # ── Password Change (logged-in) ───────────────────────────────
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

    # ── Password Reset ────────────────────────────────────────────
    # Step 1: User enters email
    path('password-reset/',
         views.PasswordResetNotifyView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.txt',
             html_email_template_name='accounts/password_reset_email.html',
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
