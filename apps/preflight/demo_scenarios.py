from django.conf import settings


DEMO_SCENARIOS = {
    "ready": {
        "title": "Consistent Package Baseline",
        "short_title": "Ready baseline",
        "filename": "coappraiser-demo-01-ready.zip",
        "subject_identifier": "SYNTHETIC-READY-001",
        "description": "A complete package whose XML, rendered report, commentary, and exhibits tell one consistent story.",
        "evidence_types": ["Structured XML fields", "Rendered report narrative", "Synthetic photo exhibits"],
        "review_focus": "Confirms that aligned evidence reaches a low-priority baseline review rather than generating invented conflicts.",
        "expected_deterministic": ["Package contents are ready for review"],
        "expected_codes": {"PREFLIGHT_BASELINE"},
        "expected_gpt_categories": ["Cleanup or advisory review"],
        "tone": "ready",
    },
    "reconcile": {
        "title": "Residential Appraisal Package 002",
        "short_title": "Package 002",
        "filename": "coappraiser-demo-02-reconcile.zip",
        "subject_identifier": "SYNTHETIC-REVIEW-002",
        "description": "A complete six-file residential appraisal package ready for evidence consistency review.",
        "evidence_types": ["XML condition and quality", "PDF condition narrative", "Comparable commentary summary"],
        "review_focus": "Surfaces relationships that ordinary completeness and field-format validation would not reconcile.",
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
        "title": "Missing Structured Report Export",
        "short_title": "Incomplete package",
        "filename": "coappraiser-demo-03-incomplete.zip",
        "subject_identifier": "SYNTHETIC-INCOMPLETE-003",
        "description": "A rendered report and exhibits are present, but the structured XML export is deliberately missing.",
        "evidence_types": ["Rendered report PDF", "Condition narrative", "Synthetic photo exhibits"],
        "review_focus": "Shows the critical package limitation before cross-document consistency review can be complete.",
        "expected_deterministic": ["No UAD XML was found"],
        "expected_codes": {"PACKAGE_XML_MISSING"},
        "expected_gpt_categories": ["Fix before delivery", "Missing-information review"],
        "tone": "critical",
    },
}


def scenario_package_path(scenario):
    return settings.BASE_DIR / "demo" / scenario["filename"]
