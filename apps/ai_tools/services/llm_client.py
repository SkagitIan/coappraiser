import json
from django.conf import settings

REQUIRED_REVISION_KEYS = {"issue_summary", "request_explanation", "recommended_action", "draft_response", "optional_report_language", "workfile_note", "verification_items", "risk_flags", "missing_information"}

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
    if settings.COAPPRAISER_LLM_PROVIDER == "mock" or (settings.DEBUG and not settings.OPENAI_API_KEY):
        return validate_output(mock_revision_response(user_prompt), REQUIRED_REVISION_KEYS)
    if settings.COAPPRAISER_LLM_PROVIDER == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(model=settings.COAPPRAISER_LLM_MODEL, temperature=0.2, response_format={"type": "json_object"}, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}])
        return validate_output(json.loads(response.choices[0].message.content), REQUIRED_REVISION_KEYS)
    raise RuntimeError("No supported LLM provider is configured.")
