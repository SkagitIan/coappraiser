import io
import json
import zipfile
import tempfile
from pathlib import Path
from unittest.mock import patch
from django.contrib.auth.models import User
from types import SimpleNamespace
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from .llm_client import LLMConfigurationError, run_llm_json
from .ai_review import SYSTEM_PROMPT, _finding_topic, run_preflight_ai_review
from .evaluation import score_gpt_findings
from .management.commands.evaluate_gpt56 import Command as EvaluateGPT56Command
from .models import AIExecution, PreflightReview, ReviewFile, ReviewFinding
from .services import (
    build_workfile_record,
    compare_cross_source_observations,
    normalize_pdf_observations,
    run_deterministic_review,
    safe_zip_members,
)
from .uad36 import import_uad_archive, inspect_uad_xml, normalize_uad36


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

    def test_uad_xml_inspection_handles_namespaces_without_guessing_fields(self):
        xml = b"""<?xml version="1.0"?>
        <m:MESSAGE xmlns:m="http://www.mismo.org/residential/2009/schemas"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.mismo.org/residential/2009/schemas MISMO_3.6.xsd">
          <m:DEAL_SETS><m:DEAL_SET><m:DEALS><m:DEAL /></m:DEALS></m:DEAL_SET></m:DEAL_SETS>
        </m:MESSAGE>"""
        profile = inspect_uad_xml(xml)
        self.assertTrue(profile["parseable"])
        self.assertEqual(profile["root_tag"], "MESSAGE")
        self.assertTrue(profile["likely_mismo_3_6"])
        self.assertEqual(profile["local_tag_counts"]["DEAL"], 1)
        self.assertIn("MESSAGE/DEAL_SETS/DEAL_SET/DEALS/DEAL", profile["sample_paths"])

    def test_uad_xml_inspection_rejects_entity_declarations(self):
        profile = inspect_uad_xml(b'<!DOCTYPE x [<!ENTITY risky "value">]><MESSAGE>&risky;</MESSAGE>')
        self.assertFalse(profile["parseable"])
        self.assertIn("entity declarations", profile["parse_error"])

    def test_uad36_normalizer_limits_values_to_subject_property(self):
        xml = b"""<?xml version="1.0"?>
        <MESSAGE xmlns="http://www.mismo.org/residential/2009/schemas"
                 MISMOReferenceModelIdentifier="3.6.0366">
          <PROPERTIES>
            <PROPERTY ValuationUseType="SubjectProperty">
              <ADDITIONAL_ADDRESSES><ADDITIONAL_ADDRESS><AddressLineText>PO Box 1</AddressLineText></ADDITIONAL_ADDRESS></ADDITIONAL_ADDRESSES>
              <ADDRESS><AddressLineText>123 Subject St</AddressLineText><AddressUnitDesignatorType>Unit</AddressUnitDesignatorType><AddressUnitIdentifier>4B</AddressUnitIdentifier><CityName>Testville</CityName></ADDRESS>
              <STRUCTURE>
                <CONSTRUCTION><ConstructionMethodType>SiteBuilt</ConstructionMethodType></CONSTRUCTION>
                <UNIT><UnitStandardAboveGradeFinishedAreaMeasure AreaUnitOfMeasureType="SquareFeet">1840</UnitStandardAboveGradeFinishedAreaMeasure></UNIT>
                <PROPERTY_DETAIL><OverallConditionRatingCode>C3</OverallConditionRatingCode><OverallQualityRatingCode>Q4</OverallQualityRatingCode></PROPERTY_DETAIL>
                <UnitValuationCommentText>Well maintained with typical wear.</UnitValuationCommentText>
              </STRUCTURE>
            </PROPERTY>
            <PROPERTY ValuationUseType="SalesComparable">
              <ADDRESS><AddressLineText>999 Comparable Ave</AddressLineText></ADDRESS>
              <PROPERTY_DETAIL><OverallConditionRatingCode>C5</OverallConditionRatingCode></PROPERTY_DETAIL>
            </PROPERTY>
          </PROPERTIES>
          <VALUATION_REPORT><SalesComparisonCommentDescription>Three sales were analyzed.</SalesComparisonCommentDescription></VALUATION_REPORT>
        </MESSAGE>"""
        observations = normalize_uad36(xml)
        by_field = {}
        for item in observations:
            by_field.setdefault(item["field_code"], []).append(item)
        self.assertEqual(by_field["subject.address.line"][0]["value"], "123 Subject St")
        self.assertEqual(by_field["subject.address.full"][0]["value"], "123 Subject St, Unit 4B")
        self.assertEqual(by_field["subject.condition"][0]["value"], "C3")
        self.assertEqual(by_field["subject.quality"][0]["value"], "Q4")
        self.assertEqual(by_field["areas.above_grade_gla"][0]["value"], "1840")
        self.assertEqual(by_field["comparables.count"][0]["value"], "1")
        self.assertEqual(by_field["narrative.sales_comparison"][0]["value"], "Three sales were analyzed.")
        self.assertNotIn("999 Comparable Ave", json.dumps(observations))
        self.assertIn("PROPERTY[@ValuationUseType='SubjectProperty']", by_field["subject.condition"][0]["source_location"])

    def test_uad36_pdf_normalizer_preserves_page_locations(self):
        text = """[CoAppraiser PDF page 1]
        Appendix D-1 cover
        [CoAppraiser PDF page 2]
        Physical Address 123 Subject St
        Overall Quality Q4
        Overall Condition C3
        Finished Above Grade 1,840 Sq. Ft.
        """
        observations = normalize_pdf_observations(text, "sample.pdf")
        by_field = {item["field_code"]: item for item in observations}
        self.assertEqual(by_field["subject.address.line"]["value"], "123 Subject St")
        self.assertEqual(by_field["subject.address.full"]["value"], "123 Subject St")
        self.assertEqual(by_field["subject.condition"]["value"], "C3")
        self.assertEqual(by_field["subject.quality"]["value"], "Q4")
        self.assertEqual(by_field["areas.above_grade_gla"]["value"], "1,840")
        self.assertEqual(by_field["subject.condition"]["source_location"], "PDF: sample.pdf, page 2")

    def test_uad36_pdf_normalizer_repairs_split_cooperative_address(self):
        text = """[CoAppraiser PDF page 4]
        Subject Property
        Physical Address 7 00 1st Ave, NW
        U
        nit 1206
        """
        observations = normalize_pdf_observations(text, "coop.pdf")
        by_field = {item["field_code"]: item for item in observations}
        self.assertEqual(by_field["subject.address.line"]["value"], "700 1st Ave, NW")
        self.assertEqual(by_field["subject.address.full"]["value"], "700 1st Ave, NW, Unit 1206")

    def test_pure_cross_source_comparison_returns_only_changed_rule(self):
        observations = [
            {
                "field_code": "subject.condition",
                "value": "C4",
                "normalized_value": "c4",
                "source_kind": "xml",
                "source_location": "XML path: subject condition",
            },
            {
                "field_code": "subject.condition",
                "value": "C3",
                "normalized_value": "c3",
                "source_kind": "pdf",
                "source_location": "PDF: report.pdf, page 2",
            },
            {
                "field_code": "subject.quality",
                "value": "Q4",
                "normalized_value": "q4",
                "source_kind": "xml",
                "source_location": "XML path: subject quality",
            },
            {
                "field_code": "subject.quality",
                "value": "Q4",
                "normalized_value": "q4",
                "source_kind": "pdf",
                "source_location": "PDF: report.pdf, page 2",
            },
        ]
        differences = compare_cross_source_observations(observations)
        self.assertEqual([item["rule_code"] for item in differences], ["CROSS_SOURCE_SUBJECT_CONDITION"])
        self.assertEqual(differences[0]["pdf_location"], "PDF: report.pdf, page 2")

    def test_gpt_evaluation_scores_topics_citations_and_boundaries(self):
        case = {
            "required_topics": ["visual_condition"],
            "allowed_topics": ["visual_condition"],
            "max_findings": 1,
        }
        finding = {
            "rule_code": "AI_VISUAL_DEFECT",
            "title": "Exterior defect needs reconciliation",
            "observed": "A visible exterior defect may not align with the report.",
            "location": "rear_exterior.jpg",
            "evidence": ["rear_exterior.jpg shows a visibly unfinished wall section."],
            "why_it_matters": "The report and exhibit should tell the same story.",
            "recommended_action": "Confirm the exhibit and reconcile the report commentary.",
            "guidance": ["Appraiser judgment is required."],
            "visual_sources": ["rear_exterior.jpg"],
        }
        score = score_gpt_findings([finding], case)
        self.assertTrue(score["passed"])
        self.assertEqual(score["topic_precision"], 1.0)
        self.assertEqual(score["topic_recall"], 1.0)

        prohibited = {**finding, "recommended_action": "Apply a $10,000 adjustment."}
        failed_score = score_gpt_findings([prohibited], case)
        self.assertFalse(failed_score["passed"])
        self.assertTrue(failed_score["boundary_failures"])

    def test_gpt_evaluation_prefers_comparable_topic_when_rendered_pdf_is_visual_source(self):
        case = {
            "required_topics": ["comparable_commentary"],
            "allowed_topics": ["comparable_commentary"],
            "max_findings": 1,
        }
        finding = {
            "rule_code": "COMP_COMMENTARY",
            "title": "Condition differences for Comps 2 and 3 are not addressed",
            "observed": "The comparable grid reports differences that the commentary does not reconcile.",
            "location": "report.pdf, page 2",
            "evidence": ["The grid and comparable commentary differ."],
            "why_it_matters": "The comparable analysis is unclear.",
            "recommended_action": "Review the comparable commentary.",
            "guidance": ["Appraiser judgment is required."],
            "visual_sources": ["report.pdf"],
        }
        score = score_gpt_findings([finding], case)
        self.assertTrue(score["passed"])
        self.assertEqual(score["actual_topics"], ["comparable_commentary"])

    def test_finding_topic_prefers_specific_comparable_commentary(self):
        self.assertEqual(
            _finding_topic(
                "Condition difference is acknowledged for only one comparable",
                "The commentary does not address two comparable condition differences.",
            ),
            "comparable_commentary",
        )

    def test_ai_review_protocol_checks_comparable_grid_without_forcing_a_finding(self):
        self.assertIn(
            "compare material facts and reported differences in the comparable grid",
            SYSTEM_PROMPT,
        )
        self.assertIn("Do not force a finding in any step.", SYSTEM_PROMPT)
        self.assertIn("Missing commentary alone is not a finding", SYSTEM_PROMPT)

    def test_eval_importer_builds_local_manifest_and_pairs_pdf_with_xml(self):
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "appendix-d-1.zip"
            destination = Path(directory) / "corpus"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr(
                    "Scenario 01/Sample Report.xml",
                    '<MESSAGE xmlns="http://www.mismo.org/residential/2009/schemas" version="3.6"/>',
                )
                archive.writestr("Scenario 01/Sample Report.pdf", b"%PDF-1.4 synthetic")
                archive.writestr("Scenario 01/matrix.xlsx", b"synthetic")
            manifest = import_uad_archive(archive_path, destination)
            self.assertEqual(manifest["summary"]["candidate_pairs"], 1)
            self.assertEqual(manifest["summary"]["xml_files"], 1)
            self.assertTrue(Path(manifest["manifest_path"]).is_file())
            self.assertTrue((Path(manifest["destination"]) / "Scenario 01" / "Sample Report.xml").is_file())

    def test_eval_importer_recurses_through_scenario_archives(self):
        with tempfile.TemporaryDirectory() as directory:
            nested_stream = io.BytesIO()
            with zipfile.ZipFile(nested_stream, "w") as nested:
                nested.writestr(
                    "SF5_Appraisal.xml",
                    '<MESSAGE xmlns="http://www.mismo.org/residential/2009/schemas" version="3.6"/>',
                )
                nested.writestr("SF5_Appraisal.pdf", b"%PDF-1.4 synthetic")
            archive_path = Path(directory) / "appendix-d-1.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("Appendix D-1 SF5_Appraisal.zip", nested_stream.getvalue())
            manifest = import_uad_archive(archive_path, Path(directory) / "corpus")
            self.assertEqual(manifest["summary"]["nested_archives"], 1)
            self.assertEqual(manifest["summary"]["xml_files"], 1)
            self.assertEqual(manifest["summary"]["candidate_pairs"], 1)
            extracted = Path(manifest["destination"]) / "Appendix D-1 SF5_Appraisal" / "SF5_Appraisal.xml"
            self.assertTrue(extracted.is_file())

    def test_eval_importer_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "unsafe.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("../outside.xml", "<MESSAGE />")
            with self.assertRaisesMessage(ValueError, "unsafe path"):
                import_uad_archive(archive_path, Path(directory) / "corpus")

    def test_eval_importer_rejects_unreviewed_archive_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "different.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("scenario.xml", "<MESSAGE />")
            with self.assertRaisesMessage(ValueError, "does not match"):
                import_uad_archive(
                    archive_path,
                    Path(directory) / "corpus",
                    source={"archive_sha256": "0" * 64},
                )

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

    def test_dashboard_uses_first_review_dropzone_then_full_width_queue(self):
        empty_dashboard = self.client.get(reverse("preflight:dashboard"))
        self.assertContains(empty_dashboard, "Drop your completed appraisal package here to run your first Preflight")
        self.assertContains(empty_dashboard, 'data-first-review-form')
        self.assertNotContains(empty_dashboard, "Quick actions")
        self.assertNotContains(empty_dashboard, "How it works")

        PreflightReview.objects.create(
            user=self.user,
            title="Long residential appraisal package filename",
            subject_identifier="12345 Example Avenue · Client file 2026-001",
            status="completed",
        )
        populated_dashboard = self.client.get(reverse("preflight:dashboard"))
        self.assertNotContains(populated_dashboard, "Drop your completed appraisal package here")
        self.assertContains(populated_dashboard, "Long residential appraisal package filename")
        self.assertContains(populated_dashboard, "12345 Example Avenue")
        create_href = f'href="{reverse("preflight:create")}"'.encode()
        self.assertEqual(populated_dashboard.content.count(create_href), 1)

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
                    "confidence": "high",
                    "visual_sources": ["report.pdf"],
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
                    "confidence": "medium",
                    "visual_sources": [],
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
                    "confidence": "high",
                    "visual_sources": [],
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

    def test_ai_boundary_filter_suppresses_valuation_directive(self):
        review = PreflightReview.objects.create(user=self.user, title="Boundary test")
        version = review.versions.create(number=1, status="uploaded")
        ReviewFile.objects.create(
            version=version,
            original_name="report.pdf",
            kind="pdf",
            sha256="pdf",
            extracted_text="Condition evidence is supplied.",
        )
        response = {
            "summary": "Review complete.",
            "findings": [
                {
                    "rule_code": "AI_VALUE_DIRECTIVE",
                    "title": "Adjustment conclusion",
                    "category": "judgment_review",
                    "severity": "warning",
                    "observed": "The comparable differs from the subject.",
                    "location": "report.pdf, page 4",
                    "evidence": ["The grid reports a location difference."],
                    "why_it_matters": "The difference was not reconciled.",
                    "recommended_action": "Apply a $15,000 adjustment to the comparable.",
                    "guidance": [],
                    "confidence": "high",
                    "visual_sources": [],
                }
            ],
            "missing_information": [],
        }
        with patch("apps.preflight.ai_review.run_llm_json", return_value=response):
            execution = run_preflight_ai_review(version)
        self.assertFalse(review.findings.filter(rule_code="AI_VALUE_DIRECTIVE").exists())
        self.assertEqual(
            execution.parsed_response["suppressed_findings"][0]["reason"],
            "The model response crossed a professional-boundary rule.",
        )

    def test_gpt_evaluator_records_execution_failure(self):
        result = EvaluateGPT56Command()._failed_case(
            {"id": "case-id", "required_topics": ["visual_condition"]},
            2,
            RuntimeError("empty structured response"),
        )
        self.assertFalse(result["score"]["passed"])
        self.assertEqual(result["score"]["missing_topics"], ["visual_condition"])
        self.assertEqual(
            result["score"]["execution_error"],
            "empty structured response",
        )

    def test_ai_finding_always_records_judgment_requirement(self):
        review = PreflightReview.objects.create(user=self.user, title="Guidance test")
        version = review.versions.create(number=1, status="uploaded")
        ReviewFile.objects.create(
            version=version,
            original_name="report.pdf",
            kind="pdf",
            sha256="pdf",
            extracted_text="An evidence relationship requires review.",
        )
        response = {
            "summary": "Review complete.",
            "findings": [
                {
                    "rule_code": "AI_SUPPORTED",
                    "title": "Narrative relationship needs review",
                    "category": "judgment_review",
                    "severity": "advisory",
                    "observed": "Two supplied statements may not align.",
                    "location": "report.pdf, page 4",
                    "evidence": ["Statement A differs from statement B."],
                    "why_it_matters": "The report should tell a consistent story.",
                    "recommended_action": "Review the two supplied statements.",
                    "guidance": ["Confirm the source evidence."],
                    "confidence": "medium",
                    "visual_sources": [],
                }
            ],
            "missing_information": [],
        }
        with patch("apps.preflight.ai_review.run_llm_json", return_value=response):
            run_preflight_ai_review(version)
        finding = review.findings.get(rule_code="AI_SUPPORTED")
        self.assertIn("Appraiser judgment is required.", finding.guidance)

    @override_settings(
        COAPPRAISER_LLM_PROVIDER="openai",
        OPENAI_API_KEY="test-key",
        COAPPRAISER_VISUAL_REVIEW_ENABLED=True,
    )
    def test_visual_finding_records_attached_source_and_confidence(self):
        review = PreflightReview.objects.create(user=self.user, title="Visual package")
        version = review.versions.create(number=1, status="uploaded")
        ReviewFile.objects.create(
            version=version,
            file=SimpleUploadedFile("report.pdf", b"%PDF-1.4 synthetic report", content_type="application/pdf"),
            original_name="report.pdf",
            kind="pdf",
            sha256="pdf-hash",
            extracted_text="Subject condition C3. Improvements are well maintained.",
        )
        ReviewFile.objects.create(
            version=version,
            file=SimpleUploadedFile("condition_exhibit.jpg", b"\xff\xd8\xff\xd9", content_type="image/jpeg"),
            original_name="condition_exhibit.jpg",
            kind="image",
            sha256="image-hash",
        )
        ReviewFinding.objects.create(
            review=review,
            version=version,
            rule_code="DETERMINISTIC_CONDITION",
            signature="deterministic-condition",
            title="Condition evidence needs review",
            category="consistency",
            severity="warning",
            observed="The extracted report contains condition evidence.",
            basis="deterministic",
        )
        response = {
            "summary": "A visual-to-narrative relationship needs review.",
            "findings": [
                {
                    "rule_code": "AI_VISUAL_CONDITION",
                    "title": "Condition photo may conflict with maintenance narrative",
                    "category": "judgment_review",
                    "severity": "warning",
                    "observed": "Visible ceiling staining appears in the condition exhibit while the report describes the subject as well maintained.",
                    "location": "condition_exhibit.jpg and report.pdf",
                    "evidence": [
                        "condition_exhibit.jpg: visible ceiling staining",
                        "report.pdf: improvements described as well maintained",
                    ],
                    "why_it_matters": "The photo and narrative may not tell the same condition story.",
                    "recommended_action": "Confirm the visible condition and reconcile the narrative before delivery.",
                    "guidance": ["Appraiser judgment is required."],
                    "confidence": "high",
                    "visual_sources": ["condition_exhibit.jpg"],
                }
            ],
            "missing_information": [],
        }
        with patch("apps.preflight.ai_review.run_llm_json", return_value=response) as mocked_llm:
            execution = run_preflight_ai_review(version)
        finding = review.findings.get(rule_code="AI_VISUAL_CONDITION")
        self.assertEqual(execution.status, "completed")
        self.assertEqual(finding.basis, "ai_visual")
        self.assertEqual(finding.confidence, "high")
        self.assertEqual(finding.visual_sources, ["condition_exhibit.jpg"])
        self.assertFalse(execution.parsed_response["suppressed_findings"])
        context = json.loads(mocked_llm.call_args.kwargs["user_prompt"])
        self.assertEqual(
            {source["file"] for source in context["visual_review"]["sources"]},
            {"report.pdf", "condition_exhibit.jpg"},
        )
        self.assertTrue(mocked_llm.call_args.kwargs["multimodal_inputs"])
        self.assertNotIn("base64", json.dumps(execution.input_snapshot))

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

    def test_public_positioning_and_removed_legacy_routes(self):
        home = self.client.get(reverse("home"))
        self.assertContains(home, "Terms &amp; Conditions")
        self.assertContains(home, "All rights reserved")
        self.assertContains(home, "all 12 paired PDF/XML scenarios")
        pricing = self.client.get(reverse("pricing"))
        self.assertContains(pricing, "$59/month")
        self.assertContains(pricing, "First Review Free")
        self.assertContains(pricing, "Supported UAD 3.6 XML normalization")
        self.assertContains(pricing, "GPT-5.6 review of selected report pages and photos")
        self.assertNotContains(pricing, "Screen, support, document, and defend")
        login = self.client.get(reverse("login"))
        signup = self.client.get(reverse("accounts:signup"))
        self.assertContains(login, "Find what the reviewer will find")
        self.assertContains(signup, "First Review Free")
        self.assertContains(login, "Selected visual review")
        self.assertContains(signup, "Traceable decisions")
        self.assertNotContains(signup, "UAD 3.6 triggers")
        self.assertContains(self.client.get(reverse("preflight_demo:landing")), "First Review Free")
        self.assertContains(self.client.get(reverse("contact")), "CoAppraiser Preflight")
        terms = self.client.get(reverse("terms"))
        self.assertContains(terms, "AI-assisted technology and output limitations")
        self.assertContains(terms, "Appraiser judgment is required")
        self.assertContains(terms, "Terms &amp; Conditions")
        faq = self.client.get(reverse("faq"))
        self.assertEqual(faq.content.count(b"<details>"), 20)
        self.assertContains(faq, "Before you run your first Preflight")
        self.assertContains(faq, "Does it replace TOTAL, ACI, ClickFORMS")
        self.assertContains(faq, "uses GPT-5.6 to visually review the rendered report")
        self.assertContains(faq, "How do you measure whether Preflight works?")
        self.assertContains(faq, "resolve, defer, or mark a finding not applicable")
        self.assertNotContains(faq, "dismiss a finding")
        self.assertEqual(self.client.get("/solutions/uad-36-compliance-copilot/").status_code, 404)
        self.assertEqual(self.client.get("/app/assignments/").status_code, 404)

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
    def test_text_only_gpt56_review_uses_responses_api(self):
        payload = {"summary": "Reviewed", "findings": [], "missing_information": []}
        with patch("openai.OpenAI") as openai_client:
            create = openai_client.return_value.responses.create
            create.return_value = SimpleNamespace(
                output_text=json.dumps(payload),
                id="resp_test",
                model="gpt-5.6",
                usage=SimpleNamespace(
                    model_dump=lambda: {"input_tokens": 120, "output_tokens": 30, "total_tokens": 150}
                ),
            )
            result = run_llm_json(system_prompt="Return JSON", user_prompt="Evidence", schema_name="preflight_review", required_keys=payload.keys())
        self.assertEqual(result, payload)
        self.assertEqual(result.response_metadata["response_id"], "resp_test")
        self.assertEqual(result.response_metadata["usage"]["total_tokens"], 150)
        self.assertEqual(result.response_metadata["attempts"], 1)
        request = create.call_args.kwargs
        self.assertEqual(request["model"], "gpt-5.6")
        self.assertEqual(request["reasoning"], {"effort": "xhigh"})
        self.assertFalse(request["store"])
        self.assertNotIn("temperature", request)
        self.assertEqual(request["text"]["format"]["type"], "json_schema")
        self.assertEqual(request["input"][0]["content"], [{"type": "input_text", "text": "Evidence"}])
        self.assertEqual(request["timeout"], 60)
        openai_client.return_value.chat.completions.create.assert_not_called()

    @override_settings(
        COAPPRAISER_LLM_PROVIDER="openai",
        COAPPRAISER_LLM_MODEL="gpt-5.6",
        OPENAI_API_KEY="test-key",
    )
    def test_responses_api_retries_once_after_invalid_structured_output(self):
        payload = {"summary": "Reviewed", "findings": [], "missing_information": []}
        with patch("openai.OpenAI") as openai_client:
            create = openai_client.return_value.responses.create
            create.side_effect = [
                SimpleNamespace(output_text="", status="incomplete"),
                SimpleNamespace(
                    output_text=json.dumps(payload),
                    id="resp_retry",
                    model="gpt-5.6",
                ),
            ]
            result = run_llm_json(
                system_prompt="Return JSON",
                user_prompt="Evidence",
                schema_name="preflight_review",
                required_keys=payload.keys(),
            )
        self.assertEqual(result, payload)
        self.assertEqual(result.response_metadata["attempts"], 2)
        self.assertEqual(create.call_count, 2)

    @override_settings(
        COAPPRAISER_LLM_PROVIDER="openai",
        COAPPRAISER_LLM_MODEL="gpt-5.6",
        OPENAI_API_KEY="test-key",
        COAPPRAISER_REASONING_EFFORT="xhigh",
        COAPPRAISER_MULTIMODAL_TIMEOUT_SECONDS=180,
    )
    def test_gpt56_multimodal_review_uses_responses_api_and_xhigh_reasoning(self):
        payload = {"summary": "Reviewed", "findings": [], "missing_information": []}
        visual_input = {
            "type": "input_image",
            "image_url": "data:image/jpeg;base64,dGVzdA==",
            "detail": "high",
        }
        with patch("openai.OpenAI") as openai_client:
            create = openai_client.return_value.responses.create
            create.return_value = SimpleNamespace(output_text=json.dumps(payload))
            result = run_llm_json(
                system_prompt="Return JSON",
                user_prompt="Evidence",
                schema_name="preflight_review",
                required_keys=payload.keys(),
                multimodal_inputs=[visual_input],
            )
        self.assertEqual(result, payload)
        request = create.call_args.kwargs
        self.assertEqual(request["model"], "gpt-5.6")
        self.assertEqual(request["reasoning"], {"effort": "xhigh"})
        self.assertFalse(request["store"])
        self.assertEqual(request["text"]["format"]["type"], "json_schema")
        self.assertEqual(request["input"][0]["content"][1], visual_input)
        self.assertNotIn("temperature", request)
        openai_client.return_value.chat.completions.create.assert_not_called()

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
        self.assertTrue(any(item["kind"] == "warning" and item["title"] == "Model review unavailable" for item in events))
        self.assertTrue(review.versions.first().files.exists())
        self.assertTrue(review.findings.filter(basis="deterministic").exists())
