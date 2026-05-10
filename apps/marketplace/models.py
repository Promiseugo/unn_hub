from django.db import models
from django.conf import settings
from django.urls import reverse
from apps.core.models import BaseListingModel


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=10, blank=True, help_text="Emoji icon e.g. 👕")

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

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

    class Meta:
        verbose_name_plural = 'Sub Categories'
        ordering = ['name']
        unique_together = ('category', 'slug')

    def __str__(self):
        return f"{self.category.name} → {self.name}"


class Listing(BaseListingModel):
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('like_new', 'Like New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
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
        default='good',
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

    class Meta:
        ordering = ['-created_at']

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
