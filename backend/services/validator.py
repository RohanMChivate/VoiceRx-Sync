import re
import os
from pathlib import Path
import pandas as pd

_CSV_PATH = Path(__file__).parent / "medications.csv"

# Brand → Generic mapping (expanded)
BRAND_MAP: dict[str, str] = {
    # Paracetamol
    "dolo":                  "Paracetamol",
    "dolo 650":              "Paracetamol",
    "calpol":                "Paracetamol",
    "crocin":                "Paracetamol",
    "tylenol":               "Paracetamol",
    "panadol":               "Paracetamol",
    "fepanil":               "Paracetamol",
    # Ibuprofen
    "brufen":                "Ibuprofen",
    "combiflam":             "Ibuprofen",
    "advil":                 "Ibuprofen",
    "nurofen":               "Ibuprofen",
    # Antibiotics
    "azithral":              "Azithromycin",
    "zithromax":             "Azithromycin",
    "ciplox":                "Ciprofloxacin",
    "cipla":                 "Ciprofloxacin",
    "metrogyl":              "Metronidazole",
    "flagyl":                "Metronidazole",
    "augmentin":             "Amoxicillin-Clavulanate",
    "amoxyclav":             "Amoxicillin-Clavulanate",
    # Antihistamines
    "allegra":               "Fexofenadine",
    "telekast":              "Montelukast",
    "montek":                "Montelukast",
    "montair":               "Montelukast",
    "cetrizine":             "Cetirizine",
    "cetirizine":            "Cetirizine",
    "levocetirizine":        "Levocetirizine",
    # Antacids
    "pan":                   "Pantoprazole",
    "pan-d":                 "Pantoprazole",
    "pantop":                "Pantoprazole",
    "omez":                  "Omeprazole",
    "omeprazole":            "Omeprazole",
    "ranitac":               "Ranitidine",
    # Vitamins
    "shelcal":               "Calcium Carbonate",
    "limcee":                "Vitamin C",
    "becosules":             "Vitamin B Complex",
}


def extract_dose_mg(dosage: str | None) -> int | None:
    if not dosage:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*mg", str(dosage).lower())
    return int(float(match.group(1))) if match else None


def normalize_medicine_name(name: str) -> str:
    if not name:
        return ""
    key = name.strip().lower()
    return BRAND_MAP.get(key, name.strip())


def _fuzzy_match(name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Try exact then contains match on the medicine name column."""
    lower = name.lower()
    # 1. exact
    exact = df[df["name"].str.lower() == lower]
    if not exact.empty:
        return exact
    # 2. startswith
    starts = df[df["name"].str.lower().str.startswith(lower)]
    if not starts.empty:
        return starts
    # 3. contains
    contains = df[df["name"].str.lower().str.contains(re.escape(lower), na=False)]
    return contains


def validate_medicines(data: dict, csv_path: str | None = None) -> dict:
    """Checks medicine dose using medications.csv. Adds warning to each medicine."""
    csv_file = Path(csv_path) if csv_path else _CSV_PATH
    try:
        med_df = pd.read_csv(csv_file)
        # Normalise column names defensively
        med_df.columns = [c.strip().lower().replace(" ", "_") for c in med_df.columns]
    except FileNotFoundError:
        for medicine in data.get("medicines", []):
            medicine.setdefault("warning", "Validation skipped — CSV not found")
        data.setdefault("safety_warnings", [])
        return data

    safety_warnings: list[str] = []

    for medicine in data.get("medicines", []):
        original_name  = medicine.get("name", "") or ""
        normalized     = normalize_medicine_name(original_name)
        medicine["name"] = normalized

        dosage  = medicine.get("dosage") or ""
        dose_mg = extract_dose_mg(dosage)

        matched = _fuzzy_match(normalized, med_df)

        if matched.empty:
            warning = "Medicine not found in safety database"
            medicine["warning"] = warning
            safety_warnings.append(f"{normalized}: {warning}")
            continue

        # Safely get max dose — column may be named differently
        max_col = next(
            (c for c in matched.columns if "max" in c and "dose" in c), None
        )
        if max_col is None:
            medicine["warning"] = "Validated (dose limit unavailable)"
            continue

        try:
            max_dose = int(matched.iloc[0][max_col])
        except (ValueError, TypeError):
            medicine["warning"] = "Validated (dose limit unreadable)"
            continue

        if dose_mg is None:
            warning = "Dose not detected clearly - verify manually"
            medicine["warning"] = warning
            safety_warnings.append(f"{normalized}: {warning}")
        elif dose_mg > max_dose:
            warning = f"[!] Dose exceeds safe single-dose limit of {max_dose} mg"
            medicine["warning"] = warning
            safety_warnings.append(f"{normalized}: {warning}")
        else:
            medicine["warning"] = "Validated"

    data["safety_warnings"] = safety_warnings
    return data