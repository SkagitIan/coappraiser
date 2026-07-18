import json

from django.conf import settings


class LLMConfigurationError(RuntimeError):
    pass


def validate_output(result, required_keys=None):
    if not isinstance(result, dict):
        raise ValueError("The AI provider returned an invalid structured response.")
    for key in required_keys or []:
        result.setdefault(key, [] if key == "missing_information" else "")
    return result


def mock_preflight_review():
    return {
        "summary": "Structured evidence was reviewed for possible report consistency concerns. This development response is not a conclusion about compliance or appraisal accuracy.",
        "findings": [
            {
                "rule_code": "AI_COHERENCE_REVIEW",
                "title": "Review whether the report tells one consistent story",
                "category": "judgment_review",
                "severity": "advisory",
                "observed": "The uploaded XML and PDF evidence were available for a focused consistency review.",
                "location": "XML/PDF evidence set",
                "why_it_matters": "A reviewer may question a report when structured fields, commentary, and exhibits do not support the same explanation.",
                "recommended_action": "Review the relevant report commentary and confirm it accurately explains the extracted evidence.",
                "evidence": ["Structured XML/PDF observations"],
                "guidance": ["Appraiser judgment required; this is not official validation."],
                "confidence": "medium",
                "visual_sources": [],
            }
        ],
        "missing_information": [],
    }


def run_llm_json(*, system_prompt, user_prompt, schema_name, required_keys=None, multimodal_inputs=None):
    if settings.COAPPRAISER_LLM_PROVIDER == "mock":
        if not settings.COAPPRAISER_ALLOW_MOCK_AI:
            raise LLMConfigurationError("Mock AI is disabled when DEBUG is false.")
        result = mock_preflight_review() if schema_name == "preflight_review" else {}
        return validate_output(result, required_keys or [])
    if settings.COAPPRAISER_LLM_PROVIDER != "openai":
        raise LLMConfigurationError("COAPPRAISER_LLM_PROVIDER must be mock or openai.")
    if not settings.OPENAI_API_KEY:
        raise LLMConfigurationError("OPENAI_API_KEY is required when COAPPRAISER_LLM_PROVIDER=openai.")

    from openai import OpenAI

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        timeout=settings.COAPPRAISER_OPENAI_TIMEOUT_SECONDS,
        max_retries=1,
    )
    if settings.COAPPRAISER_REASONING_EFFORT not in {"none", "low", "medium", "high", "xhigh", "max"}:
        raise LLMConfigurationError(
            "COAPPRAISER_REASONING_EFFORT must be none, low, medium, high, xhigh, or max."
        )
    response = client.responses.create(
        model=settings.COAPPRAISER_LLM_MODEL,
        instructions=system_prompt,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": user_prompt},
                    *(multimodal_inputs or []),
                ],
            }
        ],
        text=_responses_text_format(schema_name),
        reasoning={"effort": settings.COAPPRAISER_REASONING_EFFORT},
        max_output_tokens=5000,
        store=False,
        timeout=(
            settings.COAPPRAISER_MULTIMODAL_TIMEOUT_SECONDS
            if multimodal_inputs
            else settings.COAPPRAISER_OPENAI_TIMEOUT_SECONDS
        ),
    )
    return validate_output(json.loads(response.output_text), required_keys or [])


def _responses_text_format(schema_name):
    if schema_name != "preflight_review":
        return {"format": {"type": "json_object"}}
    return {
        "format": {
            "type": "json_schema",
            "name": schema_name,
            "strict": True,
            "schema": _preflight_output_schema(),
        }
    }


def _preflight_output_schema():
    finding_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "rule_code": {"type": "string"},
            "title": {"type": "string"},
            "category": {
                "type": "string",
                "enum": ["fix_before_delivery", "judgment_review", "cleanup"],
            },
            "severity": {
                "type": "string",
                "enum": ["critical", "warning", "advisory"],
            },
            "observed": {"type": "string"},
            "location": {"type": "string"},
            "why_it_matters": {"type": "string"},
            "recommended_action": {"type": "string"},
            "evidence": {"type": "array", "items": {"type": "string"}},
            "guidance": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            "visual_sources": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "rule_code",
            "title",
            "category",
            "severity",
            "observed",
            "location",
            "why_it_matters",
            "recommended_action",
            "evidence",
            "guidance",
            "confidence",
            "visual_sources",
        ],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "summary": {"type": "string"},
            "findings": {"type": "array", "items": finding_schema},
            "missing_information": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["summary", "findings", "missing_information"],
    }
