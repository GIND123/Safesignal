"""
SafeSignal Knowledge Enrichment Layer

Enriches FHIR medication data with external evidence from authoritative sources:

  1. RxNorm / RxNav (NLM) — normalise drug names to RxCUI identifiers for
     standardized medication identification.

  2. FDA OpenFDA Drug Labels API — pull boxed warnings, contraindications, and
     warnings & precautions directly from official FDA-approved drug labelling.

  3. FDA Label Cross-Reference — detect documented drug-drug interactions by
     scanning each drug's FDA label drug_interactions section for co-prescribed
     drug names. This gives FDA-label-cited interaction evidence.

When the LLM reasons about drug-lab mismatches it can now cite FDA label language,
not just its training knowledge. This is evidence that a pure rule-based CDS
system cannot produce and that a raw LLM call without enrichment cannot cite.

APIs (publicly funded, no proprietary terms):
  RxNorm ingredient lookup:   https://rxnav.nlm.nih.gov/REST/rxcui.json?name=...
  FDA OpenFDA drug labels:    https://api.fda.gov/drug/label.json?api_key=...&search=...

Call enrich_medications(medications) between FHIR data retrieval and LLM reasoning.
All failures are handled gracefully — enrichment is additive; the system works
without it if an API is unreachable.
"""
from __future__ import annotations

import logging
import os
from itertools import combinations
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

FDA_API_KEY  = os.getenv("FDA_API_KEY", "")
FDA_BASE_URL = "https://api.fda.gov/drug/label.json"
RXNAV_BASE   = "https://rxnav.nlm.nih.gov/REST"
_TIMEOUT     = 12  # seconds — kept short so enrichment never blocks the agent


# ── Text helpers ───────────────────────────────────────────────────────────────

def _extract_ingredient(med_display: str) -> str:
    """
    Extract the base ingredient name from a FHIR medication display string.
    "Metformin 1000mg BID"  -> "metformin"
    "Warfarin 5mg daily"    -> "warfarin"
    "Lisinopril 20mg daily" -> "lisinopril"
    """
    if not med_display:
        return ""
    first_word = med_display.strip().split()[0]
    return first_word.lower().rstrip(".,;:()")


def _first_list_item(label: dict, field: str, max_len: int = 700) -> str:
    """Return the first element of an FDA label list field, truncated."""
    val = label.get(field)
    if isinstance(val, list) and val:
        text = str(val[0]).strip()
        return text[:max_len] + "..." if len(text) > max_len else text
    return ""


# ── RxNorm lookup ──────────────────────────────────────────────────────────────

def lookup_rxcui(ingredient: str) -> Optional[str]:
    """
    Look up the RxNorm RxCUI for a drug ingredient name.
    Returns the first matching RxCUI string, or None on failure / not found.
    """
    if not ingredient:
        return None
    try:
        resp = httpx.get(
            f"{RXNAV_BASE}/rxcui.json",
            params={"name": ingredient, "search": 1},
            timeout=_TIMEOUT,
        )
        if resp.status_code != 200:
            return None
        ids = (resp.json().get("idGroup") or {}).get("rxnormId") or []
        return ids[0] if ids else None
    except Exception as exc:
        logger.debug("rxnorm_rxcui_failed ingredient=%s err=%s", ingredient, exc)
        return None


# ── FDA OpenFDA label lookup ───────────────────────────────────────────────────

