from django.conf import settings


DEMO_SCENARIOS = {
    "ready": {
        "eval_case_id": "aligned-package-no-ai-finding",
        "title": "Same Subject · Aligned Evidence",
        "short_title": "Aligned evidence",
        "filename": "coappraiser-demo-01-ready.zip",
        "subject_identifier": "SYNTHETIC-SUBJECT-001",
        "description": "XML, rendered report, commentary, and five sanitized residential photos tell one consistent story.",
        "evidence_types": ["Structured XML fields", "Rendered report narrative", "Five sanitized residential photos"],
        "review_focus": "Confirms that aligned evidence produces a clear action queue rather than an invented conflict.",
        "expected_deterministic": [],
        "expected_codes": set(),
        "expected_gpt_categories": ["No additional supported conflict"],
        "tone": "ready",
    },
    "reconcile": {
        "eval_case_id": "visual-condition-evidence",
        "title": "Same Subject · Reconcile Evidence",
        "short_title": "Reconcile evidence",
        "filename": "coappraiser-demo-02-reconcile.zip",
        "subject_identifier": "SYNTHETIC-SUBJECT-001",
        "description": "The same subject, now with cross-source conflicts, thin comparable support, and a narrative that contradicts the rear photos.",
        "evidence_types": ["XML condition and quality", "PDF narrative", "Comparable support", "Five residential photos"],
        "review_focus": "Shows GPT-5.6 cross-checking the visible deck and enclosure against report language while rules catch exact data conflicts.",
        "expected_deterministic": [
            "XML/PDF condition conflict",
            "Structured/narrative condition conflict",
            "Structured/narrative quality conflict",
            "Incomplete comparable commentary",
        ],
        "expected_codes": {
            "CROSS_SOURCE_SUBJECT_CONDITION",
            "XML_NARRATIVE_CONDITION",
            "XML_NARRATIVE_QUALITY",
            "COMPARABLE_COMMENTARY_INCOMPLETE",
        },
        "expected_gpt_categories": ["Fix before delivery", "Appraiser judgment review"],
        "tone": "review",
    },
    "incomplete": {
        "eval_case_id": "incomplete-comparable-commentary",
        "title": "Same Subject · Missing XML Export",
        "short_title": "Incomplete package",
        "filename": "coappraiser-demo-03-incomplete.zip",
        "subject_identifier": "SYNTHETIC-SUBJECT-001",
        "description": "The same subject's rendered report and five photos are present, but the structured XML export is deliberately missing and only one of three comparables has individual commentary.",
        "evidence_types": ["Rendered report PDF", "Condition narrative", "Five sanitized residential photos"],
        "review_focus": "Shows the missing-export limitation while GPT-5.6 separately checks the rendered comparable grid against its commentary.",
        "expected_deterministic": ["No UAD XML was found"],
        "expected_codes": {"PACKAGE_XML_MISSING"},
        "expected_gpt_categories": ["Comparable commentary review"],
        "tone": "critical",
    },
}


def scenario_package_path(scenario):
    return settings.BASE_DIR / "demo" / scenario["filename"]


def scenario_snapshot_path(slug):
    return settings.BASE_DIR / "demo" / "snapshots" / f"{slug}.json"
