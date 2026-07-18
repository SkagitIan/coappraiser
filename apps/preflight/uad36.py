"""Safe corpus inventory and structural inspection for UAD 3.6 XML."""

from __future__ import annotations

import hashlib
import io
import json
import re
import stat
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath


EVAL_MAX_FILES = 5000
EVAL_MAX_EXPANDED_BYTES = 1024 * 1024 * 1024
EVAL_MAX_MEMBER_BYTES = 150 * 1024 * 1024
SUPPORTED_CORPUS_SUFFIXES = {".xml", ".pdf", ".xlsx", ".xls", ".csv", ".txt", ".md", ".jpg", ".jpeg", ".png"}
EVAL_MAX_ARCHIVE_DEPTH = 2


def local_name(tag):
    return str(tag).rsplit("}", 1)[-1]


def inspect_uad_xml(content):
    """Return a bounded structural profile without treating unknown tags as facts."""
    profile = {
        "parseable": False,
        "root_tag": "",
        "namespace_uris": [],
        "schema_references": [],
        "local_tag_counts": {},
        "sample_paths": [],
        "likely_mismo_3_6": False,
    }
    if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
        profile["parse_error"] = "DTD and entity declarations are not accepted."
        return profile
    try:
        namespace_uris = []
        for _event, value in ET.iterparse(io.BytesIO(content), events=("start-ns",)):
            uri = value[1]
            if uri and uri not in namespace_uris:
                namespace_uris.append(uri)
        root = ET.fromstring(content)
    except (ET.ParseError, ValueError, TypeError) as exc:
        profile["parse_error"] = str(exc)[:300]
        return profile

    counts = Counter()
    sample_paths = []

    def walk(element, parents=()):
        name = local_name(element.tag)
        path = "/".join((*parents, name))
        counts[name] += 1
        if len(sample_paths) < 80 and path not in sample_paths:
            sample_paths.append(path)
        for child in list(element):
            walk(child, (*parents, name))

    walk(root)
    schema_references = [
        str(value)
        for key, value in root.attrib.items()
        if (
            "schemaLocation" in local_name(key)
            or "version" in local_name(key).lower()
            or "referencemodelidentifier" in local_name(key).lower()
        )
    ]
    signals = " ".join(
        [local_name(root.tag), *namespace_uris, *schema_references, *map(str, root.attrib.values())]
    ).lower()
    profile.update(
        {
            "parseable": True,
            "root_tag": local_name(root.tag),
            "namespace_uris": namespace_uris[:30],
            "schema_references": schema_references[:20],
            "local_tag_counts": dict(counts.most_common(150)),
            "sample_paths": sample_paths,
            "likely_mismo_3_6": "mismo" in signals and bool(re.search(r"3[._-]?6", signals)),
        }
    )
    return profile


UAD_SUBJECT_FIELDS = {
    "OverallConditionRatingCode": "subject.condition",
    "OverallQualityRatingCode": "subject.quality",
    "UnitStandardAboveGradeFinishedAreaMeasure": "areas.above_grade_gla",
    "UnitStandardBelowGradeFinishedAreaMeasure": "areas.below_grade_finished",
    "ConstructionMethodType": "subject.construction_method",
    "AttachmentType": "subject.attachment_type",
    "PropertyStructureBuiltYear": "subject.year_built",
}

UAD_ADDRESS_FIELDS = {
    "AddressLineText": "subject.address.line",
    "AddressUnitDesignatorType": "subject.address.unit_designator",
    "AddressUnitIdentifier": "subject.address.unit",
    "CityName": "subject.address.city",
    "CountyName": "subject.address.county",
    "StateCode": "subject.address.state",
    "PostalCode": "subject.address.postal_code",
}

UAD_SUBJECT_REPEATABLE_FIELDS = {
    "DefectItemDescription": "subject.defect",
    "UnitValuationCommentText": "narrative.unit_valuation",
    "StructureValuationCommentText": "narrative.structure_valuation",
}

