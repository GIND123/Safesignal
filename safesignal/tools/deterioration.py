"""
SafeSignal Tool 2: detect_silent_deterioration

ADK tool function called by the SafeSignal agent when the clinician asks about
trends, whether a condition is worsening, or longitudinal analysis.

Fetches historical observation time series (up to 24 months) for all tracked
LOINC codes, active conditions (for clinical context), and recent encounter
notes (to detect discrepancy between what the data shows and what providers
documented). Returns structured data for the agent's LLM to analyse.
"""
import logging

import httpx
from google.adk.tools import ToolContext

from .fhir_client import FHIRClient, _get_fhir_context_from_state

logger = logging.getLogger(__name__)


def detect_silent_deterioration(tool_context: ToolContext) -> dict:
    """
    Retrieves longitudinal observation data to detect silent deterioration trends.

    Fetches up to 24 months of historical observations for key clinical indicators
    (eGFR, HbA1c, potassium, INR, blood pressure, creatinine, etc.), active
    conditions, and recent encounter notes. Returns time-series data for
    SafeSignal's clinical reasoning to identify progressive worsening that
    individual visit notes may describe as "stable."

    Use this tool when asked about trends, whether a condition is getting worse,
    or when performing longitudinal lab/vital sign analysis.
    No arguments required — patient context comes from the session.
    """
    ctx = _get_fhir_context_from_state(tool_context)
    if isinstance(ctx, dict):
        return ctx
    fhir_url, fhir_token, patient_id = ctx

    logger.info("safesignal_detect_silent_deterioration patient_id=%s", patient_id)

    try:
        client = FHIRClient(fhir_url, fhir_token)
        data   = client.get_deterioration_data(patient_id)
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
        "status":              "success",
        "patient_id":          patient_id,
        "tool":                "detect_silent_deterioration",
        "observation_series":  data["observation_series"],
        "conditions":          data["conditions"],
        "recent_encounters":   data["recent_encounters"],
        "analysis_context": (
            "Analyse the above time-series observation data for silent deterioration. "
            "For each tracked observation series with two or more data points, state the "
            "trajectory explicitly: 'Value changed from A → B over N months (rate: X/month).' "
            "If only one data point exists for a metric, state that a trend cannot be assessed. "
            "Flag discrepancies between trend data and encounter note language — if a note "
            "says 'stable' but the data shows progressive decline, call it out explicitly. "
            "Follow the SafeSignal output format: short finding title (include first and last "
            "values in the title), 1–3 sentence explanation with rate and clinical context, "
            "Evidence block with bullet points (ResourceType/ID — value, date), "
            "Missing evidence only if genuinely absent. "
            "Use severity levels URGENT / WARNING / INFORMATIONAL. Omit empty sections."
        ),
    }
