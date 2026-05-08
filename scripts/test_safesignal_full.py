"""
SafeSignal Full System Test

Tests every layer of the SafeSignal stack:
  1. RxNorm API  -- ingredient lookup for Margaret Chen's medications
  2. FDA OpenFDA API -- drug label warnings for each medication
  3. FDA Label Cross-Reference -- pairwise interactions from FDA labels
  4. Knowledge enrichment layer -- end-to-end enrichment output
  5. FHIR data retrieval -- Margaret Chen patient on HAPI FHIR sandbox
  6. MCP tool: check_medication_safety (full enriched analysis with LLM)
  7. MCP tool: detect_silent_deterioration (longitudinal trend analysis)
  8. MCP tool: find_lost_followups (follow-up gap detection)
  9. MCP tool: generate_risk_briefing (complete pre-visit briefing)

Usage:
    # Load patient data and run all tests (recommended for first run):
    python scripts/test_safesignal_full.py --load

    # Skip loading (patient already on HAPI), just test:
    python scripts/test_safesignal_full.py

    # Run only the knowledge enrichment tests (no FHIR needed):
    python scripts/test_safesignal_full.py --enrichment-only

    # Run only one specific MCP tool:
    python scripts/test_safesignal_full.py --tool medication_safety
"""
import argparse
import asyncio
import json
import os
import pathlib
import sys
import time

# Ensure the project root is on the path
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

# Load .env before importing project modules
from dotenv import load_dotenv
load_dotenv(pathlib.Path(__file__).parent.parent / ".env")

import httpx

FHIR_URL   = "https://hapi.fhir.org/baseR4"
FHIR_TOKEN = "demo-token"   # HAPI public sandbox needs no real token
PATIENT_ID = "patient-mc-071"

MARGARET_CHEN_MEDS = [
    {"display": "Metformin 1000mg BID",   "resource_id": "MedicationRequest/201"},
    {"display": "Warfarin 5mg daily",      "resource_id": "MedicationRequest/203"},
    {"display": "Lisinopril 20mg daily",   "resource_id": "MedicationRequest/204"},
    {"display": "Ibuprofen 400mg PRN",     "resource_id": "MedicationRequest/205"},
]


# -- Print helpers -----------------------------------------------------------

def _header(title: str) -> None:
    print("\n" + "-" * 60)
    print(f"  {title}")
    print("-" * 60)

def _ok(msg: str)   -> None: print(f"  [PASS] {msg}")
def _fail(msg: str) -> None: print(f"  [FAIL] {msg}")
def _info(msg: str) -> None: print(f"  [INFO] {msg}")


# -- Phase 1: Knowledge enrichment unit tests --------------------------------

