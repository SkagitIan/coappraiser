import json

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .demo_scenarios import scenario_snapshot_path
from .models import AIExecution, FindingDecision, ReviewFinding


SNAPSHOT_SCHEMA_VERSION = 1


def load_demo_snapshot(slug):
    path = scenario_snapshot_path(slug)
    if not path.is_file():
        raise FileNotFoundError(f"Demo snapshot is missing: {path}")
    snapshot = json.loads(path.read_text(encoding="utf-8"))
    if snapshot.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        raise ValueError(f"Unsupported demo snapshot schema in {path}")
    if snapshot.get("scenario_slug") != slug:
        raise ValueError(f"Demo snapshot scenario mismatch in {path}")
    return snapshot


def hydrate_demo_snapshot(version, slug):
    """Attach a previously captured Preflight agent result to a freshly ingested demo review."""
    snapshot = load_demo_snapshot(slug)
    if version.ai_executions.exists() or version.findings.exclude(basis="deterministic").exists():
        return version.ai_executions.order_by("-created_at").first()

    execution_data = snapshot["ai_execution"]
    completed_at = parse_datetime(execution_data.get("completed_at", "")) or timezone.now()
    execution = AIExecution.objects.create(
        version=version,
        operation="preflight_consistency_review",
        provider=execution_data["provider"],
        model_name=execution_data["model_name"],
        prompt_version=execution_data["prompt_version"],
        system_prompt="Recorded Preflight agent demo snapshot; see snapshot hashes for capture provenance.",
        input_snapshot=execution_data["input_snapshot"],
        raw_response=json.dumps(execution_data["parsed_response"], ensure_ascii=False),
        parsed_response=execution_data["parsed_response"],
        status="completed",
        completed_at=completed_at,
    )
    for item in snapshot.get("findings", []):
        finding = ReviewFinding.objects.create(
            review=version.review,
            version=version,
            rule_code=str(item["rule_code"])[:80],
            signature=str(item["signature"])[:180],
            title=str(item["title"])[:200],
            category=item["category"],
            severity=item["severity"],
            observed=item["observed"],
            location=str(item.get("location", ""))[:300],
            why_it_matters=item["why_it_matters"],
            recommended_action=item["recommended_action"],
            evidence=item.get("evidence", []),
            guidance=item.get("guidance", ["Appraiser judgment is required."]),
            basis=item["basis"],
            confidence=item.get("confidence", ""),
            visual_sources=item.get("visual_sources", []),
        )
        FindingDecision.objects.create(finding=finding, decided_by=version.review.user)
    return execution
