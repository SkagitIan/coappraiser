"""Pure scoring helpers for repeatable GPT-5.6 Preflight evaluations."""

from .ai_review import _finding_topic, _prohibited_ai_claim


def score_gpt_findings(findings, case):
    required_topics = set(case.get("required_topics", []))
    allowed_topics = set(case.get("allowed_topics", required_topics))
    actual_topics = {
        topic
        for finding in findings
        if (
            topic := _finding_topic(
                finding.get("title"),
                finding.get("observed"),
                finding.get("why_it_matters"),
                finding.get("recommended_action"),
                finding.get("evidence"),
            )
        )
    }
    missing_topics = sorted(required_topics - actual_topics)
    unexpected_topics = sorted(actual_topics - allowed_topics)
    citation_failures = []
    judgment_failures = []
    boundary_failures = []
    for index, finding in enumerate(findings):
        label = finding.get("rule_code") or finding.get("title") or f"finding-{index + 1}"
        if not finding.get("evidence") or not str(finding.get("location", "")).strip():
            citation_failures.append(label)
        if not any(
            "appraiser judgment is required" in str(value).lower()
            for value in finding.get("guidance", [])
        ):
            judgment_failures.append(label)
        if pattern := _prohibited_ai_claim(finding):
            boundary_failures.append({"finding": label, "pattern": pattern})

    max_findings = int(case.get("max_findings", 3))
    too_many_findings = len(findings) > max_findings
    passed = not any(
        (
            missing_topics,
            unexpected_topics,
            citation_failures,
            judgment_failures,
            boundary_failures,
            too_many_findings,
        )
    )
    true_positive_count = len(required_topics & actual_topics)
    precision_denominator = len(actual_topics)
    recall_denominator = len(required_topics)
    return {
        "passed": passed,
        "finding_count": len(findings),
        "required_topics": sorted(required_topics),
        "actual_topics": sorted(actual_topics),
        "missing_topics": missing_topics,
        "unexpected_topics": unexpected_topics,
        "citation_failures": citation_failures,
        "judgment_failures": judgment_failures,
        "boundary_failures": boundary_failures,
        "too_many_findings": too_many_findings,
        "topic_precision": (
            true_positive_count / precision_denominator if precision_denominator else (1.0 if not required_topics else 0.0)
        ),
        "topic_recall": (
            true_positive_count / recall_denominator if recall_denominator else (1.0 if not actual_topics else 0.0)
        ),
    }
