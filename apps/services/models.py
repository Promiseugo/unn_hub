from django.db import models
from django.conf import settings
from django.urls import reverse
from apps.core.models import BaseListingModel


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = 'Service Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class ServiceOffer(BaseListingModel):
    """
    Rentals and student jobs are handled as categories here for MVP.
    e.g. ServiceCategory name = 'Room Rental' or 'Part-time Job'
    """
    DELIVERY_CHOICES = [
        ('online', 'Online'),
        ('physical', 'Physical'),
        ('both', 'Both'),
    ]

    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='services',
    )
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='services',
    )
    delivery_mode = models.CharField(
        max_length=20,
        choices=DELIVERY_CHOICES,
        default='physical',
    )
    price_label = models.CharField(
        max_length=50,
        default='per session',
        help_text="e.g. per hour, per session, negotiable",
    )

    class Meta:
        ordering = ['-created_at']

    def get_absolute_url(self):
        return reverse('services:service-detail', kwargs={'pk': self.pk})
