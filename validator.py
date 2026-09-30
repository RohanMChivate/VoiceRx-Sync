import re
import pandas as pd


def extract_dose_mg(dosage: str):
    """
    Extracts dose number from text.

    Example:
    '500mg' -> 500
    '500 mg' -> 500
    """
    if not dosage:
        return None

    match = re.search(r"(\d+)\s*mg", dosage.lower())

    if match:
        return int(match.group(1))

    return None


def normalize_medicine_name(name: str) -> str:
    """
    Converts simple brand names to generic names for demo.
    """
    if not name:
        return ""

    name = name.strip()

    brand_map = {
        "dolo": "Paracetamol",
        "dolo 650": "Paracetamol",
        "calpol": "Paracetamol",
    }

    return brand_map.get(name.lower(), name)


def validate_medicines(data: dict, csv_path: str = "medications.csv") -> dict:
    """
    Checks medicine dose using medications.csv.
    Adds warning to each medicine.
    """
    med_df = pd.read_csv(csv_path)

    safety_warnings = []

    for medicine in data.get("medicines", []):
        original_name = medicine.get("name", "")
        normalized_name = normalize_medicine_name(original_name)

        medicine["name"] = normalized_name

        dosage = medicine.get("dosage", "")
        dose_mg = extract_dose_mg(dosage)

        matched = med_df[
            med_df["name"].str.lower() == normalized_name.lower()
        ]

        if matched.empty:
            warning = "Medicine not found in safety database"
            medicine["warning"] = warning
            safety_warnings.append(f"{normalized_name}: {warning}")
            continue

        max_dose = int(matched.iloc[0]["max_single_dose_mg"])

        if dose_mg is None:
            warning = "Dose not detected clearly"
            medicine["warning"] = warning
            safety_warnings.append(f"{normalized_name}: {warning}")

        elif dose_mg > max_dose:
            warning = f"Dose exceeds safe single-dose limit of {max_dose}mg"
            medicine["warning"] = warning
            safety_warnings.append(f"{normalized_name}: {warning}")

        else:
            medicine["warning"] = "Validated"

    data["safety_warnings"] = safety_warnings

    return data