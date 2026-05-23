from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class Thread(TimeStampedModel):
    """
    A conversation between two users.
    subject is optional context, e.g. "Re: iPhone 12 for sale".
    """
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='threads',
    )
    subject = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Thread {self.id}: {self.subject or '(no subject)'}"

    def get_other_participant(self, user):
        """Return the other person in this thread (for display)."""
        return self.participants.exclude(pk=user.pk).first()

    def unread_count_for(self, user):
        """Count messages in this thread not yet read by this user."""
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class Message(TimeStampedModel):
    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
    )
    body = models.TextField()
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['thread', 'is_read', 'sender']),
            models.Index(fields=['sender', '-created_at']),
        ]

    def __str__(self):
        return f"Message from {self.sender.email} in Thread {self.thread.id}"
