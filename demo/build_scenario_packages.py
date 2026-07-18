"""Build three controlled same-subject CoAppraiser demonstration packages."""

from __future__ import annotations

import shutil
import textwrap
import zipfile
from pathlib import Path

import reportlab
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


DEMO_DIR = Path(__file__).resolve().parent
SCENARIO_DIR = DEMO_DIR / "scenarios"
PHOTO_SOURCE_DIR = DEMO_DIR / "photo_sources"
FIXED_ZIP_TIME = (2026, 7, 17, 12, 0, 0)
REPORTLAB_FONT_DIR = Path(reportlab.__file__).resolve().parent / "fonts"
PDF_FONT = "DemoSans"
PDF_FONT_BOLD = "DemoSansBold"
pdfmetrics.registerFont(TTFont(PDF_FONT, REPORTLAB_FONT_DIR / "Vera.ttf"))
pdfmetrics.registerFont(TTFont(PDF_FONT_BOLD, REPORTLAB_FONT_DIR / "VeraBd.ttf"))

PHOTO_EXHIBITS = (
    ("rear_exterior_condition.jpg", "Rear exterior and storage enclosure"),
    ("rear_deck_exterior.jpg", "Rear exterior and covered deck"),
    ("covered_deck_exterior.jpg", "Covered deck detail"),
    ("kitchen_interior.jpg", "Kitchen interior"),
    ("bathroom_interior.jpg", "Bathroom interior"),
)

SCENARIOS = [
    {
        "slug": "01_ready",
        "archive": "coappraiser-demo-01-ready.zip",
        "identifier": "SYNTHETIC-SUBJECT-001",
        "location": "Subject A, Fictional County, WA",
        "condition_xml": "C4",
        "condition_pdf": "C4",
        "condition_narrative": "C4",
        "quality_xml": "Q3",
        "quality_pdf": "Q3",
        "quality_narrative": "Q3",
        "gla_xml": "2140",
        "gla_pdf": "2,140",
        "comp_count": "3",
        "commentary_count": "3",
        "defect": "",
        "summary": "The same-subject package is complete and its report narrative accounts for the visible exhibits.",
        "visual_narrative": [
            "Rear photographs show a covered deck and an attached storage enclosure.",
            "The storage enclosure is excluded from above-grade GLA.",
            "Incomplete exterior cladding at the enclosure is disclosed for appraiser review.",
            "No cause, repair scope, cost, or value effect is represented.",
        ],
        "deliberate": [
            "No deliberate inconsistency is present.",
            "XML and PDF identifiers, GLA, and condition agree.",
            "Structured and narrative condition and quality agree.",
            "The covered deck, storage enclosure, and incomplete cladding visible in the photos are disclosed in the addendum.",
            "All three comparables have commentary.",
        ],
        "expected": [
            "One deterministic advisory baseline finding indicating that the package is ready for review.",
            "No deterministic conflict or missing-file finding.",
        ],
        "include_xml": True,
        "accent": "#2563EB",
    },
    {
        "slug": "02_reconcile",
        "archive": "coappraiser-demo-02-reconcile.zip",
        "identifier": "SYNTHETIC-SUBJECT-001",
        "location": "Subject A, Fictional County, WA",
        "condition_xml": "C4",
        "condition_pdf": "C3",
        "condition_narrative": "C3",
        "quality_xml": "Q3",
        "quality_pdf": "Q4",
        "quality_narrative": "Q4",
        "gla_xml": "2180",
        "gla_pdf": "2,180",
        "comp_count": "3",
        "commentary_count": "1",
        "defect": "",
        "summary": "The same-subject package contains intentional data, narrative, support, and photo conflicts.",
        "visual_narrative": [
            "The addendum states that no rear deck, covered patio, or accessory enclosure was observed.",
            "The exterior is described as complete with no unfinished cladding noted.",
            "These statements deliberately conflict with the supplied rear photographs.",
            "No cause, repair scope, cost, or value effect is represented.",
        ],
        "deliberate": [
            "XML condition C4 conflicts with PDF condition C3.",
            "Structured XML condition C4 conflicts with narrative condition C3.",
            "Structured XML quality Q3 conflicts with narrative quality Q4.",
            "Three comparables are identified, but only one has commentary.",
            "The PDF says there is no rear deck or accessory enclosure, while the rear photos visibly show both.",
            "The PDF describes complete exterior cladding, while a rear photo visibly shows an unfinished enclosure wall.",
        ],
        "expected": [
            "Warning to reconcile condition between XML and PDF.",
            "Warning to reconcile structured and narrative condition.",
            "Warning to reconcile structured and narrative quality.",
            "Warning to review incomplete comparable commentary.",
            "A GPT-5.6 visual review prompt may identify the deck/enclosure and exterior-description conflicts using exact photo filenames.",
        ],
        "include_xml": True,
        "accent": "#D97706",
    },
    {
        "slug": "03_incomplete",
        "archive": "coappraiser-demo-03-incomplete.zip",
        "identifier": "SYNTHETIC-SUBJECT-001",
        "location": "Subject A, Fictional County, WA",
        "condition_xml": "",
        "condition_pdf": "C4",
        "condition_narrative": "",
        "quality_xml": "",
        "quality_pdf": "Q3",
        "quality_narrative": "",
        "gla_xml": "",
        "gla_pdf": "1,760",
        "comp_count": "3",
        "commentary_count": "3",
        "defect": "",
        "summary": "The same-subject rendered report and photos are present, but the structured XML export is missing.",
        "visual_narrative": [
            "Rear photographs show a covered deck and an attached storage enclosure.",
            "The enclosure is excluded from the reported above-grade GLA.",
            "The visible incomplete cladding is identified for appraiser review.",
            "No cause, repair scope, cost, or value effect is represented.",
        ],
        "deliberate": [
            "The structured XML report export is intentionally omitted.",
            "The rendered PDF and five sanitized photo exhibits remain present.",
        ],
        "expected": [
            "One critical deterministic finding that no UAD XML was found.",
            "Review cannot perform XML-to-PDF consistency checks until XML is supplied.",
        ],
        "include_xml": False,
        "accent": "#B91C1C",
    },
]


