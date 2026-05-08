"""
Unit tests for safesignal.tools.knowledge_enrichment

These tests exercise pure in-process logic (ingredient extraction and FDA label
cross-reference) without hitting external APIs. They run cleanly under pytest -q.
"""
from safesignal.tools.knowledge_enrichment import (
    _extract_ingredient,
    _find_fda_label_interactions,
)


def test_extract_ingredient_with_dose():
    assert _extract_ingredient("Metformin 1000mg BID") == "metformin"


def test_extract_ingredient_with_frequency():
    assert _extract_ingredient("Warfarin 5mg daily") == "warfarin"


def test_extract_ingredient_with_complex_name():
    assert _extract_ingredient("Lisinopril 20mg once daily") == "lisinopril"


def test_extract_ingredient_empty():
    assert _extract_ingredient("") == ""


def test_fda_cross_reference_finds_warfarin_ibuprofen():
    """
    FDA label cross-reference should detect the Warfarin-Ibuprofen interaction
    because ibuprofen's FDA label drug_interactions section mentions anticoagulants.
    Uses synthetic enriched med dicts with pre-populated FDA label text to avoid
    live API calls.
    """
    enriched_meds = [
        {
            "display": "Warfarin 5mg daily",
            "rxnorm_ingredient": "warfarin",
            "rxcui": "855332",
            "fda_drug_interactions_label": (
                "Nonsteroidal anti-inflammatory drugs (NSAIDs) including ibuprofen "
                "can inhibit platelet aggregation and may prolong bleeding time. "
                "Concomitant use with warfarin increases bleeding risk."
            ),
            "fda_warnings": "",
        },
        {
            "display": "Ibuprofen 400mg PRN",
            "rxnorm_ingredient": "ibuprofen",
            "rxcui": "41493",
            "fda_drug_interactions_label": (
                "Anticoagulants: Clinical studies and post-marketing reports show "
                "that concomitant use of NSAIDs and warfarin have a synergistic effect "
                "on bleeding."
            ),
            "fda_warnings": "",
        },
    ]

    interactions = _find_fda_label_interactions(enriched_meds)
    assert len(interactions) >= 1, "Expected at least one interaction for Warfarin+Ibuprofen"

    sources = {ix["source"] for ix in interactions}
    assert any("FDA" in s for s in sources), f"Expected FDA source, got: {sources}"


def test_fda_cross_reference_no_false_positive():
    """
    Two unrelated medications with no FDA label cross-mention should produce
    no interactions.
    """
    enriched_meds = [
        {
            "display": "Atorvastatin 40mg daily",
            "rxnorm_ingredient": "atorvastatin",
            "rxcui": "83367",
            "fda_drug_interactions_label": "Avoid concomitant use with strong CYP3A4 inhibitors.",
            "fda_warnings": "",
        },
        {
            "display": "Amlodipine 5mg daily",
            "rxnorm_ingredient": "amlodipine",
            "rxcui": "17767",
            "fda_drug_interactions_label": "Simvastatin: Limit simvastatin dose when co-administered.",
            "fda_warnings": "",
        },
    ]

    interactions = _find_fda_label_interactions(enriched_meds)
    assert interactions == [], f"Expected no interactions, got: {interactions}"
