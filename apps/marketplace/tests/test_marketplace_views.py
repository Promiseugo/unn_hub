from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.marketplace.models import Category, Listing
from apps.trust.models import SafetyAcknowledgement


class MarketplaceViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="seller1",
            email="seller1@example.com",
            password="ComplexPass123!",
        )
        self.category = Category.objects.create(
            name="Electronics Test",
            slug="electronics-test",
        )
        self.viewer = User.objects.create_user(
            username="viewer1",
            email="viewer1@example.com",
            password="ComplexPass123!",
        )
        for user in (self.user, self.viewer):
            user.is_verified = True
            user.save(update_fields=["is_verified"])
            SafetyAcknowledgement.objects.create(user=user)
        self.listing = Listing.objects.create(
            seller=self.user,
            category=self.category,
            title="Phone for sale",
            description="Good battery life",
            price="90000",
            condition="used",
            location="Hostel",
        )

    def test_authenticated_user_can_create_listing(self):
        self.client.force_login(self.user)
        initial_count = Listing.objects.count()

        response = self.client.post(
            reverse("marketplace:listing-create"),
            {
                "title": "HP Laptop",
                "description": "Solid condition",
                "price": "250000",
                "category": self.category.pk,
                "condition": "used",
                "location": "Odim",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Listing.objects.count(), initial_count + 1)
        listing = Listing.objects.order_by("-created_at").first()
        self.assertEqual(listing.seller, self.user)
        self.assertEqual(listing.category, self.category)

    def test_listing_view_count_increments_once_per_session(self):
        self.client.force_login(self.viewer)
        detail_url = reverse("marketplace:listing-detail", kwargs={"pk": self.listing.pk})

        first = self.client.get(detail_url)
        self.assertEqual(first.status_code, 200)
        self.listing.refresh_from_db(fields=["view_count"])
        self.assertEqual(self.listing.view_count, 1)

        second = self.client.get(detail_url)
        self.assertEqual(second.status_code, 200)
        self.listing.refresh_from_db(fields=["view_count"])
        self.assertEqual(self.listing.view_count, 1)

    def test_listing_owner_views_are_not_counted(self):
        self.client.force_login(self.user)
        detail_url = reverse("marketplace:listing-detail", kwargs={"pk": self.listing.pk})

        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.listing.refresh_from_db(fields=["view_count"])
        self.assertEqual(self.listing.view_count, 0)

    def test_authenticated_viewer_is_counted_once_across_sessions(self):
        detail_url = reverse("marketplace:listing-detail", kwargs={"pk": self.listing.pk})

        first_client = Client()
        first_client.force_login(self.viewer)
        first = first_client.get(detail_url)
        self.assertEqual(first.status_code, 200)
        self.listing.refresh_from_db(fields=["view_count"])
        self.assertEqual(self.listing.view_count, 1)

        second_client = Client()
        second_client.force_login(self.viewer)
        second = second_client.get(detail_url)
        self.assertEqual(second.status_code, 200)
        self.listing.refresh_from_db(fields=["view_count"])
        self.assertEqual(self.listing.view_count, 1)
