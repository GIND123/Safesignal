"""
Run the SafeSignal MCP generate_risk_briefing tool against Margaret Chen
on the HAPI FHIR public sandbox. Saves the complete risk briefing to a file.

Usage: python scripts/_run_briefing.py
"""
import sys, os, asyncio, io
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FHIR_URL   = "https://hapi.fhir.org/baseR4"
FHIR_TOKEN = "demo-token"
PATIENT_ID = "patient-mc-071"
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "risk_briefing_output.txt")

async def main():
    print("SafeSignal MCP - generate_risk_briefing")
    print(f"Patient: {PATIENT_ID}")
    print(f"FHIR: {FHIR_URL}")
    print("-" * 60)

    # Step 1: Verify patient exists
    import httpx
    try:
        r = httpx.get(f"{FHIR_URL}/Patient/{PATIENT_ID}",
                      headers={"Accept": "application/fhir+json"}, timeout=10)
        if r.status_code == 200:
            p = r.json()
            name = p.get("name", [{}])[0]
            full = f"{' '.join(name.get('given', []))} {name.get('family', '')}".strip()
            print(f"[OK] Patient found: {full}")
        else:
            print(f"[FAIL] Patient not found HTTP {r.status_code}. Run load_margaret_chen.py first.")
            return
    except Exception as e:
        print(f"[FAIL] FHIR unreachable: {e}")
        return

    # Step 2: Run enrichment
    print("\n[INFO] Running knowledge enrichment...")
    from safesignal.tools.fhir_client import FHIRClient
    from safesignal.tools.knowledge_enrichment import enrich_medications

    client = FHIRClient(FHIR_URL, FHIR_TOKEN)
    meds = client.get_medications(PATIENT_ID)
    print(f"[OK] Retrieved {len(meds)} medications from FHIR")

    enrichment = enrich_medications(meds)
    enriched_meds = enrichment["medications_enriched"]
    interactions  = enrichment["drug_interactions"]
    print(f"[OK] Enrichment: {len(enriched_meds)} meds enriched, {len(interactions)} FDA-cited interactions")

    for m in enriched_meds:
        fda_fields = [k for k in m if k.startswith("fda_")]
        print(f"  {m.get('rxnorm_ingredient','?')}: rxcui={m.get('rxcui','?')}, FDA={fda_fields}")

    if interactions:
        print("\n  FDA-label-cited drug interactions:")
        for ix in interactions:
            print(f"    {ix['drug1']} <-> {ix['drug2']}")
            print(f"    {ix['description'][:150]}")

    # Step 3: Run the full MCP briefing
    print("\n" + "=" * 60)
    print("Calling generate_risk_briefing MCP tool (LLM call)...")
    print("=" * 60)

    from safesignal_mcp.server import generate_risk_briefing
    import time
    t0 = time.time()
    result = await generate_risk_briefing(
        patient_id=PATIENT_ID,
        fhir_url=FHIR_URL,
        fhir_token=FHIR_TOKEN,
        context="Routine follow-up - diabetes, CKD stage 4, atrial fibrillation",
    )
    elapsed = time.time() - t0

    print(f"\n[OK] Briefing generated in {elapsed:.1f}s ({len(result)} characters)")

    # Save to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"[OK] Saved to: {OUTPUT_FILE}")

    # Print ASCII-safe preview
    print("\n" + "=" * 60)
    print("BRIEFING PREVIEW (first 3000 chars, ASCII-safe):")
    print("=" * 60)
    preview = result[:3000].encode("ascii", errors="replace").decode("ascii")
    print(preview)
    if len(result) > 3000:
        print(f"\n... ({len(result) - 3000} more characters in output file)")

    # Validation checks
    print("\n" + "=" * 60)
    print("VALIDATION:")
    print("=" * 60)
    checks = {
        "URGENT section": "URGENT" in result.upper(),
        "WARNING section": "WARNING" in result.upper(),
        "Metformin risk cited": "metformin" in result.lower(),
        "eGFR cited": "egfr" in result.lower() or "renal" in result.lower(),
        "Ibuprofen risk cited": "ibuprofen" in result.lower(),
        "Warfarin cited": "warfarin" in result.lower(),
        "FDA evidence cited": any(w in result.lower() for w in ["fda", "black box", "contraindication", "label"]),
        "Compliance disclaimer": "clinician review" in result.lower(),
        "FOBT/follow-up": any(w in result.lower() for w in ["fobt", "fecal", "colonoscopy", "follow"]),
    }
    for check, ok in checks.items():
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {check}")

    passed = sum(1 for v in checks.values() if v)
    print(f"\n  {passed}/{len(checks)} validation checks passed")

if __name__ == "__main__":
    asyncio.run(main())
