import csv
import hashlib
import io
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

MAX_IMPORT_BYTES = 1_048_576
MAX_ROWS = 1_000
MAX_COLUMNS = 80
MAX_JSON_DEPTH = 10
MAX_SCALAR_LENGTH = 8_000
CSV_MIME_TYPES = {"text/csv", "application/csv", "text/plain"}
JSON_MIME_TYPES = {"application/json", "text/json"}
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
SPACE_RE = re.compile(r"\s+")
PHONE_RE = re.compile(r"\D+")


class ImportValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedImport:
    rows: list[dict[str, Any]]
    content_hash: str
    media_type: str


def _decode(payload: bytes) -> str:
    if len(payload) > MAX_IMPORT_BYTES:
        raise ImportValidationError(f"Import exceeds {MAX_IMPORT_BYTES} bytes")
    if b"\x00" in payload:
        raise ImportValidationError("NUL bytes are not permitted")
    try:
        return payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ImportValidationError("Import must be valid UTF-8") from exc


def _reject_unsafe_scalar(value: Any, *, depth: int = 0) -> None:
    if depth > MAX_JSON_DEPTH:
        raise ImportValidationError(f"JSON nesting exceeds {MAX_JSON_DEPTH} levels")
    if isinstance(value, dict):
        if len(value) > MAX_COLUMNS:
            raise ImportValidationError(f"Object exceeds {MAX_COLUMNS} fields")
        for key, item in value.items():
            if not isinstance(key, str) or not key or len(key) > 120:
                raise ImportValidationError("JSON keys must be 1 to 120 characters")
            _reject_unsafe_scalar(item, depth=depth + 1)
    elif isinstance(value, list):
        if len(value) > MAX_ROWS:
            raise ImportValidationError(f"Array exceeds {MAX_ROWS} items")
        for item in value:
            _reject_unsafe_scalar(item, depth=depth + 1)
    elif isinstance(value, str) and len(value) > MAX_SCALAR_LENGTH:
        raise ImportValidationError(f"Text value exceeds {MAX_SCALAR_LENGTH} characters")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ImportValidationError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(payload: bytes, media_type: str) -> ParsedImport:
    if media_type.split(";", 1)[0].strip().casefold() not in JSON_MIME_TYPES:
        raise ImportValidationError("JSON content type is not allowed")
    text = _decode(payload)
    try:
        value = json.loads(text, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ImportValidationError("Malformed JSON import") from exc
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ImportValidationError("JSON import must be an array of objects")
    if len(value) > MAX_ROWS:
        raise ImportValidationError(f"Import exceeds {MAX_ROWS} rows")
    _reject_unsafe_scalar(value)
    return ParsedImport(value, hashlib.sha256(payload).hexdigest(), "application/json")


def parse_csv(payload: bytes, media_type: str) -> ParsedImport:
    if media_type.split(";", 1)[0].strip().casefold() not in CSV_MIME_TYPES:
        raise ImportValidationError("CSV content type is not allowed")
    text = _decode(payload)
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        header = next(reader)
    except (StopIteration, csv.Error) as exc:
        raise ImportValidationError("CSV requires a header row") from exc
    normalized_header = [item.strip() for item in header]
    if not normalized_header or len(normalized_header) > MAX_COLUMNS:
        raise ImportValidationError(f"CSV must contain 1 to {MAX_COLUMNS} columns")
    if any(not item or len(item) > 120 for item in normalized_header):
        raise ImportValidationError("CSV headers must be 1 to 120 characters")
    folded = [item.casefold() for item in normalized_header]
    if len(folded) != len(set(folded)):
        raise ImportValidationError("Duplicate CSV headers are not permitted")
    rows: list[dict[str, Any]] = []
    try:
        for line_number, values in enumerate(reader, start=2):
            if line_number > MAX_ROWS + 1:
                raise ImportValidationError(f"Import exceeds {MAX_ROWS} rows")
            if len(values) != len(normalized_header):
                raise ImportValidationError(f"CSV row {line_number} has the wrong column count")
            for value in values:
                if len(value) > MAX_SCALAR_LENGTH:
                    raise ImportValidationError(
                        f"CSV row {line_number} contains an oversized value"
                    )
                if value.lstrip().startswith(FORMULA_PREFIXES):
                    raise ImportValidationError(
                        f"CSV row {line_number} contains a spreadsheet formula"
                    )
            rows.append(dict(zip(normalized_header, values, strict=True)))
    except csv.Error as exc:
        raise ImportValidationError("Malformed CSV import") from exc
    return ParsedImport(rows, hashlib.sha256(payload).hexdigest(), "text/csv")


def parse_import(payload: bytes, media_type: str, filename: str) -> ParsedImport:
    safe_name = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    if not safe_name or safe_name != filename or len(safe_name) > 240:
        raise ImportValidationError("Unsafe import filename")
    suffix = safe_name.rsplit(".", 1)[-1].casefold() if "." in safe_name else ""
    if suffix == "csv":
        return parse_csv(payload, media_type)
    if suffix == "json":
        return parse_json(payload, media_type)
    raise ImportValidationError("Only .csv and .json imports are supported")


def normalize_text(value: Any) -> str:
    return SPACE_RE.sub(" ", str(value or "").strip().casefold())


def normalized_record(record: dict[str, Any]) -> dict[str, str]:
    website = normalize_text(record.get("website") or record.get("source_url"))
    return {
        "organization": normalize_text(
            record.get("organization_name") or record.get("organization")
        ),
        "program": normalize_text(record.get("program_name") or record.get("name")),
        "phone": PHONE_RE.sub("", normalize_text(record.get("phone"))),
        "address": normalize_text(record.get("address")),
        "website_domain": (urlparse(website).hostname or "").casefold(),
        "source_identifier": normalize_text(record.get("source_identifier") or record.get("id")),
        "geographic_scope": normalize_text(record.get("geographic_scope")),
    }


def record_fingerprint(record: dict[str, Any]) -> str:
    normalized = normalized_record(record)
    canonical = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def classify_duplicate(candidate: dict[str, Any], existing: Iterable[dict[str, Any]]) -> str:
    target = normalized_record(candidate)
    best_score = 0
    conflict = False
    for record in existing:
        current = normalized_record(record)
        if (
            target["source_identifier"]
            and target["source_identifier"] == current["source_identifier"]
        ):
            return "exact_match" if target == current else "conflict_with_published"
        fields = (
            "organization",
            "program",
            "phone",
            "address",
            "website_domain",
            "geographic_scope",
        )
        score = sum(bool(target[field]) and target[field] == current[field] for field in fields)
        if score >= 5:
            return "exact_match"
        if score >= 3:
            best_score = max(best_score, score)
        if (
            score >= 2
            and target["phone"]
            and current["phone"]
            and target["phone"] != current["phone"]
        ):
            conflict = True
    if conflict and best_score >= 3:
        return "conflict_with_published"
    if best_score >= 3:
        return "likely_duplicate"
    if best_score == 2:
        return "possible_duplicate"
    return "new_resource"
