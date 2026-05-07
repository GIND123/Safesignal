"""
SafeSignal Tool 3: find_lost_followups

ADK tool function called by the SafeSignal agent when the clinician asks about
follow-up gaps, missed results, or care continuity.

Fetches diagnostic reports and abnormal lab observations (past 12 months), then
fetches subsequent encounters and procedures. Returns structured data for the
agent's LLM to determine whether each abnormal finding received appropriate
documented follow-up action within expected timeframes.
"""
import logging

import httpx
from google.adk.tools import ToolContext

from .fhir_client import FHIRClient, _get_fhir_context_from_state

logger = logging.getLogger(__name__)


def find_lost_followups(tool_context: ToolContext) -> dict:
    """
    Identifies abnormal findings that may lack documented follow-up actions.

    Fetches DiagnosticReport resources and abnormal Observations from the past
    12 months, then retrieves subsequent Encounters, Procedures, and referral
    records to determine whether appropriate follow-up was documented within
    clinically expected timeframes (e.g., colonoscopy within 60 days of positive
    FOBT, GI referral within 60 days, urology referral within 90 days of elevated
    PSA, etc.).

    Use this tool when asked about follow-up gaps, missed results, or whether
    any abnormal findings lack documented subsequent action.
    No arguments required — patient context comes from the session.
    """
    ctx = _get_fhir_context_from_state(tool_context)
    if isinstance(ctx, dict):
        return ctx
    fhir_url, fhir_token, patient_id = ctx

    logger.info("safesignal_find_lost_followups patient_id=%s", patient_id)

    try:
        client = FHIRClient(fhir_url, fhir_token)
        data   = client.get_followup_data(patient_id)
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
        "tool":               "find_lost_followups",
        "diagnostic_reports": data["diagnostic_reports"],
        "abnormal_labs":      data["abnormal_labs"],
        "encounters":         data["encounters"],
        "procedures":         data["procedures"],
        "analysis_context": (
            "Analyze the above data to identify abnormal findings that lack documented "
            "follow-up actions. For each diagnostic report or abnormal lab, check whether "
            "any subsequent encounter, procedure, or referral after the finding date "
            "constitutes appropriate follow-up within expected timeframes. "
            "Use your clinical knowledge to determine whether documented actions constitute "
            "adequate follow-up — do not require exact procedure name matching. "
            "Calculate days elapsed since each finding. "
            "Use severity levels URGENT / WARNING / INFORMATIONAL."
        ),
    }
