import io
import zipfile
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from .models import PreflightReview
from .services import safe_zip_members


class PreflightTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("preflight", password="pass12345")
        self.client.login(username="preflight", password="pass12345")

    def test_zip_path_traversal_is_rejected(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr("../secret.txt", "no")
        with self.assertRaisesMessage(ValueError, "unsafe path"):
            safe_zip_members(io.BytesIO(stream.getvalue()))

    def test_upload_creates_review_and_intake_findings(self):
        xml = SimpleUploadedFile("report.xml", b"<?xml version='1.0'?><report />", content_type="application/xml")
        response = self.client.post(reverse("preflight:create"), {"title": "Test package", "subject_identifier": "123 Main", "files": [xml]})
        self.assertEqual(response.status_code, 302)
        review = PreflightReview.objects.get(user=self.user)
        self.assertEqual(review.status, "completed")
        self.assertTrue(review.findings.filter(rule_code="PACKAGE_PDF_MISSING").exists())

    def test_user_cannot_open_another_users_review(self):
        other = User.objects.create_user("other", password="pass12345")
        review = PreflightReview.objects.create(user=other, title="Private")
        response = self.client.get(reverse("preflight:detail", args=[review.pk]))
        self.assertEqual(response.status_code, 404)

    def test_public_positioning_and_deprecated_routes(self):
        pricing = self.client.get(reverse("pricing"))
        self.assertContains(pricing, "$59/month")
        self.assertContains(pricing, "first scan is free")
        self.assertContains(self.client.get(reverse("login")), "Start your free scan")
        self.assertContains(self.client.get(reverse("accounts:signup")), "Your first Preflight scan is free")
        self.assertRedirects(self.client.get(reverse("uad_solution_legacy")), reverse("home"))
