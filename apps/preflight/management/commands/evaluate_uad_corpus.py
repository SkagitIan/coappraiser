import json
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.preflight.services import extract_pdf_text, normalize_pdf_observations
from apps.preflight.uad36 import normalize_uad36


REQUIRED_NORMALIZED_FIELDS = {
    "subject.address.line",
    "subject.address.full",
    "subject.condition",
    "subject.quality",
    "areas.above_grade_gla",
}
CROSS_SOURCE_FIELDS = {
    "subject.address.full",
    "subject.condition",
    "subject.quality",
    "areas.above_grade_gla",
}


def _normalized(value):
    return "".join(character for character in str(value).lower() if character.isalnum())


class Command(BaseCommand):
    help = "Measure verified UAD normalization coverage across a locally imported corpus."

    def add_arguments(self, parser):
        parser.add_argument(
            "corpus",
            nargs="?",
            help="Extracted corpus directory containing manifest.json; defaults to the newest local UAD D-1 corpus.",
        )
        parser.add_argument("--strict", action="store_true", help="Fail when a scenario is missing a required field.")

    def handle(self, *args, **options):
        corpus = self._resolve_corpus(options["corpus"])
        manifest_path = corpus / "manifest.json"
        if not manifest_path.is_file():
            raise CommandError(f"Missing corpus manifest: {manifest_path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        scenarios = []
        field_coverage = Counter()
        pairs_by_xml = {pair["xml"]: pair["pdf"] for pair in manifest.get("pairs", [])}

        for item in manifest.get("files", []):
            if item.get("kind") != "xml":
                continue
            xml_path = corpus / Path(*Path(item["path"]).parts)
            if not xml_path.is_file():
                raise CommandError(f"Manifest XML is missing: {xml_path}")
            observations = normalize_uad36(xml_path.read_bytes())
            xml_values = {}
            for observation in observations:
                xml_values.setdefault(observation["field_code"], observation["value"])
            fields = {observation["field_code"] for observation in observations}
            field_coverage.update(fields)
            missing = sorted(REQUIRED_NORMALIZED_FIELDS - fields)
            pdf_relative = pairs_by_xml.get(item["path"])
            pdf_values = {}
            pdf_error = ""
            if pdf_relative:
                pdf_path = corpus / Path(*Path(pdf_relative).parts)
                try:
                    with pdf_path.open("rb") as pdf_file:
                        pdf_text = extract_pdf_text(pdf_file)
                    for observation in normalize_pdf_observations(pdf_text, pdf_path.name):
                        pdf_values.setdefault(observation["field_code"], observation["value"])
                except (OSError, ValueError) as exc:
                    pdf_error = str(exc)
            cross_source = {}
            for field_code in sorted(CROSS_SOURCE_FIELDS):
                xml_value = xml_values.get(field_code)
                pdf_value = pdf_values.get(field_code)
                cross_source[field_code] = {
                    "xml": xml_value,
                    "pdf": pdf_value,
                    "matched": bool(
                        xml_value
                        and pdf_value
                        and _normalized(xml_value) == _normalized(pdf_value)
                    ),
                }
            cross_source_failures = [
                field_code for field_code, result in cross_source.items() if not result["matched"]
            ]
            scenarios.append(
                {
                    "scenario": Path(item["path"]).stem,
                    "xml": item["path"],
                    "observation_count": len(observations),
                    "fields": sorted(fields),
                    "missing_required_fields": missing,
                    "pdf": pdf_relative,
                    "pdf_error": pdf_error,
                    "cross_source": cross_source,
                    "cross_source_failures": cross_source_failures,
                    "passed": not missing and not cross_source_failures and not pdf_error,
                }
            )

        if not scenarios:
            raise CommandError("The corpus manifest contains no XML scenarios.")
        passed = sum(scenario["passed"] for scenario in scenarios)
        report = {
            "schema_version": 1,
            "corpus_id": manifest.get("corpus_id"),
            "archive_sha256": manifest.get("archive", {}).get("sha256"),
            "required_fields": sorted(REQUIRED_NORMALIZED_FIELDS),
            "summary": {
                "scenarios": len(scenarios),
                "passed": passed,
                "failed": len(scenarios) - passed,
            },
            "field_coverage": dict(sorted(field_coverage.items())),
            "scenarios": scenarios,
        }
        report_dir = settings.BASE_DIR / ".eval-data" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"uad-normalization-{report['archive_sha256'][:12]}.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        for scenario in scenarios:
            status = "PASS" if scenario["passed"] else "FAIL"
            missing = ", ".join(scenario["missing_required_fields"]) or "none"
            self.stdout.write(
                f"{status} {scenario['scenario']}: {scenario['observation_count']} observations; missing: {missing}"
            )
            if scenario["cross_source_failures"]:
                self.stdout.write(
                    "  PDF/XML failures: " + ", ".join(scenario["cross_source_failures"])
                )
        summary = report["summary"]
        self.stdout.write(
            self.style.SUCCESS(
                f"Normalization coverage: {summary['passed']}/{summary['scenarios']} scenarios passed. "
                f"Report: {report_path}"
            )
        )
        if options["strict"] and summary["failed"]:
            raise CommandError(f"{summary['failed']} UAD scenario(s) failed required normalization coverage.")

    def _resolve_corpus(self, supplied):
        if supplied:
            return Path(supplied).expanduser().resolve()
        root = settings.BASE_DIR / ".eval-data" / "uad-d1"
        candidates = [path for path in root.iterdir() if path.is_dir() and (path / "manifest.json").is_file()] if root.exists() else []
        if not candidates:
            raise CommandError("No local UAD corpus found. Run import_uad_eval_corpus first.")
        return max(candidates, key=lambda path: (path / "manifest.json").stat().st_mtime)
