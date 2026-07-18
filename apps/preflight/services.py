import hashlib
import io
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from uuid import uuid4
from pathlib import PurePosixPath

from django.core.files.base import ContentFile
from django.conf import settings
from django.db.models import Case, IntegerField, When
from django.utils import timezone

from .models import ExtractedObservation, FindingDecision, ReviewFile, ReviewFinding, ReviewVersion, WorkfileReviewRecord
from .uad36 import inspect_uad_xml, normalize_uad36

MAX_EXPANDED_BYTES = 100 * 1024 * 1024
MAX_FILES = 500
MAX_STORED_XML_TEXT_BYTES = 2 * 1024 * 1024


def extract_pdf_text(uploaded_file):
    try:
        from pypdf import PdfReader

        reader = PdfReader(uploaded_file)
        return "\n\n".join(
            f"[CoAppraiser PDF page {page_number}]\n{page.extract_text() or ''}"
            for page_number, page in enumerate(reader.pages, start=1)
        ).strip()
    except Exception as exc:
        raise ValueError("CoAppraiser could not read this PDF package.") from exc


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
    "quality": "subject.quality",
    "narrative_condition": "narrative.condition",
    "narrative_quality": "narrative.quality",
    "comparable_count": "comparables.count",
    "comparable_commentary_count": "comparables.commentary_count",
}


def _normalized(value):
    return re.sub(r"[^a-z0-9.]", "", str(value).lower())


def extract_xml_observations(version, record):
    xml_profile = (record.metadata or {}).get("xml_profile")
    if xml_profile and not xml_profile.get("parseable"):
        return []
    xml_content = record.extracted_text
    if record.file:
        try:
            with record.file.open("rb") as source:
                xml_content = source.read()
        except OSError:
            pass
    try:
        root = ET.fromstring(xml_content)
    except (ET.ParseError, ValueError):
        return []
    normalized_uad = normalize_uad36(
        xml_content.encode("utf-8") if isinstance(xml_content, str) else xml_content
    )
    if normalized_uad:
        return [
            ExtractedObservation.objects.create(
                version=version,
                source_file=record,
                field_code=item["field_code"],
                value=item["value"],
                normalized_value=_normalized(item["value"]),
                source_kind="xml",
                source_location=item["source_location"],
                metadata=item.get("metadata", {}),
            )
            for item in normalized_uad
        ]
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
    "subject.condition": r"(?m)^Condition\s*:\s*([^\r\n]+)",
    "subject.defect": r"(?m)^Defect\s*:\s*([^\r\n]+)",
    "subject.quality": r"Overall\s+Quality\s+(Q[1-6])\b",
}

# UAD 3.6 rendered reports use different labels from the legacy synthetic
# fixtures. Keep the most specific subject-summary label first.
PDF_UAD36_PATTERNS = {
    "areas.above_grade_gla": r"Finished\s+Above\s+Grade\s+([\d,]+)\s+Sq\.\s*Ft\.",
    "subject.condition": r"Overall\s+Condition\s+(C[1-6])\b",
}


def normalize_pdf_observations(extracted_text, original_name):
    sections = []
    marker = re.compile(r"\[CoAppraiser PDF page (\d+)\]\r?\n")
    matches = list(marker.finditer(extracted_text or ""))
    if matches:
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(extracted_text)
            sections.append((int(match.group(1)), extracted_text[match.end() : end]))
    else:
        sections.append((None, extracted_text or ""))

    normalized = []
    found_fields = set()
    address_pattern = re.compile(
        r"Physical\s+Address\s+([^\r\n]+)"
        r"(?:\r?\n\s*(?:Unit|U\s*\r?\n\s*nit)\s+(\S+))?",
        re.IGNORECASE,
    )
    for page_number, page_text in sections:
        address_match = address_pattern.search(page_text)
        if not address_match:
            continue
        line = re.sub(r"(?<=\d)\s+(?=\d{2}\b)", "", address_match.group(1).strip())
        unit = (address_match.group(2) or "").strip()
        full_address = f"{line}, Unit {unit}" if unit else line
        location = f"PDF: {original_name}"
        if page_number:
            location += f", page {page_number}"
        page_metadata = {"page": page_number} if page_number else {}
        normalized.extend(
            [
                {
                    "field_code": "subject.address.full",
                    "value": full_address,
                    "source_location": location,
                    "metadata": page_metadata,
                },
                {
                    "field_code": "subject.address.line",
                    "value": line,
                    "source_location": location,
                    "metadata": {**page_metadata, "derived": "address_line"},
                },
            ]
        )
        found_fields.update({"subject.address.full", "subject.address.line"})
        break

    for field_code, pattern in [*PDF_PATTERNS.items(), *PDF_UAD36_PATTERNS.items()]:
        if field_code in found_fields:
            continue
        for page_number, page_text in sections:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if not match:
                continue
            value = match.group(1).strip()
            location = f"PDF: {original_name}"
            if page_number:
                location += f", page {page_number}"
            normalized.append(
                {
                    "field_code": field_code,
                    "value": value,
                    "source_location": location,
                    "metadata": {"page": page_number} if page_number else {},
                }
            )
            found_fields.add(field_code)
            break
    return normalized


