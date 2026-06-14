from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.messaging.models import Thread
from apps.trust.models import SafetyAcknowledgement


class MessagingViewsTests(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(
            username="sender",
            email="sender@example.com",
            password="ComplexPass123!",
            is_verified=True,
        )
        self.recipient = User.objects.create_user(
            username="receiver",
            email="receiver@example.com",
            password="ComplexPass123!",
        )
        SafetyAcknowledgement.objects.create(user=self.sender)

    def test_new_thread_reuses_existing_conversation(self):
        self.client.force_login(self.sender)
        url = reverse("messaging:new-thread", kwargs={"username": self.recipient.username})

        first = self.client.post(url, {"subject": "Hello", "body": "First message"})
        self.assertEqual(first.status_code, 302)
        self.assertEqual(Thread.objects.count(), 1)

        second = self.client.post(url, {"subject": "Hello again", "body": "Second message"})
        self.assertEqual(second.status_code, 302)
        self.assertEqual(Thread.objects.count(), 1)
