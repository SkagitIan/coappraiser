import io
import json
import zipfile
from pathlib import Path
from unittest.mock import patch
from django.contrib.auth.models import User
from types import SimpleNamespace
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from apps.ai_tools.services.llm_client import LLMConfigurationError, run_llm_json
from .ai_review import run_preflight_ai_review
from .models import AIExecution, PreflightReview, ReviewFile, ReviewFinding
from .services import build_workfile_record, run_deterministic_review, safe_zip_members


class PreflightTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("preflight", password="pass12345")
        self.client.login(username="preflight", password="pass12345")

    def complete_stream(self, review):
        response = self.client.post(reverse("preflight:stream", args=[review.pk]))
        payload = b"".join(response.streaming_content).decode()
        response.close()
        review.refresh_from_db()
        return [json.loads(line) for line in payload.splitlines()]

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
        events = self.complete_stream(review)
        self.assertEqual(events[-1]["kind"], "complete")
        self.assertEqual(review.status, "completed")
        self.assertEqual(review.versions.get().status, "completed")
        self.assertTrue(review.findings.filter(rule_code="PACKAGE_PDF_MISSING").exists())

    def test_zip_upload_extracts_package_members(self):
        fixture = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "preflight" / "01_complete_package.zip"
        package = SimpleUploadedFile("synthetic-package.zip", fixture.read_bytes(), content_type="application/zip")
        response = self.client.post(reverse("preflight:create"), {"title": "ZIP package", "files": [package]})
        self.assertEqual(response.status_code, 302)
        review = PreflightReview.objects.get(user=self.user, title="ZIP package")
        self.assertEqual(review.versions.first().files.count(), 4)
        self.complete_stream(review)
        detail = self.client.get(reverse("preflight:detail", args=[review.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Source evidence")
        self.assertContains(detail, "Review complete")

    def test_ai_review_is_saved_and_adds_interpretation_finding(self):
        fixture = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "preflight" / "01_complete_package.zip"
        package = SimpleUploadedFile("synthetic-ai-package.zip", fixture.read_bytes(), content_type="application/zip")
        response = self.client.post(reverse("preflight:create"), {"title": "AI package", "files": [package]})
        self.assertEqual(response.status_code, 302)
        review = PreflightReview.objects.get(user=self.user, title="AI package")
        events = self.complete_stream(review)
        execution = AIExecution.objects.get(version=review.versions.first())
        self.assertEqual(execution.status, "completed")
        self.assertEqual(execution.provider, "mock")
        self.assertTrue(review.findings.filter(basis="ai_interpretation").exists())
        self.assertTrue(any(item["title"] == "Preflight evidence finding" for item in events))

    def test_ai_failure_does_not_discard_deterministic_findings(self):
        review = PreflightReview.objects.create(user=self.user, title="AI failure")
        version = review.versions.create(number=1, status="uploaded")
        ReviewFile.objects.create(version=version, original_name="report.xml", kind="xml", sha256="xml", extracted_text="<report />")
        ReviewFile.objects.create(version=version, original_name="report.pdf", kind="pdf", sha256="pdf", extracted_text="Subject Identifier: 123")
        with patch("apps.preflight.ai_review.run_llm_json", side_effect=RuntimeError("provider unavailable")):
            run_deterministic_review(version)
        self.assertEqual(review.status, "completed")
        self.assertTrue(review.findings.filter(rule_code="PACKAGE_IMAGES_MISSING").exists())
        self.assertEqual(version.ai_executions.get().status, "failed")

    def test_ai_context_and_duplicate_suppression_keep_novel_finding(self):
        review = PreflightReview.objects.create(user=self.user, title="AI evidence context")
        version = review.versions.create(number=1, status="uploaded")
        ReviewFile.objects.create(
            version=version,
            original_name="report.pdf",
            kind="pdf",
            sha256="pdf",
            extracted_text="Synthetic CoAppraiser Preflight report. This is synthetic test data, not a real appraisal report. Condition: C3",
        )
        ReviewFile.objects.create(version=version, original_name="condition_exhibit.jpg", kind="image", sha256="jpg")
        ReviewFinding.objects.create(
            review=review,
            version=version,
            rule_code="CROSS_SOURCE_SUBJECT_CONDITION",
            signature="condition-conflict",
            title="Condition differs between XML and PDF",
            category="consistency",
            severity="warning",
            observed="XML reports C4 while the PDF reports C3.",
            basis="deterministic",
        )
        response = {
            "summary": "Review complete.",
            "findings": [
                {
                    "rule_code": "AI_CONDITION",
                    "title": "Conflicting subject condition ratings",
                    "category": "consistency",
                    "severity": "critical",
                    "observed": "Condition differs.",
                    "location": "report.pdf",
                    "evidence": ["PDF reports C3."],
                    "why_it_matters": "The report should be internally consistent.",
                    "recommended_action": "Reconcile the condition evidence.",
                    "guidance": ["Appraiser judgment is required."],
                },
                {
                    "rule_code": "AI_ROOF",
                    "title": "Roof leakage needs supporting reconciliation",
                    "category": "judgment_review",
                    "severity": "warning",
                    "observed": "The narrative reports active roof leakage.",
                    "location": "report.pdf addendum",
                    "evidence": ["Observed scenario item: active roof leakage."],
                    "why_it_matters": "The reported defect may affect report consistency.",
                    "recommended_action": "Review the report treatment and available exhibit.",
                    "guidance": ["Appraiser judgment is required."],
                },
                {
                    "rule_code": "AI_DEMO_NOTICE",
                    "title": "Package is explicitly a demonstration fixture",
                    "category": "fix_before_delivery",
                    "severity": "critical",
                    "observed": "The report contains synthetic data notices.",
                    "location": "report.pdf",
                    "evidence": ["Synthetic demonstration fixture."],
                    "why_it_matters": "This is not a live assignment.",
                    "recommended_action": "Replace the demonstration package.",
                    "guidance": ["Appraiser judgment is required."],
                },
            ],
            "missing_information": [],
        }
        with patch("apps.preflight.ai_review.run_llm_json", return_value=response) as mocked_llm:
            execution = run_preflight_ai_review(version)
        context = json.loads(mocked_llm.call_args.kwargs["user_prompt"])
        self.assertTrue(context["review_context"]["synthetic_demo"])
        self.assertIn({"file": "condition_exhibit.jpg", "kind": "image"}, context["file_inventory"])
        self.assertEqual(context["deterministic_findings"][0]["rule_code"], "CROSS_SOURCE_SUBJECT_CONDITION")
        self.assertFalse(review.findings.filter(rule_code="AI_CONDITION").exists())
        self.assertFalse(review.findings.filter(rule_code="AI_DEMO_NOTICE").exists())
        self.assertTrue(review.findings.filter(rule_code="AI_ROOF").exists())
        self.assertEqual(
            {item["topic"] for item in execution.parsed_response["suppressed_findings"]},
            {"condition", "demo_metadata"},
        )

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
        self.assertContains(pricing, "First Review Free")
        self.assertContains(self.client.get(reverse("login")), "Find what the reviewer will find")
        self.assertContains(self.client.get(reverse("accounts:signup")), "First Review Free")
        self.assertContains(self.client.get(reverse("preflight_demo:landing")), "First Review Free")
        self.assertContains(self.client.get(reverse("contact")), "CoAppraiser Preflight")
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

    def test_demo_scenarios_have_predictable_deterministic_outcomes(self):
        demo_dir = Path(__file__).resolve().parents[2] / "demo"
        scenarios = {
            "coappraiser-demo-01-ready.zip": {"PREFLIGHT_BASELINE"},
            "coappraiser-demo-02-reconcile.zip": {
                "CROSS_SOURCE_SUBJECT_CONDITION",
                "XML_NARRATIVE_CONDITION",
                "XML_NARRATIVE_QUALITY",
                "COMPARABLE_COMMENTARY_INCOMPLETE",
            },
            "coappraiser-demo-03-incomplete.zip": {"PACKAGE_XML_MISSING"},
        }
        for index, (filename, expected_codes) in enumerate(scenarios.items(), start=1):
            package = SimpleUploadedFile(filename, (demo_dir / filename).read_bytes(), content_type="application/zip")
            response = self.client.post(reverse("preflight:create"), {"title": f"Demo scenario {index}", "files": [package]})
            self.assertEqual(response.status_code, 302)
            review = PreflightReview.objects.get(title=f"Demo scenario {index}")
            self.complete_stream(review)
            codes = set(review.findings.filter(basis="deterministic").values_list("rule_code", flat=True))
            self.assertEqual(codes, expected_codes)
            detail = self.client.get(reverse("preflight:detail", args=[review.pk]))
            self.assertContains(detail, "Preflight checks")
            self.assertContains(detail, "Preflight evidence review")
            self.assertContains(detail, "You make and document every final appraisal decision")

    def test_decision_note_is_saved_in_workfile_record(self):
        fixture = Path(__file__).resolve().parents[2] / "demo" / "coappraiser-demo-02-reconcile.zip"
        package = SimpleUploadedFile("demo.zip", fixture.read_bytes(), content_type="application/zip")
        self.client.post(reverse("preflight:create"), {"title": "Decision demo", "files": [package]})
        review = PreflightReview.objects.get(title="Decision demo")
        self.complete_stream(review)
        finding = review.findings.filter(basis="deterministic").first()
        response = self.client.post(reverse("preflight:decision", args=[finding.pk]), {"status": "deferred", "note": "Verify the source commentary before delivery."})
        self.assertEqual(response.status_code, 200)
        finding.decision.refresh_from_db()
        self.assertEqual(finding.decision.status, "deferred")
        self.assertEqual(finding.decision.note, "Verify the source commentary before delivery.")
        record = build_workfile_record(review)
        saved = next(item for item in record.snapshot["findings"] if item["rule_code"] == finding.rule_code)
        self.assertEqual(saved["decision_note"], finding.decision.note)
        self.assertTrue(saved["appraiser_judgment_required"])
        self.assertIn("supporting_evidence", saved)

    @override_settings(
        COAPPRAISER_LLM_PROVIDER="openai",
        COAPPRAISER_LLM_MODEL="gpt-5.6",
        OPENAI_API_KEY="test-key",
    )
    def test_gpt5_request_uses_supported_structured_output_parameters(self):
        payload = {"summary": "Reviewed", "findings": [], "missing_information": []}
        with patch("openai.OpenAI") as openai_client:
            create = openai_client.return_value.chat.completions.create
            create.return_value = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))])
            result = run_llm_json(system_prompt="Return JSON", user_prompt="Evidence", schema_name="preflight_review", required_keys=payload.keys())
        self.assertEqual(result, payload)
        request = create.call_args.kwargs
        self.assertEqual(request["model"], "gpt-5.6")
        self.assertNotIn("temperature", request)
        self.assertEqual(request["response_format"]["type"], "json_schema")

    @override_settings(
        DEBUG=False,
        COAPPRAISER_ALLOW_MOCK_AI=False,
        COAPPRAISER_LLM_PROVIDER="mock",
    )
    def test_mock_ai_is_rejected_in_production_configuration(self):
        with self.assertRaisesMessage(LLMConfigurationError, "Mock AI is disabled"):
            run_llm_json(system_prompt="", user_prompt="", schema_name="preflight_review")

    def test_ai_failure_message_confirms_package_state_is_preserved(self):
        fixture = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "preflight" / "01_complete_package.zip"
        package = SimpleUploadedFile("failure-demo.zip", fixture.read_bytes(), content_type="application/zip")
        with patch("apps.preflight.ai_review.run_llm_json", side_effect=RuntimeError("provider unavailable")):
            response = self.client.post(reverse("preflight:create"), {"title": "Failure demo", "files": [package]})
            review = PreflightReview.objects.get(title="Failure demo")
            events = self.complete_stream(review)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(any(item["kind"] == "warning" and item["title"] == "GPT review unavailable" for item in events))
        self.assertTrue(review.versions.first().files.exists())
        self.assertTrue(review.findings.filter(basis="deterministic").exists())
