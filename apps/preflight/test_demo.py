from datetime import timedelta
from unittest.mock import patch

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
        self.assertContains(response, "Find what the reviewer will find")
        self.assertContains(response, "Drop package to start the demo")
        self.assertContains(response, "Start the evidence review", count=1)
        self.assertContains(response, "See outcome", count=2)
        for slug in DEMO_SCENARIOS:
            self.assertContains(response, reverse("preflight_demo:start", args=[slug]))
        self.assertContains(response, "Synthetic package")
        self.assertContains(response, "Appraiser judgment is required")
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
            self.assertEqual(execution.provider, "mock")
            self.assertEqual(execution.status, "completed")

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
        html_record = self.client.get(reverse("preflight_demo:workfile", args=[review.pk]))
        self.assertContains(html_record, "Workfile review record")
        self.assertContains(html_record, finding.decision.note)
        json_record = self.client.get(reverse("preflight_demo:workfile_download", args=[review.pk]))
        self.assertEqual(json_record.status_code, 200)
        self.assertEqual(json_record["Content-Type"], "application/json")
        self.assertIn("attachment;", json_record["Content-Disposition"])
        self.assertEqual(review.workfile_record.snapshot["findings"][0]["severity"], "warning")

    def test_custom_upload_routes_remain_protected(self):
        response = self.client.get(reverse("preflight:create"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('preflight:create')}")
        self.assertFalse(self.client.session.get("_auth_user_id"))

    @override_settings(
        DEBUG=False,
        COAPPRAISER_LLM_PROVIDER="mock",
        COAPPRAISER_ALLOW_MOCK_AI=False,
    )
    def test_public_demo_never_silently_uses_production_mock(self):
        review = self._run(self.client, "ready")
        execution = review.versions.get().ai_executions.get()
        self.assertEqual(execution.provider, "mock")
        self.assertEqual(execution.status, "failed")
        self.assertFalse(review.findings.filter(basis="ai_interpretation").exists())
        detail = self.client.get(reverse("preflight_demo:detail", args=[review.pk]))
        self.assertContains(detail, "No mock or canned results were substituted")
        self.assertContains(detail, "Retry GPT-5.6 review")

        with self.settings(
            DEBUG=True,
            COAPPRAISER_LLM_PROVIDER="mock",
            COAPPRAISER_ALLOW_MOCK_AI=True,
        ):
            retry = self.client.post(reverse("preflight_demo:retry", args=[review.pk]))
        self.assertRedirects(retry, reverse("preflight_demo:detail", args=[review.pk]))
        execution = review.versions.get().ai_executions.get()
        self.assertEqual(execution.status, "completed")

    def test_cleanup_command_removes_expired_demo_records_and_files(self):
        review = self._run(self.client, "ready")
        user = get_user_model().objects.get(pk=self.client.session[DEMO_SESSION_USER_KEY])
        self.assertTrue(user.username.startswith(DEMO_USERNAME_PREFIX))
        get_user_model().objects.filter(pk=user.pk).update(date_joined=timezone.now() - timedelta(hours=48))
        call_command("cleanup_demo_reviews", limit=10)
        self.assertFalse(get_user_model().objects.filter(pk=user.pk).exists())
        self.assertFalse(PreflightReview.objects.filter(pk=review.pk).exists())
