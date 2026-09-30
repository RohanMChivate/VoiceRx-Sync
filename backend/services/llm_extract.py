import os
import re
import json
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# ──────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT — few-shot examples + explicit per-field rules
# ──────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are MedExtract, a precise medical prescription extraction engine.

Extract structured data from a doctor's consultation transcript and return ONLY a JSON object.

━━━ REQUIRED JSON SCHEMA ━━━
{
  "age":          integer or null,
  "symptoms":     [string, ...],
  "diagnosis":    string or null,
  "medicines":    [
    {
      "name":      string,
      "dosage":    string or null,
      "frequency": string or null,
      "duration":  string or null
    }
  ],
  "advice":       string or null
}

NOTE: Do NOT extract or include patient name or patient ID — those are handled separately.

━━━ FIELD DEFINITIONS (read carefully) ━━━

▸ name      — The drug name only. No dose, no route, no frequency here.
              Map brand → generic: Dolo/Calpol/Crocin→Paracetamol,
              Azithral/Zithromax→Azithromycin, Ciplox→Ciprofloxacin,
              Metrogyl/Flagyl→Metronidazole, Augmentin→Amoxicillin-Clavulanate,
              Combiflam→Ibuprofen+Paracetamol, Pan/Pan-D/Pantop→Pantoprazole,
              Montair/Montek/Telekast→Montelukast, Allegra→Fexofenadine,
              Limcee→Vitamin C, Becosules→Vitamin B Complex,
              Shelcal→Calcium Carbonate.

▸ dosage    — ONLY the amount + unit. Examples: "500 mg", "250 mg", "1 g",
              "10 ml", "1 tablet", "2 puffs", "8 mg IV".
              NEVER put frequency words here ("twice", "daily", "OD", etc.).

▸ frequency — ONLY how often per day. Normalize to:
              OD / once daily  →  "once daily"
              BD / twice daily →  "twice daily"
              TDS / thrice     →  "three times a day"
              QID / four times →  "four times a day"
              SOS / PRN        →  "as needed"
              HS / at night    →  "at bedtime"
              NEVER put dosage amounts or duration here.

▸ duration  — ONLY the time span. Examples: "5 days", "2 weeks", "1 month",
              "3 months", "stat" (for one-time).
              NEVER put dosage or frequency here.

━━━ FEW-SHOT EXAMPLES ━━━

Input: "Metformin 500mg twice a day for 3 months"
Output medicine object:
{"name":"Metformin","dosage":"500 mg","frequency":"twice daily","duration":"3 months"}

Input: "Amoxicillin 250mg TDS for 7 days"
Output medicine object:
{"name":"Amoxicillin","dosage":"250 mg","frequency":"three times a day","duration":"7 days"}

Input: "Dolo 650 twice daily for 5 days, Pan-D once daily for 5 days, Limcee once daily"
Output medicines array — NOTICE each drug gets its OWN dosage/frequency/duration:
[
  {"name":"Paracetamol","dosage":"650 mg","frequency":"twice daily","duration":"5 days"},
  {"name":"Pantoprazole","dosage":null,"frequency":"once daily","duration":"5 days"},
  {"name":"Vitamin C","dosage":null,"frequency":"once daily","duration":null}
]

Input: "Azithromycin 500mg OD for 3 days, Ibuprofen 400mg TDS for 5 days, Pantoprazole 40mg OD for 5 days"
Output medicines array:
[
  {"name":"Azithromycin","dosage":"500 mg","frequency":"once daily","duration":"3 days"},
  {"name":"Ibuprofen","dosage":"400 mg","frequency":"three times a day","duration":"5 days"},
  {"name":"Pantoprazole","dosage":"40 mg","frequency":"once daily","duration":"5 days"}
]

Input: "Give Metformin 500mg BD and Glimepiride 1mg OD both for 1 month, also Aspirin 75mg OD"
Output medicines array:
[
  {"name":"Metformin","dosage":"500 mg","frequency":"twice daily","duration":"1 month"},
  {"name":"Glimepiride","dosage":"1 mg","frequency":"once daily","duration":"1 month"},
  {"name":"Aspirin","dosage":"75 mg","frequency":"once daily","duration":null}
]

━━━ RULES ━━━
1. Output ONLY the JSON object. No markdown, no code fences, no explanation.
2. Each medicine in the transcript MUST become its own SEPARATE object in the medicines array.
3. CRITICAL — keep each drug's fields independent:
   - The dosage, frequency, duration you write for drug N must belong to drug N only.
   - Do NOT copy or reuse one drug's values for another drug.
