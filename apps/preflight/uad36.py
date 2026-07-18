"""Safe corpus inventory and structural inspection for UAD 3.6 XML."""

from __future__ import annotations

import hashlib
import io
import json
import re
import shutil
import stat
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath


EVAL_MAX_FILES = 5000
EVAL_MAX_EXPANDED_BYTES = 1024 * 1024 * 1024
EVAL_MAX_MEMBER_BYTES = 150 * 1024 * 1024
SUPPORTED_CORPUS_SUFFIXES = {".xml", ".pdf", ".xlsx", ".xls", ".csv", ".txt", ".md", ".jpg", ".jpeg", ".png"}


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
        if "schemaLocation" in local_name(key) or "version" in local_name(key).lower()
    ]
    signals = " ".join([local_name(root.tag), *namespace_uris, *schema_references]).lower()
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
    destination = Path(destination_root).resolve() / archive_sha[:12]
    files = []
    pair_candidates = {}

    try:
        archive = zipfile.ZipFile(archive_path)
    except zipfile.BadZipFile as exc:
        raise ValueError("The selected file is not a readable ZIP archive.") from exc

    with archive:
        safe_members = _safe_archive_members(archive)
        for member, relative_path in safe_members:
            suffix = relative_path.suffix.lower()
            content = archive.read(member)
            item = {
                "path": relative_path.as_posix(),
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "kind": suffix.lstrip(".") or "other",
            }
            if suffix == ".xml":
                item["xml_profile"] = inspect_uad_xml(content)
            files.append(item)
            if suffix in {".xml", ".pdf"}:
                pair_candidates.setdefault(_pair_key(relative_path), {})[suffix.lstrip(".")] = relative_path.as_posix()
            if extract and suffix in SUPPORTED_CORPUS_SUFFIXES:
                target = (destination / Path(*relative_path.parts)).resolve()
                if destination not in target.parents:
                    raise ValueError(f"Archive member escapes the destination: {member.filename}")
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("wb") as target_file:
                    target_file.write(content)

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
