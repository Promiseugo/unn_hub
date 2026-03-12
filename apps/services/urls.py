from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('', views.service_list, name='service-list'),
    path('create/', views.service_create, name='service-create'),
    path('<uuid:pk>/', views.service_detail, name='service-detail'),
    path('<uuid:pk>/edit/', views.service_edit, name='service-edit'),
    path('<uuid:pk>/delete/', views.service_delete, name='service-delete'),
]
