from django.urls import path
from . import views

app_name = 'interactions'

urlpatterns = [
    path(
        'react/<str:app_label>/<str:model_name>/<str:object_id>/',
        views.react,
        name='react',
    ),
    path(
        'comment/<str:app_label>/<str:model_name>/<str:object_id>/',
        views.add_comment,
        name='add-comment',
    ),
    path(
        'comment/delete/<int:comment_id>/',
        views.delete_comment,
        name='delete-comment',
    ),
]
