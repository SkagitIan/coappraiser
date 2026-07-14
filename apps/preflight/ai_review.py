import json
import logging
from django.conf import settings
from django.utils import timezone
from apps.ai_tools.services.llm_client import run_llm_json
from .models import AIExecution, FindingDecision, ReviewFinding

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {value for value, _ in ReviewFinding.CATEGORIES}
VALID_SEVERITIES = {value for value, _ in ReviewFinding.SEVERITIES}

SYSTEM_PROMPT = """You are CoAppraiser Preflight's focused consistency reviewer. Review only the extracted evidence supplied by the application. Do not determine value, select comps, calculate adjustments, claim compliance, or invent facts. Return JSON with summary, findings, and missing_information. Each finding must be a possible issue for appraiser review, not a command to reach a substantive appraisal conclusion. Label uncertainty clearly and cite only supplied evidence."""


def _review_context(version):
    observations = [{"field": o.field_code, "value": o.value, "source": o.source_kind, "location": o.source_location} for o in version.observations.all()]
    excerpts = [{"file": f.original_name, "kind": f.kind, "text": (f.extracted_text or "")[:4000]} for f in version.files.filter(kind="pdf")]
    return {"observations": observations, "pdf_excerpts": excerpts}


def run_preflight_ai_review(version):
    context = _review_context(version)
    if not context["observations"] and not context["pdf_excerpts"]:
        return AIExecution.objects.create(version=version, operation="preflight_consistency_review", provider=settings.COAPPRAISER_LLM_PROVIDER, model_name=settings.COAPPRAISER_LLM_MODEL, system_prompt=SYSTEM_PROMPT, input_snapshot=context, status="skipped", completed_at=timezone.now())
    execution = AIExecution.objects.create(version=version, operation="preflight_consistency_review", provider=settings.COAPPRAISER_LLM_PROVIDER, model_name=settings.COAPPRAISER_LLM_MODEL, system_prompt=SYSTEM_PROMPT, input_snapshot=context, status="running")
    try:
        result = run_llm_json(system_prompt=SYSTEM_PROMPT, user_prompt=json.dumps(context, ensure_ascii=False), schema_name="preflight_review", required_keys=["summary", "findings", "missing_information"])
        execution.raw_response = json.dumps(result, ensure_ascii=False)
        execution.parsed_response = result
        for item in result.get("findings", []):
            if not isinstance(item, dict) or not item.get("title"):
                continue
            code = str(item.get("rule_code") or "AI_REVIEW")[:80]
            title = str(item.get("title"))[:200]
            category = item.get("category") if item.get("category") in VALID_CATEGORIES else "judgment_review"
            severity = item.get("severity") if item.get("severity") in VALID_SEVERITIES else "advisory"
            finding = ReviewFinding.objects.create(review=version.review, version=version, rule_code=code, signature=f"AI:{code}:{title.lower()}", title=title, category=category, severity=severity, observed=str(item.get("observed", "")), location=str(item.get("location", ""))[:300], why_it_matters=str(item.get("why_it_matters", "")), recommended_action=str(item.get("recommended_action", "Review the supplied evidence and apply professional judgment.")), evidence=item.get("evidence", []), guidance=item.get("guidance", []), basis="ai_interpretation")
            FindingDecision.objects.create(finding=finding, decided_by=version.review.user)
        execution.status = "completed"
        execution.completed_at = timezone.now()
        execution.save(update_fields=["raw_response", "parsed_response", "status", "completed_at"])
    except Exception as exc:
        logger.exception("Preflight AI review failed for version %s", version.pk)
        execution.status = "failed"
        execution.error_message = str(exc)[:2000]
        execution.completed_at = timezone.now()
        execution.save(update_fields=["status", "error_message", "completed_at"])
    return execution
