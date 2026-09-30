"""
Extracts a patient ID from a doctor's spoken transcript using regex heuristics.

The doctor is expected to say something like:
  - "Patient ID P1234"
  - "Patient number 00421"
  - "PID-00421"
  - "Patient ID is OP-2024-1053"
  - "MR number 84521"
  - "Patient P T 0 0 4 2"  (digit-by-digit, Whisper joins them)

Returns the extracted ID string, or None if nothing is found.
"""
import re


# ── Ordered from most-specific to most-general ──────────────────────────────

_PATTERNS: list[tuple[str, int]] = [
    # "patient ID [is] <id>"  /  "patient number [is] <id>"  /  "patient no <id>"
    (
        r"patient\s+(?:i\.?d\.?|identification|number|num|no\.?|code)\s*"
        r"(?:is\s+)?"
        r"([A-Za-z]{0,4}[\s\-]?\d{2,10}(?:[\s\-]?[A-Za-z\d]+)?)",
        1,
    ),
    # "PID 12345"  /  "PID-12345"  /  "P.I.D. 12345"
    (r"\bP\.?I\.?D\.?[\s\-]?([A-Za-z\d]{3,14})", 1),
    # "MRN 12345"  /  "MR number 12345"  /  "MR no 12345"
    (r"\bMR\.?N?(?:\s+(?:number|no\.?))?\s*[\-]?\s*(\d{4,12})", 1),
    # "OP number 12345"  /  "IP number 12345"
    (r"\b(?:OP|IP)[\s\-]?(?:number|no\.?)?\s*[\-]?\s*(\d{3,10})", 1),
    # "patient #P1234"  /  "patient PT0042"  /  "patient 12345"
    (r"\bpatient\s+#?\s*([A-Za-z]{0,3}\d{3,10})", 1),
    # Standalone alphanumeric ID-like string after "ID" keyword
    (r"\bID\s*[:\-]?\s*([A-Za-z]{0,3}\d{3,10}[A-Za-z\d\-]*)", 1),
]


def _normalise(raw: str) -> str:
    """
    Collapse spaces/hyphens that appear when a doctor spells out an ID
    digit-by-digit (Whisper often inserts spaces between spoken digits).
    e.g. "P 0 0 4 2 1" → "P004221",  "P-0042" → "P0042"
    """
    # Remove internal spaces only when surrounded by single chars (spoken digits)
    # e.g. "P 0 0 4" → "P004"
    collapsed = re.sub(r"(?<=[A-Za-z\d])\s(?=[A-Za-z\d])", "", raw)
    # Remove hyphens
    collapsed = collapsed.replace("-", "")
    return collapsed.strip().upper()


def extract_patient_id_from_transcript(transcript: str) -> str | None:
    """
    Scans the transcript for a patient ID using a series of regex patterns.
    Returns the normalised ID string, or None if nothing matches.
    """
    if not transcript:
        return None

    text = transcript.strip()

    for pattern, group in _PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            raw = m.group(group)
            pid = _normalise(raw)
            if pid:
                return pid

    return None
