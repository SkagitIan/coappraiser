import io
import zipfile
from pathlib import Path
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from .models import PreflightReview, ReviewFile
from .services import run_deterministic_review, safe_zip_members


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

    def test_zip_upload_extracts_package_members(self):
        fixture = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "preflight" / "01_complete_package.zip"
        package = SimpleUploadedFile("synthetic-package.zip", fixture.read_bytes(), content_type="application/zip")
        response = self.client.post(reverse("preflight:create"), {"title": "ZIP package", "files": [package]})
        self.assertEqual(response.status_code, 302)
        review = PreflightReview.objects.get(user=self.user, title="ZIP package")
        self.assertEqual(review.versions.first().files.count(), 4)
        detail = self.client.get(response.url)
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Extracted evidence")

    def test_cross_source_gla_conflict_creates_evidence_rich_finding(self):
        review = PreflightReview.objects.create(user=self.user, title="Conflict package")
        version = review.versions.create(number=1, status="uploaded")
        ReviewFile.objects.create(version=version, original_name="report.xml", kind="xml", sha256="xml", extracted_text="<report><areas><above_grade_gla>1800</above_grade_gla></areas></report>")
        ReviewFile.objects.create(version=version, original_name="report.pdf", kind="pdf", sha256="pdf", extracted_text="Above-grade GLA: 2000 sq ft")
        ReviewFile.objects.create(version=version, original_name="front.jpg", kind="image", sha256="jpg")
        run_deterministic_review(version)
        finding = review.findings.get(rule_code="CROSS_SOURCE_AREAS_ABOVE_GRADE_GLA")
        self.assertIn("1800", finding.observed)
        self.assertEqual(len(finding.evidence), 2)

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

    def test_file_download_is_authorized_and_review_delete_cleans_records(self):
        xml = SimpleUploadedFile("private.xml", b"<?xml version='1.0'?><report />", content_type="application/xml")
        self.client.post(reverse("preflight:create"), {"title": "Private package", "files": [xml]})
        review = PreflightReview.objects.get(user=self.user)
        review_file = review.versions.first().files.first()
        download = self.client.get(reverse("preflight:download_file", args=[review_file.pk]))
        self.assertEqual(download.status_code, 200)
        b"".join(download.streaming_content)
        download.close()
        self.client.post(reverse("preflight:delete_review", args=[review.pk]))
        self.assertFalse(PreflightReview.objects.filter(pk=review.pk).exists())
