"""
accounts/models.py

Custom User model + Profile.

CRITICAL: AUTH_USER_MODEL = 'accounts.User' must be set in
settings/base.py BEFORE running any migrations. Changing it
after the first migration requires dropping the database.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import TimeStampedModel


class User(AbstractUser):
    """
    Custom user model.
    We use email as the unique identifier for login
    instead of the default username.
    """
    TIER_UNVERIFIED = 'unverified'
    TIER_STUDENT = 'verified_student'
    TIER_STAFF = 'verified_staff'
    TIER_EXTERNAL = 'verified_external'
    TIER_BUSINESS = 'verified_business'
    TIER_CHOICES = [
        (TIER_UNVERIFIED, 'Unverified'),
        (TIER_STUDENT, 'Verified student'),
        (TIER_STAFF, 'Verified staff'),
        (TIER_EXTERNAL, 'Verified external'),
        (TIER_BUSINESS, 'Verified business'),
    ]

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    matric_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Optional UNN matric number (e.g. 2019/234567). Used for manual student verification.",
    )
    trust_tier = models.CharField(max_length=32, choices=TIER_CHOICES, default=TIER_UNVERIFIED)
    phone_verified = models.BooleanField(default=False)
    external_seller_approved = models.BooleanField(default=False)
    identity_risk_score = models.PositiveSmallIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    is_suspended = models.BooleanField(default=False)
    suspension_reason = models.TextField(blank=True)

    # Switch login field from username → email
    USERNAME_FIELD = 'email'
    # username is still required for display purposes
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if self.is_verified and self.trust_tier == self.TIER_UNVERIFIED:
            self.trust_tier = self.TIER_STUDENT
            update_fields = kwargs.get('update_fields')
            if update_fields is not None:
                kwargs['update_fields'] = set(update_fields) | {'trust_tier'}
        super().save(*args, **kwargs)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email


class Profile(TimeStampedModel):
    """
    Extended user profile — auto-created via signal when User is saved.
    Never create Profile manually; it is always paired 1:1 with a User.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    bio = models.TextField(blank=True)
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
    )
    department = models.CharField(max_length=100, blank=True)
    level = models.CharField(
        max_length=10,
        blank=True,
        help_text="e.g. 300L",
    )

    # Cached aggregates — updated via signal in reviews/signals.py
    # Caching avoids expensive DB aggregation on every profile page load
    avg_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
    )
    total_reviews = models.PositiveIntegerField(default=0)
    student_id_verified = models.BooleanField(default=False)
    successful_transactions = models.PositiveIntegerField(default=0)
    response_rate = models.PositiveSmallIntegerField(default=0)
    trust_score = models.PositiveSmallIntegerField(default=20)
    trusted_seller = models.BooleanField(default=False)
    top_rated_seller = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile of {self.user.email}"

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def badges(self):
        badges = []
        if self.user.is_verified:
            badges.append(('verified-student', 'Verified Student'))
        if self.trusted_seller:
            badges.append(('trusted-seller', 'Trusted Seller'))
        if self.top_rated_seller:
            badges.append(('top-rated-seller', 'Top Rated Seller'))
        return badges
