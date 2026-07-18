import json
import logging
from django.conf import settings
from django.utils import timezone
from apps.ai_tools.services.llm_client import run_llm_json
from .models import AIExecution, FindingDecision, ReviewFinding

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {value for value, _ in ReviewFinding.CATEGORIES}
VALID_SEVERITIES = {value for value, _ in ReviewFinding.SEVERITIES}

SYSTEM_PROMPT = """You are CoAppraiser Preflight's focused consistency reviewer. Review only the extracted evidence supplied by the application. Do not determine value, select comps, recommend or calculate final adjustments, declare USPAP compliance, guarantee lender/AMC/GSE acceptance, or invent facts.

The input includes a file inventory, extracted observations and PDF excerpts, plus deterministic findings already shown to the appraiser. Do not repeat or substantially restate a deterministic finding. Add only distinct, evidence-grounded interpretive findings. A file inventory proves presence only: do not claim a file or exhibit is missing when it is listed, and do not claim to have inspected image contents because image text is not supplied.

Return structured JSON with summary, no more than four distinct findings, and missing_information. Every finding must include a concise title, category, severity, observed issue, exact supplied source location when available, supporting evidence, why the issue matters, a recommended review action, and guidance that explicitly says appraiser judgment is required.

Use critical only for a package-level omission that prevents a core review or an explicitly supplied urgent material issue. Use warning for a supported inconsistency that likely needs review before delivery. Use advisory for clarity, cleanup, or limited support. Do not escalate an issue already classified by a deterministic check. Describe possible inconsistencies for review; never direct a substantive appraisal conclusion. Label uncertainty clearly, cite only supplied evidence, and phrase assignment-specific requirements as items for the appraiser to verify."""


def _review_context(version):
    observations = [{"field": o.field_code, "value": o.value, "source": o.source_kind, "location": o.source_location} for o in version.observations.all()]
    excerpts = [{"file": f.original_name, "kind": f.kind, "text": (f.extracted_text or "")[:4000]} for f in version.files.filter(kind="pdf")]
    files = [{"file": f.original_name, "kind": f.kind} for f in version.files.all()]
    deterministic_findings = [
        {
            "rule_code": finding.rule_code,
            "title": finding.title,
            "severity": finding.severity,
            "observed": finding.observed,
            "location": finding.location,
            "evidence": finding.evidence,
        }
        for finding in version.findings.filter(basis="deterministic")
    ]
    return {
        "file_inventory": files,
        "observations": observations,
        "pdf_excerpts": excerpts,
        "deterministic_findings": deterministic_findings,
    }


def _finding_topic(*parts):
    text = " ".join(str(part or "") for part in parts).lower()
    if any(term in text for term in ("defect", "leak", "roof", "stain", "water", "repair")):
        return "property_defect"
    if "xml" in text and any(term in text for term in ("missing", "omitted", "not found", "not supplied")):
        return "xml_missing"
    if "quality" in text:
        return "quality"
    if "condition" in text:
        return "condition"
    if ("comparable" in text or "comp " in text) and "comment" in text:
        return "comparable_commentary"
    if "gla" in text or "gross living area" in text:
        return "gla"
    if "identifier" in text:
        return "identifier"
    return ""


def run_preflight_ai_review(version):
    context = _review_context(version)
    if not context["observations"] and not context["pdf_excerpts"]:
        return AIExecution.objects.create(version=version, operation="preflight_consistency_review", provider=settings.COAPPRAISER_LLM_PROVIDER, model_name=settings.COAPPRAISER_LLM_MODEL, system_prompt=SYSTEM_PROMPT, input_snapshot=context, status="skipped", completed_at=timezone.now())
    execution = AIExecution.objects.create(version=version, operation="preflight_consistency_review", provider=settings.COAPPRAISER_LLM_PROVIDER, model_name=settings.COAPPRAISER_LLM_MODEL, system_prompt=SYSTEM_PROMPT, input_snapshot=context, status="running")
    try:
        result = run_llm_json(system_prompt=SYSTEM_PROMPT, user_prompt=json.dumps(context, ensure_ascii=False), schema_name="preflight_review", required_keys=["summary", "findings", "missing_information"])
        execution.raw_response = json.dumps(result, ensure_ascii=False)
        deterministic_topics = {
            _finding_topic(finding.title, finding.observed, finding.evidence)
            for finding in version.findings.filter(basis="deterministic")
        }
        deterministic_topics.discard("")
        suppressed_findings = []
        for item in result.get("findings", []):
            if not isinstance(item, dict) or not item.get("title"):
                continue
            topic = _finding_topic(
                item.get("title"),
                item.get("observed"),
                item.get("why_it_matters"),
                item.get("recommended_action"),
                item.get("evidence"),
            )
            if topic and topic in deterministic_topics:
                suppressed_findings.append(
                    {
                        "title": str(item.get("title"))[:200],
                        "topic": topic,
                        "reason": "A deterministic finding already covers this issue.",
                    }
                )
                continue
            code = str(item.get("rule_code") or "AI_REVIEW")[:80]
            title = str(item.get("title"))[:200]
            category = item.get("category") if item.get("category") in VALID_CATEGORIES else "judgment_review"
            severity = item.get("severity") if item.get("severity") in VALID_SEVERITIES else "advisory"
            evidence = item.get("evidence", [])
            guidance = item.get("guidance", [])
            if not isinstance(evidence, list) or not isinstance(guidance, list):
                continue
            finding = ReviewFinding.objects.create(review=version.review, version=version, rule_code=code, signature=f"AI:{code}:{title.lower()}", title=title, category=category, severity=severity, observed=str(item.get("observed", "")), location=str(item.get("location", ""))[:300], why_it_matters=str(item.get("why_it_matters", "")), recommended_action=str(item.get("recommended_action", "Review the supplied evidence and apply professional judgment.")), evidence=evidence, guidance=guidance or ["Appraiser judgment is required."], basis="ai_interpretation")
            FindingDecision.objects.create(finding=finding, decided_by=version.review.user)
        execution.parsed_response = dict(result)
        execution.parsed_response["suppressed_findings"] = suppressed_findings
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
