from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from apps.core.models import BaseListingModel


def default_listing_expiry():
    return timezone.now() + timezone.timedelta(days=30)


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=10, blank=True, help_text="Emoji icon")
    banner_image = models.ImageField(
        upload_to='categories/banners/',
        blank=True,
        null=True,
    )
    is_featured = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=1000)
    seo_title = models.CharField(max_length=160, blank=True)
    seo_description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='subcategories',
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    icon = models.CharField(max_length=10, blank=True, help_text="Emoji icon")
    banner_image = models.ImageField(
        upload_to='subcategories/banners/',
        blank=True,
        null=True,
    )
    is_featured = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=1000)
    seo_title = models.CharField(max_length=160, blank=True)
    seo_description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Sub Categories'
        ordering = ['sort_order', 'name']
        unique_together = ('category', 'slug')

    def __str__(self):
        return f"{self.category.name} → {self.name}"


class Listing(BaseListingModel):
    APPROVAL_PENDING = 'pending'
    APPROVAL_APPROVED = 'approved'
    APPROVAL_REJECTED = 'rejected'
    APPROVAL_FLAGGED = 'flagged'
    APPROVAL_CHOICES = [
        (APPROVAL_PENDING, 'Pending review'),
        (APPROVAL_APPROVED, 'Approved'),
        (APPROVAL_REJECTED, 'Rejected'),
        (APPROVAL_FLAGGED, 'Flagged'),
    ]

    CONDITION_CHOICES = [
        ('brand_new', 'Brand New'),
        ('used', 'Used'),
    ]

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listings',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='listings',
    )
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='listings',
    )
    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='used',
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g. Odim Hostel, Faculty of Engineering",
    )
    video = models.FileField(
        upload_to='listings/videos/%Y/%m/',
        blank=True,
        null=True,
        help_text="Optional. MP4, MOV or WebM. Max 50MB.",
    )
    view_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(default=default_listing_expiry)
    approval_status = models.CharField(
        max_length=16,
        choices=APPROVAL_CHOICES,
        default=APPROVAL_APPROVED,
    )
    risk_score = models.PositiveSmallIntegerField(default=0)
    risk_reasons = models.JSONField(default=list, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_listings',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'is_sold', 'expires_at', '-created_at']),
            models.Index(fields=['category', 'subcategory', '-created_at']),
            models.Index(fields=['condition', '-created_at']),
            models.Index(fields=['approval_status', 'risk_score', '-created_at']),
        ]

    @property
    def is_expired(self):
        return self.expires_at <= timezone.now()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = default_listing_expiry()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('marketplace:listing-detail', kwargs={'pk': self.pk})

    def primary_image(self):
        img = self.images.filter(is_primary=True).first()
        return img or self.images.first()


class ListingImage(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField(upload_to='listings/%Y/%m/')
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.listing.title}"
