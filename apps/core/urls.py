from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('privacy/', views.privacy_policy, name='privacy-policy'),
    path('terms/', views.terms_of_service, name='terms-of-service'),
]