def lookup_fda_label(ingredient: str) -> dict:
    """
    Fetch boxed warnings, contraindications, warnings & precautions, and drug
    interaction text from the FDA OpenFDA Drug Labels API for a given ingredient.

    Returns a dict with keys:
        boxed_warning, contraindications, warnings, drug_interactions, openfda_name
    All values are strings (empty string if not found / not applicable).
    Returns {} on API failure.
    """
    if not ingredient:
        return {}

    def _query(search_expr: str) -> Optional[dict]:
        params: dict = {"search": search_expr, "limit": 1}
        if FDA_API_KEY:
            params["api_key"] = FDA_API_KEY
        try:
            resp = httpx.get(FDA_BASE_URL, params=params, timeout=_TIMEOUT)
            if resp.status_code == 200:
                results = resp.json().get("results") or []
                return results[0] if results else None
        except Exception as exc:
            logger.debug("fda_label_query_failed search=%s err=%s", search_expr, exc)
        return None

    # Try exact generic name first, then substance name as fallback
    label = (
        _query(f'openfda.generic_name:"{ingredient}"')
        or _query(f"openfda.substance_name:{ingredient}")
    )
    if not label:
        return {}

    openfda   = label.get("openfda") or {}
    gen_names = openfda.get("generic_name") or []

    return {
        "boxed_warning":    _first_list_item(label, "boxed_warning"),
        "contraindications": _first_list_item(label, "contraindications"),
        "warnings":         _first_list_item(label, "warnings_and_cautions")
                            or _first_list_item(label, "warnings"),
        "drug_interactions": _first_list_item(label, "drug_interactions"),
        "openfda_name":     gen_names[0].lower() if gen_names else ingredient,
        "_raw_label":       label,  # kept for cross-reference scanning
    }


# ── FDA label cross-reference for drug-drug interactions ──────────────────────

def _find_fda_label_interactions(enriched_meds: list[dict]) -> list[dict]:
    """
    Detect drug-drug interactions by scanning each FDA drug label's drug_interactions
    section for the names of other co-prescribed medications.

    For each pair (drug_A, drug_B):
      - Check if drug_A's FDA label drug_interactions text mentions drug_B
      - Check if drug_B's FDA label drug_interactions text mentions drug_A

    This gives FDA-label-verified interaction evidence — more clinically authoritative
    than training knowledge alone because the quote is from the regulatory label.

    Returns list of dicts: {drug1, drug2, mention_in, excerpt, source}.
    """
    interactions: list[dict] = []

    for med_a, med_b in combinations(enriched_meds, 2):
        name_a = med_a.get("rxnorm_ingredient", "")
        name_b = med_b.get("rxnorm_ingredient", "")
        if not name_a or not name_b:
            continue

        # Check A's label for B's name
        fda_ix_a = med_a.get("fda_drug_interactions_label", "").lower()
        fda_warn_a = med_a.get("fda_warnings", "").lower()
        full_a_text = fda_ix_a + " " + fda_warn_a

        # Check B's label for A's name
        fda_ix_b = med_b.get("fda_drug_interactions_label", "").lower()
        fda_warn_b = med_b.get("fda_warnings", "").lower()
        full_b_text = fda_ix_b + " " + fda_warn_b

        # Also check common class names (NSAID, anticoagulant, ACE inhibitor)
        class_aliases = {
            "warfarin":    ["warfarin", "anticoagulant", "coumarin"],
            "ibuprofen":   ["ibuprofen", "nsaid", "nonsteroidal", "non-steroidal"],
            "metformin":   ["metformin", "biguanide"],
            "lisinopril":  ["lisinopril", "ace inhibitor", "acei"],
        }

        def _mentions(text: str, drug: str) -> str:
            """Return a snippet if the drug or its class aliases appear in text."""
            aliases = class_aliases.get(drug, [drug])
            for alias in aliases:
                idx = text.find(alias)
                if idx != -1:
                    start = max(0, idx - 50)
                    end   = min(len(text), idx + 200)
                    return text[start:end].strip()
            return ""

        a_mentions_b = _mentions(full_a_text, name_b)
        b_mentions_a = _mentions(full_b_text, name_a)

        if a_mentions_b:
            interactions.append({
                "drug1":       med_a.get("display", name_a),
                "drug2":       med_b.get("display", name_b),
                "severity":    "documented",
                "description": f"Per {name_a.capitalize()} FDA label: ...{a_mentions_b[:300]}...",
                "source":      "FDA Drug Label (OpenFDA) - drug interactions section",
            })
        elif b_mentions_a:
            interactions.append({
                "drug1":       med_b.get("display", name_b),
                "drug2":       med_a.get("display", name_a),
                "severity":    "documented",
                "description": f"Per {name_b.capitalize()} FDA label: ...{b_mentions_a[:300]}...",
                "source":      "FDA Drug Label (OpenFDA) - drug interactions section",
            })

    return interactions


