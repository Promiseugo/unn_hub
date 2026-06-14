from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.services.models import ServiceCategory, ServiceOffer
from apps.trust.models import SafetyAcknowledgement


class ServicesViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="provider1",
            email="provider1@example.com",
            password="ComplexPass123!",
        )
        self.category = ServiceCategory.objects.create(name="Tutoring", slug="tutoring")
        self.viewer = User.objects.create_user(
            username="serviceviewer",
            email="serviceviewer@example.com",
            password="ComplexPass123!",
        )
        for user in (self.user, self.viewer):
            user.is_verified = True
            user.save(update_fields=["is_verified"])
            SafetyAcknowledgement.objects.create(user=user)
        self.offer = ServiceOffer.objects.create(
            provider=self.user,
            category=self.category,
            title="Chemistry Tutorials",
            description="Exam-focused classes",
            price="7000",
            price_label="per class",
            delivery_mode="physical",
        )

    def test_authenticated_user_can_create_service_offer(self):
        self.client.force_login(self.user)
        initial_count = ServiceOffer.objects.count()

        response = self.client.post(
            reverse("services:service-create"),
            {
                "title": "Math Tutoring",
                "description": "Linear algebra and calculus support",
                "price": "5000",
                "price_label": "per session",
                "category": self.category.pk,
                "delivery_mode": "physical",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ServiceOffer.objects.count(), initial_count + 1)
        offer = ServiceOffer.objects.order_by("-created_at").first()
        self.assertEqual(offer.provider, self.user)
        self.assertEqual(offer.category, self.category)

    def test_service_view_count_increments_once_per_session(self):
        self.client.force_login(self.viewer)
        detail_url = reverse("services:service-detail", kwargs={"pk": self.offer.pk})

        first = self.client.get(detail_url)
        self.assertEqual(first.status_code, 200)
        self.offer.refresh_from_db(fields=["view_count"])
        self.assertEqual(self.offer.view_count, 1)

        second = self.client.get(detail_url)
        self.assertEqual(second.status_code, 200)
        self.offer.refresh_from_db(fields=["view_count"])
        self.assertEqual(self.offer.view_count, 1)
