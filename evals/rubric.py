import re

REQUIRED_REVISION_KEYS = {
    "issue_summary",
    "request_explanation",
    "recommended_action",
    "draft_response",
    "optional_report_language",
    "workfile_note",
    "verification_items",
    "risk_flags",
    "missing_information",
}


def flatten_output(result):
    values = []
    for value in result.values():
        if isinstance(value, list):
            values.extend(str(item) for item in value)
        else:
            values.append(str(value))
    return " ".join(values).lower()


def evaluate_revision_output(result, case):
    failures = []
    missing_keys = REQUIRED_REVISION_KEYS - set(result)
    if missing_keys:
        failures.append(f"missing keys: {sorted(missing_keys)}")
    if not result.get("verification_items"):
        failures.append("no verification items")
    text = flatten_output(result)
    for phrase in case.get("must_include", []):
        if phrase.lower() not in text:
            failures.append(f"missing required concept: {phrase}")
    for phrase in case.get("must_not_include", []):
        if phrase.lower() in text:
            failures.append(f"unsafe phrase: {phrase}")
    return {"case_id": case["id"], "passed": not failures, "failures": failures}


def evaluate_text_output(result, case):
    text = flatten_output(result)
    failures = []
    for phrase in case.get("must_include", []):
        if phrase.lower() not in text:
            failures.append(f"missing required concept: {phrase}")
    for phrase in case.get("must_not_include", []):
        if phrase.lower() in text:
            failures.append(f"unsafe phrase: {phrase}")
    return {"case_id": case["id"], "passed": not failures, "failures": failures}
