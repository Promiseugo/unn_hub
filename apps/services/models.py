from django.db import models
from django.conf import settings
from django.urls import reverse
from apps.core.models import BaseListingModel


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=10, blank=True, help_text="Emoji icon e.g. 🎨")

    class Meta:
        verbose_name_plural = 'Service Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class ServiceSubCategory(models.Model):
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name='subcategories',
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField()

    class Meta:
        verbose_name_plural = 'Service Sub Categories'
        ordering = ['name']
        unique_together = ('category', 'slug')

    def __str__(self):
        return f"{self.category.name} → {self.name}"


class ServiceOffer(BaseListingModel):
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
    subcategory = models.ForeignKey(
        ServiceSubCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
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
    video = models.FileField(
        upload_to='services/videos/%Y/%m/',
        blank=True,
        null=True,
        help_text="Optional intro video. MP4, MOV or WebM. Max 50MB.",
    )
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def get_absolute_url(self):
        return reverse('services:service-detail', kwargs={'pk': self.pk})