# ── Main enrichment entry point ────────────────────────────────────────────────

def enrich_medications(medications: list[dict]) -> dict:
    """
    Enrich a list of FHIR-normalised medication dicts with FDA label data
    and cross-referenced drug-drug interaction evidence from FDA labels.

    Call this between FHIR data retrieval and LLM reasoning:
        data = client.get_medication_safety_data(patient_id)
        enrichment = enrich_medications(data["medications"])

    Args:
        medications: List of medication dicts from FHIRClient.get_medications().
            Expected keys: display, code, system, authored_on, status,
                           prescriber, dosage, resource_id.

    Returns:
        {
            "medications_enriched": [
                {
                    ...original FHIR fields...,
                    "rxnorm_ingredient": "metformin",
                    "rxcui": "6809",                    # or "not_found"
                    "fda_boxed_warning": "...",           # omitted if empty
                    "fda_contraindications": "...",       # omitted if empty
                    "fda_warnings": "...",                # omitted if empty
                    "fda_drug_interactions_label": "...", # omitted if empty
                }
            ],
            "drug_interactions": [
                {
                    "drug1": "Warfarin 5mg daily",
                    "drug2": "Ibuprofen 400mg PRN",
                    "severity": "documented",
                    "description": "Per warfarin FDA label: ...",
                    "source": "FDA Drug Label (OpenFDA)"
                }
            ],
            "enrichment_sources": ["FDA OpenFDA Drug Labels", "RxNorm"]
        }
    """
    enriched_meds: list[dict] = []

    for med in medications:
        ingredient = _extract_ingredient(med.get("display", ""))

        # ── Step 1: RxNorm RxCUI lookup ────────────────────────────────────────
        rxcui: Optional[str] = None
        if ingredient:
            rxcui = lookup_rxcui(ingredient)
            if rxcui:
                logger.debug("rxnorm_ok ingredient=%s rxcui=%s", ingredient, rxcui)
            else:
                logger.debug("rxnorm_not_found ingredient=%s", ingredient)

        # ── Step 2: FDA label lookup ───────────────────────────────────────────
        fda = lookup_fda_label(ingredient)
        if fda:
            logger.debug("fda_label_ok ingredient=%s", ingredient)

        # ── Build enriched record ──────────────────────────────────────────────
        enriched = {**med, "rxnorm_ingredient": ingredient, "rxcui": rxcui or "not_found"}
        enriched.pop("_raw_label", None)  # don't pass through raw label ref

        if fda.get("boxed_warning"):
            enriched["fda_boxed_warning"] = fda["boxed_warning"]
        if fda.get("contraindications"):
            enriched["fda_contraindications"] = fda["contraindications"]
        if fda.get("warnings"):
            enriched["fda_warnings"] = fda["warnings"]
        if fda.get("drug_interactions"):
            enriched["fda_drug_interactions_label"] = fda["drug_interactions"]

        enriched_meds.append(enriched)

    # ── Step 3: FDA label cross-reference for drug-drug interactions ───────────
    # Detect interactions by scanning each drug's FDA label for co-prescribed drug names
    interactions = _find_fda_label_interactions(enriched_meds)

    if interactions:
        logger.info(
            "fda_label_interactions_found count=%d",
            len(interactions),
        )

    return {
        "medications_enriched": enriched_meds,
        "drug_interactions":    interactions,
        "enrichment_sources":   [
            "FDA OpenFDA Drug Labels (api.fda.gov)",
            "RxNorm Identifier Resolution (rxnav.nlm.nih.gov)",
            "FDA Label Cross-Reference Interaction Scan",
        ],
    }
