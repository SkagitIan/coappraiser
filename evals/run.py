import json
import os
import sys
from pathlib import Path

import django

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.ai_tools.services.file_tools import analyze_csv
from apps.ai_tools.services.llm_client import run_skill
from apps.ai_tools.services.uad_issue import mock_uad_response
from apps.ai_tools.services.skill_loader import load_skill
from evals.rubric import evaluate_revision_output, evaluate_text_output


def run_case(case):
    if case["workflow"] == "revision_response":
        prompt = "REVISION REQUEST:\n{}\nREPORT EXCERPT:\n{}\nAPPRAISER NOTES:\n{}".format(
            case["revision_request"], case.get("report_excerpt", ""), case.get("appraiser_notes", "")
        )
        result = run_skill(
            system_prompt=load_skill("revision-response")["instructions"],
            user_prompt=prompt,
            output_schema={},
        )
        return evaluate_revision_output(result, case)
    if case["workflow"] == "uad_issue":
        return evaluate_text_output(mock_uad_response(case["issue_text"]), case)
    if case["workflow"] == "market_evidence":
        from io import BytesIO
        upload = BytesIO(case["csv"].encode())
        upload.name = f"{case['id']}.csv"
        summary = analyze_csv(upload)
        result = {
            "summary": summary,
            "notes": case["appraiser_notes"],
            "verification": "The appraiser should verify applicability to the assignment.",
        }
        return evaluate_text_output(result, case)
    raise ValueError(f"Unknown workflow: {case['workflow']}")


if __name__ == "__main__":
    cases = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))
    results = [run_case(case) for case in cases]
    print(json.dumps({"passed": all(item["passed"] for item in results), "results": results}, indent=2))
    raise SystemExit(0 if all(item["passed"] for item in results) else 1)
