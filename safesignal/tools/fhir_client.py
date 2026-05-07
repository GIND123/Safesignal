"""
SafeSignal FHIR client — comprehensive R4 data retrieval.

FHIRClient wraps all FHIR resource fetches needed by the four SafeSignal clinical
tools. It normalizes raw FHIR bundles into compact Python dicts that are optimised
for LLM consumption — verbose FHIR boilerplate stripped, key clinical fields kept.

Used by:
  • ADK tools (safesignal/tools/*.py) — reads credentials from ToolContext.state
  • MCP server tools (safesignal_mcp/server.py) — credentials passed explicitly

LOINC codes tracked by default:
  33914-3  eGFR (CKD-EPI)
  4548-4   HbA1c
  2823-3   Potassium
  6301-6   INR
  55284-4  Blood pressure panel
  8480-6   Systolic BP
  8462-4   Diastolic BP
  2160-0   Creatinine
  2951-2   Sodium
  1742-6   ALT
  1920-8   AST
  1751-7   Albumin
  29463-7  Body weight
  39156-5  BMI
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import httpx
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

_FHIR_TIMEOUT = 20  # seconds

# LOINC codes → friendly label (used to group observation series)
TRACKED_LOINC_CODES: dict[str, str] = {
    "33914-3": "eGFR",
    "4548-4":  "HbA1c",
    "2823-3":  "Potassium",
    "6301-6":  "INR",
    "55284-4": "Blood Pressure",
    "8480-6":  "Systolic BP",
    "8462-4":  "Diastolic BP",
    "2160-0":  "Creatinine",
    "2951-2":  "Sodium",
    "1742-6":  "ALT",
    "1920-8":  "AST",
    "1751-7":  "Albumin",
    "29463-7": "Weight",
    "39156-5": "BMI",
}

# Codes to look for when checking "abnormal" observations (in addition to DiagnosticReports)
CANCER_SCREEN_LOINC_CODES = {
    "2335-8",   # FOBT
    "14563-1",  # FOBT specimen 1
    "10524-7",  # Mammography
    "2857-1",   # PSA
    "10524-7",  # Cytology (Pap)
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_fhir_context_from_state(tool_context: ToolContext):
    """
    Extract FHIR credentials from ADK session state.
    Returns (fhir_url, fhir_token, patient_id) or an error dict.
    """
    fhir_url   = (tool_context.state.get("fhir_url",   "") or "").rstrip("/")
    fhir_token = tool_context.state.get("fhir_token", "") or ""
    patient_id = tool_context.state.get("patient_id", "") or ""

    missing = [n for n, v in [("fhir_url", fhir_url), ("fhir_token", fhir_token), ("patient_id", patient_id)] if not v]
    if missing:
        return {
            "status": "error",
            "error_message": (
                f"FHIR context not available — missing: {', '.join(missing)}. "
                "Ensure the caller includes 'fhir-context' in the A2A message metadata."
            ),
        }
    return fhir_url, fhir_token, patient_id


def _coding_display(codings: list) -> str:
    for c in codings:
        if c.get("display"):
            return c["display"]
    return ""


def _coding_code(codings: list) -> str:
    return codings[0].get("code", "") if codings else ""


def _date_str(resource: dict) -> str:
    return (
        resource.get("effectiveDateTime")
        or (resource.get("effectivePeriod") or {}).get("start")
        or resource.get("authoredOn")
        or resource.get("recordedDate")
        or resource.get("onsetDateTime")
        or ""
    )


# ── FHIRClient ────────────────────────────────────────────────────────────────

class FHIRClient:
    """Authenticated FHIR R4 client with normalising helpers for SafeSignal."""

    def __init__(self, fhir_url: str, token: str):
        self.base = fhir_url.rstrip("/")
        self.token = token
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/fhir+json",
        }

    # ── Low-level GET ──────────────────────────────────────────────────────────

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.base}/{path}"
        resp = httpx.get(url, params=params, headers=self._headers, timeout=_FHIR_TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def _bundle_entries(self, bundle: dict) -> list[dict]:
        return [e.get("resource", {}) for e in bundle.get("entry", []) if e.get("resource")]

    # ── Patient ────────────────────────────────────────────────────────────────

    def get_patient(self, patient_id: str) -> dict:
        try:
            p = self._get(f"Patient/{patient_id}")
        except Exception as exc:
            logger.warning("fhir_get_patient_failed patient_id=%s err=%s", patient_id, exc)
            return {}

        names    = p.get("name", [])
        official = next((n for n in names if n.get("use") == "official"), names[0] if names else {})
        given    = " ".join(official.get("given", []))
        family   = official.get("family", "")
        full_name = f"{given} {family}".strip()

        birth_date = p.get("birthDate", "")
        age = None
        if birth_date:
            try:
                bd  = datetime.strptime(birth_date, "%Y-%m-%d")
                today = datetime.now()
                age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
            except ValueError:
                pass

        return {
            "id":         patient_id,
            "name":       full_name or "Unknown",
            "birth_date": birth_date,
            "age":        age,
            "sex":        p.get("gender", "unknown"),
        }

    # ── Conditions ────────────────────────────────────────────────────────────

    def get_conditions(self, patient_id: str) -> list[dict]:
        try:
            bundle = self._get("Condition", params={
                "patient": patient_id,
                "clinical-status": "active",
                "_count": "100",
            })
        except Exception as exc:
            logger.warning("fhir_get_conditions_failed patient_id=%s err=%s", patient_id, exc)
            return []

        results = []
        for res in self._bundle_entries(bundle):
            code    = res.get("code", {})
            codings = code.get("coding", [])
            results.append({
                "display":    code.get("text") or _coding_display(codings) or "Unknown condition",
                "code":       _coding_code(codings),
                "system":     codings[0].get("system", "") if codings else "",
                "onset":      res.get("onsetDateTime", ""),
                "status":     "active",
                "resource_id": res.get("id", ""),
            })
        return results

    # ── Medications ───────────────────────────────────────────────────────────

    def get_medications(self, patient_id: str) -> list[dict]:
        try:
            bundle = self._get("MedicationRequest", params={
                "patient": patient_id,
                "status":  "active",
                "_count":  "100",
            })
        except Exception as exc:
            logger.warning("fhir_get_medications_failed patient_id=%s err=%s", patient_id, exc)
            return []

        results = []
        for res in self._bundle_entries(bundle):
            med_concept = res.get("medicationCodeableConcept", {})
            med_codings = med_concept.get("coding", [])
            med_name    = med_concept.get("text") or _coding_display(med_codings) or (
                res.get("medicationReference", {}).get("display", "Unknown")
            )
            dosage_list = [d.get("text", "") for d in res.get("dosageInstruction", []) if d.get("text")]
            results.append({
                "display":       med_name,
                "code":          _coding_code(med_codings),
                "system":        med_codings[0].get("system", "") if med_codings else "",
                "authored_on":   res.get("authoredOn", ""),
                "status":        res.get("status", "active"),
                "prescriber":    (res.get("requester") or {}).get("display", "Unknown"),
                "dosage":        dosage_list[0] if dosage_list else "Not specified",
                "resource_id":   f"MedicationRequest/{res.get('id', '')}",
            })
        return results

    # ── Observations — by category or LOINC codes ─────────────────────────────

    def get_lab_observations(self, patient_id: str, lookback_days: int = 730) -> list[dict]:
        """Fetch recent laboratory observations (category=laboratory)."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        try:
            bundle = self._get("Observation", params={
                "patient":  patient_id,
                "category": "laboratory",
                "date":     f"ge{cutoff}",
                "_sort":    "-date",
                "_count":   "200",
            })
        except Exception as exc:
            logger.warning("fhir_get_lab_obs_failed patient_id=%s err=%s", patient_id, exc)
            return []

        return self._parse_observations(self._bundle_entries(bundle))

    def get_vital_observations(self, patient_id: str, lookback_days: int = 730) -> list[dict]:
        """Fetch recent vital-signs observations."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        try:
            bundle = self._get("Observation", params={
                "patient":  patient_id,
                "category": "vital-signs",
                "date":     f"ge{cutoff}",
                "_sort":    "-date",
                "_count":   "200",
            })
        except Exception as exc:
            logger.warning("fhir_get_vital_obs_failed patient_id=%s err=%s", patient_id, exc)
            return []

        return self._parse_observations(self._bundle_entries(bundle))

    def _parse_observations(self, resources: list[dict]) -> list[dict]:
        results = []
        for res in resources:
            code     = res.get("code", {})
            codings  = code.get("coding", [])
            obs_name = code.get("text") or _coding_display(codings) or "Unknown"
            loinc_code = next((c.get("code", "") for c in codings if "loinc" in c.get("system", "").lower()), "")

            value, unit = None, None
            if "valueQuantity" in res:
                vq    = res["valueQuantity"]
                value = vq.get("value")
                unit  = vq.get("unit") or vq.get("code")
            elif "valueCodeableConcept" in res:
                vcc = res["valueCodeableConcept"]
                value = vcc.get("text") or _coding_display(vcc.get("coding", []))
            elif "valueString" in res:
                value = res["valueString"]

            # Blood pressure panel — extract systolic/diastolic from components
            components = []
            for comp in res.get("component", []):
                comp_code  = comp.get("code", {})
                comp_name  = comp_code.get("text") or _coding_display(comp_code.get("coding", []))
                comp_loinc = next((c.get("code", "") for c in comp_code.get("coding", []) if "loinc" in c.get("system", "").lower()), "")
                comp_vq    = comp.get("valueQuantity", {})
                components.append({
                    "name":  comp_name,
                    "loinc": comp_loinc,
                    "value": comp_vq.get("value"),
                    "unit":  comp_vq.get("unit") or comp_vq.get("code"),
                })

            interp_list = res.get("interpretation", []) or []
            interp = ""
            if interp_list:
                first = interp_list[0]
                interp = first.get("text") or _coding_display(first.get("coding", []))

            results.append({
                "name":           obs_name,
                "loinc":          loinc_code,
                "value":          value,
                "unit":           unit,
                "components":     components if components else None,
                "effective_date": _date_str(res),
                "interpretation": interp,
                "resource_id":    f"Observation/{res.get('id', '')}",
            })
        return results

    # ── Build observation series by LOINC ─────────────────────────────────────

    def build_observation_series(self, all_observations: list[dict]) -> dict[str, list[dict]]:
        """
        From a flat list of observations, build a dict keyed by friendly label
        (e.g. "eGFR", "HbA1c") with values as time-sorted lists of data points.
        """
        series: dict[str, list[dict]] = {}

        for obs in all_observations:
            loinc   = obs.get("loinc", "")
            label   = TRACKED_LOINC_CODES.get(loinc, "")
            if not label:
                continue

            point = {
                "value":       obs["value"],
                "unit":        obs.get("unit"),
                "date":        obs.get("effective_date", ""),
                "resource_id": obs.get("resource_id", ""),
                "interpretation": obs.get("interpretation", ""),
            }
            series.setdefault(label, []).append(point)

            # For blood pressure panels, also index individual components
            for comp in (obs.get("components") or []):
                comp_label = TRACKED_LOINC_CODES.get(comp.get("loinc", ""), "")
                if comp_label and comp.get("value") is not None:
                    series.setdefault(comp_label, []).append({
                        "value":       comp["value"],
                        "unit":        comp.get("unit"),
                        "date":        obs.get("effective_date", ""),
                        "resource_id": obs.get("resource_id", ""),
                    })

        # Sort each series oldest → newest
        for label in series:
            series[label].sort(key=lambda x: x.get("date", ""))

        return series

    # ── Diagnostic Reports ────────────────────────────────────────────────────

    def get_diagnostic_reports(self, patient_id: str, lookback_days: int = 365) -> list[dict]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        try:
            bundle = self._get("DiagnosticReport", params={
                "patient": patient_id,
                "date":    f"ge{cutoff}",
                "_sort":   "-date",
                "_count":  "100",
            })
        except Exception as exc:
            logger.warning("fhir_get_dr_failed patient_id=%s err=%s", patient_id, exc)
            return []

        results = []
        for res in self._bundle_entries(bundle):
            code    = res.get("code", {})
            codings = code.get("coding", [])
            results.append({
                "display":       code.get("text") or _coding_display(codings) or "Unknown report",
                "loinc":         next((c.get("code", "") for c in codings if "loinc" in c.get("system", "").lower()), ""),
                "status":        res.get("status", ""),
                "effective_date": res.get("effectiveDateTime", ""),
                "conclusion":    res.get("conclusion", ""),
                "conclusion_codes": [
                    {"code": c.get("code", ""), "display": c.get("display", "")}
                    for cc in (res.get("conclusionCode") or [])
                    for c in cc.get("coding", [])
                ],
                "resource_id":   f"DiagnosticReport/{res.get('id', '')}",
                "ordering_provider": (
                    (res.get("resultsInterpreter") or [{}])[0].get("display", "")
                ),
            })
        return results

    # ── Encounters ────────────────────────────────────────────────────────────

    def get_encounters(self, patient_id: str, lookback_days: int = 365) -> list[dict]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        try:
            bundle = self._get("Encounter", params={
                "patient": patient_id,
                "date":    f"ge{cutoff}",
                "_sort":   "-date",
                "_count":  "50",
            })
        except Exception as exc:
            logger.warning("fhir_get_encounters_failed patient_id=%s err=%s", patient_id, exc)
            return []

        results = []
        for res in self._bundle_entries(bundle):
            type_list = res.get("type", [])
            enc_type  = (type_list[0].get("text") if type_list else "") or (
                _coding_display((type_list[0].get("coding") or []) if type_list else [])
            )
            period     = res.get("period") or {}
            start_date = period.get("start", "")[:10] if period.get("start") else ""
            participants = [
                (p.get("individual") or {}).get("display", "")
                for p in (res.get("participant") or [])
            ]
            reason_list  = res.get("reasonCode") or []
            reason       = reason_list[0].get("text", "") if reason_list else ""
            notes_list   = res.get("note") or []
            note_text    = notes_list[0].get("text", "") if notes_list else ""

            results.append({
                "date":          start_date,
                "type":          enc_type or "Visit",
                "providers":     [p for p in participants if p],
                "reason":        reason,
                "note_snippet":  note_text[:300] if note_text else "",
                "resource_id":   f"Encounter/{res.get('id', '')}",
            })
        return results

    # ── Procedures ────────────────────────────────────────────────────────────

    def get_procedures(self, patient_id: str, lookback_days: int = 365) -> list[dict]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        try:
            bundle = self._get("Procedure", params={
                "patient": patient_id,
                "date":    f"ge{cutoff}",
                "_sort":   "-date",
                "_count":  "100",
            })
        except Exception as exc:
            logger.warning("fhir_get_procedures_failed patient_id=%s err=%s", patient_id, exc)
            return []

        results = []
        for res in self._bundle_entries(bundle):
            code    = res.get("code", {})
            codings = code.get("coding", [])
            results.append({
                "display":     code.get("text") or _coding_display(codings) or "Unknown procedure",
                "date":        res.get("performedDateTime", "") or (res.get("performedPeriod") or {}).get("start", ""),
                "status":      res.get("status", ""),
                "resource_id": f"Procedure/{res.get('id', '')}",
            })
        return results

    # ── Allergies ─────────────────────────────────────────────────────────────

    def get_allergies(self, patient_id: str) -> list[dict]:
        try:
            bundle = self._get("AllergyIntolerance", params={
                "patient":         patient_id,
                "clinical-status": "active",
                "_count":          "50",
            })
        except Exception as exc:
            logger.warning("fhir_get_allergies_failed patient_id=%s err=%s", patient_id, exc)
            return []

        results = []
        for res in self._bundle_entries(bundle):
            code    = res.get("code", {})
            codings = code.get("coding", [])
            reactions = [
                r["manifestation"][0].get("text") or _coding_display(r["manifestation"][0].get("coding", []))
                for r in (res.get("reaction") or [])
                if r.get("manifestation")
            ]
            results.append({
                "display":   code.get("text") or _coding_display(codings) or "Unknown allergen",
                "reaction":  reactions[0] if reactions else "Unknown reaction",
                "type":      res.get("type", "allergy"),
                "status":    "active",
                "resource_id": f"AllergyIntolerance/{res.get('id', '')}",
            })
        return results

    # ── Full patient context ───────────────────────────────────────────────────

    def get_full_patient_context(self, patient_id: str) -> dict:
        """
        Fetch all FHIR resources needed for a complete SafeSignal risk briefing
        and return a normalised patient context dict.
        """
        logger.info("safesignal_fhir_full_context_start patient_id=%s", patient_id)

        patient = self.get_patient(patient_id)
        conditions = self.get_conditions(patient_id)
        medications = self.get_medications(patient_id)

        lab_obs   = self.get_lab_observations(patient_id, lookback_days=730)
        vital_obs = self.get_vital_observations(patient_id, lookback_days=730)
        all_obs   = lab_obs + vital_obs

        observation_series = self.build_observation_series(all_obs)

        diagnostic_reports = self.get_diagnostic_reports(patient_id, lookback_days=365)
        encounters         = self.get_encounters(patient_id, lookback_days=365)
        procedures         = self.get_procedures(patient_id, lookback_days=365)
        allergies          = self.get_allergies(patient_id)

        logger.info(
            "safesignal_fhir_full_context_done patient_id=%s "
            "meds=%d conditions=%d obs_series=%d reports=%d encounters=%d",
            patient_id, len(medications), len(conditions),
            len(observation_series), len(diagnostic_reports), len(encounters),
        )

        return {
            "patient":            patient,
            "conditions":         conditions,
            "medications":        medications,
            "observation_series": observation_series,
            "diagnostic_reports": diagnostic_reports,
            "encounters":         encounters,
            "procedures":         procedures,
            "allergies":          allergies,
        }

    # ── Medication-safety focused fetch ───────────────────────────────────────

    def get_medication_safety_data(self, patient_id: str) -> dict:
        """Focused fetch for medication safety analysis."""
        medications = self.get_medications(patient_id)
        lab_obs     = self.get_lab_observations(patient_id, lookback_days=365)
        vital_obs   = self.get_vital_observations(patient_id, lookback_days=180)
        all_obs     = lab_obs + vital_obs
        obs_series  = self.build_observation_series(all_obs)
        conditions  = self.get_conditions(patient_id)
        allergies   = self.get_allergies(patient_id)

        # Flatten the most recent value for each tracked lab
        latest_labs = {}
        for label, series in obs_series.items():
            if series:
                latest = series[-1]
                latest_labs[label] = {
                    "value":       latest["value"],
                    "unit":        latest.get("unit"),
                    "date":        latest.get("date"),
                    "resource_id": latest.get("resource_id"),
                }

        return {
            "medications":        medications,
            "latest_labs":        latest_labs,
            "observation_series": obs_series,
            "conditions":         conditions,
            "allergies":          allergies,
        }

    # ── Deterioration focused fetch ───────────────────────────────────────────

    def get_deterioration_data(self, patient_id: str) -> dict:
        """Focused fetch for deterioration (trend) analysis."""
        lab_obs   = self.get_lab_observations(patient_id, lookback_days=730)
        vital_obs = self.get_vital_observations(patient_id, lookback_days=730)
        all_obs   = lab_obs + vital_obs
        obs_series = self.build_observation_series(all_obs)
        conditions = self.get_conditions(patient_id)
        encounters = self.get_encounters(patient_id, lookback_days=365)

        return {
            "observation_series": obs_series,
            "conditions":         conditions,
            "recent_encounters":  encounters,
        }

    # ── Lost follow-up focused fetch ──────────────────────────────────────────

    def get_followup_data(self, patient_id: str) -> dict:
        """Focused fetch for lost follow-up detection."""
        diagnostic_reports = self.get_diagnostic_reports(patient_id, lookback_days=365)
        encounters         = self.get_encounters(patient_id, lookback_days=365)
        procedures         = self.get_procedures(patient_id, lookback_days=365)
        # Also include abnormal lab observations
        lab_obs = [
            obs for obs in self.get_lab_observations(patient_id, lookback_days=365)
            if obs.get("interpretation") in ("H", "L", "LL", "HH", "A", "AA",
                                              "High", "Low", "Critical", "Abnormal")
        ]

        return {
            "diagnostic_reports": diagnostic_reports,
            "abnormal_labs":      lab_obs,
            "encounters":         encounters,
            "procedures":         procedures,
        }
