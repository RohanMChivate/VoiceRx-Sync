from datetime import datetime

import streamlit as st

from auth import logout
from database import get_consultations_by_doctor, get_consultation_by_id

# ─── Auth guard ──────────────────────────────────────────────────────────────
doctor = st.session_state.get("doctor", {})

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #0f172a; }
    h1,h2,h3,h4,label,p,div { color: #e2e8f0 !important; }

    .page-title {
        font-size: 1.8rem; font-weight: 700;
        background: linear-gradient(135deg, #a5b4fc, #c4b5fd);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    .stTextInput input {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important;
        color: #e2e8f0 !important;
    }
    .consult-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 14px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.6rem;
        transition: border-color 0.2s;
    }
    .consult-card:hover { border-color: rgba(99,102,241,0.4); }
    .patient-name { font-size: 1.05rem; font-weight: 700; color: #e2e8f0; }
    .meta-line { font-size: 0.78rem; color: rgba(255,255,255,0.4); margin-top: 0.2rem; }
    .badge-approved {
        background: rgba(34,197,94,0.15); color: #86efac;
        border: 1px solid rgba(34,197,94,0.3);
        border-radius: 20px; padding: 0.2rem 0.7rem;
        font-size: 0.72rem; font-weight: 600;
    }
    .badge-pending {
        background: rgba(251,191,36,0.15); color: #fde68a;
        border: 1px solid rgba(251,191,36,0.3);
        border-radius: 20px; padding: 0.2rem 0.7rem;
        font-size: 0.72rem; font-weight: 600;
    }
    .detail-panel {
        background: rgba(99,102,241,0.06);
        border: 1px solid rgba(99,102,241,0.15);
        border-radius: 16px;
        padding: 1.5rem;
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

# ─── Title ────────────────────────────────────────────────────────────────────
st.markdown('<p class="page-title">📋 All Consultations</p>', unsafe_allow_html=True)
st.caption(f"Showing consultations for Dr. {doctor.get('name', '')}")
st.markdown("---")

# ─── Fetch all consultations ──────────────────────────────────────────────────
with st.spinner("Loading consultations…"):
    all_consultations = get_consultations_by_doctor(doctor["email"])

if not all_consultations:
    st.info("No consultations yet. Start your first one!")
    st.stop()

# ─── Search & Filter ─────────────────────────────────────────────────────────
f1, f2, f3 = st.columns([2, 1.2, 1.2])
with f1:
    search = st.text_input("🔍 Search patient name or diagnosis", placeholder="e.g. Ramu, fever…")
with f2:
    status_filter = st.selectbox(
        "Status", ["All", "Approved", "Pending"], label_visibility="collapsed"
    )
with f3:
    sort_order = st.selectbox(
        "Sort", ["Newest First", "Oldest First"], label_visibility="collapsed"
    )

# ─── Apply filters ────────────────────────────────────────────────────────────
filtered = all_consultations

if search.strip():
    q = search.strip().lower()
    filtered = [
        c for c in filtered
        if q in (c.get("patient_name") or "").lower()
        or q in (c.get("diagnosis") or "").lower()
    ]

if status_filter == "Approved":
    filtered = [c for c in filtered if c.get("doctor_approved")]
elif status_filter == "Pending":
    filtered = [c for c in filtered if not c.get("doctor_approved")]

if sort_order == "Oldest First":
    filtered = list(reversed(filtered))

st.caption(f"{len(filtered)} consultation(s) found")
st.markdown("<br>", unsafe_allow_html=True)

# ─── Two-column layout: list + detail ────────────────────────────────────────
list_col, detail_col = st.columns([1, 1.5], gap="large")

if "selected_consult_id" not in st.session_state:
    st.session_state.selected_consult_id = None

with list_col:
    for c in filtered:
        approved = c.get("doctor_approved", False)
        badge = "✅ Approved" if approved else "⏳ Pending"
        created = c.get("created_at", "")
        if hasattr(created, "strftime"):
            created_str = created.strftime("%d %b %Y, %I:%M %p")
        else:
            created_str = str(created)[:16]

        diag = c.get("diagnosis") or "No diagnosis"
        patient = c.get("patient_name") or "Unknown"
        age = c.get("age", "?")
        med_count = len(c.get("medicines", []))

        clicked = st.button(
            f"👤  {patient}  |  {diag}  |  Age {age}  |  {med_count} med(s)\n{created_str}",
            key=f"btn_{c['_id']}",
            use_container_width=True,
        )
        if clicked:
            st.session_state.selected_consult_id = c["_id"]

with detail_col:
    if st.session_state.selected_consult_id:
        consult = get_consultation_by_id(st.session_state.selected_consult_id)
        if consult:
            st.markdown('<div class="detail-panel">', unsafe_allow_html=True)

            approved = consult.get("doctor_approved", False)
            created = consult.get("created_at", "")
            if hasattr(created, "strftime"):
                created_str = created.strftime("%d %b %Y, %I:%M %p")
            else:
                created_str = str(created)[:16]

            st.markdown(
                f"### 👤 {consult.get('patient_name', 'Unknown')}",
            )
            st.caption(f"Consultation on {created_str}")

            m1, m2, m3 = st.columns(3)
            m1.metric("Age", consult.get("age", "—"))
            m2.metric("Diagnosis", consult.get("diagnosis") or "—")
            m3.metric("Status", "✅ Approved" if approved else "⏳ Pending")

            symptoms = consult.get("symptoms", [])
            if symptoms:
                st.write("**Symptoms:**", ", ".join(symptoms))

            warnings = consult.get("safety_warnings", [])
            if warnings:
                st.warning("**Safety Warnings:** " + " | ".join(warnings))

            medicines = consult.get("medicines", [])
            if medicines:
                st.write("**Prescribed Medicines:**")
                for med in medicines:
                    status_icon = "✅" if med.get("warning") == "Validated" else "⚠️"
                    st.write(
                        f"{status_icon} **{med.get('name', '?')}** — "
                        f"{med.get('dosage', '')} · {med.get('frequency', '')} · "
                        f"for {med.get('duration', '')}"
                    )

            st.divider()
            t1, t2 = st.tabs(["📄 Medical JSON", "🏥 FHIR JSON"])
            with t1:
                st.json(consult.get("medical_json", {}))
            with t2:
                st.json(consult.get("fhir_json", {}))

            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.error("Consultation not found.")
    else:
        st.markdown(
            """
            <div style="
                text-align:center;
                padding:3rem 1rem;
                color:rgba(255,255,255,0.3);
                border: 1px dashed rgba(255,255,255,0.1);
                border-radius:16px;
            ">
                <div style="font-size:2.5rem; margin-bottom:0.75rem;">👈</div>
                <div style="font-size:0.95rem;">Select a consultation from the list<br>to view full details</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
