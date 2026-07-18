import base64
import json
import logging
import mimetypes
from django.conf import settings
from django.utils import timezone
from .llm_client import run_llm_json
from .models import AIExecution, FindingDecision, ReviewFinding

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {value for value, _ in ReviewFinding.CATEGORIES}
VALID_SEVERITIES = {value for value, _ in ReviewFinding.SEVERITIES}

SYSTEM_PROMPT = """You are CoAppraiser Preflight's multimodal consistency reviewer. Review only the supplied appraisal evidence. Do not determine value, select comps, recommend or calculate final adjustments, declare USPAP compliance, guarantee lender/AMC/GSE acceptance, or invent facts.

The input includes operational review_context metadata, a file inventory, extracted XML/PDF observations, deterministic findings already shown to the appraiser, and—when listed in visual_review.sources—the rendered report PDF and selected appraisal photographs. review_context is instruction metadata, not appraisal evidence: never compare it with a document or report a conflict involving review_context. Do not repeat or substantially restate a deterministic finding. Add only distinct, evidence-grounded interpretive findings. A file inventory proves presence only. You may claim visual inspection only for an attached file listed in visual_review.sources.

When review_context.synthetic_demo is true, synthetic-data notices, demonstration labels, placeholder identities, omitted signatures, and language explaining that the package is not a real appraisal are intentional safeguards. Do not report them or synthetic placeholder phrasing as findings. Review only the deliberate evidence relationships within the fixture.

For attached visuals, make narrow observations about what is plainly visible and cross-check those observations against supplied report evidence. Never identify a person, infer protected or sensitive traits, diagnose a cause, estimate age or repair cost, make a safety determination, or convert a visible condition into a valuation conclusion. Poor image quality or ambiguity is not a finding. Prefer no visual finding unless the relationship is clear. Cite the exact image filename; for the rendered PDF cite the filename and page number whenever available. Include visual_sources only when the finding actually relies on visual inspection.

Return structured JSON with summary, no more than three distinct findings, and missing_information. Prefer zero findings to a weak, generic, low-confidence, or merely cautionary finding. Report only a clear contradiction, a materially unsupported relationship, or missing information that directly blocks a meaningful review. Do not report generic limitations, boilerplate language, ordinary appraisal uncertainty, or a request for more explanation unless the supplied evidence shows a specific inconsistency.

Every finding must include a concise title, category, severity, observed issue, exact supplied source location when available, supporting evidence, why the issue matters, a recommended review action, confidence, visual_sources, and guidance that explicitly says appraiser judgment is required. Use high confidence only for a direct, unambiguous relationship and medium when the evidence supports review but needs confirmation. Do not return low-confidence findings. Keep the observed issue to two short sentences, why_it_matters to one sentence, recommended_action to one direct action, and evidence to the three strongest supplied items. Use plain, solution-focused language.

Use critical only for a package-level omission that prevents a core review or an explicitly supplied urgent material issue. Use warning for a supported inconsistency that likely needs review before delivery. Use advisory for clarity, cleanup, or limited support. Do not escalate an issue already classified by a deterministic check. Describe possible inconsistencies for review; never direct a substantive appraisal conclusion. Label uncertainty clearly, cite only supplied evidence, and phrase assignment-specific requirements as items for the appraiser to verify."""


def _review_context(version):
    extracted_package_text = " ".join(
        (review_file.extracted_text or "")[:4000] for review_file in version.files.all()
    ).lower()
    synthetic_identifier = version.observations.filter(
        field_code="subject.identifier", value__istartswith="SYNTHETIC"
    ).exists()
    synthetic_demo = (
        version.review.user.username.startswith("__coappraiser_demo__")
        or synthetic_identifier
        or (
            "synthetic" in extracted_package_text
            and any(
                marker in extracted_package_text
                for marker in (
                    "not a real appraisal",
                    "demonstration data",
                    "synthetic test data",
                )
            )
        )
    )
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
        "review_context": {
            "synthetic_demo": synthetic_demo,
            "note": "Synthetic notices and placeholder identities are expected safeguards, not review findings." if synthetic_demo else "",
        },
        "file_inventory": files,
        "observations": observations,
        "pdf_excerpts": excerpts,
        "deterministic_findings": deterministic_findings,
    }


def _visual_priority(review_file):
    name = review_file.original_name.lower()
    keywords = (
        "condition",
        "damage",
        "defect",
        "roof",
        "repair",
        "interior",
        "exterior",
        "front",
        "kitchen",
        "bath",
    )
    return (not any(keyword in name for keyword in keywords), name)


def _read_visual_file(review_file, max_bytes, remaining_bytes):
    allowed = min(max_bytes, remaining_bytes)
    if allowed <= 0:
        return None
    try:
        if review_file.file.size > allowed:
            return None
        with review_file.file.open("rb") as source:
            data = source.read(allowed + 1)
    except (OSError, ValueError):
        logger.warning("Could not read visual source %s", review_file.pk, exc_info=True)
        return None
    return data if len(data) <= allowed else None


