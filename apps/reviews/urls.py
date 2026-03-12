from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('add/<str:app_label>/<str:model_name>/<str:object_id>/',
         views.add_review, name='add-review'),
]
