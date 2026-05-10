"""
SafeSignal — A2A application entry point.

Start the server with:
    uvicorn safesignal.app:a2a_app --host 0.0.0.0 --port 8004

The agent card (public, no auth required) is served at:
    GET http://localhost:8004/.well-known/agent-card.json

All A2A endpoints require X-API-Key authentication.

Environment variables:
    SAFESIGNAL_URL       Public base URL (default: http://localhost:8004)
    PO_PLATFORM_BASE_URL Prompt Opinion workspace URL (for FHIR extension URI)
    API_KEYS             Comma-separated valid API keys
    SAFESIGNAL_MODEL     LiteLLM model string (default: gemini/gemini-2.5-flash)
"""
import os

from a2a.types import AgentSkill
from shared.app_factory import create_a2a_app

from .agent import root_agent

_base_url = os.getenv("SAFESIGNAL_URL", os.getenv("BASE_URL", "http://localhost:8004"))
_po_base  = os.getenv("PO_PLATFORM_BASE_URL", "http://localhost:5139")

a2a_app = create_a2a_app(
    agent=root_agent,
    name="SafeSignal",
    description=(
        "FHIR-aware clinical risk intelligence agent. Detects hidden medication-lab "
        "mismatches, lost-to-follow-up findings, and silent deterioration patterns in "
        "patient charts. Designed for clinician review before patient visits. "
        "Does not diagnose or prescribe — all findings require clinician assessment."
    ),
    url=_base_url,
    version="1.0.0",
    port=8004,
    fhir_extension_uri=f"{_po_base}/schemas/a2a/v1/fhir-context",
    fhir_scopes=[
        {"name": "patient/Patient.rs",            "required": True},
        {"name": "patient/Condition.rs",           "required": True},
        {"name": "patient/MedicationRequest.rs",   "required": True},
        {"name": "patient/Observation.rs",         "required": True},
        {"name": "patient/DiagnosticReport.rs",    "required": True},
        {"name": "patient/Encounter.rs",           "required": True},
        {"name": "patient/Procedure.rs",           "required": True},
        {"name": "patient/ServiceRequest.rs",      "required": True},
        {"name": "patient/AllergyIntolerance.rs",  "required": True},
    ],
    skills=[
        AgentSkill(
            id="pre-visit-risk-briefing",
            name="Pre-Visit Risk Briefing",
            description=(
                "Generate a comprehensive severity-ordered risk briefing before a patient visit. "
                "Identifies medication safety issues, deterioration trends, and follow-up gaps "
                "across the full FHIR chart. Ask: 'What should I know before seeing this patient today?'"
            ),
            tags=["risk", "briefing", "fhir", "clinical-decision-support"],
        ),
        AgentSkill(
            id="medication-safety",
            name="Medication Safety Analysis",
            description=(
                "Cross-reference active medications against current lab values, trending results, "
                "active conditions, and allergies to identify medication-lab mismatches and "
                "compound risks from multiple prescribers."
            ),
            tags=["medications", "safety", "labs", "fhir"],
        ),
        AgentSkill(
            id="deterioration-detection",
            name="Silent Deterioration Detection",
            description=(
                "Analyse longitudinal observation time series to detect progressive clinical "
                "worsening that individual visit notes may describe as 'stable'. "
                "Tracks eGFR, HbA1c, blood pressure, potassium, and other key indicators."
            ),
            tags=["trends", "deterioration", "longitudinal", "fhir"],
        ),
        AgentSkill(
            id="followup-gap-detection",
            name="Lost Follow-Up Detection",
            description=(
                "Identify abnormal diagnostic findings and critical lab results that have no "
                "documented subsequent follow-up action within clinically expected timeframes."
            ),
            tags=["followup", "gaps", "diagnostic-reports", "fhir"],
        ),
    ],
)
