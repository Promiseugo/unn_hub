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
def save_user_profile(sender, instance, created, update_fields, **kwargs):
    """Keep profile in sync on user saves that touch profile-relevant fields."""
    if created:
        return  # create_user_profile handles this case
    # Skip when only last_login (or other non-profile fields) changed — avoids
    # a full profile overwrite on every login() call.
    if update_fields is not None and update_fields <= frozenset(['last_login']):
        return
    if hasattr(instance, 'profile'):
        instance.profile.save()
