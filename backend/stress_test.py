import json, sys
sys.path.insert(0, '.')
from services.llm_extract import extract_medical_json

cases = [
    "Give tab Metformin 500mg twice a day for 3 months.",
    "Prescribe Amoxicillin 250mg three times daily for 7 days and Paracetamol 1g as needed.",
    "Patient needs Atorvastatin 10mg at night, Amlodipine 5mg in the morning for 1 month.",
    "Give injection Dexamethasone 8mg IV stat.",
    "Azithromycin 500mg day one then 250mg daily for four days.",
    "Dolo 650 BD for 5 days, Pan-D OD for 5 days, Limcee OD.",
    "Metrogyl 400mg TDS for 7 days, Ciplox 500mg BD for 5 days.",
]

for c in cases:
    r = extract_medical_json(c)
    print("INPUT:", c[:70])
    for m in r.get("medicines", []):
        print("  MED:", m)
    print()
