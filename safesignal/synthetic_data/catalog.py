"""Catalog of synthetic FHIR patients used for demo and regression testing."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SyntheticCase:
    """Metadata for one synthetic FHIR patient bundle."""

    key: str
    patient_id: str
    patient_name: str
    bundle_filename: str
    summary: str
    medication_keywords: tuple[str, ...] = ()
    deterioration_keywords: tuple[str, ...] = ()
    followup_keywords: tuple[str, ...] = ()
    briefing_keywords: tuple[str, ...] = ()
    expected_min_counts: dict[str, int] = field(default_factory=dict)

    @property
    def bundle_path(self) -> Path:
        return Path(__file__).resolve().parent / self.bundle_filename


DEFAULT_CASE_KEY = "margaret_chen"

_CASES = {
    "margaret_chen": SyntheticCase(
        key="margaret_chen",
        patient_id="patient-mc-071",
        patient_name="Margaret Chen",
        bundle_filename="margaret_chen.json",
        summary="Baseline CKD, diabetes, anticoagulation, and missed FOBT follow-up.",
        medication_keywords=("metformin", "egfr", "ibuprofen", "warfarin"),
        deterioration_keywords=("egfr", "a1c", "blood pressure"),
        followup_keywords=("fobt", "fecal", "colonoscopy"),
        briefing_keywords=("metformin", "ibuprofen", "warfarin", "fobt"),
        expected_min_counts={
            "conditions": 4,
            "medications": 4,
            "observation_series": 7,
            "diagnostic_reports": 1,
            "encounters": 3,
            "procedures": 0,
            "service_requests": 0,
            "allergies": 1,
        },
    ),
    "samuel_brooks_extreme": SyntheticCase(
        key="samuel_brooks_extreme",
        patient_id="patient-sb-067",
        patient_name="Samuel Brooks",
        bundle_filename="samuel_brooks_extreme.json",
        summary=(
            "Extreme polypharmacy and lab derangement case with documented GI and nephrology follow-up."
        ),
        medication_keywords=("potassium", "inr", "metformin", "spironolactone"),
        deterioration_keywords=("egfr", "creatinine", "blood pressure"),
        followup_keywords=("colonoscopy", "referral", "fobt"),
        briefing_keywords=("potassium", "inr", "colonoscopy", "metformin"),
        expected_min_counts={
            "conditions": 4,
            "medications": 5,
            "observation_series": 8,
            "diagnostic_reports": 1,
            "encounters": 3,
            "procedures": 1,
            "service_requests": 2,
            "allergies": 0,
        },
    ),
    "natalie_cho_sparse": SyntheticCase(
        key="natalie_cho_sparse",
        patient_id="patient-nc-046",
        patient_name="Natalie Cho",
        bundle_filename="natalie_cho_sparse.json",
        summary=(
            "Sparse-chart edge case with no active medications and timely mammogram-to-biopsy follow-up."
        ),
        medication_keywords=(),
        deterioration_keywords=("blood pressure", "weight"),
        followup_keywords=("mammogram", "biopsy", "bi-rads"),
        briefing_keywords=("mammogram", "biopsy", "bi-rads"),
        expected_min_counts={
            "conditions": 1,
            "medications": 0,
            "observation_series": 4,
            "diagnostic_reports": 1,
            "encounters": 2,
            "procedures": 1,
            "service_requests": 1,
            "allergies": 0,
        },
    ),
}

CASE_CHOICES = tuple(sorted(_CASES))


def get_case(key: str) -> SyntheticCase:
    try:
        return _CASES[key]
    except KeyError as exc:
        raise KeyError(f"Unknown synthetic case: {key}") from exc


def iter_cases() -> tuple[SyntheticCase, ...]:
    return tuple(_CASES[key] for key in CASE_CHOICES)
