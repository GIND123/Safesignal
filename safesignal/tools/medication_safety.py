"""
SafeSignal Tool 1: check_medication_safety

ADK tool function called by the SafeSignal agent when the clinician asks about
medication safety. Fetches active medications, current/trending lab values,
active conditions, and allergies from FHIR, then returns structured data for
the agent's LLM to analyse using the SafeSignal clinical reasoning prompt.

Returns data — the agent's LLM does the clinical reasoning.
"""
import logging

import httpx
from google.adk.tools import ToolContext

from .fhir_client import FHIRClient, _get_fhir_context_from_state

logger = logging.getLogger(__name__)


def check_medication_safety(tool_context: ToolContext) -> dict:
    """
    Retrieves medication safety data for the current patient from FHIR.

    Fetches active medications, recent laboratory observations (eGFR, HbA1c,
    potassium, INR, creatinine, sodium, ALT, AST), active conditions, and
    active allergies. Returns a structured dataset for SafeSignal's clinical
    reasoning to identify medication-lab mismatches and compound risks.

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

    return {
        "status":             "success",
        "patient_id":         patient_id,
        "tool":               "check_medication_safety",
        "medications":        data["medications"],
        "latest_labs":        data["latest_labs"],
        "observation_series": data["observation_series"],
        "conditions":         data["conditions"],
        "allergies":          data["allergies"],
        "analysis_context": (
            "Analyze the above patient data for medication safety issues. "
            "Identify medication-lab mismatches, drugs that are now contraindicated "
            "by current lab values, monitoring gaps, and compound risks where multiple "
            "medications together create elevated danger. Cite specific resource IDs, "
            "dates, and values. Use severity levels URGENT / WARNING / INFORMATIONAL."
        ),
    }
