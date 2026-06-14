"""
accounts/signals.py

Auto-create a Profile whenever a new User is registered.
This removes the need to manually call Profile.objects.create()
everywhere in your registration logic.
"""

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Called automatically after User.save() when created=True."""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    """Keep profile in sync on every user save."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
