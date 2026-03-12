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
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(default=False)

    # Switch login field from username → email
    USERNAME_FIELD = 'email'
    # username is still required for display purposes
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

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

    def __str__(self):
        return f"Profile of {self.user.email}"

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username
