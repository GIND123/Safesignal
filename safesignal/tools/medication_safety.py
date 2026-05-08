"""
SafeSignal Tool 1: check_medication_safety

ADK tool function called by the SafeSignal agent when the clinician asks about
medication safety. Fetches active medications, current/trending lab values,
active conditions, and allergies from FHIR, enriches medication data with
FDA label warnings and NLM drug-drug interaction data, then returns the full
enriched dataset for the agent's LLM to analyse.

The enrichment layer (knowledge_enrichment.py) adds:
  - FDA boxed warnings, contraindications, and warnings from official drug labels
  - NLM database-verified pairwise drug-drug interactions

This means the LLM can cite FDA label language as evidence, not just its own
training knowledge — a significant differentiator for clinical credibility.
"""
import logging

import httpx
from google.adk.tools import ToolContext

from .fhir_client import FHIRClient, _get_fhir_context_from_state
from .knowledge_enrichment import enrich_medications

logger = logging.getLogger(__name__)


def check_medication_safety(tool_context: ToolContext) -> dict:
    """
    Retrieves and enriches medication safety data for the current patient from FHIR.

    Fetches active medications, recent laboratory observations (eGFR, HbA1c,
    potassium, INR, creatinine, sodium, ALT, AST), active conditions, and
    active allergies. Each medication is enriched with FDA drug label data
    (boxed warnings, contraindications, warnings) and NLM drug-drug interaction
    data before being returned for clinical reasoning.

    Use this tool when asked specifically about medication safety, drug
    interactions, or whether any medications need review given current labs.
    No arguments required — patient context comes from the session.
    """
    ctx = _get_fhir_context_from_state(tool_context)
    if isinstance(ctx, dict):
        return ctx
    fhir_url, fhir_token, patient_id = ctx

    logger.info("safesignal_check_medication_safety patient_id=%s", patient_id)

    try:
        client = FHIRClient(fhir_url, fhir_token)
        data   = client.get_medication_safety_data(patient_id)
    except httpx.HTTPStatusError as exc:
        return {
            "status":        "error",
            "http_status":   exc.response.status_code,
            "error_message": f"FHIR server returned HTTP {exc.response.status_code}: {exc.response.text[:300]}",
        }
    except Exception as exc:
        return {
            "status":        "error",
            "error_message": f"Failed to retrieve FHIR data: {exc}",
        }

    # Enrich medication list with FDA label data and NLM interactions
    enrichment = enrich_medications(data["medications"])
    logger.info(
        "safesignal_med_enrichment_done meds=%d interactions=%d",
        len(enrichment["medications_enriched"]),
        len(enrichment["drug_interactions"]),
    )

    return {
        "status":               "success",
        "patient_id":           patient_id,
        "tool":                 "check_medication_safety",

        # Enriched medications (FDA labels + RxNorm identifiers)
        "medications":          enrichment["medications_enriched"],

        # NLM database-verified drug-drug interactions
        "drug_interactions":    enrichment["drug_interactions"],

        # Lab data for cross-referencing
        "latest_labs":          data["latest_labs"],
        "observation_series":   data["observation_series"],
        "conditions":           data["conditions"],
        "allergies":            data["allergies"],

        "enrichment_sources":   enrichment["enrichment_sources"],

        "analysis_context": (
            "Analyze the above patient data for medication safety issues. "
            "Medications include FDA drug label data (fda_boxed_warning, fda_contraindications, "
            "fda_warnings fields) — quote this language when citing risks. "
            "drug_interactions contains NLM database-verified pairwise interactions — "
            "cite these as authoritative evidence. "
            "Identify medication-lab mismatches, drugs now contraindicated by current lab values, "
            "monitoring gaps, and compound risks. "
            "Cite specific FHIR resource IDs, dates, values, AND any FDA/NLM evidence. "
            "Use severity levels URGENT / WARNING / INFORMATIONAL."
        ),
    }
