from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from apps.core.models import TimeStampedModel


class Reaction(TimeStampedModel):
    """
    Generic like/dislike for any object (Listing, ServiceOffer, RentalListing).
    One reaction per user per object — updates in place if changed.
    """
    LIKE = 'like'
    DISLIKE = 'dislike'
    CHOICES = [(LIKE, 'Like'), (DISLIKE, 'Dislike')]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reactions',
    )
    reaction_type = models.CharField(max_length=10, choices=CHOICES)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=36)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} {self.reaction_type}"


class Comment(TimeStampedModel):
    """
    Generic threaded comment for any object.
    Top-level comments have parent=None.
    Replies have parent pointing to another Comment.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    body = models.TextField(max_length=1000)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
    )
    is_active = models.BooleanField(default=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=36)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.username}"

    @property
    def is_reply(self):
        return self.parent is not None
