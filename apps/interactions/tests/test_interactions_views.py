import json

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.interactions.models import Reaction
from apps.marketplace.models import Category, Listing
from apps.trust.models import SafetyAcknowledgement


class InteractionsViewsTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="ComplexPass123!",
        )
        self.other_user = User.objects.create_user(
            username="viewer",
            email="viewer@example.com",
            password="ComplexPass123!",
        )
        for user in (self.owner, self.other_user):
            user.is_verified = True
            user.save(update_fields=["is_verified"])
            SafetyAcknowledgement.objects.create(user=user)
        category = Category.objects.create(name="Books", slug="books")
        self.listing = Listing.objects.create(
            seller=self.owner,
            category=category,
            title="Thermo textbook",
            description="Used textbook",
            price="12000",
            condition="used",
            location="Engineering",
        )

    def test_user_cannot_react_to_own_content(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse(
                "interactions:react",
                kwargs={
                    "app_label": "marketplace",
                    "model_name": "listing",
                    "object_id": str(self.listing.pk),
                },
            ),
            data=json.dumps({"reaction_type": "like"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Reaction.objects.count(), 0)

    def test_user_can_toggle_reaction(self):
        self.client.force_login(self.other_user)
        url = reverse(
            "interactions:react",
            kwargs={
                "app_label": "marketplace",
                "model_name": "listing",
                "object_id": str(self.listing.pk),
            },
        )

        first = self.client.post(
            url,
            data=json.dumps({"reaction_type": "like"}),
            content_type="application/json",
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(Reaction.objects.count(), 1)

        second = self.client.post(
            url,
            data=json.dumps({"reaction_type": "like"}),
            content_type="application/json",
        )
        self.assertEqual(second.status_code, 200)
        self.assertEqual(Reaction.objects.count(), 0)
