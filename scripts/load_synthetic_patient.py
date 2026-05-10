"""Load one of the packaged SafeSignal synthetic FHIR bundles into a FHIR server."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

import httpx

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from safesignal.synthetic_data.catalog import CASE_CHOICES, DEFAULT_CASE_KEY, get_case
from safesignal.synthetic_data.bundle_utils import to_transaction_bundle

DEFAULT_FHIR_URL = "https://hapi.fhir.org/baseR4"


def load_bundle(case_key: str, fhir_url: str, token: str | None) -> None:
    case = get_case(case_key)
    fhir_url = fhir_url.rstrip("/")

    with case.bundle_path.open(encoding="utf-8") as f:
        bundle = json.load(f)
    upload_bundle = to_transaction_bundle(bundle)

    headers = {"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    print(f"Loading synthetic case '{case.key}' ({case.patient_name}) to: {fhir_url}")
    print(f"Bundle entries: {len(bundle.get('entry', []))}")
    print(f"Bundle type: {bundle.get('type', '(missing)')}")
    if bundle.get("type") != "transaction":
        print("Upload mode: converted to transaction bundle to preserve stable resource IDs")
    print(f"Scenario: {case.summary}")
    print()

    try:
        resp = httpx.post(fhir_url, json=upload_bundle, headers=headers, timeout=60)
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        print(f"ERROR: FHIR server returned HTTP {exc.response.status_code}")
        print(exc.response.text[:500])
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    result = resp.json()
    entry_count = len(result.get("entry", []))
    print(f"Bundle upload complete. {entry_count} resources processed.")
    print()

    errors = []
    for i, entry in enumerate(result.get("entry", [])):
        response = entry.get("response", {})
        status = response.get("status", "")
        if status.startswith("4") or status.startswith("5"):
            errors.append(f"  Entry {i}: {status} - {response.get('outcome', {})}")

    if errors:
        print(f"WARNING: {len(errors)} entries had errors:")
        for error in errors:
            print(error)
    else:
        print("All resources loaded successfully.")

    print()
    print("-" * 60)
    print("SafeSignal Demo Configuration")
    print("-" * 60)
    print(f"  Case:       {case.key}")
    print(f"  Patient:    {case.patient_name}")
    print(f"  Patient ID: {case.patient_id}")
    print(f"  FHIR URL:   {fhir_url}")
    print(f"  Token:      {token or '(any string - HAPI public needs no real token)'}")
    print()
    print("In Prompt Opinion, set the SHARP context to:")
    print(f'  patientId:  "{case.patient_id}"')
    print(f'  fhirUrl:    "{fhir_url}"')
    print(f'  fhirToken:  "{token or "demo-token"}"')
    print()
    print("Then ask SafeSignal:")
    print('  "What should I know before seeing this patient today?"')


def verify_patient(case_key: str, fhir_url: str, token: str | None) -> None:
    case = get_case(case_key)
    fhir_url = fhir_url.rstrip("/")
    headers = {"Accept": "application/fhir+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    print(f"\nVerifying patient {case.patient_id}...")
    try:
        resp = httpx.get(f"{fhir_url}/Patient/{case.patient_id}", headers=headers, timeout=15)
        if resp.status_code == 200:
            patient = resp.json()
            name = patient.get("name", [{}])[0]
            full_name = f"{' '.join(name.get('given', []))} {name.get('family', '')}".strip()
            print(f"  Found: {full_name} (ID: {case.patient_id})")
        else:
            print(f"  Not found (HTTP {resp.status_code}) - run load_synthetic_patient.py first")
    except Exception as exc:
        print(f"  Verification failed: {exc}")


def _print_case_list() -> None:
    print("Available synthetic cases:")
    for case_key in CASE_CHOICES:
        case = get_case(case_key)
        print(f"  - {case.key}: {case.patient_name} - {case.summary}")


def main(default_case: str = DEFAULT_CASE_KEY) -> int:
    parser = argparse.ArgumentParser(description="Load a SafeSignal synthetic patient into a FHIR server")
    parser.add_argument("--case", default=default_case, choices=CASE_CHOICES, help="Synthetic case to load")
    parser.add_argument("--fhir-url", default=DEFAULT_FHIR_URL, help="FHIR R4 server base URL")
    parser.add_argument("--token", default=None, help="Bearer token for authentication")
    parser.add_argument("--verify-only", action="store_true", help="Only verify if patient exists, do not load")
    parser.add_argument("--list-cases", action="store_true", help="Print available synthetic cases")
    args = parser.parse_args()

    if args.list_cases:
        _print_case_list()
        return 0

    if args.verify_only:
        verify_patient(args.case, args.fhir_url, args.token)
    else:
        load_bundle(args.case, args.fhir_url, args.token)
        verify_patient(args.case, args.fhir_url, args.token)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