def build_exhibit(path: Path, source_name: str) -> None:
    """Re-encode a sanitized owner-supplied reference photo without metadata."""
    source = PHOTO_SOURCE_DIR / source_name
    if not source.is_file():
        raise FileNotFoundError(f"Missing sanitized demo photo source: {source}")
    with Image.open(source) as image:
        image.convert("RGB").save(path, "JPEG", quality=84, optimize=True, progressive=True)


def _line(c: canvas.Canvas, label: str, value: str, y: float) -> float:
    c.setFont(PDF_FONT_BOLD, 10)
    c.setFillColor(colors.HexColor("#334155"))
    c.drawString(54, y, label)
    c.setFont(PDF_FONT, 10)
    c.setFillColor(colors.HexColor("#111827"))
    c.drawString(190, y, value)
    return y - 22


def _page_header(c: canvas.Canvas, scenario: dict, section: str, page: int) -> None:
    c.setFillColor(colors.HexColor(scenario["accent"]))
    c.rect(0, 742, 612, 50, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(PDF_FONT_BOLD, 13)
    c.drawString(42, 762, "SYNTHETIC RESIDENTIAL APPRAISAL")
    c.setFont(PDF_FONT, 9)
    c.drawRightString(570, 762, f"{section} | Page {page}")


def _page_footer(c: canvas.Canvas) -> None:
    c.setFillColor(colors.HexColor("#B91C1C"))
    c.setFont(PDF_FONT_BOLD, 9)
    c.drawCentredString(306, 24, "DEMONSTRATION DATA ONLY - NOT AN APPRAISAL OR VALUE OPINION")


def _wrapped(lines, width=82):
    for line in lines:
        yield from textwrap.wrap(line, width=width) or [""]


def build_pdf(path: Path, scenario: dict) -> None:
    c = canvas.Canvas(str(path), pagesize=letter, invariant=1)
    c.setTitle(f"Synthetic report - {scenario['identifier']}")
    c.setAuthor("CoAppraiser synthetic fixture generator")
    comp_3_condition = "C3" if scenario["condition_pdf"] == "C4" else "C4"

    _page_header(c, scenario, "Subject", 1)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont(PDF_FONT_BOLD, 18)
    c.drawString(54, 700, "Subject and assignment summary")
    y = 665
    y = _line(c, "Subject Identifier:", scenario["identifier"], y)
    y = _line(c, "Synthetic Location:", scenario["location"], y)
    y = _line(c, "Property Type:", "Detached one-unit residence", y)
    y = _line(c, "Above-grade GLA:", f"{scenario['gla_pdf']} sq ft", y)
    y = _line(c, "Condition:", scenario["condition_pdf"], y)
    y = _line(c, "Quality:", scenario["quality_pdf"], y)
    y = _line(c, "Defect:", scenario["defect"] or "None reported in the synthetic scenario", y)
    c.setFillColor(colors.HexColor("#F8FAFC"))
    c.roundRect(54, 345, 504, 165, 8, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont(PDF_FONT_BOLD, 11)
    c.drawString(72, 484, "Scenario narrative")
    c.setFont(PDF_FONT, 10)
    text = c.beginText(72, 462)
    text.setLeading(15)
    for line in (
        scenario["summary"],
        f"The rendered report describes the subject as {scenario['condition_pdf']}.",
        "All assignment data, identities, locations, and conclusions in this report are synthetic.",
        "Sanitized owner-supplied photographs are used only as controlled visual evidence.",
        "No borrower, lender, client, appraiser, signature, or credential is represented.",
    ):
        for wrapped_line in _wrapped([line], 86):
            text.textLine(wrapped_line)
    c.drawText(text)
    _page_footer(c)
    c.showPage()

    _page_header(c, scenario, "Sales comparison", 2)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont(PDF_FONT_BOLD, 18)
    c.drawString(54, 700, "Sales comparison overview")
    headers = ["Item", "Subject", "Comp 1", "Comp 2", "Comp 3"]
    rows = [
        ["Identifier", scenario["identifier"], "SYN-COMP-01", "SYN-COMP-02", "SYN-COMP-03"],
        ["Sale status", "Subject", "Closed", "Closed", "Closed"],
        ["Condition", scenario["condition_pdf"], "C3", "C3", comp_3_condition],
        ["Quality", scenario["quality_pdf"], "Q3", "Q3", "Q3"],
        ["GLA", scenario["gla_pdf"], "2,080", "2,225", "1,990"],
    ]
    x_positions = [54, 150, 270, 380, 490]
    c.setFont(PDF_FONT_BOLD, 8)
    c.setFillColor(colors.HexColor(scenario["accent"]))
    for x, header in zip(x_positions, headers):
        c.drawString(x, 650, header)
    c.setStrokeColor(colors.HexColor("#CBD5E1"))
    c.line(54, 640, 558, 640)
    for x in (140, 260, 370, 480, 558):
        c.line(x, 490, x, 655)
    c.setFillColor(colors.HexColor("#111827"))
    row_y = 620
    for row in rows:
        for column, (x, value) in enumerate(zip(x_positions, row)):
            c.setFont(PDF_FONT, 5.8 if column else 7)
            c.drawString(x, row_y, str(value))
        c.setStrokeColor(colors.HexColor("#E2E8F0"))
        c.line(54, row_y - 10, 558, row_y - 10)
        row_y -= 28
    c.setFont(PDF_FONT_BOLD, 11)
    c.drawString(54, 450, "Comparable commentary")
    c.setFont(PDF_FONT, 9)
    commentary_total = int(scenario["commentary_count"])
    commentary = [
        "Comparable 1: similar utility; verify all reported differences in the workfile.",
        "Comparable 2: similar market area; commentary is synthetic and requires review.",
        "Comparable 3: condition differs; no adjustment conclusion is represented here.",
    ]
    text = c.beginText(54, 425)
    text.setLeading(18)
    for line in commentary[:commentary_total]:
        text.textLine(line)
    if commentary_total < int(scenario["comp_count"]):
        text.textLine("No individual commentary was supplied for the remaining comparable(s).")
    c.drawText(text)
    _page_footer(c)
    c.showPage()

    _page_header(c, scenario, "Addendum", 3)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont(PDF_FONT_BOLD, 18)
    c.drawString(54, 700, "Condition and quality addendum")
    c.setFont(PDF_FONT, 10)
    text = c.beginText(54, 665)
    text.setLeading(17)
    lines = [
        f"Rendered condition commentary: {scenario['condition_pdf']}.",
        f"Rendered quality commentary: {scenario['quality_pdf']}.",
        *scenario["visual_narrative"],
        "The appraiser must reconcile all source evidence and make every final decision.",
        "This synthetic report does not determine value, recommend an adjustment,",
        "declare USPAP compliance, or guarantee lender or GSE acceptance.",
    ]
    if scenario["defect"]:
        lines.insert(2, f"Observed scenario item: {scenario['defect']}. Review the related exhibit.")
    for line in _wrapped(lines):
        text.textLine(line)
    c.drawText(text)
    c.setFont(PDF_FONT_BOLD, 11)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.drawString(54, 420, "Photo register")
    c.setFont(PDF_FONT, 9)
    photo_y = 398
    for filename, label in PHOTO_EXHIBITS:
        c.drawString(72, photo_y, f"{filename} - {label}")
        photo_y -= 17
    c.setFillColor(colors.HexColor("#FEF2F2"))
    c.roundRect(54, 250, 504, 82, 8, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#991B1B"))
    c.setFont(PDF_FONT_BOLD, 11)
    c.drawString(72, 305, "Professional boundary")
    c.setFont(PDF_FONT, 9)
    c.drawString(72, 282, "Appraiser judgment is required for every finding and report decision.")
    c.drawString(72, 264, "This controlled package is not assignment evidence.")
    _page_footer(c)
    c.save()


def build_xml(path: Path, scenario: dict) -> None:
    defect = f"\n    <defect>{scenario['defect']}</defect>" if scenario["defect"] else ""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<synthetic_uad_report version="3.6" data_classification="SYNTHETIC_DEMO_ONLY">
  <subject>
    <identifier>{scenario['identifier']}</identifier>
    <property_type>Detached</property_type>
    <condition>{scenario['condition_xml']}</condition>
    <quality>{scenario['quality_xml']}</quality>{defect}
  </subject>
  <areas>
    <above_grade_gla>{scenario['gla_xml']}</above_grade_gla>
    <below_grade_finished>0</below_grade_finished>
  </areas>
  <commentary>
    <narrative_condition>{scenario['condition_narrative']}</narrative_condition>
    <narrative_quality>{scenario['quality_narrative']}</narrative_quality>
  </commentary>
  <sales_comparison>
    <comparable_count>{scenario['comp_count']}</comparable_count>
    <comparable_commentary_count>{scenario['commentary_count']}</comparable_commentary_count>
  </sales_comparison>
</synthetic_uad_report>
"""
    path.write_text(xml, encoding="utf-8", newline="\n")


def build_manifest(path: Path, scenario: dict) -> None:
    xml_status = "included" if scenario["include_xml"] else "intentionally missing"
    deliberate = "\n".join(f"- {item}" for item in scenario["deliberate"])
    expected = "\n".join(f"- {item}" for item in scenario["expected"])
    content = f"""COAPPRAISER SYNTHETIC DEMONSTRATION PACKAGE

Scenario: {scenario['slug']}
Identifier: {scenario['identifier']}
Purpose: {scenario['summary']}
XML status: {xml_status}

CONTROLLED DATA NOTICE
This is a synthetic appraisal package: every assignment fact, identifier, report
statement, comparable, and conclusion is fictional. It contains no borrower,
client, lender, appraiser, signature, credential, address, or value opinion.
The residential photographs are owner-supplied reference images, selected to
exclude visible addresses, signs, vehicles, people, and personal portraits, then
re-encoded without EXIF metadata. They are not evidence from a real assignment.
Appraiser judgment is required.

DELIBERATE SCENARIO CONDITIONS
{deliberate}

EXPECTED FINDING TYPES
{expected}

GPT-5.6 OUTPUT
GPT-5.6 output may vary slightly in wording, prioritization, or additional
evidence-grounded interpretive findings. Preflight evidence-review findings appear
separately from deterministic findings. The deterministic outcome listed above is designed
to remain predictable.
"""
    path.write_text(content, encoding="utf-8", newline="\n")


def build_archive(source_dir: Path, archive_path: Path) -> None:
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source in sorted(source_dir.iterdir()):
            info = zipfile.ZipInfo(source.name, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes())


def main() -> None:
    if SCENARIO_DIR.exists():
        shutil.rmtree(SCENARIO_DIR)
    SCENARIO_DIR.mkdir(parents=True)
    for old_archive in DEMO_DIR.glob("coappraiser-demo-*.zip"):
        old_archive.unlink()
    for scenario in SCENARIOS:
        source_dir = SCENARIO_DIR / scenario["slug"]
        source_dir.mkdir()
        build_pdf(source_dir / "report.pdf", scenario)
        for filename, _label in PHOTO_EXHIBITS:
            build_exhibit(source_dir / filename, filename)
        build_manifest(source_dir / "README.txt", scenario)
        if scenario["include_xml"]:
            build_xml(source_dir / "report.xml", scenario)
        build_archive(source_dir, DEMO_DIR / scenario["archive"])
        print(f"Built {scenario['archive']}")


if __name__ == "__main__":
    main()
