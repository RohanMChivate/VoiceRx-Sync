from datetime import datetime


def build_fhir_prescription(data: dict) -> dict:
    """
    Creates a simple FHIR-compatible demo prescription payload.
    Patient identity is represented by the encrypted patient_id token.
    """

    patient_id = data.get("patient_id") or "UNKNOWN"

    fhir_bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": datetime.now().isoformat(),
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "identifier": [
                        {
                            "system": "urn:voicerx:patient-id",
                            "value":  patient_id,   # stored as encrypted token
                        }
                    ],
                    "extension": [
                        {
                            "url":          "age",
                            "valueInteger": data.get("age"),
                        }
                    ],
                }
            },

            {
                "resource": {
                    "resourceType": "Condition",
                    "code": {
                        "text": data.get("diagnosis")
                    },
                    "note": [
                        {
                            "text": "Symptoms: " + ", ".join(data.get("symptoms", []))
                        }
                    ]
                }
            }
        ]
    }

    for medicine in data.get("medicines", []):
        dosage_text = (
            f"{medicine.get('dosage', '')} "
            f"{medicine.get('frequency', '')} "
            f"for {medicine.get('duration', '')}"
        )

        fhir_bundle["entry"].append(
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {
                        "text": medicine.get("name", "")
                    },
                    "dosageInstruction": [
                        {
                            "text": dosage_text
                        }
                    ],
                    "note": [
                        {
                            "text": medicine.get("warning", "")
                        }
                    ]
                }
            }
        )

    return fhir_bundle