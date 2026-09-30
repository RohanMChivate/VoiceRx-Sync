from datetime import datetime

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from auth import logout
from database import get_analytics, get_consultations_by_doctor

# ─── Auth guard ──────────────────────────────────────────────────────────────
doctor = st.session_state.get("doctor", {})

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp { background: #0f172a; }

    .dash-header {
        background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.1));
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 20px;
        padding: 1.5rem 2rem;
        display: flex;
        align-items: center;
        gap: 1.25rem;
        margin-bottom: 1.5rem;
    }
    .doc-avatar {
        width: 56px; height: 56px;
        border-radius: 50%;
        border: 2px solid rgba(99,102,241,0.6);
        object-fit: cover;
    }
    .doc-name { color: #e2e8f0; font-size: 1.3rem; font-weight: 700; margin: 0; }
    .doc-email { color: rgba(255,255,255,0.45); font-size: 0.82rem; margin: 0; }

    .kpi-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        text-align: center;
    }
    .kpi-icon { font-size: 1.8rem; margin-bottom: 0.25rem; }
    .kpi-value { color: #e2e8f0; font-size: 2rem; font-weight: 700; line-height: 1.1; }
    .kpi-label { color: rgba(255,255,255,0.45); font-size: 0.78rem; margin-top: 0.25rem; }

    .section-title {
        color: #a5b4fc;
        font-size: 1rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin: 1.5rem 0 0.75rem;
    }

    .consult-row {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 12px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: background 0.2s;
    }
    .consult-row:hover { background: rgba(99,102,241,0.12); }
    .consult-name { color: #e2e8f0; font-weight: 600; font-size: 0.95rem; }
    .consult-meta { color: rgba(255,255,255,0.4); font-size: 0.78rem; }
    .badge-approved {
        background: rgba(34,197,94,0.15);
        color: #86efac;
        border: 1px solid rgba(34,197,94,0.3);
        border-radius: 20px; padding: 0.2rem 0.6rem;
        font-size: 0.72rem; font-weight: 600;
    }
    .badge-pending {
        background: rgba(251,191,36,0.15);
        color: #fde68a;
        border: 1px solid rgba(251,191,36,0.3);
        border-radius: 20px; padding: 0.2rem 0.6rem;
        font-size: 0.72rem; font-weight: 600;
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
            <img src="{doctor.get('picture', '')}" class="doc-avatar"
                 style="width:64px;height:64px;border-radius:50%;margin-bottom:0.5rem;">
            <div style="color:#e2e8f0;font-weight:700;">{doctor.get('name','Doctor')}</div>
            <div style="color:rgba(255,255,255,0.4);font-size:0.78rem;">{doctor.get('email','')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    st.page_link("pages/1_Dashboard.py",       label="📊  Dashboard",         )
    st.page_link("pages/2_New_Consultation.py", label="🎙️  New Consultation",  )
    st.page_link("pages/3_All_Consultations.py",label="📋  All Consultations", )
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        logout()
        st.rerun()

# ─── Header ──────────────────────────────────────────────────────────────────
pic = doctor.get("picture", "")
name = doctor.get("name", "Doctor")
email = doctor.get("email", "")

st.markdown(
    f"""
    <div class="dash-header">
        <img src="{pic}" class="doc-avatar">
        <div>
            <p class="doc-name">Welcome back, {name.split()[0]} 👋</p>
            <p class="doc-email">{email}</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─── Period filter ────────────────────────────────────────────────────────────
col_f1, col_f2, col_f3 = st.columns([3, 1, 1])
with col_f1:
    st.markdown('<p class="section-title">Analytics Overview</p>', unsafe_allow_html=True)
with col_f2:
    period = st.selectbox(
        "Period",
        options=["today", "week", "month", "year", "all"],
        index=2,
        format_func=lambda x: {
            "today": "Today",
            "week": "Last 7 Days",
            "month": "Last 30 Days",
            "year": "Last Year",
            "all": "All Time",
        }[x],
        label_visibility="collapsed",
    )

# ─── Fetch data ───────────────────────────────────────────────────────────────
with st.spinner("Loading analytics…"):
    analytics = get_analytics(email, period)
    consultations = get_consultations_by_doctor(email)

# ─── KPI cards ───────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(
        f"""<div class="kpi-card">
            <div class="kpi-icon">📋</div>
            <div class="kpi-value">{analytics['total_all']}</div>
            <div class="kpi-label">Total Consultations</div>
        </div>""",
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        f"""<div class="kpi-card">
            <div class="kpi-icon">📅</div>
            <div class="kpi-value">{analytics['today_count']}</div>
            <div class="kpi-label">Today's Consultations</div>
        </div>""",
        unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        f"""<div class="kpi-card">
            <div class="kpi-icon">✅</div>
            <div class="kpi-value">{analytics['approval_rate']}%</div>
            <div class="kpi-label">Approval Rate</div>
        </div>""",
        unsafe_allow_html=True,
    )
with k4:
    st.markdown(
        f"""<div class="kpi-card">
            <div class="kpi-icon">💊</div>
            <div class="kpi-value" style="font-size:1.1rem;padding-top:0.4rem;">
                {analytics['most_prescribed']}
            </div>
            <div class="kpi-label">Most Prescribed</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ─── Charts ──────────────────────────────────────────────────────────────────
chart_left, chart_right = st.columns([2, 1])

CHART_BG = "rgba(0,0,0,0)"
GRID_COLOR = "rgba(255,255,255,0.07)"
TEXT_COLOR = "rgba(255,255,255,0.6)"

with chart_left:
    st.markdown('<p class="section-title">Consultations Over Time</p>', unsafe_allow_html=True)
    timeline = analytics.get("timeline", [])
    if timeline:
        dates = [t["date"] for t in timeline]
        counts = [t["count"] for t in timeline]
        fig_line = go.Figure(
            go.Scatter(
                x=dates,
                y=counts,
                mode="lines+markers",
                line=dict(color="#6366f1", width=2.5),
                marker=dict(color="#8b5cf6", size=7),
                fill="tozeroy",
                fillcolor="rgba(99,102,241,0.1)",
            )
        )
        fig_line.update_layout(
            paper_bgcolor=CHART_BG,
            plot_bgcolor=CHART_BG,
            font=dict(color=TEXT_COLOR, family="Inter"),
            xaxis=dict(gridcolor=GRID_COLOR, showgrid=True, zeroline=False),
            yaxis=dict(gridcolor=GRID_COLOR, showgrid=True, zeroline=False, tickformat="d"),
            margin=dict(l=0, r=0, t=10, b=0),
            height=260,
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No consultation data for this period yet.")

with chart_right:
    st.markdown('<p class="section-title">Diagnosis Split</p>', unsafe_allow_html=True)
    diag = analytics.get("diagnosis_distribution", [])
    if diag:
        fig_pie = go.Figure(
            go.Pie(
                labels=[d["_id"] for d in diag],
                values=[d["count"] for d in diag],
                hole=0.55,
                marker=dict(
                    colors=px.colors.sequential.Plasma,
                    line=dict(color="rgba(0,0,0,0)", width=0),
                ),
                textfont=dict(color="white"),
            )
        )
        fig_pie.update_layout(
            paper_bgcolor=CHART_BG,
            font=dict(color=TEXT_COLOR, family="Inter"),
            showlegend=True,
            legend=dict(font=dict(color=TEXT_COLOR, size=11)),
            margin=dict(l=0, r=0, t=10, b=0),
            height=260,
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No diagnosis data yet.")

# ─── Top Medicines bar chart ──────────────────────────────────────────────────
st.markdown('<p class="section-title">Top Prescribed Medicines</p>', unsafe_allow_html=True)
top_meds = analytics.get("top_medicines", [])
if top_meds:
    med_names = [m["_id"] for m in top_meds]
    med_counts = [m["count"] for m in top_meds]
    fig_bar = go.Figure(
        go.Bar(
            x=med_counts,
            y=med_names,
            orientation="h",
            marker=dict(
                color=med_counts,
                colorscale="Viridis",
                line=dict(width=0),
            ),
            text=med_counts,
            textposition="outside",
            textfont=dict(color="rgba(255,255,255,0.7)"),
        )
    )
    fig_bar.update_layout(
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(color=TEXT_COLOR, family="Inter"),
        xaxis=dict(gridcolor=GRID_COLOR, showgrid=True, zeroline=False, tickformat="d"),
        yaxis=dict(gridcolor=GRID_COLOR, showgrid=False, zeroline=False, autorange="reversed"),
        margin=dict(l=0, r=40, t=10, b=0),
        height=260,
    )
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.info("No medicine data for this period.")

# ─── Recent consultations ─────────────────────────────────────────────────────
st.markdown('<p class="section-title">Recent Consultations</p>', unsafe_allow_html=True)

recent = consultations[:10]

if not recent:
    st.info("No consultations yet. Start your first one →")
else:
    for c in recent:
        approved = c.get("doctor_approved", False)
        badge = (
            '<span class="badge-approved">✅ Approved</span>'
            if approved
            else '<span class="badge-pending">⏳ Pending</span>'
        )
        created = c.get("created_at", "")
        if hasattr(created, "strftime"):
            created = created.strftime("%d %b %Y, %I:%M %p")

        with st.expander(
            f"👤 {c.get('patient_name', 'Unknown')}  •  {c.get('diagnosis') or 'No diagnosis'}  •  {created}",
            expanded=False,
        ):
            dc1, dc2, dc3 = st.columns(3)
            dc1.metric("Patient", c.get("patient_name", "—"))
            dc2.metric("Age", c.get("age", "—"))
            dc3.metric("Diagnosis", c.get("diagnosis") or "—")

            symptoms = c.get("symptoms", [])
            if symptoms:
                st.write("**Symptoms:**", ", ".join(symptoms))

            meds = c.get("medicines", [])
            if meds:
                st.write("**Medicines:**")
                for m in meds:
                    st.write(
                        f"- **{m.get('name','?')}** — {m.get('dosage','')} "
                        f"{m.get('frequency','')} for {m.get('duration','')}"
                    )

            t1, t2 = st.tabs(["📄 Medical JSON", "🏥 FHIR JSON"])
            with t1:
                st.json(c.get("medical_json", {}))
            with t2:
                st.json(c.get("fhir_json", {}))
