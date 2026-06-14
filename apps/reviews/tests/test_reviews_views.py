from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.marketplace.models import Category, Listing
from apps.reviews.models import Review
from apps.trust.models import SafetyAcknowledgement, TrustTransaction


class ReviewsViewsTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller",
            email="seller@example.com",
            password="ComplexPass123!",
        )
        self.reviewer = User.objects.create_user(
            username="reviewer",
            email="reviewer@example.com",
            password="ComplexPass123!",
            is_verified=True,
        )
        SafetyAcknowledgement.objects.create(user=self.reviewer)
        category = Category.objects.create(name="Devices", slug="devices")
        self.listing = Listing.objects.create(
            seller=self.seller,
            category=category,
            title="Calculator",
            description="Scientific calculator",
            price="6000",
            condition="used",
            location="Hilltop",
        )
        TrustTransaction.objects.create(
            buyer=self.reviewer,
            seller=self.seller,
            status=TrustTransaction.STATUS_COMPLETED,
            content_type=ContentType.objects.get_for_model(Listing),
            object_id=str(self.listing.pk),
        )

    def test_duplicate_reviews_are_blocked(self):
        self.client.force_login(self.reviewer)
        url = reverse(
            "reviews:add-review",
            kwargs={
                "app_label": "marketplace",
                "model_name": "listing",
                "object_id": str(self.listing.pk),
            },
        )

        first = self.client.post(url, {"rating": 4, "comment": "Good item"})
        self.assertEqual(first.status_code, 302)
        self.assertEqual(Review.objects.count(), 1)

        second = self.client.post(url, {"rating": 5, "comment": "Another review"})
        self.assertEqual(second.status_code, 302)
        self.assertEqual(Review.objects.count(), 1)

        review = Review.objects.get()
        self.assertEqual(review.content_type, ContentType.objects.get_for_model(Listing))
        self.assertEqual(review.object_id, str(self.listing.pk))

    def test_review_requires_completed_transaction(self):
        outsider = User.objects.create_user(
            username="outsider",
            email="outsider@example.com",
            password="ComplexPass123!",
            is_verified=True,
        )
        SafetyAcknowledgement.objects.create(user=outsider)
        self.client.force_login(outsider)
        url = reverse(
            "reviews:add-review",
            kwargs={
                "app_label": "marketplace",
                "model_name": "listing",
                "object_id": str(self.listing.pk),
            },
        )

        response = self.client.post(url, {"rating": 5, "comment": "Looks good"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Review.objects.count(), 0)
