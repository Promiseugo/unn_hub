from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('unread-count/', views.unread_count, name='unread-count'),
    path('', views.inbox, name='inbox'),
    path('<int:pk>/', views.thread_detail, name='thread-detail'),
    path('new/<str:username>/', views.new_thread, name='new-thread'),
]
