import json
from django.conf import settings

REQUIRED_REVISION_KEYS = {"issue_summary", "request_explanation", "recommended_action", "draft_response", "optional_report_language", "workfile_note", "verification_items", "risk_flags", "missing_information"}


class LLMConfigurationError(RuntimeError):
    pass


def validate_output(result, required_keys=None):
    if not isinstance(result, dict):
        raise ValueError("The AI provider returned an invalid structured response.")
    for key in required_keys or []:
        result.setdefault(key, [] if key.endswith("items") or key.endswith("flags") or key == "missing_information" else "")
    return result

def mock_revision_response(user_prompt):
    request = user_prompt.split("REVISION REQUEST:", 1)[-1].split("REPORT EXCERPT:", 1)[0].strip()
    return {
        "issue_summary": f"The request asks for additional support or clarification regarding: {request[:240]}",
        "request_explanation": "The reviewer appears to be asking for analysis and support, not merely a restatement of the report conclusion.",
        "recommended_action": "Review the underlying data, analysis, and report section identified by the request. Add only support you can verify.",
        "draft_response": "Thank you for the request. I will review the cited analysis and provide additional explanation and supporting information where applicable. Any revised language will be based on verified assignment data.",
        "optional_report_language": "The analysis was reviewed in response to the request. Any additional explanation is based on the available assignment data and remains subject to appraiser verification.",
        "workfile_note": "Development mock output generated for review. The source request and this draft should be retained with the assignment workfile.",
        "verification_items": ["Confirm the requested issue against the report, workfile, and available source data.", "Confirm that any added explanation is supported and does not imply unsupported precision."],
        "risk_flags": ["Draft language. Review and verify before use.", "Do not imply that CoAppraiser determined a value or final adjustment."],
        "missing_information": [],
    }

def run_skill(*, system_prompt, user_prompt, output_schema):
    if settings.COAPPRAISER_LLM_PROVIDER == "mock":
        if not settings.COAPPRAISER_ALLOW_MOCK_AI:
            raise LLMConfigurationError("Mock AI is disabled when DEBUG is false.")
        return validate_output(mock_revision_response(user_prompt), REQUIRED_REVISION_KEYS)
    if settings.COAPPRAISER_LLM_PROVIDER == "openai":
        if not settings.OPENAI_API_KEY:
            raise LLMConfigurationError("OPENAI_API_KEY is required when COAPPRAISER_LLM_PROVIDER=openai.")
        from openai import OpenAI
        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.COAPPRAISER_OPENAI_TIMEOUT_SECONDS,
            max_retries=1,
        )
        request = {
            "model": settings.COAPPRAISER_LLM_MODEL,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        }
        if not settings.COAPPRAISER_LLM_MODEL.startswith("gpt-5"):
            request["temperature"] = 0.2
        response = client.chat.completions.create(**request)
        return validate_output(json.loads(response.choices[0].message.content), REQUIRED_REVISION_KEYS)
    raise RuntimeError("No supported LLM provider is configured.")


def mock_preflight_review():
    return {
        "summary": "Structured evidence was reviewed for possible report consistency concerns. This development response is not a conclusion about compliance or appraisal accuracy.",
        "findings": [{
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
        }],
        "missing_information": []
    }


def run_llm_json(*, system_prompt, user_prompt, schema_name, required_keys=None, multimodal_inputs=None):
    if settings.COAPPRAISER_LLM_PROVIDER == "mock":
        if not settings.COAPPRAISER_ALLOW_MOCK_AI:
            raise LLMConfigurationError("Mock AI is disabled when DEBUG is false.")
        return validate_output(mock_preflight_review() if schema_name == "preflight_review" else {}, required_keys or [])
    if settings.COAPPRAISER_LLM_PROVIDER == "openai":
        if not settings.OPENAI_API_KEY:
            raise LLMConfigurationError("OPENAI_API_KEY is required when COAPPRAISER_LLM_PROVIDER=openai.")
        from openai import OpenAI
        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.COAPPRAISER_OPENAI_TIMEOUT_SECONDS,
            max_retries=1,
        )
        if multimodal_inputs:
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
                            *multimodal_inputs,
                        ],
                    }
                ],
                text=_responses_text_format(schema_name),
                reasoning={"effort": settings.COAPPRAISER_REASONING_EFFORT},
                max_output_tokens=5000,
                store=False,
                timeout=settings.COAPPRAISER_MULTIMODAL_TIMEOUT_SECONDS,
            )
            return validate_output(json.loads(response.output_text), required_keys or [])
        request = {
            "model": settings.COAPPRAISER_LLM_MODEL,
            "response_format": _response_format(schema_name),
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        }
        if not settings.COAPPRAISER_LLM_MODEL.startswith("gpt-5"):
            request["temperature"] = 0.1
        response = client.chat.completions.create(**request)
        return validate_output(json.loads(response.choices[0].message.content), required_keys or [])
    raise RuntimeError("No supported LLM provider is configured.")


def _response_format(schema_name):
    if schema_name != "preflight_review":
        return {"type": "json_object"}
    return {
        "type": "json_schema",
        "json_schema": {
            "name": schema_name,
            "strict": True,
            "schema": _preflight_output_schema(),
        },
    }


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
            "category": {"type": "string", "enum": ["fix_before_delivery", "judgment_review", "cleanup"]},
            "severity": {"type": "string", "enum": ["critical", "warning", "advisory"]},
            "observed": {"type": "string"},
            "location": {"type": "string"},
            "why_it_matters": {"type": "string"},
            "recommended_action": {"type": "string"},
            "evidence": {"type": "array", "items": {"type": "string"}},
            "guidance": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            "visual_sources": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["rule_code", "title", "category", "severity", "observed", "location", "why_it_matters", "recommended_action", "evidence", "guidance", "confidence", "visual_sources"],
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
