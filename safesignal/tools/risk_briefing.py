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

        # Drug-drug interactions (source field: "NLM RxNav (ONCHigh)" or "FDA Drug Label (OpenFDA)")
        "drug_interactions":    drug_interactions,

        "observation_series":   obs_series,
        "diagnostic_reports":   context["diagnostic_reports"],
        "encounters":           context["encounters"],
        "procedures":           context["procedures"],
        "service_requests":     context.get("service_requests", []),
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
            "service_requests":     len(context.get("service_requests", [])),
            "known_allergies":      len(context["allergies"]),
            "key_conditions":       condition_summary,
            "interactions_found":   len(drug_interactions),
        },

        "enrichment_sources": enrichment_sources,

        "analysis_instructions": (
            f"Produce a complete SafeSignal Risk Briefing for {name}, Age {age}. "
            "Analyse ALL three domains in order:\n"
            "(1) MEDICATION-LAB MISMATCHES AND COMPOUND RISKS: Cross-reference all medications "
            "against current labs, observation trends, conditions, and allergies. "
            "Medications include fda_boxed_warning, fda_contraindications, fda_warnings fields — "
            "quote the relevant FDA label language under 'FDA/NLM Citation:' in each Evidence block. "
            "drug_interactions entries each have a source field — cite verbatim: "
            "'Per [source]: [description] (severity: [level])'. "
            "If no active medications, state that clearly.\n"
            "(2) SILENT DETERIORATION: For each observation series with two or more data points, "
            "state the trajectory explicitly: 'Value changed from A → B over N months.' "
            "If a clinical note says 'stable' but the data shows decline, flag the contradiction.\n"
            "(3) LOST-TO-FOLLOW-UP: For each abnormal diagnostic report or abnormal lab, "
            "check encounters, procedures, AND service_requests (referrals) before concluding a gap. "
            "If service_requests is empty, qualify the finding rather than asserting no referral was placed. "
            "If follow-up is documented, report it as resolved under INFORMATIONAL — not as a gap.\n"
            "FORMAT RULES: "
            "Use the SafeSignal output format — short finding title, 1–3 sentence explanation with "
            "specific values/dates/trajectory, Evidence block with bullet-point FHIR citations, "
            "FDA/NLM Citation block only when applicable, Missing evidence only when genuinely absent. "
            "Do NOT write 'Missing evidence: None identified.' "
            "Omit entire sections (URGENT / WARNING / INFORMATIONAL) that have no findings. "
            "Organise by severity: URGENT first, then WARNING, then INFORMATIONAL. "
            "End with the compliance disclaimer."
        ),
    }
