import json
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.assignments.models import Assignment, Document
from apps.ai_tools.models import AIActionLog
from apps.workfile.models import OutputArtifact, VerificationItem


class SyntheticCustomerJourneyTests(TestCase):
    def test_admin_dashboard_is_staff_only_and_shows_counts(self):
        user = User.objects.create_user("synthetic-admin", password="pass12345", is_staff=True)
        self.client.login(username="synthetic-admin", password="pass12345")
        response = self.client.get("/admin/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin dashboard")
        self.client.logout()
        user = User.objects.create_user("synthetic-regular", password="pass12345")
        self.client.login(username="synthetic-regular", password="pass12345")
        self.assertEqual(self.client.get("/admin/dashboard/").status_code, 302)

    def test_source_upload_is_saved_and_extracted(self):
        user = User.objects.create_user("synthetic-upload", password="pass12345")
        self.client.login(username="synthetic-upload", password="pass12345")
        assignment = Assignment.objects.create(user=user, title="Synthetic upload assignment")
        response = self.client.post(
            reverse("assignments:detail", args=[assignment.pk]),
            {
                "title": "Reviewer request",
                "document_type": "revision_request",
                "pasted_text": "Please support the GLA adjustment.",
            },
        )
        self.assertEqual(response.status_code, 302)
        document = Document.objects.get(assignment=assignment)
        self.assertEqual(document.pasted_text, "Please support the GLA adjustment.")

    def test_revision_journey_creates_workfile_trail(self):
        user = User.objects.create_user("synthetic-owner", password="pass12345")
        self.client.login(username="synthetic-owner", password="pass12345")
        assignment = Assignment.objects.create(user=user, title="Synthetic GLA assignment")
        response = self.client.post(
            reverse("ai_tools:generate_revision", args=[assignment.pk]),
            {
                "revision_request": "Please provide support for the GLA adjustment.",
                "report_excerpt": "Subject is 1,620 square feet.",
                "appraiser_notes": "Verify paired sales before use.",
            },
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AIActionLog.objects.filter(assignment=assignment).count(), 1)
        self.assertEqual(OutputArtifact.objects.filter(assignment=assignment).count(), 1)
        self.assertGreater(VerificationItem.objects.filter(assignment=assignment).count(), 0)
        self.assertContains(response, "Draft Response")

    def test_other_user_cannot_read_assignment_workflow(self):
        owner = User.objects.create_user("synthetic-owner-2", password="pass12345")
        other = User.objects.create_user("synthetic-other", password="pass12345")
        assignment = Assignment.objects.create(user=owner, title="Private synthetic assignment")
        self.client.login(username="synthetic-other", password="pass12345")
        response = self.client.get(reverse("ai_tools:revision_response", args=[assignment.pk]))
        self.assertEqual(response.status_code, 404)

    def test_market_upload_journey_creates_evidence_artifact(self):
        user = User.objects.create_user("synthetic-market", password="pass12345")
        self.client.login(username="synthetic-market", password="pass12345")
        assignment = Assignment.objects.create(user=user, title="Synthetic market assignment")
        upload = SimpleUploadedFile(
            "synthetic-sales.csv",
            b"sale_date,sale_price,list_price,dom\n2025-01-01,300000,305000,10\n",
            content_type="text/csv",
        )
        response = self.client.post(
            reverse("ai_tools:generate_market_evidence", args=[assignment.pk]),
            {"csv_file": upload, "appraiser_notes": "Stable segment; verify applicability."},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(OutputArtifact.objects.filter(assignment=assignment, artifact_type="market_evidence_memo").exists())
