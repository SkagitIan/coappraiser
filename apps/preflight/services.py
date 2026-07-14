import hashlib
import io
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from uuid import uuid4
from pathlib import PurePosixPath

from django.core.files.base import ContentFile

from apps.ai_tools.services.file_tools import extract_pdf_text
from .models import ExtractedObservation, FindingDecision, ReviewFile, ReviewFinding, ReviewVersion, WorkfileReviewRecord

MAX_EXPANDED_BYTES = 100 * 1024 * 1024
MAX_FILES = 500


def classify(name, content=b""):
    ext = os.path.splitext(name.lower())[1]
    if ext == ".xml" or content.lstrip().startswith(b"<?xml"):
        return "xml"
    if ext == ".pdf" or content.startswith(b"%PDF"):
        return "pdf"
    if ext in {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}:
        return "image"
    if "ssr" in name.lower() and ext in {".json", ".pdf"}:
        return "ssr"
    return "other"


def safe_zip_members(uploaded):
    uploaded.seek(0)
    with zipfile.ZipFile(uploaded) as archive:
        members = [m for m in archive.infolist() if not m.is_dir()]
        if len(members) > MAX_FILES:
            raise ValueError("This ZIP contains too many files. Upload the completed package or a smaller export.")
        total = 0
        for member in members:
            path = PurePosixPath(member.filename)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("The ZIP contains an unsafe path and was rejected.")
            total += member.file_size
            if total > MAX_EXPANDED_BYTES:
                raise ValueError("This ZIP expands beyond the supported package size.")
        return [(m.filename, archive.read(m)) for m in members]


def _hash(content):
    return hashlib.sha256(content).hexdigest()


XML_FIELD_MAP = {
    "identifier": "subject.identifier",
    "condition": "subject.condition",
    "above_grade_gla": "areas.above_grade_gla",
    "below_grade_finished": "areas.below_grade_finished",
    "property_type": "subject.property_type",
    "defect": "subject.defect",
}


def _normalized(value):
    return re.sub(r"[^a-z0-9.]", "", str(value).lower())


def extract_xml_observations(version, record):
    try:
        root = ET.fromstring(record.extracted_text)
    except (ET.ParseError, ValueError):
        return []
    observations = []
    for element in root.iter():
        field_code = XML_FIELD_MAP.get(element.tag.rsplit("}", 1)[-1])
        value = (element.text or "").strip()
        if field_code and value:
            observations.append(ExtractedObservation.objects.create(version=version, source_file=record, field_code=field_code, value=value, normalized_value=_normalized(value), source_kind="xml", source_location=f"XML path: {field_code}"))
    return observations


PDF_PATTERNS = {
    "subject.identifier": r"Subject\s+Identifier\s*:\s*([^\r\n]+)",
    "areas.above_grade_gla": r"Above[- ]grade\s+GLA\s*:\s*([\d,]+)",
    "subject.condition": r"Condition\s*:\s*([^\r\n]+)",
    "subject.defect": r"Defect\s*:\s*([^\r\n]+)",
}


