"""
Professional Medical Prescription PDF Generator
Uses fpdf2 for a colorful, clinical prescription format.
"""
import os
from datetime import datetime
from pathlib import Path

from fpdf import FPDF
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")


# ── Colour palette ────────────────────────────────────────────────────────────
HEADER_BG      = (23,  82, 140)   # deep navy blue
HEADER_TEXT    = (255, 255, 255)
ACCENT         = (41, 182, 246)   # sky blue
RX_BG          = (240, 248, 255)  # light alice blue
SECTION_TITLE  = (23,  82, 140)
ROW_ALT        = (245, 250, 255)
TABLE_HEADER   = (41, 182, 246)
TABLE_TXT      = (255, 255, 255)
WARN_BG        = (255, 243, 205)
WARN_BORDER    = (255, 193,   7)
FOOTER_BG      = (23,  82, 140)
FOOTER_TEXT    = (200, 220, 255)
TEXT_DARK      = (30,  40,  60)
TEXT_MID       = (80, 100, 130)
DIVIDER        = (200, 220, 240)
APPROVED_GREEN = (34, 197, 94)
PENDING_AMBER  = (251, 191, 36)


def _decrypt_pid(token: str) -> str:
    try:
        from services.encryption import decrypt_patient_id
        return decrypt_patient_id(token)
    except Exception:
        return "[DECRYPTION ERROR]"


class PrescriptionPDF(FPDF):
    """Custom FPDF subclass with helper drawing methods."""

    def set_draw_color_rgb(self, r, g, b):
        self.set_draw_color(r, g, b)

    def hline(self, y=None, color=DIVIDER, thickness=0.4):
        if y is None:
            y = self.get_y()
        self.set_draw_color(*color)
        self.set_line_width(thickness)
        self.line(10, y, 200, y)
        self.set_line_width(0.2)