def _build_multimodal_inputs(version):
    if (
        settings.COAPPRAISER_LLM_PROVIDER != "openai"
        or not settings.COAPPRAISER_VISUAL_REVIEW_ENABLED
    ):
        return [], []

    inputs = []
    manifest = []
    total_bytes = 0
    files = list(version.files.all())
    pdfs = sorted(
        (review_file for review_file in files if review_file.kind == "pdf"),
        key=lambda item: (
            not any(term in item.original_name.lower() for term in ("report", "appraisal", "1004")),
            item.original_name.lower(),
        ),
    )
    if pdfs:
        review_file = pdfs[0]
        data = _read_visual_file(
            review_file,
            settings.COAPPRAISER_VISUAL_MAX_PDF_BYTES,
            settings.COAPPRAISER_VISUAL_MAX_TOTAL_BYTES - total_bytes,
        )
        if data:
            inputs.append(
                {
                    "type": "input_file",
                    "filename": review_file.original_name,
                    "file_data": f"data:application/pdf;base64,{base64.b64encode(data).decode('ascii')}",
                    "detail": "high",
                }
            )
            total_bytes += len(data)
            manifest.append(
                {
                    "file": review_file.original_name,
                    "kind": "rendered_pdf",
                    "detail": "high",
                    "bytes": len(data),
                    "sha256": review_file.sha256,
                }
            )

    images = sorted(
        (review_file for review_file in files if review_file.kind == "image"),
        key=_visual_priority,
    )
    for review_file in images[: settings.COAPPRAISER_VISUAL_MAX_IMAGES]:
        data = _read_visual_file(
            review_file,
            settings.COAPPRAISER_VISUAL_MAX_IMAGE_BYTES,
            settings.COAPPRAISER_VISUAL_MAX_TOTAL_BYTES - total_bytes,
        )
        if not data:
            continue
        media_type = mimetypes.guess_type(review_file.original_name)[0]
        if media_type not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
            continue
        inputs.extend(
            [
                {
                    "type": "input_text",
                    "text": (
                        f"VISUAL SOURCE FILE: {review_file.original_name}. "
                        "Use this exact filename in visual_sources if this image supports a finding."
                    ),
                },
                {
                    "type": "input_image",
                    "image_url": f"data:{media_type};base64,{base64.b64encode(data).decode('ascii')}",
                    "detail": "high",
                },
            ]
        )
        total_bytes += len(data)
        manifest.append(
            {
                "file": review_file.original_name,
                "kind": "appraisal_photo",
                "detail": "high",
                "bytes": len(data),
                "sha256": review_file.sha256,
            }
        )
    return inputs, manifest


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
    multimodal_inputs, visual_sources = _build_multimodal_inputs(version)
    context["visual_review"] = {
        "enabled": bool(multimodal_inputs),
        "sources": visual_sources,
        "instruction": "Only these attached files may support visual observations.",
    }
    execution = AIExecution.objects.create(version=version, operation="preflight_consistency_review", provider=settings.COAPPRAISER_LLM_PROVIDER, model_name=settings.COAPPRAISER_LLM_MODEL, system_prompt=SYSTEM_PROMPT, input_snapshot=context, status="running")
    try:
        result = run_llm_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=json.dumps(context, ensure_ascii=False),
            schema_name="preflight_review",
            required_keys=["summary", "findings", "missing_information"],
            multimodal_inputs=multimodal_inputs,
        )
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
            item_text = json.dumps(item, ensure_ascii=False).lower()
            if context["review_context"]["synthetic_demo"] and any(
                term in item_text for term in ("synthetic", "demonstration fixture", "demo fixture")
            ):
                suppressed_findings.append(
                    {
                        "title": str(item.get("title"))[:200],
                        "topic": "demo_metadata",
                        "reason": "Synthetic fixture safeguards are expected in demo mode.",
                    }
                )
                continue
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
            item_visual_sources = item.get("visual_sources", [])
            confidence = item.get("confidence")
            if (
                not isinstance(evidence, list)
                or not isinstance(guidance, list)
                or not isinstance(item_visual_sources, list)
                or confidence not in {"high", "medium", "low"}
            ):
                continue
            if confidence == "low":
                suppressed_findings.append(
                    {
                        "title": title,
                        "topic": topic,
                        "reason": "Low-confidence AI findings are not shown to the appraiser.",
                    }
                )
                continue
            attached_names = {source["file"] for source in visual_sources}
            verified_visual_sources = [
                str(source)[:300]
                for source in item_visual_sources
                if any(name in str(source) for name in attached_names)
            ]
            basis = "ai_visual" if verified_visual_sources else "ai_interpretation"
            finding = ReviewFinding.objects.create(
                review=version.review,
                version=version,
                rule_code=code,
                signature=f"AI:{code}:{title.lower()}",
                title=title,
                category=category,
                severity=severity,
                observed=str(item.get("observed", "")),
                location=str(item.get("location", ""))[:300],
                why_it_matters=str(item.get("why_it_matters", "")),
                recommended_action=str(item.get("recommended_action", "Review the supplied evidence and apply professional judgment.")),
                evidence=evidence,
                guidance=guidance or ["Appraiser judgment is required."],
                basis=basis,
                confidence=confidence,
                visual_sources=verified_visual_sources,
            )
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
