"""Build the three synthetic CoAppraiser Preflight demonstration packages."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import reportlab
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


DEMO_DIR = Path(__file__).resolve().parent
SCENARIO_DIR = DEMO_DIR / "scenarios"
FIXED_ZIP_TIME = (2026, 7, 17, 12, 0, 0)
REPORTLAB_FONT_DIR = Path(reportlab.__file__).resolve().parent / "fonts"
PDF_FONT = "DemoSans"
PDF_FONT_BOLD = "DemoSansBold"
pdfmetrics.registerFont(TTFont(PDF_FONT, REPORTLAB_FONT_DIR / "Vera.ttf"))
pdfmetrics.registerFont(TTFont(PDF_FONT_BOLD, REPORTLAB_FONT_DIR / "VeraBd.ttf"))

SCENARIOS = [
    {
        "slug": "01_ready",
        "archive": "coappraiser-demo-01-ready.zip",
        "identifier": "SYNTHETIC-READY-001",
        "location": "101 Demonstration Way, Example, WA",
        "condition_xml": "C3",
        "condition_pdf": "C3",
        "condition_narrative": "C3",
        "quality_xml": "Q3",
        "quality_narrative": "Q3",
        "gla_xml": "2140",
        "gla_pdf": "2,140",
        "comp_count": "3",
        "commentary_count": "3",
        "defect": "",
        "summary": "Complete package with aligned structured data, report commentary, and exhibits.",
        "deliberate": [
            "No deliberate inconsistency is present.",
            "XML and PDF identifiers, GLA, and condition agree.",
            "Structured and narrative condition and quality agree.",
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
        "identifier": "SYNTHETIC-REVIEW-002",
        "location": "202 Demonstration Way, Example, WA",
        "condition_xml": "C4",
        "condition_pdf": "C3",
        "condition_narrative": "C3",
        "quality_xml": "Q3",
        "quality_narrative": "Q4",
        "gla_xml": "2180",
        "gla_pdf": "2,180",
        "comp_count": "3",
        "commentary_count": "1",
        "defect": "active roof leakage",
        "summary": "Complete package containing intentional cross-source and commentary conflicts.",
        "deliberate": [
            "XML condition C4 conflicts with PDF condition C3.",
            "Structured XML condition C4 conflicts with narrative condition C3.",
            "Structured XML quality Q3 conflicts with narrative quality Q4.",
            "Three comparables are identified, but only one has commentary.",
        ],
        "expected": [
            "Warning to reconcile condition between XML and PDF.",
            "Warning to reconcile structured and narrative condition.",
            "Warning to reconcile structured and narrative quality.",
            "Warning to review incomplete comparable commentary.",
        ],
        "include_xml": True,
        "accent": "#D97706",
    },
    {
        "slug": "03_incomplete",
        "archive": "coappraiser-demo-03-incomplete.zip",
        "identifier": "SYNTHETIC-INCOMPLETE-003",
        "location": "303 Demonstration Way, Example, WA",
        "condition_xml": "",
        "condition_pdf": "C4",
        "condition_narrative": "",
        "quality_xml": "",
        "quality_narrative": "",
        "gla_xml": "",
        "gla_pdf": "1,760",
        "comp_count": "3",
        "commentary_count": "2",
        "defect": "water staining at rear bedroom ceiling",
        "summary": "Rendered report and exhibits are present, but the structured XML export is missing.",
        "deliberate": [
            "The structured XML report export is intentionally omitted.",
            "The rendered PDF and three synthetic exhibits remain present.",
        ],
        "expected": [
            "One critical deterministic finding that no UAD XML was found.",
            "Review cannot perform XML-to-PDF consistency checks until XML is supplied.",
        ],
        "include_xml": False,
        "accent": "#B91C1C",
    },
]


def _font(size: int):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def build_exhibit(path: Path, scenario: dict, label: str, variant: int) -> None:
    image = Image.new("RGB", (1200, 800), "#DCEAF7")
    draw = ImageDraw.Draw(image)
    accent = scenario["accent"]
    draw.rectangle((0, 560, 1200, 800), fill="#BED49B")
    draw.rectangle((250, 285, 950, 650), fill="#F3EFE6", outline="#334155", width=8)
    draw.polygon([(210, 310), (600, 80), (990, 310)], fill=accent, outline="#334155")
    draw.rectangle((520, 430, 680, 650), fill="#8B5E3C", outline="#334155", width=6)
    for x in (340, 760):
        draw.rectangle((x, 390, x + 110, 500), fill="#BFE3F7", outline="#334155", width=5)
    if variant == 2:
        draw.ellipse((780, 150, 930, 250), fill="#F4B942", outline="#7C2D12", width=6)
    if variant == 3:
        draw.rectangle((705, 510, 840, 550), fill="#7C3F2B", outline="#7F1D1D", width=6)
    draw.rectangle((0, 0, 1200, 64), fill="#111827")
    draw.text((28, 15), "SYNTHETIC EXHIBIT - NOT A REAL PROPERTY", fill="white", font=_font(28))
    draw.rectangle((35, 690, 1165, 775), fill="white", outline="#334155", width=3)
    draw.text((60, 705), f"{label} | {scenario['identifier']}", fill="#111827", font=_font(25))
    draw.text((60, 742), "Generated solely for CoAppraiser demonstration and testing.", fill="#475569", font=_font(20))
    image.save(path, "JPEG", quality=90, optimize=True)


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


def build_pdf(path: Path, scenario: dict) -> None:
    c = canvas.Canvas(str(path), pagesize=letter, invariant=1)
    c.setTitle(f"Synthetic report - {scenario['identifier']}")
    c.setAuthor("CoAppraiser synthetic fixture generator")

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
    y = _line(c, "Quality:", "See narrative commentary", y)
    y = _line(c, "Defect:", scenario["defect"] or "None reported in the synthetic scenario", y)
    c.setFillColor(colors.HexColor("#F8FAFC"))
    c.roundRect(54, 390, 504, 120, 8, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont(PDF_FONT_BOLD, 11)
    c.drawString(72, 484, "Scenario narrative")
    c.setFont(PDF_FONT, 10)
    text = c.beginText(72, 462)
    text.setLeading(15)
    for line in (
        scenario["summary"],
        f"The rendered report describes the subject as {scenario['condition_pdf']}.",
        "All names, locations, facts, and exhibits in this file are synthetic.",
        "No borrower, lender, client, appraiser, signature, or credential is represented.",
    ):
        text.textLine(line)
    c.drawText(text)
    _page_footer(c)
    c.showPage()

    _page_header(c, scenario, "Sales comparison", 2)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont(PDF_FONT_BOLD, 18)
    c.drawString(54, 700, "Sales comparison overview")
    headers = ["Item", "Subject", "Comparable 1", "Comparable 2", "Comparable 3"]
    rows = [
        ["Identifier", scenario["identifier"], "SYN-COMP-01", "SYN-COMP-02", "SYN-COMP-03"],
        ["Sale status", "Subject", "Closed", "Closed", "Closed"],
        ["Condition", scenario["condition_pdf"], "C3", "C3", "C4"],
        ["Quality", "See narrative", "Q3", "Q3", "Q3"],
        ["GLA", scenario["gla_pdf"], "2,080", "2,225", "1,990"],
    ]
    x_positions = [54, 150, 270, 380, 490]
    c.setFont(PDF_FONT_BOLD, 8)
    c.setFillColor(colors.HexColor(scenario["accent"]))
    for x, header in zip(x_positions, headers):
        c.drawString(x, 650, header)
    c.setStrokeColor(colors.HexColor("#CBD5E1"))
    c.line(54, 640, 558, 640)
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont(PDF_FONT, 7)
    row_y = 620
    for row in rows:
        for x, value in zip(x_positions, row):
            c.drawString(x, row_y, str(value))
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
        f"Scenario identifier: {scenario['identifier']}.",
        "The appraiser must reconcile all source evidence and make every final decision.",
        "This synthetic report does not determine value, recommend an adjustment,",
        "declare USPAP compliance, or guarantee lender or GSE acceptance.",
    ]
    if scenario["defect"]:
        lines.insert(2, f"Observed scenario item: {scenario['defect']}. Review the related exhibit.")
    for line in lines:
        text.textLine(line)
    c.drawText(text)
    c.setFillColor(colors.HexColor("#FEF2F2"))
    c.roundRect(54, 420, 504, 105, 8, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#991B1B"))
    c.setFont(PDF_FONT_BOLD, 12)
    c.drawString(72, 495, "Professional boundary")
    c.setFont(PDF_FONT, 10)
    c.drawString(72, 470, "Appraiser judgment is required for every finding and report decision.")
    c.drawString(72, 450, "This package is a controlled demonstration fixture, not assignment evidence.")
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

SYNTHETIC DATA NOTICE
This package contains no real appraisal, borrower, client, lender, appraiser,
signature, credential, or property information. Appraiser judgment is required.

DELIBERATE SCENARIO CONDITIONS
{deliberate}

EXPECTED DETERMINISTIC FINDING TYPES
{expected}

GPT-5.6 OUTPUT
GPT-5.6 output may vary slightly in wording, prioritization, or additional
evidence-grounded interpretive findings. GPT-generated findings appear separately
from deterministic findings. The deterministic outcome listed above is designed
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
        build_exhibit(source_dir / "front_exterior.jpg", scenario, "Front exterior", 1)
        build_exhibit(source_dir / "interior_kitchen.jpg", scenario, "Interior kitchen", 2)
        build_exhibit(source_dir / "condition_exhibit.jpg", scenario, "Condition exhibit", 3)
        build_manifest(source_dir / "README.txt", scenario)
        if scenario["include_xml"]:
            build_xml(source_dir / "report.xml", scenario)
        build_archive(source_dir, DEMO_DIR / scenario["archive"])
        print(f"Built {scenario['archive']}")


if __name__ == "__main__":
    main()
