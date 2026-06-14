from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.marketplace.models import Category, Listing
from apps.trust.models import Report, TrustScoreEvent, TrustTransaction
from apps.trust.scoring import update_trust_score


class TrustScoringTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller",
            email="seller@example.com",
            password="ComplexPass123!",
            is_verified=True,
        )
        self.buyer = User.objects.create_user(
            username="buyer",
            email="buyer@example.com",
            password="ComplexPass123!",
            is_verified=True,
        )
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
        self.listing_ct = ContentType.objects.get_for_model(Listing)

    def test_only_actionable_resolved_reports_penalize_trust_score(self):
        baseline = update_trust_score(self.seller)
        Report.objects.create(
            reporter=self.buyer,
            reported_user=self.seller,
            reason=Report.REASON_SCAM,
            details="Suspicious behavior",
            status=Report.STATUS_OPEN,
            content_type=self.listing_ct,
            object_id=str(self.listing.pk),
        )

        self.assertEqual(update_trust_score(self.seller), baseline)

        report = Report.objects.get()
        report.status = Report.STATUS_RESOLVED
        report.is_actionable = True
        report.save(update_fields=["status", "is_actionable", "updated_at"])

        self.assertEqual(update_trust_score(self.seller), baseline - 12)

    def test_completed_transactions_drive_successful_transaction_count(self):
        baseline = update_trust_score(self.seller)
        TrustTransaction.objects.create(
            buyer=self.buyer,
            seller=self.seller,
            status=TrustTransaction.STATUS_COMPLETED,
            content_type=self.listing_ct,
            object_id=str(self.listing.pk),
        )

        new_score = update_trust_score(self.seller, reason="trust_transaction_changed")
        self.seller.profile.refresh_from_db()

        self.assertEqual(self.seller.profile.successful_transactions, 1)
        self.assertEqual(new_score, baseline + 4)
        self.assertTrue(TrustScoreEvent.objects.filter(
            user=self.seller,
            old_score=baseline,
            new_score=new_score,
            reason="trust_transaction_changed",
        ).exists())

    def test_two_sided_confirmation_completes_transaction_and_unlocks_review(self):
        request_url = reverse(
            "trust:request-transaction",
            kwargs={
                "app_label": "marketplace",
                "model_name": "listing",
                "object_id": str(self.listing.pk),
            },
        )
        self.client.force_login(self.buyer)
        response = self.client.post(request_url)
        self.assertEqual(response.status_code, 302)

        transaction = TrustTransaction.objects.get()
        self.assertEqual(transaction.status, TrustTransaction.STATUS_PENDING)

        response = self.client.post(reverse("trust:confirm-transaction", kwargs={"pk": transaction.pk}))
        self.assertEqual(response.status_code, 302)
        transaction.refresh_from_db()
        self.assertIsNotNone(transaction.buyer_confirmed_at)
        self.assertIsNone(transaction.seller_confirmed_at)
        self.assertEqual(transaction.status, TrustTransaction.STATUS_PENDING)

        self.client.force_login(self.seller)
        response = self.client.post(reverse("trust:confirm-transaction", kwargs={"pk": transaction.pk}))
        self.assertEqual(response.status_code, 302)
        transaction.refresh_from_db()

        self.assertIsNotNone(transaction.seller_confirmed_at)
        self.assertEqual(transaction.status, TrustTransaction.STATUS_COMPLETED)
        self.assertTrue(TrustTransaction.completed_for_review(
            reviewer=self.buyer,
            owner=self.seller,
            content_type=self.listing_ct,
            object_id=str(self.listing.pk),
        ))

    def test_disputed_completed_transaction_stops_counting_toward_score(self):
        transaction = TrustTransaction.objects.create(
            buyer=self.buyer,
            seller=self.seller,
            status=TrustTransaction.STATUS_COMPLETED,
            content_type=self.listing_ct,
            object_id=str(self.listing.pk),
            buyer_confirmed_at=timezone.now(),
            seller_confirmed_at=timezone.now(),
            completed_at=timezone.now(),
        )
        completed_score = update_trust_score(self.seller)
        self.client.force_login(self.buyer)

        response = self.client.post(reverse("trust:dispute-transaction", kwargs={"pk": transaction.pk}))

        self.assertEqual(response.status_code, 302)
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, TrustTransaction.STATUS_DISPUTED)
        self.assertEqual(update_trust_score(self.seller), completed_score - 4)