4. Use null for any field not explicitly stated in the transcript. Do NOT invent values.
5. If one drug appears with two doses (e.g. step-down), create two separate objects.
6. symptoms: short lowercase strings e.g. ["fever","headache"]. Expand SOB→"shortness of breath".
7. advice: single string with lifestyle/follow-up instructions, or null.
"""

_EMPTY: dict = {
    "patient_id":   None,   # filled in by the router after encryption — never by LLM
    "age":          None,
    "symptoms":     [],
    "diagnosis":    None,
    "medicines":    [],
    "advice":       None,
}

# ──────────────────────────────────────────────────────────────────────────────
# Patterns used for Python-side field-swap correction
# ──────────────────────────────────────────────────────────────────────────────
_FREQ_PATTERN = re.compile(
    r"\b(once|twice|thrice|daily|OD|BD|TDS|QID|SOS|PRN|HS|"
    r"once daily|twice daily|three times|four times|every \d+ hours?|"
    r"at bedtime|as needed|morning|night|evening)\b",
    re.IGNORECASE,
)
_DOSE_PATTERN = re.compile(
    r"\b(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|IU|units?|puffs?|tablets?|drops?))\b",
    re.IGNORECASE,
)
_DUR_PATTERN = re.compile(
    r"\b(\d+\s*(?:days?|weeks?|months?|years?))\b",
    re.IGNORECASE,
)


def _looks_like_frequency(s: str) -> bool:
    return bool(s and _FREQ_PATTERN.search(s))


def _looks_like_dose(s: str) -> bool:
    return bool(s and _DOSE_PATTERN.search(s))


def _looks_like_duration(s: str) -> bool:
    return bool(s and _DUR_PATTERN.search(s))


def _sanitize_medicine(med: dict) -> dict:
    """
    Detect and correct obviously swapped fields.

    Common failure modes:
    - dosage  = "twice daily"   → should be in frequency
    - frequency = "500 mg"      → should be in dosage
    - duration  = "twice daily" → should be in frequency
    """
    name      = med.get("name")      or ""
    dosage    = med.get("dosage")    or ""
    frequency = med.get("frequency") or ""
    duration  = med.get("duration")  or ""

    # Collect all non-empty values to redistribute if needed
    pool = {
        "dosage":    dosage,
        "frequency": frequency,
        "duration":  duration,
    }

    # Detect clearly wrong placements
    fixed = {"dosage": None, "frequency": None, "duration": None}

    for field, val in pool.items():
        if not val:
            continue
        # If dosage slot contains a frequency-like string, move it
        if field == "dosage" and not _looks_like_dose(val) and _looks_like_frequency(val):
            fixed["frequency"] = fixed["frequency"] or val
        # If frequency slot contains a dose-like string, move it
        elif field == "frequency" and not _looks_like_frequency(val) and _looks_like_dose(val):
            fixed["dosage"] = fixed["dosage"] or val
        # If duration slot contains a frequency-like string, move it
        elif field == "duration" and not _looks_like_duration(val) and _looks_like_frequency(val):
            fixed["frequency"] = fixed["frequency"] or val
        # If frequency slot contains a duration-like string, move it
        elif field == "frequency" and not _looks_like_frequency(val) and _looks_like_duration(val):
            fixed["duration"] = fixed["duration"] or val
        else:
            fixed[field] = fixed[field] or val  # keep in place

    return {
        "name":      name or "Unknown",
        "dosage":    fixed["dosage"],
        "frequency": fixed["frequency"],
        "duration":  fixed["duration"],
    }


# ──────────────────────────────────────────────────────────────────────────────
# API helpers
# ──────────────────────────────────────────────────────────────────────────────

def get_api_key() -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set.")
    return api_key


def get_groq_client() -> Groq:
    return Groq(api_key=get_api_key())


def _safe_parse(content: str) -> dict:
    """Parse JSON with 3-tier fallback: direct → strip fences → regex extract."""
    content = content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Strip ```json ... ``` fences
    fenced = re.sub(r"^```(?:json)?\s*", "", content)
    fenced = re.sub(r"\s*```$", "", fenced).strip()
    try:
        return json.loads(fenced)
    except json.JSONDecodeError:
        pass

    # Last resort: extract first {...} block
    m = re.search(r"\{.*\}", content, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass

    return dict(_EMPTY)


# ──────────────────────────────────────────────────────────────────────────────
# Main extraction function
# ──────────────────────────────────────────────────────────────────────────────

def extract_medical_json(transcript: str) -> dict:
    """Converts a doctor's spoken transcript into a validated prescription dict."""
    if not transcript or not transcript.strip():
        return dict(_EMPTY)

    client = get_groq_client()

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"Transcript:\n{transcript.strip()}"},
        ],
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=1024,
    )

    content = response.choices[0].message.content or ""
    result  = _safe_parse(content)

    # ── Ensure all required top-level keys exist ──────────────────────────────
    for key, default in _EMPTY.items():
        result.setdefault(key, default)

    # ── Normalise age → int or None ───────────────────────────────────────────
    if result.get("age") is not None:
        try:
            result["age"] = int(float(str(result["age"])))
        except (ValueError, TypeError):
            result["age"] = None

    # ── Ensure symptoms is a list of strings ─────────────────────────────────
    # IMPORTANT: use `or []` not .get("symptoms", []) — the default only fires
    # when the key is MISSING; when LLM returns "symptoms": null it returns None.
    syms = result.get("symptoms") or []
    if isinstance(syms, str):
        syms = [s.strip() for s in syms.split(",") if s.strip()]
    result["symptoms"] = [str(s).strip() for s in syms if s]

    # ── Sanitize each medicine object ────────────────────────────────────────
    clean_meds = []
    for med in (result.get("medicines") or []):
        if not isinstance(med, dict):
            continue
        # Normalise key aliases the model sometimes uses
        if "medicine" in med and "name" not in med:
            med["name"] = med.pop("medicine")
        if "drug" in med and "name" not in med:
            med["name"] = med.pop("drug")
        if "dose" in med and "dosage" not in med:
            med["dosage"] = med.pop("dose")
        if "freq" in med and "frequency" not in med:
            med["frequency"] = med.pop("freq")
        if "days" in med and "duration" not in med:
            med["duration"] = med.pop("days")

        clean_meds.append(_sanitize_medicine(med))

    result["medicines"] = clean_meds

    # ── Strip patient_name if model still emits it (defensive) ───────────────
    result.pop("patient_name", None)

    # ── patient_id is always None here — the router injects it post-encryption ─
    result["patient_id"] = None

    return result