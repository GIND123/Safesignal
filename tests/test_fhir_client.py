from safesignal.tools.fhir_client import FHIRClient


def test_get_encounters_reads_narrative_text() -> None:
    client = FHIRClient("https://example.test/fhir", "token")
    bundle = {
        "resourceType": "Bundle",
        "entry": [
            {
                "resource": {
                    "resourceType": "Encounter",
                    "id": "enc-1",
                    "status": "finished",
                    "type": [{"text": "Office Visit"}],
                    "participant": [{"individual": {"display": "Dr. Test"}}],
                    "period": {"start": "2026-03-02", "end": "2026-03-02"},
                    "reasonCode": [{"text": "Follow-up"}],
                    "text": {
                        "status": "generated",
                        "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\">Reviewed abnormal mammogram with patient.</div>",
                    },
                }
            }
        ],
    }

    client._get = lambda path, params=None: bundle

    encounters = client.get_encounters("patient-1")

    assert encounters == [
        {
            "date": "2026-03-02",
            "type": "Office Visit",
            "providers": ["Dr. Test"],
            "reason": "Follow-up",
            "note_snippet": "Reviewed abnormal mammogram with patient.",
            "resource_id": "Encounter/enc-1",
        }
    ]