UAD_REPORT_NARRATIVE_FIELDS = {
    "SalesComparisonCommentDescription": "narrative.sales_comparison",
    "ValuationReconciliationSummaryCommentDescription": "narrative.reconciliation",
    "PriceTrendsAnalysisDescription": "narrative.price_trends",
}


def _attribute(element, name):
    for key, value in element.attrib.items():
        if local_name(key) == name:
            return value
    return ""


def _descendants_with_paths(element, base_path):
    """Yield descendants with stable, human-readable sibling indexes."""
    sibling_totals = Counter(local_name(child.tag) for child in list(element))
    sibling_seen = Counter()
    for child in list(element):
        name = local_name(child.tag)
        sibling_seen[name] += 1
        suffix = f"[{sibling_seen[name]}]" if sibling_totals[name] > 1 else ""
        path = f"{base_path}/{name}{suffix}"
        yield child, path
        yield from _descendants_with_paths(child, path)


def normalize_uad36(content):
    """Normalize a conservative set of verified UAD 3.6 subject/report fields."""
    profile = inspect_uad_xml(content)
    if not profile["parseable"] or profile["root_tag"] != "MESSAGE":
        return []
    try:
        root = ET.fromstring(content)
    except (ET.ParseError, ValueError, TypeError):
        return []

    subject = next(
        (
            element
            for element in root.iter()
            if local_name(element.tag) == "PROPERTY"
            and _attribute(element, "ValuationUseType") == "SubjectProperty"
        ),
        None,
    )
    if subject is None:
        return []

    version = _attribute(root, "MISMOReferenceModelIdentifier")
    observations = []
    seen_single = set()
    subject_path = "PROPERTY[@ValuationUseType='SubjectProperty']"
    address = next((child for child in list(subject) if local_name(child.tag) == "ADDRESS"), None)
    address_values = {}
    if address is not None:
        address_path = f"{subject_path}/ADDRESS"
        for child in list(address):
            tag = local_name(child.tag)
            field_code = UAD_ADDRESS_FIELDS.get(tag)
            value = (child.text or "").strip()
            if field_code and value:
                child_path = f"{address_path}/{tag}"
                observations.append(
                    {
                        "field_code": field_code,
                        "value": value,
                        "source_location": f"XML path: {child_path}",
                        "metadata": {"uad_version": version, "xml_tag": tag},
                    }
                )
                address_values[field_code] = (value, child_path)
                seen_single.add(field_code)
        line = address_values.get("subject.address.line")
        if line:
            unit = address_values.get("subject.address.unit")
            designator = address_values.get("subject.address.unit_designator")
            full_address = line[0]
            component_paths = [line[1]]
            if unit:
                full_address += f", {(designator or ('Unit', ''))[0]} {unit[0]}"
                component_paths.append(unit[1])
            observations.append(
                {
                    "field_code": "subject.address.full",
                    "value": full_address,
                    "source_location": "XML paths: " + " + ".join(component_paths),
                    "metadata": {"uad_version": version, "derived": "address_components"},
                }
            )
            seen_single.add("subject.address.full")

    for element, path in _descendants_with_paths(subject, subject_path):
        tag = local_name(element.tag)
        value = (element.text or "").strip()
        if not value:
            continue
        field_code = UAD_SUBJECT_FIELDS.get(tag)
        if field_code and field_code not in seen_single:
            observations.append(
                {
                    "field_code": field_code,
                    "value": value,
                    "source_location": f"XML path: {path}",
                    "metadata": {
                        "uad_version": version,
                        "xml_tag": tag,
                        "attributes": {local_name(key): item for key, item in element.attrib.items()},
                    },
                }
            )
            seen_single.add(field_code)
            continue
        field_code = UAD_SUBJECT_REPEATABLE_FIELDS.get(tag)
        if field_code:
            observations.append(
                {
                    "field_code": field_code,
                    "value": value,
                    "source_location": f"XML path: {path}",
                    "metadata": {"uad_version": version, "xml_tag": tag},
                }
            )

    comparable_count = sum(
        1
        for element in root.iter()
        if local_name(element.tag) == "PROPERTY"
        and _attribute(element, "ValuationUseType") == "SalesComparable"
    )
    if comparable_count:
        observations.append(
            {
                "field_code": "comparables.count",
                "value": str(comparable_count),
                "source_location": "XML path: PROPERTIES/PROPERTY[@ValuationUseType='SalesComparable']",
                "metadata": {"uad_version": version, "derived": "count"},
            }
        )

    report_seen = set()
    for element, path in _descendants_with_paths(root, local_name(root.tag)):
        tag = local_name(element.tag)
        field_code = UAD_REPORT_NARRATIVE_FIELDS.get(tag)
        value = (element.text or "").strip()
        if field_code and value and field_code not in report_seen:
            observations.append(
                {
                    "field_code": field_code,
                    "value": value,
                    "source_location": f"XML path: {path}",
                    "metadata": {"uad_version": version, "xml_tag": tag},
                }
            )
            report_seen.add(field_code)
    return observations


