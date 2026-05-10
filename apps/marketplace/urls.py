from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('listings/', views.listing_list, name='listing-list'),
    path('listings/create/', views.listing_create, name='listing-create'),
    path('listings/<uuid:pk>/', views.listing_detail, name='listing-detail'),
    path('listings/<uuid:pk>/edit/', views.listing_edit, name='listing-edit'),
    path('listings/<uuid:pk>/delete/', views.listing_delete, name='listing-delete'),
    path('listings/<uuid:pk>/sold/', views.listing_mark_sold, name='listing-mark-sold'),
]
