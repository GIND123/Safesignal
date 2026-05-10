"""Local validation for the packaged synthetic FHIR bundles."""

from __future__ import annotations

import json
from pathlib import Path

from safesignal.synthetic_data.catalog import iter_cases


def _load_bundle(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _iter_references(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "reference" and isinstance(value, str):
                yield value
            else:
                yield from _iter_references(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_references(item)


def test_bundles_are_transaction_bundles_with_one_patient() -> None:
    for case in iter_cases():
        bundle = _load_bundle(case.bundle_path)
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "transaction"
        patient_entries = [
            entry for entry in bundle["entry"]
            if entry["resource"]["resourceType"] == "Patient"
        ]
        assert len(patient_entries) == 1
        assert patient_entries[0]["resource"]["id"] == case.patient_id


def test_bundle_request_urls_match_resource_ids() -> None:
    for case in iter_cases():
        bundle = _load_bundle(case.bundle_path)
        for entry in bundle["entry"]:
            resource = entry["resource"]
            request = entry["request"]
            expected_url = f"{resource['resourceType']}/{resource['id']}"
            assert request["method"] == "PUT"
            assert request["url"] == expected_url
            assert entry["fullUrl"] == expected_url


def test_all_patient_references_target_the_case_patient() -> None:
    for case in iter_cases():
        bundle = _load_bundle(case.bundle_path)
        patient_ref = f"Patient/{case.patient_id}"
        for entry in bundle["entry"]:
            resource = entry["resource"]
            if resource["resourceType"] == "Patient":
                continue
            for reference in _iter_references(resource):
                if reference.startswith("Patient/"):
                    assert reference == patient_ref


def test_encounters_use_portable_narrative_not_note() -> None:
    for case in iter_cases():
        bundle = _load_bundle(case.bundle_path)
        for entry in bundle["entry"]:
            resource = entry["resource"]
            if resource["resourceType"] != "Encounter":
                continue
            assert "note" not in resource
            assert resource["text"]["status"] == "generated"
            assert resource["text"]["div"].startswith("<div xmlns=\"http://www.w3.org/1999/xhtml\">")
