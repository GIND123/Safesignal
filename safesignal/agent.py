"""
SafeSignal — FHIR-Aware Clinical Risk Intelligence Agent.

This ADK agent is the "A2A Superhero" — it orchestrates the four SafeSignal
MCP-style tools into a pre-visit clinical risk briefing for clinicians.

Identity:
  name: safesignal
  version: 1.0.0
  capabilities: pre-visit risk briefing, medication safety, trajectory analysis,
                follow-up gap detection, FHIR R4 data retrieval

Tools (the "Superpowers"):
  generate_risk_briefing     — full pre-visit briefing (primary)
  check_medication_safety    — medication-lab mismatch detection
  detect_silent_deterioration — longitudinal trend analysis
  find_lost_followups        — follow-up gap detection

Model selection:
  Set SAFESIGNAL_MODEL in .env to override.
  Default: gemini/gemini-2.5-flash (or set to anthropic/claude-sonnet-4-6, etc.)
"""
import os

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from shared.fhir_hook import extract_fhir_context
from safesignal.tools import (
    check_medication_safety,
    detect_silent_deterioration,
    find_lost_followups,
    generate_risk_briefing,
)
from safesignal.prompts.clinical_prompts import SAFESIGNAL_AGENT_INSTRUCTION

# ── Model selection ────────────────────────────────────────────────────────────
# All models are handled via LiteLLM. Use the appropriate prefix:
#   SAFESIGNAL_MODEL=gemini/gemini-2.5-flash        (Google AI Studio, default)
#   SAFESIGNAL_MODEL=anthropic/claude-sonnet-4-6    (Anthropic — best for clinical reasoning)
#   SAFESIGNAL_MODEL=openai/gpt-4.1                 (OpenAI)
#   SAFESIGNAL_MODEL=vertex_ai/gemini-2.5-pro       (Vertex AI)
# ──────────────────────────────────────────────────────────────────────────────
_model_name = os.getenv("SAFESIGNAL_MODEL", "gemini/gemini-2.5-flash")
_model      = LiteLlm(model=_model_name)

root_agent = Agent(
    name="safesignal",
    model=_model,
    description=(
        "SafeSignal is a FHIR-aware clinical risk intelligence agent. "
        "Before a patient visit, it scans the patient's FHIR chart data to detect "
        "hidden clinical risks: dangerous medication-lab mismatches, lost-to-follow-up "
        "findings, and silent deterioration patterns that individual visit notes miss. "
        "Designed for clinician review — does not diagnose or prescribe."
    ),
    instruction=SAFESIGNAL_AGENT_INSTRUCTION,
    tools=[
        generate_risk_briefing,
        check_medication_safety,
        detect_silent_deterioration,
        find_lost_followups,
    ],
    # Reads fhir_url, fhir_token, and patient_id from A2A message metadata
    # and writes them into session state before every LLM call.
    before_model_callback=extract_fhir_context,
)