def create_prescription_pdf(
    data:        dict,
    doctor:      dict | None = None,
    doctor_info: dict | None = None,
    filename:    str  = "temp/digital_prescription.pdf",
) -> str:
    """
    Creates a professional, colorful prescription PDF.

    Args:
        data:        Prescription dict (medicines, diagnosis, symptoms, etc.)
        doctor:      Doctor profile from MongoDB (hospital_name, qualification, etc.)
        doctor_info: Basic doctor dict (name, email, picture)
        filename:    Output path
    """
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True)

    doctor       = doctor       or {}
    doctor_info  = doctor_info  or {}
    now          = datetime.now()

    # ── Resolved fields ───────────────────────────────────────────────────────
    hospital_name    = doctor.get("hospital_name")    or "VoiceRx Medical Centre"
    hospital_address = doctor.get("hospital_address") or ""
    hospital_city    = doctor.get("hospital_city")    or ""
    hospital_phone   = doctor.get("hospital_phone")   or ""
    doctor_name      = doctor_info.get("name")        or doctor.get("name") or "Doctor"
    qualification    = doctor.get("qualification")    or ""
    reg_no           = doctor.get("registration_no")  or ""

    encrypted_pid    = data.get("patient_id")
    patient_id       = _decrypt_pid(encrypted_pid) if encrypted_pid else "N/A"
    age              = data.get("age")
    diagnosis        = data.get("diagnosis") or "Not specified"
    symptoms         = data.get("symptoms") or []
    medicines        = data.get("medicines") or []
    advice           = data.get("advice") or ""
    warnings         = data.get("safety_warnings") or []
    approved         = data.get("doctor_approved", False)

    date_str = now.strftime("%d %B %Y")
    time_str = now.strftime("%I:%M %p")

    # ── PDF Setup ─────────────────────────────────────────────────────────────
    pdf = PrescriptionPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ═════════════════════════════════════════════════════════════════════════
    # HEADER — Hospital / Clinic letterhead
    # ═════════════════════════════════════════════════════════════════════════
    pdf.set_fill_color(*HEADER_BG)
    pdf.rect(0, 0, 210, 38, style="F")

    # Hospital name
    pdf.set_xy(10, 7)
    pdf.set_text_color(*HEADER_TEXT)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 9, hospital_name, ln=True)

    # Address / city / phone row
    addr_parts = [p for p in [hospital_address, hospital_city, hospital_phone] if p]
    if addr_parts:
        pdf.set_x(10)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(190, 215, 245)
        pdf.cell(0, 5, "  |  ".join(addr_parts), ln=True)

    # Doctor name + qualification (right-aligned in header)
    pdf.set_xy(10, 26)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*HEADER_TEXT)
    dr_line = f"Dr. {doctor_name}"
    if qualification:
        dr_line += f"   {qualification}"
    if reg_no:
        dr_line += f"   Reg: {reg_no}"
    pdf.cell(0, 5, dr_line, align="R", ln=True)

    # ── Accent stripe ─────────────────────────────────────────────────────────
    pdf.set_fill_color(*ACCENT)
    pdf.rect(0, 38, 210, 2.5, style="F")

    # ═════════════════════════════════════════════════════════════════════════
    # DATE / TIME + STATUS bar
    # ═════════════════════════════════════════════════════════════════════════
    pdf.set_xy(10, 43)
    pdf.set_text_color(*TEXT_MID)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(100, 5, f"Date: {date_str}    Time: {time_str}", ln=False)

    # Approval badge (right side)
    badge_x = 155
    if approved:
        pdf.set_fill_color(*APPROVED_GREEN)
        pdf.rect(badge_x, 41, 45, 8, style="F")
        pdf.set_xy(badge_x, 42.5)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(45, 5, "[OK]  DOCTOR APPROVED", align="C")
    else:
        pdf.set_fill_color(*PENDING_AMBER)
        pdf.rect(badge_x, 41, 45, 8, style="F")
        pdf.set_xy(badge_x, 42.5)
        pdf.set_text_color(90, 60, 0)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(45, 5, "[..] PENDING REVIEW", align="C")

    pdf.ln(8)
    pdf.hline()

    # ═════════════════════════════════════════════════════════════════════════
    # ℞  SECTION
    # ═════════════════════════════════════════════════════════════════════════
    pdf.set_fill_color(*RX_BG)
    pdf.rect(0, pdf.get_y() + 2, 210, 26, style="F")

    pdf.set_xy(10, pdf.get_y() + 4)
    # Draw "Rx" as a styled navy box — avoids Unicode glyph issues
    pdf.set_fill_color(*HEADER_BG)
    pdf.rect(10, pdf.get_y(), 18, 14, style="F")
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(18, 14, "Rx", align="C", ln=False)

    # Patient ID + Age
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*TEXT_DARK)
    pdf.set_xy(32, pdf.get_y())
    pdf.cell(0, 6, f"Patient ID:  {patient_id}", ln=True)

    pdf.set_x(32)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*TEXT_MID)
    age_str = f"{age} years" if age else "Age not specified"
    pdf.cell(80, 5, f"Age: {age_str}", ln=False)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*SECTION_TITLE)
    pdf.cell(0, 5, f"Diagnosis:  {diagnosis}", ln=True)

    pdf.ln(4)
    pdf.hline()
    pdf.ln(3)

    # ═════════════════════════════════════════════════════════════════════════
    # SYMPTOMS
    # ═════════════════════════════════════════════════════════════════════════
    if symptoms:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*SECTION_TITLE)
        pdf.cell(0, 6, "Presenting Complaints", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*TEXT_DARK)
        sym_text = "  /  ".join(s.capitalize() for s in symptoms)
        pdf.multi_cell(0, 6, sym_text)
        pdf.ln(2)
        pdf.hline()
        pdf.ln(3)

    # ═════════════════════════════════════════════════════════════════════════
    # MEDICINES TABLE
    # ═════════════════════════════════════════════════════════════════════════
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*SECTION_TITLE)
    pdf.cell(0, 7, "Prescription", ln=True)
    pdf.ln(1)

    if medicines:
        # Table header
        col_w = [8, 62, 34, 42, 30, 14]   # #, Name, Dosage, Frequency, Duration, Valid
        headers = ["#", "Medicine", "Dosage", "Frequency", "Duration", "Valid"]

        pdf.set_fill_color(*TABLE_HEADER)
        pdf.set_text_color(*TABLE_TXT)
        pdf.set_font("Helvetica", "B", 9)
        x_start = 10
        pdf.set_x(x_start)
        for w, h in zip(col_w, headers):
            pdf.cell(w, 8, h, border=0, align="C", fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 9)
        for i, med in enumerate(medicines):
            is_alt = i % 2 == 1
            pdf.set_fill_color(*(ROW_ALT if is_alt else (255, 255, 255)))
            pdf.set_text_color(*TEXT_DARK)

            row = [
                str(i + 1),
                med.get("name") or "-",
                med.get("dosage") or "-",
                med.get("frequency") or "-",
                med.get("duration") or "-",
                "[OK]" if med.get("warning") == "Validated" else "[!]",
            ]
            aligns = ["C", "L", "C", "L", "C", "C"]

            pdf.set_x(x_start)
            # Row height may need to expand for long medicine names
            row_h = 7
            for w, txt, align in zip(col_w, row, aligns):
                pdf.cell(w, row_h, txt, border=0, align=align, fill=True)
            pdf.ln()

            # Show warning text below row if not validated
            warn_txt = med.get("warning", "")
            if warn_txt and warn_txt != "Validated":
                pdf.set_x(x_start + col_w[0])
                pdf.set_font("Helvetica", "I", 7.5)
                pdf.set_text_color(180, 80, 0)
                pdf.cell(0, 5, f"  [!]  {warn_txt}", ln=True, fill=False)
                pdf.set_font("Helvetica", "", 9)

        # Bottom border of table
        pdf.hline(color=ACCENT, thickness=0.6)
    else:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(*TEXT_MID)
        pdf.cell(0, 8, "No medicines prescribed.", ln=True)

    pdf.ln(3)

    # ═════════════════════════════════════════════════════════════════════════
    # SAFETY WARNINGS box
    # ═════════════════════════════════════════════════════════════════════════
    notable_warns = [w for w in warnings if w and "Validated" not in w]
    if notable_warns:
        pdf.set_fill_color(*WARN_BG)
        pdf.set_draw_color(*WARN_BORDER)
        pdf.set_line_width(0.5)
        box_y = pdf.get_y()
        pdf.rect(10, box_y, 190, 6 + len(notable_warns) * 6, style="FD")
        pdf.set_line_width(0.2)

        pdf.set_xy(13, box_y + 2)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(160, 80, 0)
        pdf.cell(0, 5, "Safety Alerts", ln=True)
        for w in notable_warns:
            pdf.set_x(13)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(120, 60, 0)
            pdf.cell(0, 5, f"  [!]  {w}", ln=True)
        pdf.ln(2)

    # ═════════════════════════════════════════════════════════════════════════
    # ADVICE / INSTRUCTIONS
    # ═════════════════════════════════════════════════════════════════════════
    if advice:
        pdf.ln(1)
        pdf.hline()
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*SECTION_TITLE)
        pdf.cell(0, 6, "Doctor's Advice and Instructions", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*TEXT_DARK)
        pdf.multi_cell(0, 6, advice)
        pdf.ln(2)

    # ═════════════════════════════════════════════════════════════════════════
    # SIGNATURE LINE
    # ═════════════════════════════════════════════════════════════════════════
    pdf.ln(4)
    pdf.hline()
    pdf.ln(10)
    # Signature block right-aligned
    sig_x = 130
    pdf.set_x(sig_x)
    pdf.set_draw_color(*TEXT_MID)
    pdf.set_line_width(0.4)
    pdf.line(sig_x, pdf.get_y(), 200, pdf.get_y())
    pdf.set_xy(sig_x, pdf.get_y() + 1)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*TEXT_DARK)
    pdf.cell(70, 5, f"Dr. {doctor_name}", align="C", ln=True)
    if qualification:
        pdf.set_x(sig_x)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*TEXT_MID)
        pdf.cell(70, 4, qualification, align="C", ln=True)
    if reg_no:
        pdf.set_x(sig_x)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*TEXT_MID)
        pdf.cell(70, 4, f"Reg. No: {reg_no}", align="C", ln=True)

    # ═════════════════════════════════════════════════════════════════════════
    # FOOTER
    # ═════════════════════════════════════════════════════════════════════════
    footer_y = 280
    pdf.set_fill_color(*FOOTER_BG)
    pdf.rect(0, footer_y, 210, 17, style="F")

    pdf.set_xy(10, footer_y + 3)
    pdf.set_font("Helvetica", "I", 7.5)
    pdf.set_text_color(*FOOTER_TEXT)
    pdf.multi_cell(
        0, 4,
        "This prescription is generated by VoiceRx Sync - an AI-assisted clinical documentation tool.\n"
        "A licensed doctor must review and approve all outputs before dispensing.",
        align="C",
    )

    pdf.output(filename)
    return filename