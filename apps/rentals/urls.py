from django.urls import path
from . import views

app_name = 'rentals'

urlpatterns = [
    path('', views.rental_list, name='rental-list'),
    path('create/', views.rental_create, name='rental-create'),
    path('my-listings/', views.my_rentals, name='my-rentals'),
    path('<uuid:pk>/', views.rental_detail, name='rental-detail'),
    path('<uuid:pk>/edit/', views.rental_edit, name='rental-edit'),
    path('<uuid:pk>/delete/', views.rental_delete, name='rental-delete'),
    path('<uuid:pk>/taken/', views.rental_mark_taken, name='rental-mark-taken'),
    path('<uuid:pk>/inquire/', views.rental_inquire, name='rental-inquire'),
]
