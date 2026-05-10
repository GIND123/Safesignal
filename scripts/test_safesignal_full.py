"""
SafeSignal Full System Test

Tests every layer of the SafeSignal stack:
  1. RxNorm API
  2. FDA OpenFDA API
  3. FDA label cross-reference interactions
  4. Knowledge enrichment layer
  5. FHIR bundle loading and retrieval
  6. MCP tool: check_medication_safety
  7. MCP tool: detect_silent_deterioration
  8. MCP tool: find_lost_followups
  9. MCP tool: generate_risk_briefing

Usage:
    python scripts/test_safesignal_full.py --load
    python scripts/test_safesignal_full.py --case samuel_brooks_extreme --load
    python scripts/test_safesignal_full.py --case natalie_cho_sparse --tool briefing --load
    python scripts/test_safesignal_full.py --list-cases
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent.parent / ".env")

import httpx

from safesignal.synthetic_data.catalog import CASE_CHOICES, DEFAULT_CASE_KEY, SyntheticCase, get_case
from safesignal.synthetic_data.bundle_utils import to_transaction_bundle

FHIR_URL = "https://hapi.fhir.org/baseR4"
FHIR_TOKEN = "demo-token"

CANONICAL_ENRICHMENT_MEDS = [
    {"display": "Metformin 1000mg BID", "code": "860975", "resource_id": "MedicationRequest/demo-metformin"},
    {"display": "Warfarin 5mg daily", "code": "855332", "resource_id": "MedicationRequest/demo-warfarin"},
    {"display": "Lisinopril 20mg daily", "code": "314076", "resource_id": "MedicationRequest/demo-lisinopril"},
    {"display": "Ibuprofen 400mg PRN", "code": "197806", "resource_id": "MedicationRequest/demo-ibuprofen"},
]


def _header(title: str) -> None:
    print("\n" + "-" * 60)
    print(f"  {title}")
    print("-" * 60)


def _ok(msg: str) -> None:
    print(f"  [PASS] {msg}")


def _fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")


def _info(msg: str) -> None:
    print(f"  [INFO] {msg}")


def _ascii_preview(text: str, limit: int = 2000) -> str:
    clipped = text[:limit]
    preview = clipped.encode("ascii", errors="replace").decode("ascii")
    if len(text) > limit:
        preview += "\n...[truncated]"
    return preview


def _required_hits(keywords: tuple[str, ...]) -> int:
    if not keywords:
        return 0
    return 2 if len(keywords) >= 3 else 1


def _validate_tool_output(result: str | None, keywords: tuple[str, ...], label: str) -> bool:
    if not result:
        _fail(f"{label} returned no output")
        return False
    lowered = result.lower()
    if "[llm error:" in lowered or lowered.startswith("fhir server error") or lowered.startswith("fhir connection error"):
        _fail(f"{label} returned an error payload")
        return False
    if not keywords:
        _ok(f"{label} returned a non-empty response")
        return True
    found = [kw for kw in keywords if kw.lower() in lowered]
    _ok(f"Expected clinical keywords found: {found}")
    return len(found) >= _required_hits(keywords)


def _print_case_list() -> None:
    print("Available synthetic cases:")
    for case_key in CASE_CHOICES:
        case = get_case(case_key)
        print(f"  - {case.key}: {case.patient_name} - {case.summary}")


def test_rxnorm() -> bool:
    _header("Phase 1a: RxNorm RxCUI Lookup")
    from safesignal.tools.knowledge_enrichment import lookup_rxcui

    test_cases = [
        ("metformin", True),
        ("warfarin", True),
        ("lisinopril", True),
        ("ibuprofen", True),
        ("notadrug999", False),
    ]

    passed = 0
    for name, should_find in test_cases:
        rxcui = lookup_rxcui(name)
        if should_find and rxcui:
            _ok(f"{name!r} -> RxCUI {rxcui}")
            passed += 1
        elif not should_find and not rxcui:
            _ok(f"{name!r} -> correctly not found")
            passed += 1
        else:
            _fail(f"{name!r} -> expected {'found' if should_find else 'not found'}, got {rxcui!r}")

    print(f"\n  Result: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_fda_labels() -> bool:
    _header("Phase 1b: FDA OpenFDA Drug Label Lookup")
    from safesignal.tools.knowledge_enrichment import lookup_fda_label

    ingredients = ["metformin", "warfarin", "lisinopril", "ibuprofen"]
    found = 0

    for ingredient in ingredients:
        label = lookup_fda_label(ingredient)
        if label:
            found += 1
            parts = []
            if label.get("boxed_warning"):
                parts.append("boxed_warning")
            if label.get("contraindications"):
                parts.append("contraindications")
            if label.get("warnings"):
                parts.append("warnings")
            if label.get("drug_interactions"):
                parts.append("drug_interactions")
            _ok(f"{ingredient!r}: found [{', '.join(parts) or 'label data'}]")
            if label.get("boxed_warning"):
                preview = label["boxed_warning"][:120].replace("\n", " ").encode("ascii", errors="replace").decode("ascii")
                _info(f"  Boxed warning preview: {preview}...")
        else:
            _fail(f"{ingredient!r}: no label data returned (check FDA_API_KEY env var)")

    print(f"\n  Result: {found}/{len(ingredients)} labels retrieved")
    return found >= 2


def test_nlm_interactions() -> bool:
    _header("Phase 1c: NLM + FDA Interaction Scan (enrich_medications)")
    _info("Calls NLM RxNav ONCHigh per drug; FDA label cross-reference fills any gaps.")
    from safesignal.tools.knowledge_enrichment import enrich_medications

    meds = [
        {"display": "Warfarin 5mg daily", "code": "855332", "resource_id": "MedicationRequest/demo-warfarin"},
        {"display": "Ibuprofen 400mg PRN", "code": "197806", "resource_id": "MedicationRequest/demo-ibuprofen"},
    ]
    result = enrich_medications(meds)
    interactions = result["drug_interactions"]

    if interactions:
        _ok(f"Found {len(interactions)} FDA-label-cited interaction(s)")
        for interaction in interactions[:3]:
            _info(f"  {interaction['drug1']} <-> {interaction['drug2']} (severity: {interaction['severity']})")
            desc = interaction["description"][:100].encode("ascii", errors="replace").decode("ascii")
            _info(f"  {desc}...")
        return True

    _fail("No FDA label interactions found for Warfarin+Ibuprofen pair")
    return False


def test_enrichment_pipeline() -> bool:
    _header("Phase 1d: Full Enrichment Pipeline (enrich_medications)")
    from safesignal.tools.knowledge_enrichment import enrich_medications

    t0 = time.time()
    result = enrich_medications(CANONICAL_ENRICHMENT_MEDS)
    elapsed = time.time() - t0

    enriched = result["medications_enriched"]
    interactions = result["drug_interactions"]
    sources = result["enrichment_sources"]

    _ok(f"Enrichment completed in {elapsed:.1f}s")
    _ok(f"Sources: {sources}")

    fda_fields_found = 0
    for med in enriched:
        name = med.get("rxnorm_ingredient", "?")
        rxcui = med.get("rxcui", "?")
        fields = [key for key in med if key.startswith("fda_")]
        _info(f"{name!r}: rxcui={rxcui}, FDA fields={fields}")
        if fields:
            fda_fields_found += 1

    _ok(f"Medications with FDA data: {fda_fields_found}/{len(enriched)}")
    _ok(f"FDA label interactions detected: {len(interactions)}")

    for interaction in interactions[:5]:
        desc = interaction["description"][:80].encode("ascii", errors="replace").decode("ascii")
        _info(f"  {interaction['drug1']} <-> {interaction['drug2']} -- {interaction['severity']}: {desc}...")

    return fda_fields_found > 0


def load_patient(fhir_url: str, case: SyntheticCase) -> bool:
    _header(f"Phase 2a: Load Synthetic FHIR Bundle ({case.patient_name})")

    with case.bundle_path.open(encoding="utf-8") as f:
        bundle = json.load(f)
    upload_bundle = to_transaction_bundle(bundle)

    _info(
        f"POSTing upload bundle ({len(upload_bundle.get('entry', []))} entries, source type={bundle.get('type', '(missing)')}) to {fhir_url}"
    )

    try:
        resp = httpx.post(
            fhir_url,
            json=upload_bundle,
            headers={"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"},
            timeout=60,
        )
        resp.raise_for_status()
        result = resp.json()
        entries_ok = sum(
            1 for entry in result.get("entry", [])
            if not str(entry.get("response", {}).get("status", "")).startswith(("4", "5"))
        )
        _ok(f"Bundle loaded: {entries_ok}/{len(result.get('entry', []))} resources OK")
        return True
    except Exception as exc:
        _fail(f"Bundle load failed: {exc}")
        return False


def verify_patient(fhir_url: str, case: SyntheticCase) -> bool:
    _header("Phase 2b: Verify Patient on FHIR Server")
    try:
        resp = httpx.get(
            f"{fhir_url}/Patient/{case.patient_id}",
            headers={"Accept": "application/fhir+json"},
            timeout=15,
        )
        if resp.status_code == 200:
            patient = resp.json()
            name = patient.get("name", [{}])[0]
            full_name = f"{' '.join(name.get('given', []))} {name.get('family', '')}".strip()
            _ok(f"Patient found: {full_name} (ID: {case.patient_id})")
            return True
        _fail(f"Patient not found (HTTP {resp.status_code}). Run with --load flag.")
        return False
    except Exception as exc:
        _fail(f"FHIR server unreachable: {exc}")
        return False


def test_fhir_data_retrieval(fhir_url: str, token: str, case: SyntheticCase) -> bool:
    _header("Phase 2c: FHIR Data Retrieval (all resource types)")
    from safesignal.tools.fhir_client import FHIRClient

    try:
        client = FHIRClient(fhir_url, token)
        context = client.get_full_patient_context(case.patient_id)
    except Exception as exc:
        _fail(f"FHIR retrieval failed: {exc}")
        return False

    actual_counts = {
        "conditions": len(context["conditions"]),
        "medications": len(context["medications"]),
        "observation_series": len(context["observation_series"]),
        "diagnostic_reports": len(context["diagnostic_reports"]),
        "encounters": len(context["encounters"]),
        "procedures": len(context["procedures"]),
        "service_requests": len(context["service_requests"]),
        "allergies": len(context["allergies"]),
    }

    patient_ok = bool(context["patient"])
    if patient_ok:
        _ok("Patient: retrieved")
    else:
        _fail("Patient: empty")

    all_ok = patient_ok
    for key, min_count in case.expected_min_counts.items():
        count = actual_counts[key]
        label = key.replace("_", " ").title()
        if count >= min_count:
            _ok(f"{label}: {count} retrieved (expected at least {min_count})")
        else:
            _fail(f"{label}: {count} retrieved (expected at least {min_count})")
            all_ok = False

    patient = context["patient"]
    _info(f"Patient: {patient.get('name')}, Age {patient.get('age')}, Sex {patient.get('sex')}")
    _info(f"Observation types: {list(context['observation_series'].keys())}")

    return all_ok


def _run_mcp_tool(tool_fn, tool_name: str, fhir_url: str, token: str, patient_id: str, **kwargs) -> str | None:
    _header(f"Phase 3: MCP Tool -- {tool_name}")
    _info(f"Calling {tool_name} for patient {patient_id}...")

    t0 = time.time()
    try:
        result = asyncio.run(
            tool_fn(
                patient_id=patient_id,
                fhir_url=fhir_url,
                fhir_token=token,
                **kwargs,
            )
        )
        elapsed = time.time() - t0
        _ok(f"Completed in {elapsed:.1f}s -- {len(result)} characters returned")
        return result
    except Exception as exc:
        _fail(f"{tool_name} failed: {exc}")
        return None


def test_medication_safety_mcp(fhir_url: str, token: str, case: SyntheticCase) -> bool:
    from safesignal_mcp.server import check_medication_safety

    result = _run_mcp_tool(
        check_medication_safety,
        "check_medication_safety",
        fhir_url,
        token,
        case.patient_id,
    )
    ok = _validate_tool_output(result, case.medication_keywords, "check_medication_safety")
    if result:
        print("\n" + "-" * 60)
        print(_ascii_preview(result))
    return ok


def test_deterioration_mcp(fhir_url: str, token: str, case: SyntheticCase) -> bool:
    from safesignal_mcp.server import detect_silent_deterioration

    result = _run_mcp_tool(
        detect_silent_deterioration,
        "detect_silent_deterioration",
        fhir_url,
        token,
        case.patient_id,
    )
    ok = _validate_tool_output(result, case.deterioration_keywords, "detect_silent_deterioration")
    if result:
        print("\n" + "-" * 60)
        print(_ascii_preview(result))
    return ok


def test_lost_followups_mcp(fhir_url: str, token: str, case: SyntheticCase) -> bool:
    from safesignal_mcp.server import find_lost_followups

    result = _run_mcp_tool(
        find_lost_followups,
        "find_lost_followups",
        fhir_url,
        token,
        case.patient_id,
    )
    ok = _validate_tool_output(result, case.followup_keywords, "find_lost_followups")
    if result:
        print("\n" + "-" * 60)
        print(_ascii_preview(result))
    return ok


def test_full_briefing_mcp(fhir_url: str, token: str, case: SyntheticCase) -> bool:
    from safesignal_mcp.server import generate_risk_briefing

    result = _run_mcp_tool(
        generate_risk_briefing,
        "generate_risk_briefing",
        fhir_url,
        token,
        case.patient_id,
        context=case.summary,
    )
    ok = _validate_tool_output(result, case.briefing_keywords, "generate_risk_briefing")
    if not result:
        return False

    urgency_found = "urgent" in result.lower()
    warning_found = "warning" in result.lower()
    compliance = "clinician review" in result.lower()
    fda_cited = "fda" in result.lower() or "label" in result.lower()

    if urgency_found:
        _ok("URGENT section present")
    else:
        _info("URGENT section not present")
    if warning_found:
        _ok("WARNING section present")
    else:
        _info("WARNING section not present")
    if compliance:
        _ok("Compliance disclaimer present")
    else:
        _fail("Compliance disclaimer missing")
        ok = False
    if fda_cited:
        _ok("FDA label evidence cited")
    else:
        _info("FDA evidence not explicitly cited")

    _header("FULL RISK BRIEFING OUTPUT")
    print(result.encode("ascii", errors="replace").decode("ascii"))
    return ok and compliance


def _print_summary(results: dict[str, bool]) -> None:
    _header("Test Summary")
    passed = sum(1 for ok in results.values() if ok)
    total = len(results)

    for name, ok in results.items():
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")

    print()
    if passed == total:
        print(f"  All {total} tests passed.")
    else:
        print(f"  {passed}/{total} tests passed.")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="SafeSignal full system test")
    parser.add_argument("--load", action="store_true", help="Load the selected bundle to HAPI FHIR before testing")
    parser.add_argument("--fhir-url", default=FHIR_URL, help=f"FHIR R4 server URL (default: {FHIR_URL})")
    parser.add_argument("--token", default=FHIR_TOKEN, help="FHIR bearer token (default: demo-token)")
    parser.add_argument("--enrichment-only", action="store_true", help="Only run knowledge enrichment tests")
    parser.add_argument("--case", default=DEFAULT_CASE_KEY, choices=CASE_CHOICES, help="Synthetic test case to exercise")
    parser.add_argument("--list-cases", action="store_true", help="Print available synthetic cases and exit")
    parser.add_argument(
        "--tool",
        choices=["medication_safety", "deterioration", "lost_followups", "briefing"],
        help="Run only one specific MCP tool test",
    )
    args = parser.parse_args()

    if args.list_cases:
        _print_case_list()
        return

    case = get_case(args.case)
    fhir_url = args.fhir_url
    token = args.token

    print("\nSafeSignal Full System Test")
    print(f"FHIR: {fhir_url}  |  Patient: {case.patient_id}  |  Date: {__import__('datetime').date.today()}")
    print(f"Case: {case.key} - {case.patient_name}")
    print(f"Scenario: {case.summary}")
    print(f"FDA API key: {'set' if os.getenv('FDA_API_KEY') else 'not set (anon rate limit)'}")
    print(f"Google API key: {'set' if os.getenv('GOOGLE_API_KEY') else 'NOT SET -- LLM tests will fail!'}")

    results: dict[str, bool] = {}

    if not args.tool:
        results["RxNorm lookup"] = test_rxnorm()
        results["FDA label lookup"] = test_fda_labels()
        results["FDA cross-ref interact"] = test_nlm_interactions()
        results["Enrichment pipeline"] = test_enrichment_pipeline()

    if args.enrichment_only:
        _print_summary(results)
        return

    if args.load:
        results["Patient load"] = load_patient(fhir_url, case)
    if not args.tool:
        results["Patient verify"] = verify_patient(fhir_url, case)
        results["FHIR data retrieval"] = test_fhir_data_retrieval(fhir_url, token, case)

    if not args.tool and not results.get("Patient verify", True):
        _header("SKIPPING LLM TOOL TESTS -- patient not found on FHIR server")
        _info("Run with --load to load the patient data first.")
        _print_summary(results)
        return

    if args.tool and not verify_patient(fhir_url, case):
        print("\nPatient not found. Run with --load to load patient data.")
        sys.exit(1)

    tool_map = {
        "medication_safety": ("Medication Safety MCP", test_medication_safety_mcp),
        "deterioration": ("Deterioration MCP", test_deterioration_mcp),
        "lost_followups": ("Lost Follow-Ups MCP", test_lost_followups_mcp),
        "briefing": ("Full Risk Briefing MCP", test_full_briefing_mcp),
    }

    if args.tool:
        name, fn = tool_map[args.tool]
        results[name] = fn(fhir_url, token, case)
    else:
        for _, (name, fn) in tool_map.items():
            results[name] = fn(fhir_url, token, case)

    _print_summary(results)


if __name__ == "__main__":
    main()
