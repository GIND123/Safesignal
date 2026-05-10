"""Helpers for transporting packaged synthetic FHIR bundles."""

from __future__ import annotations

from copy import deepcopy


def to_transaction_bundle(bundle: dict) -> dict:
    """
    Convert a portable collection bundle into a transaction bundle that
    preserves client-assigned resource IDs during server-side loading.
    """
    if bundle.get("resourceType") != "Bundle":
        raise ValueError("Expected a FHIR Bundle resource")

    if bundle.get("type") == "transaction":
        return deepcopy(bundle)

    converted = deepcopy(bundle)
    converted["type"] = "transaction"
    converted_entries = []

    for index, entry in enumerate(converted.get("entry", [])):
        resource = entry.get("resource") or {}
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id")
        if not resource_type or not resource_id:
            raise ValueError(
                f"Bundle entry {index} must include resource.resourceType and resource.id"
            )

        converted_entries.append({
            "fullUrl": entry.get("fullUrl") or f"{resource_type}/{resource_id}",
            "resource": resource,
            "request": {
                "method": "PUT",
                "url": f"{resource_type}/{resource_id}",
            },
        })

    converted["entry"] = converted_entries
    return converted