def mutate_uad_subject_field(content, field_code, replacement):
    """Create a controlled local mutation of one verified subject field."""
    if field_code not in UAD_SUBJECT_FIELDS.values():
        raise ValueError(f"Field is not supported for controlled mutation: {field_code}")
    profile = inspect_uad_xml(content)
    if not profile["parseable"]:
        raise ValueError(profile.get("parse_error") or "XML is not parseable.")
    root = ET.fromstring(content)
    subject = next(
        (
            element
            for element in root.iter()
            if local_name(element.tag) == "PROPERTY"
            and _attribute(element, "ValuationUseType") == "SubjectProperty"
        ),
        None,
    )
    if subject is None:
        raise ValueError("UAD XML has no SubjectProperty element.")
    target_tag = next(tag for tag, code in UAD_SUBJECT_FIELDS.items() if code == field_code)
    target = next(
        (element for element in subject.iter() if local_name(element.tag) == target_tag),
        None,
    )
    if target is None:
        raise ValueError(f"Subject field is absent and cannot be mutated: {field_code}")
    original = (target.text or "").strip()
    if original == str(replacement):
        raise ValueError(f"Mutation replacement must differ from the original {field_code} value.")
    target.text = str(replacement)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True), original


def _safe_archive_members(archive):
    members = [member for member in archive.infolist() if not member.is_dir()]
    if len(members) > EVAL_MAX_FILES:
        raise ValueError(f"Archive contains more than {EVAL_MAX_FILES} files.")
    expanded = 0
    safe = []
    for member in members:
        normalized = member.filename.replace("\\", "/")
        path = PurePosixPath(normalized)
        unix_mode = member.external_attr >> 16
        if (
            not normalized
            or path.is_absolute()
            or ".." in path.parts
            or re.match(r"^[a-zA-Z]:", normalized)
            or stat.S_ISLNK(unix_mode)
        ):
            raise ValueError(f"Archive contains an unsafe path: {member.filename}")
        if member.flag_bits & 0x1:
            raise ValueError(f"Encrypted archive members are not supported: {member.filename}")
        if member.file_size > EVAL_MAX_MEMBER_BYTES:
            raise ValueError(f"Archive member exceeds the size limit: {member.filename}")
        expanded += member.file_size
        if expanded > EVAL_MAX_EXPANDED_BYTES:
            raise ValueError("Archive expands beyond the evaluation corpus size limit.")
        safe.append((member, path))
    return safe


def _pair_key(path):
    parts = [part for part in path.with_suffix("").parts if part]
    text = "-".join(parts[-2:]).lower()
    text = re.sub(r"\b(xml|pdf|urar|report|appraisal|sample|scenario)\b", "", text)
    return re.sub(r"[^a-z0-9]+", "", text)