def extract_pdf_observations(version, record):
    observations = []
    for field_code, pattern in PDF_PATTERNS.items():
        match = re.search(pattern, record.extracted_text or "", re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            observations.append(ExtractedObservation.objects.create(version=version, source_file=record, field_code=field_code, value=value, normalized_value=_normalized(value), source_kind="pdf", source_location=f"PDF: {record.original_name}"))
    return observations


def extract_observations(version):
    version.observations.all().delete()
    observations = []
    for record in version.files.all():
        if record.kind == "xml":
            observations.extend(extract_xml_observations(version, record))
        elif record.kind == "pdf":
            observations.extend(extract_pdf_observations(version, record))
    return observations


def ingest_files(version, uploaded_files):
    entries = []
    for uploaded in uploaded_files:
        name = uploaded.name
        raw = uploaded.read()
        if name.lower().endswith(".zip") or raw.startswith(b"PK"):
            entries.extend(safe_zip_members(io.BytesIO(raw)))
        else:
            entries.append((name, raw))
    if not entries:
        raise ValueError("Upload a UAD ZIP package or at least one report file.")
    seen = set()
    for name, raw in entries:
        digest = _hash(raw)
        if digest in seen:
            continue
        seen.add(digest)
        record = ReviewFile(version=version, original_name=os.path.basename(name), kind=classify(name, raw), sha256=digest)
        storage_name = f"{uuid4().hex}_{os.path.basename(name)}"
        record.file.save(storage_name, ContentFile(raw), save=False)
        if record.kind == "pdf":
            try:
                record.extracted_text = extract_pdf_text(io.BytesIO(raw))
            except ValueError:
                record.metadata = {"parse_error": "PDF text could not be extracted."}
        elif record.kind == "image":
            record.metadata = {"bytes": len(raw), "supported": True}
        elif record.kind == "xml":
            record.extracted_text = raw.decode("utf-8", errors="replace")[:250000]
        record.save()
    return list(version.files.all())


def run_deterministic_review(version):
    review = version.review
    files = list(version.files.all())
    kinds = {f.kind for f in files}
    findings = []
    observations = extract_observations(version)

    def add(code, title, category, severity, observed, location, why, action, evidence=None, basis="deterministic"):
        finding = ReviewFinding.objects.create(review=review, version=version, rule_code=code, signature=f"{code}:{location}", title=title, category=category, severity=severity, observed=observed, location=location, why_it_matters=why, recommended_action=action, evidence=evidence or [], basis=basis, guidance=[{"label": "UAD 3.6 readiness support", "url": "https://singlefamily.fanniemae.com/delivering/uniform-mortgage-data-program/uniform-appraisal-dataset"}])
        FindingDecision.objects.create(finding=finding, decided_by=review.user)
        findings.append(finding)

    if "xml" not in kinds:
        add("PACKAGE_XML_MISSING", "No UAD XML was found", "fix_before_delivery", "critical", "The uploaded package contains no file classified as UAD XML.", "Package contents", "Structured report data cannot be checked without the XML export.", "Confirm that the appraisal software export includes the UAD XML file.")
    if "pdf" not in kinds:
        add("PACKAGE_PDF_MISSING", "No rendered PDF was found", "fix_before_delivery", "warning", "The uploaded package contains no rendered report PDF.", "Package contents", "Cross-checking structured data against the report requires the rendered report.", "Export and upload the completed report PDF.")
    if "image" not in kinds:
        add("PACKAGE_IMAGES_MISSING", "No report images were found", "judgment_review", "warning", "No image files were found in the uploaded package.", "Package contents", "Photo and exhibit support cannot be reviewed from the files provided.", "Confirm whether images are embedded elsewhere or upload the package Images folder.")
    by_field = {}
    for observation in observations:
        by_field.setdefault(observation.field_code, {}).setdefault(observation.source_kind, []).append(observation)

    def compare_field(field_code, label, location):
        xml_value = (by_field.get(field_code, {}).get("xml") or [None])[0]
        pdf_value = (by_field.get(field_code, {}).get("pdf") or [None])[0]
        if xml_value and pdf_value and xml_value.normalized_value != pdf_value.normalized_value:
            add("CROSS_SOURCE_" + field_code.upper().replace(".", "_"), f"{label} differs between XML and PDF", "fix_before_delivery", "warning", f"XML reports {xml_value.value}; PDF reports {pdf_value.value}.", location, "Conflicting source values can create a revision trigger or make the report difficult to reconcile.", f"Review the {label.lower()} in the appraisal software and confirm which source is correct.", [xml_value.source_location, pdf_value.source_location])

    compare_field("subject.identifier", "Subject identifier", "Subject section")
    compare_field("areas.above_grade_gla", "Above-grade GLA", "Area section")
    compare_field("subject.condition", "Condition", "Condition section")
    if by_field.get("subject.defect", {}).get("xml") and "image" not in kinds:
        defect = by_field["subject.defect"]["xml"][0]
        add("DEFECT_WITHOUT_PHOTO_SUPPORT", "Reported defect has no photo support", "judgment_review", "warning", f"The XML reports: {defect.value}", defect.source_location, "A reported defect may need supporting exhibit or photo documentation.", "Confirm whether the report package includes the relevant photo and that it is connected to the correct report section.", [defect.source_location])
    xmls = [f for f in files if f.kind == "xml"]
    for xml in xmls:
        if not xml.extracted_text.strip():
            add("XML_EMPTY", "UAD XML appears empty", "fix_before_delivery", "critical", f"The XML file {xml.original_name} contains no readable text.", "XML file", "An empty or unreadable XML export may prevent downstream validation and review.", "Re-export the XML from the appraisal software and confirm it opens correctly.", [xml.original_name])
    pdfs = [f for f in files if f.kind == "pdf"]
    for pdf in pdfs:
        if not pdf.extracted_text.strip():
            add("PDF_TEXT_UNAVAILABLE", "PDF text could not be read", "cleanup", "advisory", f"No extractable text was found in {pdf.original_name}.", "PDF file", "Some cross-source checks may be unavailable when the report is image-only or protected.", "Review the PDF visually and confirm the export is readable.", [pdf.original_name])
    if not findings:
        add("PREFLIGHT_BASELINE", "Package contents are ready for review", "cleanup", "advisory", "XML, PDF, and image files were identified and hashed.", "Package contents", "The package passed basic intake checks; this is not official validation.", "Review the prioritized findings and confirm the report in your existing software.", list(kinds))
    version.status = "reviewed"
    version.save(update_fields=["status"])
    from .ai_review import run_preflight_ai_review
    run_preflight_ai_review(version)
    version.status = "completed"
    review.status = "completed"
    review.save(update_fields=["status", "updated_at"])
    return findings


def build_workfile_record(review):
    latest = review.versions.first()
    findings = list(review.findings.filter(version=latest).select_related("decision")) if latest else []
    snapshot = {"subject_identifier": review.subject_identifier, "review_date": review.updated_at.isoformat(), "version": latest.number if latest else None, "rule_version": latest.rule_version if latest else None, "findings": [{"title": f.title, "rule_code": f.rule_code, "severity": f.severity, "status": getattr(f.decision, "status", "open"), "location": f.location} for f in findings], "limitations": "CoAppraiser Preflight performed an automated review using the files provided and rules available at the time. It does not guarantee compliance, acceptance, or appraisal accuracy. The appraiser remains responsible for all analysis, reporting, and final conclusions.", "ai_use_disclosure": "This review may include automated interpretation; deterministic checks and AI interpretations are labeled in the review.", "file_hashes": [f.sha256 for f in latest.files.all()] if latest else []}
    record, _ = WorkfileReviewRecord.objects.update_or_create(review=review, defaults={"snapshot": snapshot})
    return record


def delete_review_with_files(review):
    """Delete remote/local file objects before deleting their database rows."""
    for version in review.versions.all():
        for review_file in version.files.all():
            if review_file.file:
                review_file.file.delete(save=False)
    review.delete()
