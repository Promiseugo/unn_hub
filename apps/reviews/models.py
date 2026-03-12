from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from apps.core.models import TimeStampedModel


class Review(TimeStampedModel):
    """
    Generic review model using Django's ContentType framework.

    This single model can store reviews for:
      - User Profiles  (content_type → Profile, object_id → profile.pk)
      - Listings       (content_type → Listing, object_id → listing.pk)
      - ServiceOffers  (content_type → ServiceOffer, object_id → service.pk)

    This avoids having separate ReviewForListing, ReviewForService models.
    """
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_given',
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField(blank=True)

    # ContentType generic relation fields
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=36)   # Supports both int and UUID PKs
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['-created_at']
        # Prevent duplicate reviews: one reviewer per target object
        unique_together = ('reviewer', 'content_type', 'object_id')

    def __str__(self):
        return f"{self.rating}★ by {self.reviewer.email}"

    def star_range(self):
        """Helper for templates: returns range(1, 6) for star display."""
        return range(1, 6)
