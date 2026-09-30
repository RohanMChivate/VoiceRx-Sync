import os
from fpdf import FPDF


def create_prescription_pdf(data: dict, filename: str = "temp/digital_prescription.pdf") -> str:
    """
    Creates a simple digital prescription PDF.
    """
    os.makedirs("temp", exist_ok=True)

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "VoiceRx Sync", ln=True)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Digital Prescription", ln=True)

    pdf.ln(5)

    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"Patient Name: {data.get('patient_name') or 'N/A'}", ln=True)
    pdf.cell(0, 8, f"Age: {data.get('age') or 'N/A'}", ln=True)
    pdf.cell(0, 8, f"Diagnosis: {data.get('diagnosis') or 'N/A'}", ln=True)

    symptoms = ", ".join(data.get("symptoms", [])) or "N/A"
    pdf.multi_cell(0, 8, f"Symptoms: {symptoms}")

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Medicines", ln=True)

    pdf.set_font("Helvetica", "", 12)

    medicines = data.get("medicines", [])

    if not medicines:
        pdf.cell(0, 8, "No medicines detected.", ln=True)

    for index, med in enumerate(medicines, start=1):
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, f"{index}. {med.get('name', 'Unknown Medicine')}", ln=True)

        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 8, f"Dosage: {med.get('dosage', 'N/A')}", ln=True)
        pdf.cell(0, 8, f"Frequency: {med.get('frequency', 'N/A')}", ln=True)
        pdf.cell(0, 8, f"Duration: {med.get('duration', 'N/A')}", ln=True)
        pdf.multi_cell(0, 8, f"Safety: {med.get('warning', 'N/A')}")

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 10)
    pdf.multi_cell(
        0,
        6,
        "Safety Note: This is a clinical documentation assistant. "
        "A licensed doctor must review and approve all outputs."
    )

    pdf.output(filename)

    return filename