"""
core/models.py

Abstract base models shared across all apps.
These are NEVER migrated directly — they exist only
to be inherited by concrete models in other apps.
"""

import uuid
from django.db import models


class TimeStampedModel(models.Model):
    """
    Adds created_at and updated_at to any model.
    Inherit from this instead of models.Model wherever you want timestamps.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True  # No DB table is created for this model


class BaseListingModel(TimeStampedModel):
    """
    Common fields shared by Listing (marketplace) and ServiceOffer (services).
    Using UUID primary keys prevents sequential ID enumeration in URLs.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    is_sold = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def __str__(self):
        return self.title
