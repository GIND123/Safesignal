"""
Load the Margaret Chen synthetic FHIR bundle into a FHIR R4 server.

This script POSTs the transaction bundle from safesignal/synthetic_data/margaret_chen.json
to a FHIR server. After running this, use patient-mc-071 as the patient ID.

Usage:
    # Load to HAPI FHIR public sandbox (no auth needed):
    python scripts/load_margaret_chen.py

    # Load to a custom FHIR server:
    python scripts/load_margaret_chen.py --fhir-url https://your-fhir-server.com/r4

    # Load with auth token:
    python scripts/load_margaret_chen.py --fhir-url https://server.com/r4 --token eyJ...

After loading:
    FHIR URL:   https://hapi.fhir.org/baseR4  (or your server)
    Patient ID: patient-mc-071
    Token:      (none required for HAPI public sandbox — use any string)
"""
import argparse
import json
import pathlib
import sys

import httpx

BUNDLE_PATH = pathlib.Path(__file__).parent.parent / "safesignal" / "synthetic_data" / "margaret_chen.json"

DEFAULT_FHIR_URL = "https://hapi.fhir.org/baseR4"
PATIENT_ID       = "patient-mc-071"


def load_bundle(fhir_url: str, token: str | None) -> None:
    fhir_url = fhir_url.rstrip("/")

    with open(BUNDLE_PATH) as f:
        bundle = json.load(f)

    headers = {"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    print(f"Loading Margaret Chen FHIR bundle to: {fhir_url}")
    print(f"Bundle entries: {len(bundle.get('entry', []))}")
    print()

    try:
        resp = httpx.post(fhir_url, json=bundle, headers=headers, timeout=60)
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
    print(f"Bundle transaction complete. {entry_count} resources processed.")
    print()

    # Check for errors in individual entries
    errors = []
    for i, entry in enumerate(result.get("entry", [])):
        response = entry.get("response", {})
        status   = response.get("status", "")
        if status.startswith("4") or status.startswith("5"):
            errors.append(f"  Entry {i}: {status} — {response.get('outcome', {})}")

    if errors:
        print(f"WARNING: {len(errors)} entries had errors:")
        for e in errors:
            print(e)
    else:
        print("All resources loaded successfully.")

    print()
    print("─" * 60)
    print("SafeSignal Demo Configuration")
    print("─" * 60)
    print(f"  FHIR URL:   {fhir_url}")
    print(f"  Patient ID: {PATIENT_ID}")
    print(f"  Token:      {token or '(any string — HAPI public needs no real token)'}")
    print()
    print("In Prompt Opinion, set the SHARP context to:")
    print(f'  patientId:  "{PATIENT_ID}"')
    print(f'  fhirUrl:    "{fhir_url}"')
    print(f'  fhirToken:  "{token or "demo-token"}"')
    print()
    print("Then ask SafeSignal:")
    print('  "What should I know before seeing this patient today?"')


def verify_patient(fhir_url: str, token: str | None) -> None:
    fhir_url = fhir_url.rstrip("/")
    headers  = {"Accept": "application/fhir+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    print(f"\nVerifying patient {PATIENT_ID}...")
    try:
        resp = httpx.get(f"{fhir_url}/Patient/{PATIENT_ID}", headers=headers, timeout=15)
        if resp.status_code == 200:
            p    = resp.json()
            name = p.get("name", [{}])[0]
            full = f"{' '.join(name.get('given', []))} {name.get('family', '')}".strip()
            print(f"  Found: {full} (ID: {PATIENT_ID})")
        else:
            print(f"  Not found (HTTP {resp.status_code}) — run load_margaret_chen.py first")
    except Exception as exc:
        print(f"  Verification failed: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load Margaret Chen synthetic patient into a FHIR server")
    parser.add_argument("--fhir-url", default=DEFAULT_FHIR_URL, help="FHIR R4 server base URL")
    parser.add_argument("--token",    default=None,             help="Bearer token for authentication")
    parser.add_argument("--verify-only", action="store_true",   help="Only verify if patient exists, don't load")
    args = parser.parse_args()

    if args.verify_only:
        verify_patient(args.fhir_url, args.token)
    else:
        load_bundle(args.fhir_url, args.token)
        verify_patient(args.fhir_url, args.token)
