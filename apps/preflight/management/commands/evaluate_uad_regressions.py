import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.preflight.services import (
    compare_cross_source_observations,
    extract_pdf_text,
    normalize_pdf_observations,
)
from apps.preflight.uad36 import mutate_uad_subject_field, normalize_uad36


def _normalized(value):
    return "".join(character for character in str(value).lower() if character.isalnum())


class Command(BaseCommand):
    help = "Run controlled UAD PDF/XML regression cases against the local official corpus."

    def add_arguments(self, parser):
        parser.add_argument(
            "corpus",
            nargs="?",
            help="Extracted corpus directory; defaults to the newest local UAD D-1 corpus.",
        )
        parser.add_argument("--strict", action="store_true", help="Fail unless every case returns exactly its expected rules.")

    def handle(self, *args, **options):
        corpus = self._resolve_corpus(options["corpus"])
        manifest = json.loads((corpus / "manifest.json").read_text(encoding="utf-8"))
        cases_path = settings.BASE_DIR / "evals" / "cases" / "uad36_cross_source.json"
        specification = json.loads(cases_path.read_text(encoding="utf-8"))
        if manifest.get("archive", {}).get("sha256") != specification["archive_sha256"]:
            raise CommandError("Regression cases do not target this corpus SHA-256.")
        pdf_by_xml = {pair["xml"]: pair["pdf"] for pair in manifest.get("pairs", [])}
        results = []

        for case in specification["cases"]:
            xml_relative = case["scenario_xml"]
            pdf_relative = pdf_by_xml.get(xml_relative)
            if not pdf_relative:
                raise CommandError(f"No paired PDF for regression case {case['id']}.")
            xml_content = (corpus / Path(*Path(xml_relative).parts)).read_bytes()
            mutation = case.get("mutation")
            original_value = None
            if mutation:
                xml_content, original_value = mutate_uad_subject_field(
                    xml_content, mutation["field"], mutation["value"]
                )
            with (corpus / Path(*Path(pdf_relative).parts)).open("rb") as pdf_file:
                pdf_text = extract_pdf_text(pdf_file)
            observations = [
                {
                    **item,
                    "source_kind": "xml",
                    "normalized_value": _normalized(item["value"]),
                }
                for item in normalize_uad36(xml_content)
            ]
            observations.extend(
                {
                    **item,
                    "source_kind": "pdf",
                    "normalized_value": _normalized(item["value"]),
                }
                for item in normalize_pdf_observations(pdf_text, Path(pdf_relative).name)
            )
            differences = compare_cross_source_observations(observations)
            actual_rules = sorted(item["rule_code"] for item in differences)
            expected_rules = sorted(case["expected_rules"])
            passed = actual_rules == expected_rules
            results.append(
                {
                    "id": case["id"],
                    "mutation": mutation,
                    "original_value": original_value,
                    "expected_rules": expected_rules,
                    "actual_rules": actual_rules,
                    "differences": differences,
                    "passed": passed,
                }
            )
            self.stdout.write(
                f"{'PASS' if passed else 'FAIL'} {case['id']}: "
                f"expected {expected_rules or 'no cross-source findings'}, "
                f"received {actual_rules or 'no cross-source findings'}"
            )

        passed_count = sum(result["passed"] for result in results)
        report = {
            "schema_version": 1,
            "corpus_id": specification["corpus_id"],
            "archive_sha256": specification["archive_sha256"],
            "summary": {
                "cases": len(results),
                "passed": passed_count,
                "failed": len(results) - passed_count,
            },
            "results": results,
        }
        report_dir = settings.BASE_DIR / ".eval-data" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"uad-regressions-{specification['archive_sha256'][:12]}.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        self.stdout.write(
            self.style.SUCCESS(
                f"Regression cases: {passed_count}/{len(results)} passed. Report: {report_path}"
            )
        )
        if options["strict"] and passed_count != len(results):
            raise CommandError(f"{len(results) - passed_count} UAD regression case(s) failed.")

    def _resolve_corpus(self, supplied):
        if supplied:
            corpus = Path(supplied).expanduser().resolve()
        else:
            root = settings.BASE_DIR / ".eval-data" / "uad-d1"
            candidates = [path for path in root.iterdir() if path.is_dir() and (path / "manifest.json").is_file()] if root.exists() else []
            if not candidates:
                raise CommandError("No local UAD corpus found. Run import_uad_eval_corpus first.")
            corpus = max(candidates, key=lambda path: (path / "manifest.json").stat().st_mtime)
        if not (corpus / "manifest.json").is_file():
            raise CommandError(f"Missing corpus manifest: {corpus / 'manifest.json'}")
        return corpus
