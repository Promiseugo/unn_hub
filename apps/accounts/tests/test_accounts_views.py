from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class AccountsViewsTests(TestCase):
    def test_register_creates_user_and_profile(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "newuser",
                "email": "newuser@unn.edu.ng",
                "first_name": "New",
                "last_name": "User",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="newuser@unn.edu.ng")
        self.assertTrue(hasattr(user, "profile"))

    def test_login_accepts_email_case_insensitively(self):
        user = User.objects.create_user(
            username="caseuser",
            email="caseuser@example.com",
            password="ComplexPass123!",
        )

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "CASEUSER@EXAMPLE.COM", "password": "ComplexPass123!"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
