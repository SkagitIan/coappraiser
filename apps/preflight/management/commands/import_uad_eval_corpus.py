import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.preflight.uad36 import import_uad_archive


class Command(BaseCommand):
    help = "Safely inventory and locally extract the official UAD Appendix D-1 evaluation archive."

    def add_arguments(self, parser):
        parser.add_argument("archive", help="Path to the Appendix D-1 ZIP downloaded from Fannie Mae.")
        parser.add_argument(
            "--inventory-only",
            action="store_true",
            help="Validate and summarize the archive without extracting files.",
        )

    def handle(self, *args, **options):
        source_path = settings.BASE_DIR / "evals" / "sources" / "uad_d1.json"
        source = json.loads(source_path.read_text(encoding="utf-8"))
        try:
            manifest = import_uad_archive(
                options["archive"],
                settings.BASE_DIR / ".eval-data" / "uad-d1",
                extract=not options["inventory_only"],
                source=source,
            )
        except (OSError, ValueError) as exc:
            raise CommandError(str(exc)) from exc

        summary = manifest["summary"]
        self.stdout.write(
            self.style.SUCCESS(
                "Validated {files} files: {xml_files} XML, {pdf_files} PDF, "
                "{nested_archives} nested ZIPs, {candidate_pairs} candidate PDF/XML pairs.".format(**summary)
            )
        )
        self.stdout.write(f"Archive SHA-256: {manifest['archive']['sha256']}")
        if manifest.get("manifest_path"):
            self.stdout.write(f"Local manifest: {Path(manifest['manifest_path'])}")
        else:
            self.stdout.write("Inventory-only mode: no files were written.")
