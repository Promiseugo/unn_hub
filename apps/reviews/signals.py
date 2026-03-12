"""
After a Review is saved or deleted, update the cached avg_rating
and total_reviews on the associated Profile.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.db.models import Avg
from .models import Review


def _update_profile_rating(profile):
    from apps.accounts.models import Profile
    ct = ContentType.objects.get_for_model(Profile)
    reviews = Review.objects.filter(content_type=ct, object_id=str(profile.pk))
    agg = reviews.aggregate(avg=Avg('rating'))
    profile.avg_rating = agg['avg'] or 0.00
    profile.total_reviews = reviews.count()
    profile.save(update_fields=['avg_rating', 'total_reviews'])


@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
def update_profile_rating(sender, instance, **kwargs):
    from apps.accounts.models import Profile
    ct = ContentType.objects.get_for_model(Profile)
    if instance.content_type == ct:
        try:
            profile = Profile.objects.get(pk=instance.object_id)
            _update_profile_rating(profile)
        except Profile.DoesNotExist:
            pass
