import json

import pytest

from civicsignal_api.services.imports import (
    ImportValidationError,
    classify_duplicate,
    parse_import,
    record_fingerprint,
)


def test_csv_import_is_bounded_and_rejects_formulas_and_path_traversal() -> None:
    parsed = parse_import(
        b"id,name,phone\n1,Community Pantry,508-555-0100\n",
        "text/csv; charset=utf-8",
        "resources.csv",
    )
    assert parsed.rows[0]["name"] == "Community Pantry"
    assert len(parsed.content_hash) == 64
    with pytest.raises(ImportValidationError, match="formula"):
        parse_import(b'id,name\n1,=HYPERLINK("x")\n', "text/csv", "resources.csv")
    with pytest.raises(ImportValidationError, match="filename"):
        parse_import(b"id,name\n1,Safe\n", "text/csv", "../resources.csv")


def test_json_import_rejects_duplicate_keys_depth_and_wrong_shape() -> None:
    parsed = parse_import(
        json.dumps([{"id": "one", "name": "Community Pantry"}]).encode(),
        "application/json",
        "resources.json",
    )
    assert parsed.rows[0]["id"] == "one"
    with pytest.raises(ImportValidationError, match="Duplicate JSON key"):
        parse_import(b'[{"id":"one","id":"two"}]', "application/json", "resources.json")
    deep: object = "value"
    for _ in range(12):
        deep = {"child": deep}
    with pytest.raises(ImportValidationError, match="nesting"):
        parse_import(json.dumps([deep]).encode(), "application/json", "resources.json")
    with pytest.raises(ImportValidationError, match="array of objects"):
        parse_import(b'{"id":"one"}', "application/json", "resources.json")


def test_deduplication_is_deterministic_and_never_silently_merges() -> None:
    existing = {
        "source_identifier": "example-veterans",
        "organization_name": "Example County",
        "name": "Veterans Services",
        "phone": "508-322-3389",
        "address": "26 Court Street, Example City, MA",
        "website": "https://example.gov/veterans",
        "geographic_scope": "Example County, Massachusetts",
    }
    assert classify_duplicate(dict(existing), [existing]) == "exact_match"
    changed = {**existing, "phone": "508-555-9999"}
    assert classify_duplicate(changed, [existing]) == "conflict_with_published"
    new = {"source_identifier": "new", "name": "Different service"}
    assert classify_duplicate(new, [existing]) == "new_resource"
    assert record_fingerprint(existing) == record_fingerprint(
        dict(reversed(list(existing.items())))
    )