def import_uad_archive(archive_path, destination_root, *, extract=True, source=None):
    archive_path = Path(archive_path).expanduser().resolve()
    if not archive_path.is_file():
        raise ValueError(f"Archive not found: {archive_path}")
    archive_bytes_hash = hashlib.sha256()
    with archive_path.open("rb") as source_file:
        for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
            archive_bytes_hash.update(chunk)
    archive_sha = archive_bytes_hash.hexdigest()
    expected_sha = (source or {}).get("archive_sha256")
    if expected_sha and archive_sha != expected_sha:
        raise ValueError(
            "Archive SHA-256 does not match the reviewed corpus version. "
            "Confirm the publisher source and update evals/sources/uad_d1.json only after review."
        )
    destination = Path(destination_root).resolve() / archive_sha[:12]
    files = []
    pair_candidates = {}
    totals = {"files": 0, "bytes": 0}

    def inventory_archive(archive, logical_prefix=PurePosixPath(), disk_prefix=PurePosixPath(), depth=0):
        safe_members = _safe_archive_members(archive)
        for member, relative_path in safe_members:
            totals["files"] += 1
            totals["bytes"] += member.file_size
            if totals["files"] > EVAL_MAX_FILES:
                raise ValueError(f"Nested archive contains more than {EVAL_MAX_FILES} total files.")
            if totals["bytes"] > EVAL_MAX_EXPANDED_BYTES:
                raise ValueError("Nested archive expands beyond the evaluation corpus size limit.")
            suffix = relative_path.suffix.lower()
            content = archive.read(member)
            logical_path = logical_prefix / relative_path
            output_path = disk_prefix / relative_path
            item = {
                "path": logical_path.as_posix(),
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "kind": suffix.lstrip(".") or "other",
                "archive_depth": depth,
            }
            if suffix == ".zip":
                item["kind"] = "zip"
                files.append(item)
                if depth >= EVAL_MAX_ARCHIVE_DEPTH:
                    raise ValueError(f"Nested archive depth exceeds {EVAL_MAX_ARCHIVE_DEPTH}: {logical_path}")
                try:
                    with zipfile.ZipFile(io.BytesIO(content)) as nested:
                        inventory_archive(
                            nested,
                            logical_prefix=logical_path.with_suffix(""),
                            disk_prefix=output_path.with_suffix(""),
                            depth=depth + 1,
                        )
                except zipfile.BadZipFile as exc:
                    raise ValueError(f"Nested ZIP is unreadable: {logical_path}") from exc
                continue
            if suffix == ".xml":
                item["xml_profile"] = inspect_uad_xml(content)
            files.append(item)
            if suffix in {".xml", ".pdf"}:
                pair_candidates.setdefault(_pair_key(logical_path), {})[suffix.lstrip(".")] = logical_path.as_posix()
            if extract and suffix in SUPPORTED_CORPUS_SUFFIXES:
                target = (destination / Path(*output_path.parts)).resolve()
                if destination not in target.parents:
                    raise ValueError(f"Archive member escapes the destination: {member.filename}")
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("wb") as target_file:
                    target_file.write(content)

    try:
        with zipfile.ZipFile(archive_path) as archive:
            inventory_archive(archive)
    except zipfile.BadZipFile as exc:
        raise ValueError("The selected file is not a readable ZIP archive.") from exc

    pairs = [
        {"key": key, **candidate}
        for key, candidate in sorted(pair_candidates.items())
        if candidate.get("xml") and candidate.get("pdf")
    ]
    manifest = {
        "schema_version": 1,
        "corpus_id": "fannie-mae-uad-appendix-d-1",
        "source": source or {},
        "archive": {"filename": archive_path.name, "sha256": archive_sha},
        "extracted": bool(extract),
        "destination": str(destination) if extract else "",
        "summary": {
            "files": len(files),
            "xml_files": sum(item["kind"] == "xml" for item in files),
            "pdf_files": sum(item["kind"] == "pdf" for item in files),
            "nested_archives": sum(item["kind"] == "zip" for item in files),
            "candidate_pairs": len(pairs),
        },
        "pairs": pairs,
        "files": files,
    }
    if extract:
        destination.mkdir(parents=True, exist_ok=True)
        manifest_path = destination / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        manifest["manifest_path"] = str(manifest_path)
    return manifest
