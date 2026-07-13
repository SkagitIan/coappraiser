from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class AccountTests(TestCase):
    def test_signup_creates_authenticated_user(self):
        response = self.client.post(reverse("accounts:signup"), {"username": "new-user", "email": "new@example.com", "password": "safe-pass-123"})
        self.assertRedirects(response, reverse("assignments:dashboard"))
        self.assertTrue(User.objects.filter(username="new-user").exists())
    def test_login_page_is_available(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)
