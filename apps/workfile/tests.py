from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from apps.assignments.models import Assignment
from apps.ai_tools.models import AIActionLog

class WorkfileTests(TestCase):
    def test_workfile_requires_login_and_displays_assignment(self):
        user = User.objects.create_user("owner", password="pass12345")
        assignment = Assignment.objects.create(user=user, title="Workfile")
        self.assertEqual(self.client.get(reverse("workfile:detail", args=[assignment.pk])).status_code, 302)
        self.client.login(username="owner", password="pass12345")
        self.assertContains(self.client.get(reverse("workfile:detail", args=[assignment.pk])), "Workfile Guardian")

