from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from apps.assignments.models import Assignment
from apps.workfile.models import OutputArtifact, VerificationItem
from .models import AIActionLog
from .services.skill_loader import load_skill
from .services.file_tools import analyze_csv
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile

class RevisionWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("owner", password="pass12345")
        self.assignment = Assignment.objects.create(user=self.user, title="Revision test")
        self.client.login(username="owner", password="pass12345")
    def test_skill_loader_reads_markdown_skill(self):
        self.assertEqual(load_skill("revision-response")["slug"], "revision-response")
    def test_revision_submission_persists_action_artifact_and_items(self):
        response = self.client.post(reverse("ai_tools:generate_revision", args=[self.assignment.pk]), {"revision_request":"Please support the GLA adjustment.", "report_excerpt":"", "appraiser_notes":""}, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AIActionLog.objects.count(), 1)
        self.assertEqual(OutputArtifact.objects.count(), 1)
        self.assertGreater(VerificationItem.objects.count(), 0)
    def test_artifact_approval_is_owner_scoped(self):
        artifact = OutputArtifact.objects.create(assignment=self.assignment, title="Draft", artifact_type="revision_response")
        response = self.client.post(reverse("ai_tools:approve_artifact", args=[artifact.pk]), HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        artifact.refresh_from_db()
        self.assertEqual(artifact.approval_status, "approved")
    def test_artifact_edit_preserves_original_content(self):
        original = {"draft_response": "Original"}
        artifact = OutputArtifact.objects.create(assignment=self.assignment, title="Draft", artifact_type="revision_response", original_generated_content=original, user_edited_content=original)
        self.client.post(reverse("ai_tools:save_artifact", args=[artifact.pk]), {"draft_response": "Edited"})
        artifact.refresh_from_db()
        self.assertEqual(artifact.original_generated_content["draft_response"], "Original")
        self.assertEqual(artifact.user_edited_content["draft_response"], "Edited")
    def test_uad_issue_submission_persists_artifact(self):
        response = self.client.post(reverse("ai_tools:generate_uad_issue", args=[self.assignment.pk]), {"issue_text": "Field value may be inconsistent."}, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(OutputArtifact.objects.filter(artifact_type="uad_issue_summary").exists())
    def test_market_csv_analyzer_detects_columns(self):
        upload = BytesIO(b"sale_date,sale_price,list_price,dom\n2025-01-01,300000,310000,10\n2025-02-01,320000,325000,8\n")
        upload.name = "sales.csv"
        summary = analyze_csv(upload)
        self.assertEqual(summary["mapping"]["sale_price"], "sale_price")
        self.assertEqual(summary["sale_price"]["count"], 2)
    def test_market_evidence_submission_persists_artifact(self):
        upload = SimpleUploadedFile("sales.csv", b"sale_date,sale_price\n2025-01-01,300000\n", content_type="text/csv")
        response = self.client.post(reverse("ai_tools:generate_market_evidence", args=[self.assignment.pk]), {"csv_file": upload, "appraiser_notes": "Stable segment"}, HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(OutputArtifact.objects.filter(artifact_type="market_evidence_memo").exists())
