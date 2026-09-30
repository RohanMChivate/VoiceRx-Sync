import json
import streamlit as st

from auth import logout
from stt import save_audio_file, transcribe_audio
from llm_extract import extract_medical_json
from validator import validate_medicines
from fhir_builder import build_fhir_prescription
from pdf_generator import create_prescription_pdf
from database import save_prescription

# ─── Auth guard ──────────────────────────────────────────────────────────────
doctor = st.session_state.get("doctor", {})

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #0f172a; }

    h1, h2, h3, h4, label, p, div { color: #e2e8f0 !important; }

    .hero-card {
        background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.08));
        border: 1px solid rgba(99,102,241,0.25);
        border-radius: 20px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
    }
    .stTextInput input, .stTextArea textarea, .stNumberInput input {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(99,102,241,0.4) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align:center; padding: 1rem 0;">
            <img src="{doctor.get('picture', '')}"
                 style="width:56px;height:56px;border-radius:50%;margin-bottom:0.5rem;">
            <div style="color:#e2e8f0;font-weight:700;">{doctor.get('name','Doctor')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    st.page_link("pages/1_Dashboard.py",        label="📊  Dashboard")
    st.page_link("pages/2_New_Consultation.py",  label="🎙️  New Consultation")
    st.page_link("pages/3_All_Consultations.py", label="📋  All Consultations")
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        logout()
        st.rerun()

# ─── Session state ────────────────────────────────────────────────────────────
for k, v in {
    "transcript": "",
    "medical_json": None,
    "final_data": None,
    "fhir_json": None,
    "pdf_path": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


def get_safe_age(value):
    try:
        return int(value) if value is not None else 0
    except Exception:
        return 0


# ─── Hero ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero-card">
        <h1 style="margin:0;">🎙️ New Consultation</h1>
        <p style="margin:0.25rem 0 0;color:rgba(255,255,255,0.5)!important;font-size:0.9rem;">
            Record a voice note → AI extracts prescription → Review → Save to MongoDB
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─── Two columns ─────────────────────────────────────────────────────────────
left_col, right_col = st.columns([1, 1.25], gap="large")

# ─── Left: Recording ──────────────────────────────────────────────────────────
with left_col:
    st.header("🎙️ Doctor Recording")

    audio_file = st.audio_input(
        "Record voice prescription",
        help="Click the microphone, speak naturally, then stop.",
    )

    if audio_file:
        st.audio(audio_file)

        if st.button("🚀 Process Voice Note", type="primary", use_container_width=True):
            try:
                with st.status("Processing prescription…", expanded=True) as status:
                    st.write("Saving audio…")
                    audio_path = save_audio_file(audio_file)

                    st.write("Transcribing voice…")
                    transcript = transcribe_audio(audio_path)
                    st.session_state.transcript = transcript

                    st.write("Extracting prescription JSON…")
                    extracted_json = extract_medical_json(transcript)

                    st.write("Checking medicine safety…")
                    validated_json = validate_medicines(extracted_json)
                    st.session_state.medical_json = validated_json

                    st.session_state.final_data = None
                    st.session_state.fhir_json = None
                    st.session_state.pdf_path = None

                    status.update(
                        label="Prescription processed!",
                        state="complete",
                        expanded=False,
                    )
                st.success("Voice note processed successfully!")

            except Exception as e:
                st.error("Something went wrong while processing the voice note.")
                st.exception(e)

    st.subheader("📝 Transcript")
    if st.session_state.transcript:
        st.info(st.session_state.transcript)
    else:
        st.caption("Transcript will appear here after processing.")

# ─── Right: Prescription form ────────────────────────────────────────────────
with right_col:
    st.header("📋 Extracted Prescription")

    if st.session_state.medical_json is None:
        st.info("Record and process a voice note to generate prescription data.")
    else:
        data = st.session_state.medical_json

        with st.form("prescription_form"):
            patient_name = st.text_input(
                "Patient Name", value=data.get("patient_name") or ""
            )
            age = st.number_input(
                "Age", min_value=0, max_value=120,
                value=get_safe_age(data.get("age")),
            )
            diagnosis = st.text_input(
                "Diagnosis", value=data.get("diagnosis") or ""
            )
            symptoms_text = st.text_area(
                "Symptoms", value=", ".join(data.get("symptoms", []))
            )

            st.subheader("Medicines")
            edited_medicines = []
            medicines = data.get("medicines", [])

            if not medicines:
                st.warning("No medicines detected.")

            for i, med in enumerate(medicines):
                st.markdown(f"**Medicine {i + 1}**")
                c1, c2 = st.columns(2)
                with c1:
                    name = st.text_input(
                        f"Name {i+1}", value=med.get("name", ""), key=f"mn_{i}"
                    )
                    dosage = st.text_input(
                        f"Dosage {i+1}", value=med.get("dosage", ""), key=f"md_{i}"
                    )
                with c2:
                    frequency = st.text_input(
                        f"Frequency {i+1}", value=med.get("frequency", ""), key=f"mf_{i}"
                    )
                    duration = st.text_input(
                        f"Duration {i+1}", value=med.get("duration", ""), key=f"mdu_{i}"
                    )

                warning = med.get("warning", "")
                if warning == "Validated":
                    st.success("✅ Dose validated")
                else:
                    st.warning(f"⚠️ {warning}")

                edited_medicines.append(
                    dict(name=name, dosage=dosage, frequency=frequency,
                         duration=duration, warning=warning)
                )

            approved = st.checkbox("Doctor reviewed and approved")
            submitted = st.form_submit_button(
                "💾 Save Final Prescription", type="primary", use_container_width=True
            )

            if submitted:
                st.session_state.final_data = {
                    "patient_name": patient_name,
                    "age": age,
                    "diagnosis": diagnosis,
                    "symptoms": [s.strip() for s in symptoms_text.split(",") if s.strip()],
                    "medicines": edited_medicines,
                    "safety_warnings": data.get("safety_warnings", []),
                    "doctor_approved": approved,
                }
                st.success("Prescription saved locally — click Sync below to push to MongoDB.")

        # ── Sync to MongoDB ────────────────────────────────────────────────────
        if st.session_state.final_data:
            st.divider()
            st.subheader("🧾 Final JSON Preview")
            st.json(st.session_state.final_data)

            if not st.session_state.final_data.get("doctor_approved"):
                st.warning("Doctor approval required before syncing.")

            if st.button(
                "🟢 Sync to MongoDB (ABDM/ABHA Demo)",
                type="primary",
                disabled=not st.session_state.final_data.get("doctor_approved"),
                use_container_width=True,
            ):
                fhir_json = build_fhir_prescription(st.session_state.final_data)
                pdf_path = create_prescription_pdf(st.session_state.final_data)

                # Save to MongoDB with doctor info
                save_prescription(
                    st.session_state.final_data,
                    fhir_json,
                    doctor,
                )

                st.session_state.fhir_json = fhir_json
                st.session_state.pdf_path = pdf_path
                st.success("✅ Saved to MongoDB!")
                st.balloons()

            if st.session_state.fhir_json:
                st.subheader("🏥 FHIR-style Demo Payload")
                st.json(st.session_state.fhir_json)

            if st.session_state.pdf_path:
                with open(st.session_state.pdf_path, "rb") as pdf_file:
                    st.download_button(
                        "📄 Download Digital Prescription PDF",
                        data=pdf_file,
                        file_name="digital_prescription.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
