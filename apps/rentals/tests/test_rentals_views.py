from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.rentals.models import RentalListing
from apps.trust.models import SafetyAcknowledgement


class RentalsViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="landlord1",
            email="landlord1@example.com",
            password="ComplexPass123!",
        )
        self.viewer = User.objects.create_user(
            username="rentalviewer",
            email="rentalviewer@example.com",
            password="ComplexPass123!",
        )
        for user in (self.user, self.viewer):
            user.is_verified = True
            user.save(update_fields=["is_verified"])
            SafetyAcknowledgement.objects.create(user=user)
        self.rental = RentalListing.objects.create(
            landlord=self.user,
            listing_type="offering",
            title="Room at Hilltop",
            description="Clean room with water",
            rental_type="room",
            price="120000",
            rental_period="annually",
            address="Hilltop Road 14",
            area="Hilltop",
            gender_preference="any",
            rooms_available=1,
            amenities="water,light",
        )

    def test_authenticated_user_can_create_rental_listing(self):
        self.client.force_login(self.user)
        initial_count = RentalListing.objects.count()

        response = self.client.post(
            reverse("rentals:rental-create"),
            {
                "listing_type": "offering",
                "title": "Self-contain near school gate",
                "description": "Clean and spacious",
                "rental_type": "self_contain",
                "price": "180000",
                "rental_period": "annually",
                "address": "No. 10 Odim Road",
                "area": "Odim",
                "gender_preference": "any",
                "rooms_available": "1",
                "amenities": ["water", "light"],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(RentalListing.objects.count(), initial_count + 1)
        listing = RentalListing.objects.order_by("-created_at").first()
        self.assertEqual(listing.landlord, self.user)
        self.assertIn("water", listing.amenities)

    def test_rental_view_count_increments_once_per_session(self):
        self.client.force_login(self.viewer)
        detail_url = reverse("rentals:rental-detail", kwargs={"pk": self.rental.pk})

        first = self.client.get(detail_url)
        self.assertEqual(first.status_code, 200)
        self.rental.refresh_from_db(fields=["view_count"])
        self.assertEqual(self.rental.view_count, 1)

        second = self.client.get(detail_url)
        self.assertEqual(second.status_code, 200)
        self.rental.refresh_from_db(fields=["view_count"])
        self.assertEqual(self.rental.view_count, 1)
