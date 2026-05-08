"""
SafeSignal Knowledge Enrichment Layer

Enriches FHIR medication data with external evidence from two authoritative sources:

  1. RxNorm / RxNav (NLM) — normalise drug names to RxCUI identifiers and fetch
     database-verified pairwise drug-drug interactions.

  2. FDA OpenFDA Drug Labels API — pull boxed warnings, contraindications, and
     warnings & precautions directly from official FDA-approved drug labelling.

When the LLM reasons about drug-lab mismatches it can now cite FDA label language,
not just its training knowledge. This is evidence that a pure rule-based CDS
system cannot produce and that a raw LLM call without enrichment cannot cite.

APIs (no proprietary terms, publicly funded):
  RxNorm ingredient lookup:   https://rxnav.nlm.nih.gov/REST/rxcui.json?name=...
  NLM drug interactions:      https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis=...
  FDA OpenFDA drug labels:    https://api.fda.gov/drug/label.json?api_key=...&search=...

Call enrich_medications(medications) between FHIR data retrieval and LLM reasoning.
All failures are handled gracefully — enrichment is additive; the system works
without it if an API is unreachable.
"""
from __future__ import annotations

import logging
import os
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
    "Metformin 1000mg BID"  → "metformin"
    "Warfarin 5mg daily"    → "warfarin"
    "Lisinopril 20mg daily" → "lisinopril"
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
        return text[:max_len] + "…" if len(text) > max_len else text
    return ""


# ── RxNorm lookups ─────────────────────────────────────────────────────────────

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


def lookup_interactions(rxcuis: list[str]) -> list[dict]:
    """
    Fetch known drug-drug interactions for a list of RxCUI identifiers from
    the NLM Drug Interaction API.

    Returns a list of interaction dicts:
        {drug1, drug2, severity, description, source}

    Empty list on error or fewer than two drugs.
    """
    if len(rxcuis) < 2:
        return []
    try:
        resp = httpx.get(
            f"{RXNAV_BASE}/interaction/list.json",
            params={"rxcuis": " ".join(rxcuis)},
            timeout=_TIMEOUT,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
    except Exception as exc:
        logger.debug("rxnorm_interactions_failed err=%s", exc)
        return []

    interactions: list[dict] = []
    for pair_group in (data.get("fullInteractionTypeGroup") or []):
        for full_type in (pair_group.get("fullInteractionType") or []):
            group_comment = full_type.get("comment", "")
            for pair in (full_type.get("interactionPair") or []):
                concepts = pair.get("interactionConcept") or []
                names    = [c.get("minConceptItem", {}).get("name", "") for c in concepts]
                desc     = pair.get("description", group_comment)
                severity = pair.get("severity", "unknown")
                if len(names) >= 2:
                    desc_short = desc[:400] + "…" if len(desc) > 400 else desc
                    interactions.append({
                        "drug1":       names[0],
                        "drug2":       names[1],
                        "severity":    severity,
                        "description": desc_short,
                        "source":      "NLM Drug Interaction API (RxNav)",
                    })
    return interactions


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
        "boxed_warning":           _first_list_item(label, "boxed_warning"),
        "contraindications":        _first_list_item(label, "contraindications"),
        "warnings":                 _first_list_item(label, "warnings_and_cautions")
                                    or _first_list_item(label, "warnings"),
        "drug_interactions":        _first_list_item(label, "drug_interactions"),
        "openfda_name":             gen_names[0].lower() if gen_names else ingredient,
    }


# ── Main enrichment entry point ────────────────────────────────────────────────

def enrich_medications(medications: list[dict]) -> dict:
    """
    Enrich a list of FHIR-normalised medication dicts with FDA label data
    and NLM drug-drug interaction data.

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
                    "rxcui": "6809",                   # or "not_found"
                    "fda_boxed_warning": "...",          # omitted if empty
                    "fda_contraindications": "...",      # omitted if empty
                    "fda_warnings": "...",               # omitted if empty
                    "fda_drug_interactions": "...",      # omitted if empty
                }
            ],
            "drug_interactions": [
                {
                    "drug1": "warfarin", "drug2": "ibuprofen",
                    "severity": "high",
                    "description": "...",
                    "source": "NLM Drug Interaction API (RxNav)"
                }
            ],
            "enrichment_sources": ["FDA OpenFDA Drug Labels", "NLM RxNav Drug Interactions"]
        }
    """
    enriched_meds: list[dict] = []
    rxcui_map: dict[str, str] = {}   # ingredient → rxcui

    for med in medications:
        ingredient = _extract_ingredient(med.get("display", ""))

        # ── Step 1: RxNorm RxCUI lookup ────────────────────────────────────────
        rxcui: Optional[str] = None
        if ingredient:
            rxcui = lookup_rxcui(ingredient)
            if rxcui:
                rxcui_map[ingredient] = rxcui
                logger.debug("rxnorm_ok ingredient=%s rxcui=%s", ingredient, rxcui)
            else:
                logger.debug("rxnorm_not_found ingredient=%s", ingredient)

        # ── Step 2: FDA label lookup ───────────────────────────────────────────
        fda = lookup_fda_label(ingredient)
        if fda:
            logger.debug("fda_label_ok ingredient=%s name=%s", ingredient, fda.get("openfda_name"))

        # ── Build enriched record ──────────────────────────────────────────────
        enriched = {**med, "rxnorm_ingredient": ingredient, "rxcui": rxcui or "not_found"}

        if fda.get("boxed_warning"):
            enriched["fda_boxed_warning"] = fda["boxed_warning"]
        if fda.get("contraindications"):
            enriched["fda_contraindications"] = fda["contraindications"]
        if fda.get("warnings"):
            enriched["fda_warnings"] = fda["warnings"]
        if fda.get("drug_interactions"):
            enriched["fda_drug_interactions_label"] = fda["drug_interactions"]

        enriched_meds.append(enriched)

    # ── Step 3: NLM pairwise interaction check ─────────────────────────────────
    rxcuis = list(rxcui_map.values())
    interactions = lookup_interactions(rxcuis)
    if interactions:
        logger.info(
            "nlm_interactions_found count=%d rxcuis=%s",
            len(interactions), rxcuis,
        )

    return {
        "medications_enriched": enriched_meds,
        "drug_interactions":    interactions,
        "enrichment_sources":   [
            "FDA OpenFDA Drug Labels (api.fda.gov)",
            "NLM RxNorm + Drug Interaction API (rxnav.nlm.nih.gov)",
        ],
    }
