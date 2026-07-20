from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
import zipfile

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .demo_scenarios import DEMO_SCENARIOS
from .demo_services import DEMO_SESSION_USER_KEY, DEMO_USERNAME_PREFIX
from .models import AIExecution, PreflightReview
from .services import ingest_files


class PublicDemoTests(TestCase):
    def test_controlled_packages_include_same_subject_photos_and_internal_readme(self):
        demo_dir = Path(__file__).resolve().parents[2] / "demo"
        expected_photos = {
            "rear_exterior_condition.jpg",
            "rear_deck_exterior.jpg",
            "covered_deck_exterior.jpg",
            "kitchen_interior.jpg",
            "bathroom_interior.jpg",
        }
        for scenario in DEMO_SCENARIOS.values():
            with zipfile.ZipFile(demo_dir / scenario["filename"]) as archive:
                names = set(archive.namelist())
                self.assertTrue(expected_photos.issubset(names))
                self.assertIn("report.pdf", names)
                self.assertIn("README.txt", names)
                readme = archive.read("README.txt").decode("utf-8")
                self.assertIn("This is a synthetic appraisal package", readme)
                self.assertIn("SYNTHETIC-SUBJECT-001", readme)
                self.assertIn("GPT-5.6 output may vary slightly", readme)
                for photo_name in expected_photos:
                    self.assertNotIn(b"Exif\x00\x00", archive.read(photo_name))

    def _start(self, client, slug):
        landing = client.get(reverse("preflight_demo:landing"))
        self.assertEqual(landing.status_code, 200)
        token = client.session["coappraiser_demo_launch_token"]
        return client.post(
            reverse("preflight_demo:start", args=[slug]),
            {"launch_token": token},
        )

    def _run(self, client, slug):
        start = self._start(client, slug)
        self.assertEqual(start.status_code, 200)
        review = PreflightReview.objects.latest("pk")
        process = client.post(reverse("preflight_demo:process", args=[review.pk]))
        self.assertRedirects(process, reverse("preflight_demo:detail", args=[review.pk]))
        review.refresh_from_db()
        self.assertEqual(review.status, "completed")
        return review

    def test_public_landing_has_three_clear_scenarios_and_no_pricing_prompt(self):
        response = self.client.get(reverse("preflight_demo:landing"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Put a complete appraisal package through Preflight")
        self.assertContains(response, "Drop a package here")
        self.assertContains(response, "Run this Preflight", count=1)
        self.assertContains(response, 'data-scenario="', count=3)
        for slug in DEMO_SCENARIOS:
            self.assertContains(response, reverse("preflight_demo:start", args=[slug]))
        self.assertContains(response, "synthetic, derived evaluation packages")
        self.assertContains(response, "One saved GPT-5.6 result for the exact package hash")
        self.assertContains(response, "No API cost")
        for stage in ["Open", "Trace", "Cross-check", "Decide"]:
            self.assertContains(response, stage)
        self.assertNotContains(response, "Generate clear support")
        self.assertNotContains(response, "use the engine to interpret and respond")
        self.assertNotContains(response, "Pricing")
        self.assertNotContains(response, "Stripe")

    def test_invalid_scenario_is_rejected(self):
        self.client.get(reverse("preflight_demo:landing"))
        token = self.client.session["coappraiser_demo_launch_token"]
        response = self.client.post(
            reverse("preflight_demo:start", args=["not-a-scenario"]),
            {"launch_token": token},
        )
        self.assertEqual(response.status_code, 404)

    def test_consumed_launch_token_cannot_create_duplicate_review(self):
        self.client.get(reverse("preflight_demo:landing"))
        token = self.client.session["coappraiser_demo_launch_token"]
        url = reverse("preflight_demo:start", args=["ready"])
        first = self.client.post(url, {"launch_token": token})
        second = self.client.post(url, {"launch_token": token})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 400)
        self.assertEqual(PreflightReview.objects.count(), 1)

    def test_each_fixture_creates_fresh_review_with_expected_findings(self):
        for slug, scenario in DEMO_SCENARIOS.items():
            review = self._run(self.client, slug)
            version = review.versions.get(number=1)
            codes = set(version.findings.filter(basis="deterministic").values_list("rule_code", flat=True))
            self.assertEqual(codes, scenario["expected_codes"])
            self.assertEqual(version.package_hash.__len__(), 64)
            self.assertTrue(version.files.exists())
            execution = AIExecution.objects.get(version=version)
            self.assertEqual(execution.provider, "openai")
            self.assertEqual(execution.model_name, "gpt-5.6")
            self.assertEqual(execution.status, "completed")
            self.assertTrue(execution.parsed_response["_demo_snapshot"])

    def test_demo_calls_normal_intake_service(self):
        with patch("apps.preflight.demo_services.ingest_files", wraps=ingest_files) as intake:
            review = self._run(self.client, "reconcile")
        intake.assert_called_once()
        self.assertGreaterEqual(review.versions.get().files.count(), 5)

    def test_repeated_process_request_does_not_duplicate_review_data(self):
        review = self._run(self.client, "reconcile")
        version = review.versions.get()
        counts = (version.files.count(), version.findings.count(), version.ai_executions.count())
        response = self.client.post(reverse("preflight_demo:process", args=[review.pk]))
        self.assertRedirects(response, reverse("preflight_demo:detail", args=[review.pk]))
        version.refresh_from_db()
        self.assertEqual(
            (version.files.count(), version.findings.count(), version.ai_executions.count()),
            counts,
        )

    def test_stream_reports_live_intake_and_recorded_model_stage(self):
        start = self._start(self.client, "reconcile")
        self.assertEqual(start.status_code, 200)
        review = PreflightReview.objects.latest("pk")
        with patch("apps.preflight.demo_views.time.sleep"):
            response = self.client.post(reverse("preflight_demo:stream", args=[review.pk]))
            body = b"".join(response.streaming_content).decode("utf-8")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Package inventory complete", body)
        self.assertIn("Evidence normalized", body)
        self.assertIn("Loading the recorded GPT-5.6 review", body)
        self.assertIn("no live API call", body)
        self.assertIn(reverse("preflight_demo:detail", args=[review.pk]), body)
        review.refresh_from_db()
        self.assertEqual(review.status, "completed")

    def test_anonymous_reviews_are_isolated_between_sessions(self):
        owner = Client()
        stranger = Client()
        review = self._run(owner, "reconcile")
        finding = review.findings.first()
        review_file = review.versions.get().files.first()
        protected_urls = [
            reverse("preflight_demo:detail", args=[review.pk]),
            reverse("preflight_demo:workfile", args=[review.pk]),
            reverse("preflight_demo:workfile_download", args=[review.pk]),
            reverse("preflight_demo:download_file", args=[review_file.pk]),
        ]
        for url in protected_urls:
            self.assertEqual(stranger.get(url).status_code, 404)
        self.assertEqual(
            stranger.post(reverse("preflight_demo:decision", args=[finding.pk]), {"status": "resolved"}).status_code,
            404,
        )
        self.assertEqual(owner.get(reverse("preflight_demo:detail", args=[review.pk])).status_code, 200)

    def test_demo_decision_and_workfile_are_available_without_registration(self):
        review = self._run(self.client, "reconcile")
        finding = review.findings.filter(basis="deterministic").first()
        decision = self.client.post(
            reverse("preflight_demo:decision", args=[finding.pk]),
            {"status": "deferred", "note": "Verify the condition evidence before delivery."},
        )
        self.assertEqual(decision.status_code, 200)
        finding.decision.refresh_from_db()
        self.assertEqual(finding.decision.status, "deferred")
        self.assertEqual(finding.decision.note, "Verify the condition evidence before delivery.")
        not_applicable_finding = review.findings.filter(basis="deterministic").exclude(pk=finding.pk).first()
        self.client.post(
            reverse("preflight_demo:decision", args=[not_applicable_finding.pk]),
            {"status": "not_applicable", "note": "Verified as not applicable to this assignment."},
        )
        html_record = self.client.get(reverse("preflight_demo:workfile", args=[review.pk]))
        self.assertContains(html_record, "Workfile review record")
        self.assertContains(html_record, finding.decision.note)
        self.assertContains(html_record, "Not applicable")
        self.assertNotContains(html_record, "Not_Applicable")
        json_record = self.client.get(reverse("preflight_demo:workfile_download", args=[review.pk]))
        self.assertEqual(json_record.status_code, 200)
        self.assertEqual(json_record["Content-Type"], "application/json")
        self.assertIn("attachment;", json_record["Content-Disposition"])
        self.assertEqual(review.workfile_record.snapshot["findings"][0]["severity"], "warning")

    def test_custom_upload_routes_remain_protected(self):
        response = self.client.get(reverse("preflight:create"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('preflight:create')}")
        self.assertFalse(self.client.session.get("_auth_user_id"))

    @override_settings(DEBUG=False, COAPPRAISER_LLM_PROVIDER="openai", COAPPRAISER_ALLOW_MOCK_AI=False)
    def test_public_demo_never_calls_live_model(self):
        with patch("apps.preflight.llm_client.run_llm_json", side_effect=AssertionError("live model called")) as model:
            review = self._run(self.client, "reconcile")
        model.assert_not_called()
        execution = review.versions.get().ai_executions.get()
        self.assertEqual(execution.provider, "openai")
        self.assertTrue(execution.parsed_response["_demo_snapshot"])
        detail = self.client.get(reverse("preflight_demo:detail", args=[review.pk]))
        self.assertContains(detail, "No live API call")
        self.assertContains(detail, "What Preflight actually reviewed")

    def test_cleanup_command_removes_expired_demo_records_and_files(self):
        review = self._run(self.client, "ready")
        user = get_user_model().objects.get(pk=self.client.session[DEMO_SESSION_USER_KEY])
        self.assertTrue(user.username.startswith(DEMO_USERNAME_PREFIX))
        get_user_model().objects.filter(pk=user.pk).update(date_joined=timezone.now() - timedelta(hours=48))
        call_command("cleanup_demo_reviews", limit=10)
        self.assertFalse(get_user_model().objects.filter(pk=user.pk).exists())
        self.assertFalse(PreflightReview.objects.filter(pk=review.pk).exists())