def extract_pdf_observations(version, record):
    return [
        ExtractedObservation.objects.create(
            version=version,
            source_file=record,
            field_code=item["field_code"],
            value=item["value"],
            normalized_value=_normalized(item["value"]),
            source_kind="pdf",
            source_location=item["source_location"],
            metadata=item.get("metadata", {}),
        )
        for item in normalize_pdf_observations(record.extracted_text or "", record.original_name)
    ]


def extract_observations(version):
    version.observations.all().delete()
    observations = []
    for record in version.files.all():
        if record.kind == "xml":
            observations.extend(extract_xml_observations(version, record))
        elif record.kind == "pdf":
            observations.extend(extract_pdf_observations(version, record))
    return observations


CROSS_SOURCE_COMPARISONS = {
    "subject.identifier": ("Subject identifier", "Subject section"),
    "subject.address.full": ("Complete subject address", "Subject section"),
    "areas.above_grade_gla": ("Above-grade GLA", "Area section"),
    "subject.condition": ("Condition", "Condition section"),
    "subject.quality": ("Quality", "Quality section"),
}


def compare_cross_source_observations(observations):
    values = {}
    for observation in observations:
        field_code = observation.get("field_code") if isinstance(observation, dict) else observation.field_code
        source_kind = observation.get("source_kind") if isinstance(observation, dict) else observation.source_kind
        values.setdefault(field_code, {}).setdefault(source_kind, observation)

    differences = []
    for field_code, (label, location) in CROSS_SOURCE_COMPARISONS.items():
        xml_value = values.get(field_code, {}).get("xml")
        pdf_value = values.get(field_code, {}).get("pdf")
        if not xml_value or not pdf_value:
            continue

        def read(item, key):
            return item.get(key, "") if isinstance(item, dict) else getattr(item, key)

        xml_normalized = read(xml_value, "normalized_value") or _normalized(read(xml_value, "value"))
        pdf_normalized = read(pdf_value, "normalized_value") or _normalized(read(pdf_value, "value"))
        if xml_normalized == pdf_normalized:
            continue
        differences.append(
            {
                "rule_code": "CROSS_SOURCE_" + field_code.upper().replace(".", "_"),
                "field_code": field_code,
                "label": label,
                "location": location,
                "xml_value": read(xml_value, "value"),
                "pdf_value": read(pdf_value, "value"),
                "xml_location": read(xml_value, "source_location"),
                "pdf_location": read(pdf_value, "source_location"),
            }
        )
    return differences


def ingest_files(version, uploaded_files):
    entries = []
    if not settings.COAPPRAISER_ALLOW_LOCAL_UPLOADS and settings.STORAGE_BACKEND != "r2":
        raise ValueError("Production appraisal uploads require private R2 storage. Your review record was saved, but no package was processed.")
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
            stored = raw[:MAX_STORED_XML_TEXT_BYTES]
            record.extracted_text = stored.decode("utf-8", errors="replace")
            record.metadata = {
                "xml_profile": inspect_uad_xml(raw),
                "text_truncated": len(raw) > len(stored),
            }
        record.save()
    return list(version.files.all())