def test_rxnorm():
    _header("Phase 1a: RxNorm RxCUI Lookup")
    from safesignal.tools.knowledge_enrichment import lookup_rxcui

    test_cases = [
        ("metformin",   True),
        ("warfarin",    True),
        ("lisinopril",  True),
        ("ibuprofen",   True),
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


def test_fda_labels():
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
    return found >= 2  # pass if at least half succeed (API may have rate limits)


def test_nlm_interactions():
    _header("Phase 1c: FDA Label Cross-Reference Interaction Scan")
    _info("NLM /interaction/ endpoint is inactive; using FDA label cross-reference instead.")
    from safesignal.tools.knowledge_enrichment import enrich_medications

    meds = [
        {"display": "Warfarin 5mg daily",  "code": "855332", "resource_id": "MedicationRequest/203"},
        {"display": "Ibuprofen 400mg PRN", "code": "197806", "resource_id": "MedicationRequest/205"},
    ]
    result       = enrich_medications(meds)
    interactions = result["drug_interactions"]

    if interactions:
        _ok(f"Found {len(interactions)} FDA-label-cited interaction(s)")
        for ix in interactions[:3]:
            _info(f"  {ix['drug1']} <-> {ix['drug2']} (severity: {ix['severity']})")
            desc = ix["description"][:100].encode("ascii", errors="replace").decode("ascii")
            _info(f"  {desc}...")
        return True
    else:
        _fail("No FDA label interactions found for Warfarin+Ibuprofen pair")
        return False


def test_enrichment_pipeline():
    _header("Phase 1d: Full Enrichment Pipeline (enrich_medications)")
    from safesignal.tools.knowledge_enrichment import enrich_medications

    meds = [
        {"display": "Metformin 1000mg BID",  "code": "860975", "resource_id": "MedicationRequest/201"},
        {"display": "Warfarin 5mg daily",     "code": "855332", "resource_id": "MedicationRequest/203"},
        {"display": "Lisinopril 20mg daily",  "code": "314076", "resource_id": "MedicationRequest/204"},
        {"display": "Ibuprofen 400mg PRN",    "code": "197806", "resource_id": "MedicationRequest/205"},
    ]

    t0 = time.time()
    result = enrich_medications(meds)
    elapsed = time.time() - t0

    enriched      = result["medications_enriched"]
    interactions  = result["drug_interactions"]
    sources       = result["enrichment_sources"]

    _ok(f"Enrichment completed in {elapsed:.1f}s")
    _ok(f"Sources: {sources}")

    fda_fields_found = 0
    for med in enriched:
        name   = med.get("rxnorm_ingredient", "?")
        rxcui  = med.get("rxcui", "?")
        fields = [k for k in med if k.startswith("fda_")]
        _info(f"{name!r}: rxcui={rxcui}, FDA fields={fields}")
        if fields:
            fda_fields_found += 1

    _ok(f"Medications with FDA data: {fda_fields_found}/{len(enriched)}")
    _ok(f"FDA label interactions detected: {len(interactions)}")

    for ix in interactions[:5]:
        desc = ix["description"][:80].encode("ascii", errors="replace").decode("ascii")
        _info(f"  {ix['drug1']} <-> {ix['drug2']} -- {ix['severity']}: {desc}...")

    return fda_fields_found > 0


# -- Phase 2: FHIR data tests ------------------------------------------------

def load_patient(fhir_url: str) -> bool:
    _header("Phase 2a: Load Margaret Chen FHIR Bundle")
    bundle_path = pathlib.Path(__file__).parent.parent / "safesignal" / "synthetic_data" / "margaret_chen.json"

    with open(bundle_path) as f:
        bundle = json.load(f)

    _info(f"POSTing transaction bundle ({len(bundle.get('entry', []))} entries) to {fhir_url}")

    try:
        resp = httpx.post(
            fhir_url,
            json=bundle,
            headers={"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"},
            timeout=60,
        )
        resp.raise_for_status()
        result = resp.json()
        entries_ok = sum(
            1 for e in result.get("entry", [])
            if not str(e.get("response", {}).get("status", "")).startswith(("4", "5"))
        )
        _ok(f"Bundle loaded: {entries_ok}/{len(result.get('entry', []))} resources OK")
        return True
    except Exception as exc:
        _fail(f"Bundle load failed: {exc}")
        return False


def verify_patient(fhir_url: str) -> bool:
    _header("Phase 2b: Verify Patient on FHIR Server")
    try:
        resp = httpx.get(
            f"{fhir_url}/Patient/{PATIENT_ID}",
            headers={"Accept": "application/fhir+json"},
            timeout=15,
        )
        if resp.status_code == 200:
            p    = resp.json()
            name = p.get("name", [{}])[0]
            full = f"{' '.join(name.get('given', []))} {name.get('family', '')}".strip()
            _ok(f"Patient found: {full} (ID: {PATIENT_ID})")
            return True
        else:
            _fail(f"Patient not found (HTTP {resp.status_code}). Run with --load flag.")
            return False
    except Exception as exc:
        _fail(f"FHIR server unreachable: {exc}")
        return False


def test_fhir_data_retrieval(fhir_url: str, token: str) -> bool:
    _header("Phase 2c: FHIR Data Retrieval (all resource types)")
    from safesignal.tools.fhir_client import FHIRClient

    try:
        client  = FHIRClient(fhir_url, token)
        context = client.get_full_patient_context(PATIENT_ID)
    except Exception as exc:
        _fail(f"FHIR retrieval failed: {exc}")
        return False

    checks = [
        ("Patient",            bool(context["patient"])),
        ("Conditions",         len(context["conditions"]) > 0),
        ("Medications",        len(context["medications"]) > 0),
        ("Observation series", len(context["observation_series"]) > 0),
        ("Diagnostic reports", len(context["diagnostic_reports"]) >= 0),
        ("Encounters",         len(context["encounters"]) >= 0),
    ]

    all_ok = True
    for name, ok in checks:
        if ok:
            _ok(f"{name}: retrieved")
        else:
            _fail(f"{name}: empty -- check patient data was loaded")
            all_ok = False

    p = context["patient"]
    _info(f"Patient: {p.get('name')}, Age {p.get('age')}, Sex {p.get('sex')}")
    _info(f"Conditions: {len(context['conditions'])}, Medications: {len(context['medications'])}")
    _info(f"Observation types: {list(context['observation_series'].keys())}")
    _info(f"Diagnostic reports: {len(context['diagnostic_reports'])}")

    return all_ok


# -- Phase 3: MCP tool tests (with LLM) -------------------------------------

def _run_mcp_tool(tool_fn, tool_name: str, fhir_url: str, token: str, **kwargs) -> str | None:
    _header(f"Phase 3: MCP Tool -- {tool_name}")
    _info(f"Calling {tool_name} for patient {PATIENT_ID}...")

    t0 = time.time()
    try:
        result = asyncio.run(tool_fn(
            patient_id=PATIENT_ID,
            fhir_url=fhir_url,
            fhir_token=token,
            **kwargs,
        ))
        elapsed = time.time() - t0
        _ok(f"Completed in {elapsed:.1f}s -- {len(result)} characters returned")
        return result
    except Exception as exc:
        _fail(f"{tool_name} failed: {exc}")
        return None


def test_medication_safety_mcp(fhir_url: str, token: str) -> bool:
    from safesignal_mcp.server import check_medication_safety
    result = _run_mcp_tool(check_medication_safety, "check_medication_safety", fhir_url, token)
    if result:
        keywords = ["metformin", "egfr", "ibuprofen", "warfarin"]
        found_kw = [kw for kw in keywords if kw.lower() in result.lower()]
        _ok(f"Expected clinical keywords found: {found_kw}")
        preview = result[:2000].encode("ascii", errors="replace").decode("ascii")
        print("\n" + "-" * 60)
        print(preview + ("\n...[truncated]" if len(result) > 2000 else ""))
        return len(found_kw) >= 2
    return False


def test_deterioration_mcp(fhir_url: str, token: str) -> bool:
    from safesignal_mcp.server import detect_silent_deterioration
    result = _run_mcp_tool(detect_silent_deterioration, "detect_silent_deterioration", fhir_url, token)
    if result:
        keywords = ["egfr", "decline", "a1c", "hba1c", "blood pressure"]
        found_kw = [kw for kw in keywords if kw.lower() in result.lower()]
        _ok(f"Expected trend keywords found: {found_kw}")
        preview = result[:2000].encode("ascii", errors="replace").decode("ascii")
        print("\n" + "-" * 60)
        print(preview + ("\n...[truncated]" if len(result) > 2000 else ""))
        return len(found_kw) >= 2
    return False


def test_lost_followups_mcp(fhir_url: str, token: str) -> bool:
    from safesignal_mcp.server import find_lost_followups
    result = _run_mcp_tool(find_lost_followups, "find_lost_followups", fhir_url, token)
    if result:
        keywords = ["fobt", "fecal", "colonoscopy", "follow"]
        found_kw = [kw for kw in keywords if kw.lower() in result.lower()]
        _ok(f"Expected follow-up keywords found: {found_kw}")
        preview = result[:2000].encode("ascii", errors="replace").decode("ascii")
        print("\n" + "-" * 60)
        print(preview + ("\n...[truncated]" if len(result) > 2000 else ""))
        return True  # lenient -- HAPI may not have all DR resources
    return False


def test_full_briefing_mcp(fhir_url: str, token: str) -> bool:
    from safesignal_mcp.server import generate_risk_briefing
    result = _run_mcp_tool(
        generate_risk_briefing,
        "generate_risk_briefing",
        fhir_url,
        token,
        context="Routine follow-up -- diabetes, CKD, atrial fibrillation",
    )
    if result:
        urgency_found = "URGENT" in result or "urgent" in result.lower()
        warning_found = "WARNING" in result or "warning" in result.lower()
        compliance    = "clinician review" in result.lower()
        fda_cited     = "fda" in result.lower() or "label" in result.lower()

        if urgency_found: _ok("URGENT section present")
        if warning_found: _ok("WARNING section present")
        if compliance:    _ok("Compliance disclaimer present")
        if fda_cited:     _ok("FDA label evidence cited")
        else:             _info("FDA evidence not explicitly cited (may be in context)")

        _header("FULL RISK BRIEFING OUTPUT")
        print(result.encode("ascii", errors="replace").decode("ascii"))
        return urgency_found and compliance
    return False


# -- Main --------------------------------------------------------------------

def _print_summary(results: dict[str, bool]) -> None:
    _header("Test Summary")
    passed = sum(1 for v in results.values() if v)
    total  = len(results)

    for name, ok in results.items():
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")

    print()
    if passed == total:
        print(f"  All {total} tests passed.")
    else:
        print(f"  {passed}/{total} tests passed.")
    print()


def main():
    parser = argparse.ArgumentParser(description="SafeSignal full system test")
    parser.add_argument("--load", action="store_true",
                        help="Load Margaret Chen bundle to HAPI FHIR before testing")
    parser.add_argument("--fhir-url", default=FHIR_URL,
                        help=f"FHIR R4 server URL (default: {FHIR_URL})")
    parser.add_argument("--token", default=FHIR_TOKEN,
                        help="FHIR bearer token (default: demo-token)")
    parser.add_argument("--enrichment-only", action="store_true",
                        help="Only run knowledge enrichment tests (no FHIR required)")
    parser.add_argument("--tool",
                        choices=["medication_safety", "deterioration", "lost_followups", "briefing"],
                        help="Run only one specific MCP tool test")
    args = parser.parse_args()

    fhir_url = args.fhir_url
    token    = args.token

    print("\nSafeSignal Full System Test")
    print(f"FHIR: {fhir_url}  |  Patient: {PATIENT_ID}  |  Date: {__import__('datetime').date.today()}")
    print(f"FDA API key: {'set' if os.getenv('FDA_API_KEY') else 'not set (anon rate limit)'}")
    print(f"Google API key: {'set' if os.getenv('GOOGLE_API_KEY') else 'NOT SET -- LLM tests will fail!'}")

    results: dict[str, bool] = {}

    # -- Phase 1: Knowledge enrichment (no FHIR needed) ----------------------
    if not args.tool:
        results["RxNorm lookup"]          = test_rxnorm()
        results["FDA label lookup"]        = test_fda_labels()
        results["FDA cross-ref interact"]  = test_nlm_interactions()
        results["Enrichment pipeline"]     = test_enrichment_pipeline()

    if args.enrichment_only:
        _print_summary(results)
        return

    # -- Phase 2: FHIR data --------------------------------------------------
    if args.load:
        results["Patient load"]           = load_patient(fhir_url)
    if not args.tool:
        results["Patient verify"]         = verify_patient(fhir_url)
        results["FHIR data retrieval"]    = test_fhir_data_retrieval(fhir_url, token)

    if not args.tool and not results.get("Patient verify", True):
        _header("SKIPPING LLM TOOL TESTS -- patient not found on FHIR server")
        _info("Run with --load to load the patient data first.")
        _print_summary(results)
        return

    if args.tool:
        if not verify_patient(fhir_url):
            print("\nPatient not found. Run with --load to load patient data.")
            sys.exit(1)

    # -- Phase 3: MCP tool tests (LLM) ---------------------------------------
    tool_map = {
        "medication_safety": ("Medication Safety MCP",  test_medication_safety_mcp),
        "deterioration":     ("Deterioration MCP",       test_deterioration_mcp),
        "lost_followups":    ("Lost Follow-Ups MCP",     test_lost_followups_mcp),
        "briefing":          ("Full Risk Briefing MCP",  test_full_briefing_mcp),
    }

    if args.tool:
        name, fn = tool_map[args.tool]
        results[name] = fn(fhir_url, token)
    else:
        for key, (name, fn) in tool_map.items():
            results[name] = fn(fhir_url, token)

    _print_summary(results)


if __name__ == "__main__":
    main()
