from django.db import models
from django.conf import settings
from django.urls import reverse
from apps.core.models import BaseListingModel


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=10, blank=True, help_text="Emoji icon")
    banner_image = models.ImageField(
        upload_to='service-categories/banners/',
        blank=True,
        null=True,
    )
    is_featured = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=1000)
    seo_title = models.CharField(max_length=160, blank=True)
    seo_description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Service Categories'
        ordering = ['sort_order', 'name']

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
    icon = models.CharField(max_length=10, blank=True, help_text="Emoji icon")
    banner_image = models.ImageField(
        upload_to='service-subcategories/banners/',
        blank=True,
        null=True,
    )
    is_featured = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=1000)
    seo_title = models.CharField(max_length=160, blank=True)
    seo_description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Service Sub Categories'
        ordering = ['sort_order', 'name']
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
        indexes = [
            models.Index(fields=['is_active', '-created_at']),
            models.Index(fields=['category', 'subcategory', '-created_at']),
            models.Index(fields=['delivery_mode', '-created_at']),
        ]

    def get_absolute_url(self):
        return reverse('services:service-detail', kwargs={'pk': self.pk})
