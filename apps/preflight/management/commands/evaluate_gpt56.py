import json
import tempfile
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from django.test import override_settings

from apps.preflight.evaluation import score_gpt_findings
from apps.preflight.models import PreflightReview
from apps.preflight.services import delete_review_with_files, ingest_files, run_deterministic_review


class Command(BaseCommand):
    help = "Run paid, repeatable GPT-5.6 demo evaluations and write a machine-readable score report."

    def add_arguments(self, parser):
        parser.add_argument("--repeat", type=int, default=1, help="Runs per case, from 1 to 5.")
        parser.add_argument("--case", dest="case_id", help="Run only one case ID.")
        parser.add_argument(
            "--confirm-paid-api",
            action="store_true",
            help="Required confirmation that this command may make paid OpenAI API requests.",
        )
        parser.add_argument("--strict", action="store_true", help="Fail unless every repeated case passes.")

    def handle(self, *args, **options):
        if not options["confirm_paid_api"]:
            raise CommandError("Pass --confirm-paid-api to authorize paid GPT-5.6 evaluation requests.")
        if not settings.OPENAI_API_KEY:
            raise CommandError("OPENAI_API_KEY is required; the evaluator never falls back to mock AI.")
        if settings.COAPPRAISER_LLM_MODEL != "gpt-5.6":
            raise CommandError("COAPPRAISER_LLM_MODEL must be gpt-5.6 for this evaluation.")
        repeat = options["repeat"]
        if repeat < 1 or repeat > 5:
            raise CommandError("--repeat must be between 1 and 5.")

        specification = json.loads(
            (settings.BASE_DIR / "evals" / "cases" / "gpt56_demo.json").read_text(encoding="utf-8")
        )
        cases = specification["cases"]
        if options["case_id"]:
            cases = [case for case in cases if case["id"] == options["case_id"]]
            if not cases:
                raise CommandError(f"Unknown GPT evaluation case: {options['case_id']}")
        results = []
        with tempfile.TemporaryDirectory(prefix="coappraiser-gpt-eval-") as media_root:
            with override_settings(
                COAPPRAISER_LLM_PROVIDER="openai",
                COAPPRAISER_ALLOW_MOCK_AI=False,
                COAPPRAISER_ALLOW_LOCAL_UPLOADS=True,
                STORAGE_BACKEND="local",
                MEDIA_ROOT=media_root,
                STORAGES={
                    "default": {
                        "BACKEND": "django.core.files.storage.FileSystemStorage",
                        "OPTIONS": {"location": media_root},
                    },
                    "staticfiles": {
                        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
                    },
                },
            ):
                for case in cases:
                    package_path = settings.BASE_DIR / case["package"]
                    if not package_path.is_file():
                        raise CommandError(f"Evaluation package is missing: {package_path}")
                    for iteration in range(1, repeat + 1):
                        results.append(self._run_case(case, iteration, package_path))

        passed = sum(result["score"]["passed"] for result in results)
        durations = [
            result["response_metadata"].get("duration_ms")
            for result in results
            if result["response_metadata"].get("duration_ms") is not None
        ]
        total_tokens = [
            result["response_metadata"].get("usage", {}).get("total_tokens")
            for result in results
            if result["response_metadata"].get("usage", {}).get("total_tokens") is not None
        ]
        report = {
            "schema_version": 1,
            "model": "gpt-5.6",
            "repeat": repeat,
            "summary": {
                "runs": len(results),
                "passed": passed,
                "failed": len(results) - passed,
                "pass_rate": passed / len(results),
                "average_duration_ms": sum(durations) / len(durations) if durations else None,
                "average_total_tokens": sum(total_tokens) / len(total_tokens) if total_tokens else None,
            },
            "results": results,
        }
        report_dir = settings.BASE_DIR / ".eval-data" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "gpt56-demo-evaluation.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        self.stdout.write(
            self.style.SUCCESS(
                f"GPT-5.6 evaluation: {passed}/{len(results)} runs passed. Report: {report_path}"
            )
        )
        if options["strict"] and passed != len(results):
            raise CommandError(f"{len(results) - passed} GPT-5.6 evaluation run(s) failed.")

    def _run_case(self, case, iteration, package_path):
        username = f"__coappraiser_eval__{uuid4().hex}"
        user = get_user_model().objects.create_user(username=username)
        review = PreflightReview.objects.create(user=user, title=f"Eval {case['id']} #{iteration}")
        version = review.versions.create(number=1, status="uploaded")
        try:
            package = SimpleUploadedFile(
                package_path.name,
                package_path.read_bytes(),
                content_type="application/zip",
            )
            ingest_files(version, [package])
            run_deterministic_review(version)
            execution = version.ai_executions.order_by("-created_at").first()
            if not execution or execution.status != "completed":
                error = execution.error_message if execution else "No AI execution was created."
                raise CommandError(f"GPT-5.6 evaluation failed for {case['id']}: {error}")
            findings = [
                {
                    "rule_code": finding.rule_code,
                    "title": finding.title,
                    "observed": finding.observed,
                    "location": finding.location,
                    "evidence": finding.evidence,
                    "why_it_matters": finding.why_it_matters,
                    "recommended_action": finding.recommended_action,
                    "guidance": finding.guidance,
                    "confidence": finding.confidence,
                    "visual_sources": finding.visual_sources,
                }
                for finding in review.findings.filter(version=version, basis__startswith="ai_")
            ]
            score = score_gpt_findings(findings, case)
            response_metadata = execution.parsed_response.get("_response_metadata", {})
            self.stdout.write(
                f"{'PASS' if score['passed'] else 'FAIL'} {case['id']} run {iteration}: "
                f"topics={score['actual_topics']}, findings={score['finding_count']}"
            )
            return {
                "case_id": case["id"],
                "iteration": iteration,
                "score": score,
                "findings": findings,
                "suppressed_findings": execution.parsed_response.get("suppressed_findings", []),
                "response_metadata": response_metadata,
            }
        finally:
            if review.pk:
                delete_review_with_files(review)
            user.delete()
