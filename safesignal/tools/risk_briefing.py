"""
SafeSignal Tool 4: generate_risk_briefing

The primary SafeSignal tool. Called by the agent for pre-visit risk briefing
requests: "What should I know before seeing this patient today?"

Fetches ALL FHIR resources needed for a complete clinical risk analysis
(Patient, Conditions, MedicationRequests, Observations × 24 months,
DiagnosticReports, Encounters, Procedures, AllergyIntolerances), enriches
the medication list with FDA label warnings and NLM drug-drug interaction data,
and returns a comprehensive enriched patient context for the SafeSignal agent's
LLM to synthesise into a severity-ordered risk briefing.

The knowledge enrichment layer adds two layers of authoritative external evidence:
  1. FDA drug label data (boxed warnings, contraindications, warnings & precautions)
     from the FDA OpenFDA Drug Labels API — so the LLM cites FDA language, not
     just its training knowledge.
  2. NLM database-verified pairwise drug-drug interactions from the RxNav
     Drug Interaction API — stronger than LLM-derived interaction reasoning.
"""
import logging

import httpx
from google.adk.tools import ToolContext

from .fhir_client import FHIRClient, _get_fhir_context_from_state
from .knowledge_enrichment import enrich_medications

logger = logging.getLogger(__name__)


def generate_risk_briefing(tool_context: ToolContext) -> dict:
    """
    Fetches comprehensive FHIR patient data and enriches it for a full SafeSignal
    risk briefing.

    Retrieves all FHIR resources needed for complete clinical risk analysis:
    patient demographics, active conditions, active medications, 24 months of
    longitudinal observations (eGFR, HbA1c, potassium, INR, blood pressure,
    creatinine, and other key labs), diagnostic reports from the past 12 months,
    recent encounters with note snippets, procedures, and active allergies.

    Medications are enriched with:
      - FDA boxed warnings, contraindications, and warnings from official drug labels
      - NLM database-verified pairwise drug-drug interactions

    Returns an enriched patient context. SafeSignal then analyses this data to
    identify medication-lab mismatches, silent deterioration patterns, and
    lost-to-follow-up findings, producing a severity-ordered pre-visit risk
    briefing citing specific FHIR evidence AND official FDA label language.

    Use this tool when asked for a pre-visit briefing or "what should I know
    before seeing this patient." This is the primary SafeSignal tool.
    No arguments required — patient context comes from the session.
    """
    ctx = _get_fhir_context_from_state(tool_context)
    if isinstance(ctx, dict):
        return ctx
    fhir_url, fhir_token, patient_id = ctx

    logger.info("safesignal_generate_risk_briefing patient_id=%s", patient_id)

    try:
        client  = FHIRClient(fhir_url, fhir_token)
        context = client.get_full_patient_context(patient_id)
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
    enrichment = enrich_medications(context["medications"])
    enriched_meds        = enrichment["medications_enriched"]
    drug_interactions    = enrichment["drug_interactions"]
    enrichment_sources   = enrichment["enrichment_sources"]

    logger.info(
        "safesignal_enrichment_done patient_id=%s meds=%d interactions=%d",
        patient_id, len(enriched_meds), len(drug_interactions),
    )

    patient   = context.get("patient", {})
    name      = patient.get("name", "Unknown Patient")
    age       = patient.get("age", "Unknown")
    condition_names   = [c.get("display", "") for c in context.get("conditions", [])]
    condition_summary = ", ".join(condition_names[:5]) if condition_names else "None documented"
    obs_series        = context.get("observation_series", {})
    series_summary    = {k: len(v) for k, v in obs_series.items()} if obs_series else {}

    return {
        "status":     "success",
        "patient_id": patient_id,
        "tool":       "generate_risk_briefing",

        # ── Patient context ──────────────────────────────────────────────────
        "patient":              context["patient"],
        "conditions":           context["conditions"],

        # Enriched medications with FDA label data
        "medications":          enriched_meds,

        # NLM database-verified drug-drug interactions
        "drug_interactions":    drug_interactions,

        "observation_series":   obs_series,
        "diagnostic_reports":   context["diagnostic_reports"],
        "encounters":           context["encounters"],
        "procedures":           context["procedures"],
        "allergies":            context["allergies"],

        # ── Data summary for agent reasoning ────────────────────────────────
        "data_summary": {
            "patient_name":         name,
            "patient_age":          age,
            "active_conditions":    len(context["conditions"]),
            "active_medications":   len(context["medications"]),
            "observation_series":   series_summary,
            "diagnostic_reports":   len(context["diagnostic_reports"]),
            "recent_encounters":    len(context["encounters"]),
            "known_allergies":      len(context["allergies"]),
            "key_conditions":       condition_summary,
            "nlm_interactions_found": len(drug_interactions),
        },

        "enrichment_sources": enrichment_sources,

        "analysis_instructions": (
            f"Produce a complete SafeSignal Risk Briefing for {name}, Age {age}. "
            "Analyse ALL of the following: "
            "(1) Medication-lab mismatches and compound risks across medications, "
            "current labs, observation trends, conditions, and allergies. "
            "Medications include fda_boxed_warning, fda_contraindications, and fda_warnings "
            "fields from the FDA OpenFDA Drug Labels API — quote this language when citing risks. "
            "The drug_interactions field contains NLM database-verified pairwise interactions — "
            "cite these as: 'Per NLM Drug Interaction Database: [description] (severity: [level])'. "
            "(2) Silent deterioration patterns in the observation series — state each value "
            "change from first to most recent and the trajectory. "
            "(3) Lost-to-follow-up findings in the diagnostic reports and abnormal labs — "
            "check whether any subsequent encounters or procedures constitute appropriate "
            "follow-up within expected timeframes. "
            "Organise findings by severity (URGENT first, then WARNING, then INFORMATIONAL). "
            "Cite the specific resource_id, date, and value for every finding. "
            "When FDA/NLM evidence is present, cite it alongside FHIR evidence. "
            "End with the compliance disclaimer."
        ),
    }
