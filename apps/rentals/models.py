import uuid
from django.db import models
from django.conf import settings
from django.urls import reverse
from apps.core.models import TimeStampedModel


class RentalListing(TimeStampedModel):
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

    LISTING_TYPE_CHOICES = [
        ('offering', 'Room / Space Available'),
        ('seeking',  'Roommate Wanted'),
    ]

    RENTAL_TYPE_CHOICES = [
        ('room',         'Single Room'),
        ('self_contain', 'Self Contain'),
        ('flat',         'Flat / Apartment'),
        ('hostel',       'Hostel Space'),
        ('roommate',     'Roommate Needed'),
    ]

    RENTAL_PERIOD_CHOICES = [
        ('monthly',    'Per Month'),
        ('semester',   'Per Semester'),
        ('annually',   'Per Year'),
        ('negotiable', 'Negotiable'),
    ]

    GENDER_CHOICES = [
        ('any',    'Any Gender'),
        ('male',   'Male Only'),
        ('female', 'Female Only'),
    ]

    AMENITY_CHOICES = [
        ('water',    'Running Water'),
        ('light',    'Electricity (NEPA)'),
        ('security', 'Security'),
        ('wifi',     'WiFi'),
        ('kitchen',  'Kitchen'),
        ('bathroom', 'Private Bathroom'),
        ('Private Transformer', 'Private Transformer'),
        ('parking',  'Parking Space'),
        ('borehole', 'Borehole'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rental_listings',
    )

    # NEW: offering a room vs seeking a roommate
    listing_type = models.CharField(
        max_length=10,
        choices=LISTING_TYPE_CHOICES,
        default='offering',
        help_text="Are you offering a room or looking for a roommate?",
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    rental_type = models.CharField(
        max_length=20,
        choices=RENTAL_TYPE_CHOICES,
        default='room',
    )

    price = models.DecimalField(max_digits=10, decimal_places=2)
    rental_period = models.CharField(
        max_length=20,
        choices=RENTAL_PERIOD_CHOICES,
        default='annually',
    )
    # Subsequent / additional payments (agency fee, agreement, later payments)
    subsequent_payment = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Additional payment amount e.g. agency fee or second payment",
    )
    subsequent_payment_note = models.CharField(
        max_length=120, blank=True,
        help_text="e.g. 'agency fee', 'agreement fee', 'then ₦120k subsequently'",
    )

    address = models.CharField(max_length=255, help_text="e.g. No. 5 Odim Road, Nsukka")
    area = models.CharField(max_length=100, blank=True, help_text="e.g. Odim, Hilltop")

    gender_preference = models.CharField(max_length=10, choices=GENDER_CHOICES, default='any')
    available_from = models.DateField(null=True, blank=True)
    rooms_available = models.PositiveSmallIntegerField(default=1)
    amenities = models.CharField(max_length=255, blank=True)

    # Video upload
    video = models.FileField(
        upload_to='rentals/videos/%Y/%m/',
        blank=True,
        null=True,
        help_text="Optional walkthrough video. MP4, MOV or WebM. Max 50MB.",
    )

    is_active = models.BooleanField(default=True)
    is_taken = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
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
        related_name='reviewed_rentals',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Rental Listing'
        verbose_name_plural = 'Rental Listings'
        indexes = [
            models.Index(fields=['is_active', 'is_taken', '-created_at']),
            models.Index(fields=['approval_status', 'risk_score', '-created_at']),
            models.Index(fields=['deleted_at']),
        ]

    def __str__(self):
        return f"{self.get_rental_type_display()} — {self.address}"

    def get_absolute_url(self):
        return reverse('rentals:rental-detail', kwargs={'pk': self.pk})

    def get_amenities_list(self):
        if self.amenities:
            return [a.strip() for a in self.amenities.split(',')]
        return []

    def get_amenities_display_list(self):
        amenity_map = dict(self.AMENITY_CHOICES)
        return [amenity_map.get(a, a) for a in self.get_amenities_list()]

    def primary_image(self):
        img = self.images.filter(is_primary=True).first()
        return img or self.images.first()

    @property
    def is_seeking(self):
        return self.listing_type == 'seeking'


class RentalImage(models.Model):
    rental = models.ForeignKey(RentalListing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='rentals/%Y/%m/')
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.rental.title}"


class RentalInquiry(TimeStampedModel):
    rental = models.ForeignKey(RentalListing, on_delete=models.CASCADE, related_name='inquiries')
    inquirer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rental_inquiries',
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('rental', 'inquirer')

    def __str__(self):
        return f"{self.inquirer.username} → {self.rental.title}"
