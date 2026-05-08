"""
SafeSignal MCP Server — "The Superpower"

Exposes four clinical reasoning tools via the Model Context Protocol (MCP),
making them available to ANY agent on the Prompt Opinion platform.

Unlike the A2A agent (which relies on the agent's main LLM for clinical
reasoning), each MCP tool here is self-contained: it fetches FHIR data,
enriches medications with FDA label warnings and NLM interaction data, then
calls the LLM internally to produce a structured clinical analysis string.
This makes the tools reusable by any agent without requiring the caller to
have the SafeSignal system prompt.

Tools:
  check_medication_safety       — medication-lab mismatch and compound risk analysis
                                   with FDA label citations and NLM interaction data
  detect_silent_deterioration   — longitudinal trend analysis
  find_lost_followups           — follow-up gap detection
  generate_risk_briefing        — full pre-visit clinical risk briefing
                                   (orchestrates all three analyses with enrichment)

Transport: SSE (Server-Sent Events) for HTTP-based access
Port: 8005

Usage by other Prompt Opinion agents:
  Connect via MCPToolset (SSE) at http://safesignal-mcp:8005/sse

Model selection:
  Set SAFESIGNAL_MCP_MODEL in .env to override.
  Default: gemini/gemini-2.5-flash
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx
import litellm
from mcp.server.fastmcp import FastMCP

from safesignal.tools.fhir_client import FHIRClient
from safesignal.tools.knowledge_enrichment import enrich_medications
from safesignal.prompts.clinical_prompts import (
    MEDICATION_SAFETY_PROMPT,
    DETERIORATION_PROMPT,
    FOLLOWUP_PROMPT,
    SAFESIGNAL_AGENT_INSTRUCTION,
    COMPLIANCE_DISCLAIMER,
)

logger = logging.getLogger(__name__)

# ── MCP server instance ────────────────────────────────────────────────────────
mcp = FastMCP(
    name="SafeSignal Clinical Tools",
    instructions=(
        "SafeSignal MCP server. Exposes four FHIR-powered clinical reasoning tools "
        "for medication safety analysis (with FDA label + NLM interaction evidence), "
        "deterioration detection, follow-up gap detection, and full pre-visit risk briefing "
        "generation. All tools require a patient context (patient_id, fhir_url, fhir_token). "
        "All findings are for clinician review only."
    ),
)

# ── LLM helper ────────────────────────────────────────────────────────────────

_DEFAULT_MODEL = os.getenv("SAFESIGNAL_MCP_MODEL", "gemini/gemini-2.5-flash")

def _call_llm(system_prompt: str, user_content: str) -> str:
    model = os.getenv("SAFESIGNAL_MCP_MODEL", _DEFAULT_MODEL)
    try:
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_content},
            ],
            temperature=0.1,  # low temperature for consistent clinical output
            max_tokens=8192,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        logger.error("safesignal_mcp_llm_error model=%s err=%s", model, exc)
        return f"[LLM error: {exc}]"


def _fhir_client(fhir_url: str, fhir_token: str) -> FHIRClient:
    return FHIRClient(fhir_url.rstrip("/"), fhir_token)


def _fhir_error(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        return f"FHIR server error HTTP {exc.response.status_code}: {exc.response.text[:200]}"
    return f"FHIR connection error: {exc}"


def _to_json(data: dict[str, Any] | list[Any]) -> str:
    """Serialise a patient context dict/list to compact JSON for LLM consumption."""
    return json.dumps(data, indent=2, default=str)


# ── Tool 1: check_medication_safety ───────────────────────────────────────────

@mcp.tool()
async def check_medication_safety(
    patient_id: str,
    fhir_url:   str,
    fhir_token: str,
) -> str:
    """
    Analyses a patient's active medications against current lab values, active
    conditions, and allergies to identify medication-lab mismatches and compound risks.

    Fetches active MedicationRequests, recent laboratory Observations (eGFR, HbA1c,
    potassium, INR, creatinine, sodium, ALT, AST), active Conditions, and
    AllergyIntolerances from the FHIR server.

    Each medication is enriched with:
      - FDA drug label data: boxed warnings, contraindications, warnings & precautions
        from the FDA OpenFDA Drug Labels API. The LLM cites FDA label language directly.
      - NLM database-verified pairwise drug-drug interactions from the RxNav API.
        These are stronger evidence than LLM training knowledge.

    Then applies clinical reasoning to detect:
      - Medications contraindicated by current lab values (e.g., Metformin with eGFR < 30)
      - Therapeutic monitoring gaps (e.g., Warfarin without recent INR)
      - Compound risks from medications prescribed by different providers
      - Rising lab values that put existing medications into dangerous range
      - Database-verified drug-drug interactions between co-prescribed medications

    Args:
        patient_id: FHIR Patient resource ID
        fhir_url:   FHIR R4 server base URL
        fhir_token: Bearer token for FHIR authentication

    Returns:
        Structured clinical safety analysis with severity-ordered findings,
        FHIR evidence citations, FDA label citations, NLM interaction citations,
        and missing evidence notes. All findings are for clinician review only.
    """
    try:
        client  = _fhir_client(fhir_url, fhir_token)
        data    = client.get_medication_safety_data(patient_id)
        patient = client.get_patient(patient_id)
    except Exception as exc:
        return _fhir_error(exc)

    # Enrich medications with FDA labels and NLM interactions
    enrichment       = enrich_medications(data["medications"])
    enriched_meds    = enrichment["medications_enriched"]
    drug_interactions = enrichment["drug_interactions"]

    logger.info(
        "mcp_med_enrichment_done patient_id=%s meds=%d interactions=%d",
        patient_id, len(enriched_meds), len(drug_interactions),
    )

    user_content = (
        f"Patient: {patient.get('name', 'Unknown')}, Age {patient.get('age', 'Unknown')}, "
        f"Sex: {patient.get('sex', 'Unknown')}\n\n"
        f"Active Medications (enriched with FDA label data):\n{_to_json(enriched_meds)}\n\n"
        f"NLM Database-Verified Drug Interactions:\n{_to_json(drug_interactions)}\n\n"
        f"Latest Lab Values:\n{_to_json(data['latest_labs'])}\n\n"
        f"Lab Observation Series (historical):\n{_to_json(data['observation_series'])}\n\n"
        f"Active Conditions:\n{_to_json(data['conditions'])}\n\n"
        f"Active Allergies:\n{_to_json(data['allergies'])}\n\n"
        "Perform a medication safety analysis on the above patient data. "
        "For medications with fda_boxed_warning, fda_contraindications, or fda_warnings fields, "
        "quote the relevant FDA label text when citing a risk. "
        "For entries in the NLM drug interactions list, cite them as database-verified evidence."
    )

    return _call_llm(MEDICATION_SAFETY_PROMPT, user_content)


# ── Tool 2: detect_silent_deterioration ───────────────────────────────────────

@mcp.tool()
async def detect_silent_deterioration(
    patient_id: str,
    fhir_url:   str,
    fhir_token: str,
) -> str:
    """
    Analyses longitudinal observation time-series data to detect progressive clinical
    deterioration that individual visit notes may describe as "stable."

    Fetches up to 24 months of historical Observations for key clinical indicators
    (eGFR, HbA1c, potassium, blood pressure, creatinine, sodium, ALT, albumin, weight),
    active Conditions for clinical context, and recent Encounter notes. Applies clinical
    reasoning to identify:
      - Progressive organ function decline (e.g., eGFR declining 52→27 over 14 months)
      - Worsening metabolic control (e.g., A1c rising 7.1→8.2 despite treatment)
      - Rising blood pressure despite antihypertensive therapy
      - Rate-of-change analysis and trajectory projection
      - Discrepancies between trend data and encounter note language

    Args:
        patient_id: FHIR Patient resource ID
        fhir_url:   FHIR R4 server base URL
        fhir_token: Bearer token for FHIR authentication

    Returns:
        Trend analysis with severity-ordered deterioration findings,
        explicit trajectory data (first value → most recent, rate of change),
        and FHIR evidence citations. All findings are for clinician review only.
    """
    try:
        client  = _fhir_client(fhir_url, fhir_token)
        data    = client.get_deterioration_data(patient_id)
        patient = client.get_patient(patient_id)
    except Exception as exc:
        return _fhir_error(exc)

    user_content = (
        f"Patient: {patient.get('name', 'Unknown')}, Age {patient.get('age', 'Unknown')}, "
        f"Sex: {patient.get('sex', 'Unknown')}\n\n"
        f"Active Conditions:\n{_to_json(data['conditions'])}\n\n"
        f"Observation Series (historical, sorted oldest→newest):\n"
        f"{_to_json(data['observation_series'])}\n\n"
        f"Recent Encounter Notes:\n{_to_json(data['recent_encounters'])}\n\n"
        "Analyse the above data for silent deterioration patterns."
    )

    return _call_llm(DETERIORATION_PROMPT, user_content)


# ── Tool 3: find_lost_followups ───────────────────────────────────────────────

@mcp.tool()
async def find_lost_followups(
    patient_id: str,
    fhir_url:   str,
    fhir_token: str,
) -> str:
    """
    Identifies abnormal diagnostic findings and critical lab results that have no
    documented follow-up action within clinically expected timeframes.

    Fetches DiagnosticReport resources (past 12 months), abnormal Observation results,
    subsequent Encounters, and Procedures. Applies clinical reasoning to determine
    whether each abnormal finding received appropriate documented follow-up, checking:
      - Positive FOBT: colonoscopy or GI referral within 60 days
      - BI-RADS 4-5 mammogram: biopsy or imaging within 30 days
      - Elevated PSA: urology referral within 90 days
      - Abnormal Pap: colposcopy within 90 days
      - Significantly elevated liver enzymes: repeat labs or hepatology within 60 days
      - Any other abnormal finding: assessed against clinical context

    Args:
        patient_id: FHIR Patient resource ID
        fhir_url:   FHIR R4 server base URL
        fhir_token: Bearer token for FHIR authentication

    Returns:
        Follow-up gap analysis with severity-ordered findings, days elapsed
        since each abnormal finding, and documentation of what follow-up was
        (or was not) found in subsequent FHIR records.
        All findings are for clinician review only.
    """
    try:
        client  = _fhir_client(fhir_url, fhir_token)
        data    = client.get_followup_data(patient_id)
        patient = client.get_patient(patient_id)
    except Exception as exc:
        return _fhir_error(exc)

    user_content = (
        f"Patient: {patient.get('name', 'Unknown')}, Age {patient.get('age', 'Unknown')}, "
        f"Sex: {patient.get('sex', 'Unknown')}\n\n"
        f"Diagnostic Reports (past 12 months):\n{_to_json(data['diagnostic_reports'])}\n\n"
        f"Abnormal Lab Observations (past 12 months):\n{_to_json(data['abnormal_labs'])}\n\n"
        f"Subsequent Encounters:\n{_to_json(data['encounters'])}\n\n"
        f"Subsequent Procedures:\n{_to_json(data['procedures'])}\n\n"
        "Identify lost-to-follow-up findings in the above data."
    )

    return _call_llm(FOLLOWUP_PROMPT, user_content)


# ── Tool 4: generate_risk_briefing ────────────────────────────────────────────

@mcp.tool()
async def generate_risk_briefing(
    patient_id: str,
    fhir_url:   str,
    fhir_token: str,
    context:    str = "",
) -> str:
    """
    Generates a complete pre-visit clinical risk briefing for a patient.

    This is the primary SafeSignal tool. It orchestrates all three clinical analysis
    modules (medication safety, deterioration detection, follow-up gap detection) into
    a single, severity-ordered risk briefing for clinician review.

    Fetches ALL relevant FHIR resources — Patient, Conditions, MedicationRequests,
    24 months of Observations, DiagnosticReports, Encounters, Procedures, and
    AllergyIntolerances.

    Medications are enriched with FDA drug label data (boxed warnings, contraindications,
    warnings) and NLM database-verified drug-drug interactions before LLM reasoning.
    The result is a briefing that cites FDA label language alongside FHIR evidence —
    a level of evidence that pure LLM reasoning cannot provide.

    Args:
        patient_id: FHIR Patient resource ID
        fhir_url:   FHIR R4 server base URL
        fhir_token: Bearer token for FHIR authentication
        context:    Optional clinician note or visit reason (e.g., "routine follow-up for diabetes")

    Returns:
        Complete SafeSignal Risk Briefing with:
          🔴 URGENT findings (immediate patient safety risks, with FDA label citations)
          🟡 WARNING findings (significant concerns, with NLM interaction data where applicable)
          ℹ️  INFORMATIONAL findings (monitoring gaps, minor concerns)
          ⚕️  Compliance disclaimer
        Each finding cites specific FHIR resource IDs, dates, values,
        and FDA/NLM evidence where available.
        All findings are for clinician review only.
    """
    try:
        client          = _fhir_client(fhir_url, fhir_token)
        patient_context = client.get_full_patient_context(patient_id)
    except Exception as exc:
        return _fhir_error(exc)

    # Enrich medications with FDA labels and NLM interactions
    enrichment        = enrich_medications(patient_context["medications"])
    enriched_meds     = enrichment["medications_enriched"]
    drug_interactions = enrichment["drug_interactions"]

    logger.info(
        "mcp_briefing_enrichment_done patient_id=%s meds=%d interactions=%d",
        patient_id, len(enriched_meds), len(drug_interactions),
    )

    patient      = patient_context.get("patient", {})
    name         = patient.get("name", "Unknown Patient")
    age          = patient.get("age", "Unknown")
    sex          = patient.get("sex", "Unknown")
    context_line = f"\nVisit context: {context}" if context else ""

    user_content = (
        f"Patient: {name}, Age {age}, Sex: {sex}{context_line}\n\n"
        f"Active Conditions:\n{_to_json(patient_context['conditions'])}\n\n"
        f"Active Medications (enriched with FDA drug label data):\n{_to_json(enriched_meds)}\n\n"
        f"NLM Database-Verified Drug Interactions:\n{_to_json(drug_interactions)}\n\n"
        f"Observation Series (historical, sorted oldest→newest):\n"
        f"{_to_json(patient_context['observation_series'])}\n\n"
        f"Diagnostic Reports (past 12 months):\n{_to_json(patient_context['diagnostic_reports'])}\n\n"
        f"Recent Encounters:\n{_to_json(patient_context['encounters'])}\n\n"
        f"Procedures (past 12 months):\n{_to_json(patient_context['procedures'])}\n\n"
        f"Active Allergies:\n{_to_json(patient_context['allergies'])}\n\n"
        f"Generate a complete SafeSignal Risk Briefing for {name}, Age {age}. "
        f"Medications include FDA drug label data — quote fda_boxed_warning / "
        f"fda_contraindications / fda_warnings text when citing medication risks. "
        f"The drug_interactions list contains NLM database-verified interactions — "
        f"cite these as: 'Per NLM Drug Interaction Database: [desc] (severity: [level])'. "
        f"Cite both FHIR evidence AND FDA/NLM label evidence for every medication finding."
    )

    return _call_llm(SAFESIGNAL_AGENT_INSTRUCTION, user_content)
