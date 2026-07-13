from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Assignment

class AssignmentAccessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("owner", password="pass12345")
        self.other = User.objects.create_user("other", password="pass12345")
    def test_signup_and_assignment_creation(self):
        self.client.login(username="owner", password="pass12345")
        response = self.client.post(reverse("assignments:create"), {"title":"Test assignment", "property_address":"1 Main St"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Assignment.objects.filter(user=self.user, title="Test assignment").exists())
    def test_user_cannot_access_other_assignment(self):
        assignment = Assignment.objects.create(user=self.other, title="Private")
        self.client.login(username="owner", password="pass12345")
        self.assertEqual(self.client.get(reverse("assignments:detail", args=[assignment.pk])).status_code, 404)
    def test_public_legacy_pages_are_wired(self):
        self.assertEqual(self.client.get("/pricing/").status_code, 200)
        self.assertContains(self.client.get("/solutions/workfile-guardian/"), "Workfile")