def run_deterministic_review(version, include_ai=True):
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

    for difference in compare_cross_source_observations(observations):
        add(
            difference["rule_code"],
            f"{difference['label']} differs between XML and PDF",
            "fix_before_delivery",
            "warning",
            f"XML reports {difference['xml_value']}; PDF reports {difference['pdf_value']}.",
            difference["location"],
            "Conflicting source values can create a revision trigger or make the report difficult to reconcile.",
            f"Review the {difference['label'].lower()} in the appraisal software and confirm which source is correct.",
            [
                f"{difference['xml_location']}: {difference['xml_value']}",
                f"{difference['pdf_location']}: {difference['pdf_value']}",
            ],
        )

    def compare_xml_narrative(structured_code, narrative_code, label, location):
        structured = (by_field.get(structured_code, {}).get("xml") or [None])[0]
        narrative = (by_field.get(narrative_code, {}).get("xml") or [None])[0]
        if structured and narrative and structured.normalized_value != narrative.normalized_value:
            add(f"XML_NARRATIVE_{label.upper()}", f"{label.title()} conflicts with narrative commentary", "fix_before_delivery", "warning", f"The structured XML reports {structured.value}, while the narrative commentary reports {narrative.value}.", location, "Structured fields and narrative commentary should tell a consistent, supportable story.", f"Review both locations in the appraisal software and reconcile the {label} using verified assignment evidence.", [f"{structured.source_location}: {structured.value}", f"{narrative.source_location}: {narrative.value}"])

    compare_xml_narrative("subject.condition", "narrative.condition", "condition", "XML subject condition and narrative condition commentary")
    compare_xml_narrative("subject.quality", "narrative.quality", "quality", "XML subject quality and narrative quality commentary")

    comp_count = (by_field.get("comparables.count", {}).get("xml") or [None])[0]
    commentary_count = (by_field.get("comparables.commentary_count", {}).get("xml") or [None])[0]
    if comp_count and commentary_count:
        try:
            incomplete_commentary = int(commentary_count.value) < int(comp_count.value)
        except ValueError:
            incomplete_commentary = False
        if incomplete_commentary:
            add("COMPARABLE_COMMENTARY_INCOMPLETE", "Comparable commentary appears incomplete", "judgment_review", "warning", f"The package identifies {comp_count.value} comparables but commentary for only {commentary_count.value}.", "XML sales comparison commentary summary", "Incomplete comparable commentary may leave the selection, differences, or reliance insufficiently explained for review.", "Review each comparable and add only commentary supported by the assignment evidence. Do not use this finding to select comps or determine an adjustment.", [f"{comp_count.source_location}: {comp_count.value}", f"{commentary_count.source_location}: {commentary_count.value}"])

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
    if not include_ai:
        return findings
    from .ai_review import run_preflight_ai_review
    run_preflight_ai_review(version)
    complete_review(version)
    return findings


def complete_review(version):
    review = version.review
    version.status = "completed"
    version.save(update_fields=["status"])
    review.status = "completed"
    review.save(update_fields=["status", "updated_at"])


def build_workfile_record(review):
    latest = review.versions.first()
    findings = list(
        review.findings.filter(version=latest)
        .select_related("decision")
        .annotate(
            severity_rank=Case(
                When(severity="critical", then=0),
                When(severity="warning", then=1),
                default=2,
                output_field=IntegerField(),
            ),
            basis_rank=Case(
                When(basis="deterministic", then=0),
                default=1,
                output_field=IntegerField(),
            ),
        )
        .order_by("severity_rank", "basis_rank", "created_at")
    ) if latest else []
    generated_at = timezone.now()
    ai_executions = latest.ai_executions.order_by("created_at") if latest else []
    snapshot = {
        "review_title": review.title,
        "subject_identifier": review.subject_identifier,
        "generated_at": generated_at.isoformat(),
        "version": latest.number if latest else None,
        "parser_version": latest.parser_version if latest else None,
        "rule_version": latest.rule_version if latest else None,
        "findings": [{
            "title": f.title,
            "rule_code": f.rule_code,
            "category": f.category,
            "severity": f.severity,
            "basis": f.basis,
            "confidence": f.confidence,
            "visual_sources": f.visual_sources,
            "observed_issue": f.observed,
            "source_location": f.location,
            "supporting_evidence": f.evidence,
            "why_it_matters": f.why_it_matters,
            "recommended_review_action": f.recommended_action,
            "appraiser_judgment_required": True,
            "decision_status": f.decision.status,
            "decision_note": f.decision.note,
            "decided_by": f.decision.decided_by.get_username(),
            "decided_at": f.decision.decided_at.isoformat(),
        } for f in findings],
        "ai_executions": [{"provider": item.provider, "model": item.model_name, "status": item.status, "prompt_version": item.prompt_version} for item in ai_executions],
        "limitations": "CoAppraiser Preflight performed an automated review using the files provided and rules available at the time. It does not determine value, recommend final adjustments, declare USPAP compliance, or guarantee lender, AMC, or GSE acceptance. The appraiser remains responsible for all analysis, reporting, and final conclusions.",
        "file_hashes": [{"name": f.original_name, "sha256": f.sha256} for f in latest.files.all()] if latest else [],
    }
    record, _ = WorkfileReviewRecord.objects.update_or_create(review=review, defaults={"snapshot": snapshot, "generated_at": generated_at})
    return record


def delete_review_with_files(review):
    """Delete remote/local file objects before deleting their database rows."""
    for version in review.versions.all():
        for review_file in version.files.all():
            if review_file.file:
                review_file.file.delete(save=False)
    review.delete()
