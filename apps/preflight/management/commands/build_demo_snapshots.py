import hashlib
import json
from datetime import datetime, timezone

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.preflight.demo_scenarios import DEMO_SCENARIOS, scenario_package_path, scenario_snapshot_path
from apps.preflight.demo_snapshots import SNAPSHOT_SCHEMA_VERSION


class Command(BaseCommand):
    help = "Build immutable public-demo snapshots from the latest paid GPT-5.6 evaluation report."

    def handle(self, *args, **options):
        report_path = settings.BASE_DIR / ".eval-data" / "reports" / "gpt56-demo-evaluation.json"
        if not report_path.is_file():
            raise CommandError("Run evaluate_gpt56 --repeat 1 --confirm-paid-api --strict first.")
        report_bytes = report_path.read_bytes()
        report = json.loads(report_bytes)
        if report.get("model") != "gpt-5.6":
            raise CommandError("The evaluation report was not produced by gpt-5.6.")
        results = {item["case_id"]: item for item in report.get("results", []) if item.get("iteration") == 1}

        for slug, scenario in DEMO_SCENARIOS.items():
            result = results.get(scenario["eval_case_id"])
            if not result or not result.get("score", {}).get("passed"):
                raise CommandError(f"A passing evaluation result is required for {slug}.")
            execution = result.get("execution_snapshot")
            if not execution:
                raise CommandError(f"Evaluation result for {slug} lacks execution_snapshot.")
            package_bytes = scenario_package_path(scenario).read_bytes()
            snapshot = {
                "schema_version": SNAPSHOT_SCHEMA_VERSION,
                "scenario_slug": slug,
                "captured_at": report.get("generated_at") or datetime.now(timezone.utc).isoformat(),
                "source": "Paid GPT-5.6 evaluation; replayed only for the exact package hash below.",
                "package_sha256": hashlib.sha256(package_bytes).hexdigest(),
                "evaluation_report_sha256": hashlib.sha256(report_bytes).hexdigest(),
                "case_spec_sha256": report.get("case_spec_sha256"),
                "system_prompt_sha256": report.get("system_prompt_sha256"),
                "ai_execution": execution,
                "findings": result.get("findings", []),
            }
            path = scenario_snapshot_path(slug)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Wrote {path.relative_to(settings.BASE_DIR)}"))
