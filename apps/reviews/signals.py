"""
reviews/signals.py

Recalculates Profile.avg_rating and Profile.total_reviews
whenever a Review is saved or deleted.

Aggregates ratings from ALL sources owned by the user:
  - Direct profile reviews
  - Listing reviews
  - ServiceOffer reviews
  - RentalListing reviews
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.db.models import Avg
from .models import Review


def _recalculate_profile(profile):
    from apps.accounts.models import Profile
    from apps.marketplace.models import Listing
    from apps.services.models import ServiceOffer
    from apps.rentals.models import RentalListing

    profile_ct = ContentType.objects.get_for_model(Profile)
    listing_ct = ContentType.objects.get_for_model(Listing)
    service_ct = ContentType.objects.get_for_model(ServiceOffer)
    rental_ct  = ContentType.objects.get_for_model(RentalListing)

    listing_ids = [str(i) for i in
        Listing.objects.filter(seller=profile.user).values_list('id', flat=True)]
    service_ids = [str(i) for i in
        ServiceOffer.objects.filter(provider=profile.user).values_list('id', flat=True)]
    rental_ids  = [str(i) for i in
        RentalListing.objects.filter(landlord=profile.user).values_list('id', flat=True)]

    from django.db.models import Q
    all_reviews = Review.objects.filter(
        Q(content_type=profile_ct, object_id=str(profile.pk))
        | Q(content_type=listing_ct, object_id__in=listing_ids)
        | Q(content_type=service_ct, object_id__in=service_ids)
        | Q(content_type=rental_ct,  object_id__in=rental_ids)
    )

    agg = all_reviews.aggregate(avg=Avg('rating'))
    profile.avg_rating    = round(agg['avg'] or 0, 2)
    profile.total_reviews = all_reviews.count()
    profile.save(update_fields=['avg_rating', 'total_reviews'])
    from apps.trust.scoring import update_trust_score
    update_trust_score(profile.user, reason='review_aggregate_changed')


def _get_profile_from_review(instance):
    from apps.accounts.models import Profile
    from apps.marketplace.models import Listing
    from apps.services.models import ServiceOffer
    from apps.rentals.models import RentalListing

    ct = instance.content_type
    try:
        if ct == ContentType.objects.get_for_model(Profile):
            return Profile.objects.get(pk=instance.object_id)
        elif ct == ContentType.objects.get_for_model(Listing):
            return Listing.objects.get(pk=instance.object_id).seller.profile
        elif ct == ContentType.objects.get_for_model(ServiceOffer):
            return ServiceOffer.objects.get(pk=instance.object_id).provider.profile
        elif ct == ContentType.objects.get_for_model(RentalListing):
            return RentalListing.objects.get(pk=instance.object_id).landlord.profile
    except Exception:
        pass
    return None


@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
def update_owner_rating(sender, instance, **kwargs):
    profile = _get_profile_from_review(instance)
    if profile:
        _recalculate_profile(profile)
