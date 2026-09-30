import streamlit as st
from auth import (
    is_authenticated,
    get_google_auth_url,
    handle_oauth_callback,
    logout,
)

# ─── Page config (ONLY called here — not in any page file) ───────────────────
st.set_page_config(
    page_title="VoiceRx Sync",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Handle OAuth callback before anything else ───────────────────────────────
code = st.query_params.get("code")
if code:
    with st.spinner("Signing you in…"):
        ok, err_msg = handle_oauth_callback(code)
    if ok:
        st.rerun()          # Re-run so navigation switches to authenticated view
    else:
        st.error(f"❌ Authentication failed: {err_msg}")
        st.info(
            "Make sure `http://localhost:8501` is added as an "
            "**Authorized Redirect URI** in Google Cloud Console → "
            "Credentials → your OAuth client."
        )


# ─── Login page UI (shown when not authenticated) ────────────────────────────
def login_page():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
            min-height: 100vh;
        }
        [data-testid="stSidebarNav"],
        section[data-testid="stSidebar"] { display: none !important; }

        .logo-ring {
            width: 90px; height: 90px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 2.5rem;
            margin: 0 auto 1.5rem;
            box-shadow: 0 0 40px rgba(99,102,241,0.5);
            animation: pulse 3s infinite;
        }
        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 40px rgba(99,102,241,0.5); }
            50%       { box-shadow: 0 0 70px rgba(139,92,246,0.8); }
        }
        .login-card {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 24px;
            padding: 2.5rem 2rem;
            max-width: 440px;
            width: 100%;
            margin: 3rem auto;
            text-align: center;
        }
        .brand-title {
            font-size: 2rem; font-weight: 700;
            background: linear-gradient(135deg, #a5b4fc, #c4b5fd);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.25rem;
        }
        .brand-subtitle {
            color: rgba(255,255,255,0.55);
            font-size: 0.95rem;
            margin-bottom: 2rem;
        }
        .feature-row {
            display: flex; gap: 0.75rem;
            margin-bottom: 2rem;
            justify-content: center; flex-wrap: wrap;
        }
        .feature-chip {
            background: rgba(99,102,241,0.15);
            border: 1px solid rgba(99,102,241,0.3);
            color: #a5b4fc;
            border-radius: 20px;
            padding: 0.35rem 0.85rem;
            font-size: 0.78rem; font-weight: 500;
        }
        .footer-note {
            color: rgba(255,255,255,0.3);
            font-size: 0.75rem; margin-top: 1.5rem;
        }
        .stLinkButton a {
            background: white !important;
            color: #1f2937 !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            width: 100% !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
        }
        .stLinkButton a:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px rgba(0,0,0,0.4) !important;
        }
        .setup-warning {
            background: rgba(239,68,68,0.1);
            border: 1px solid rgba(239,68,68,0.3);
            border-radius: 12px; padding: 1rem;
            color: #fca5a5; font-size: 0.85rem;
            text-align: left; margin-top: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown('<div class="logo-ring">🩺</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-title">VoiceRx Sync</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="brand-subtitle">AI-powered clinical documentation for doctors</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="feature-row">
            <span class="feature-chip">🎙️ Voice → Rx</span>
            <span class="feature-chip">🏥 FHIR Ready</span>
            <span class="feature-chip">📊 Analytics</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    auth_url = get_google_auth_url()

    if auth_url:
        st.link_button("🔵  Sign in with Google", auth_url, use_container_width=True)
        st.markdown(
            '<p class="footer-note">Sign in with your Google account.<br>'
            "Your data is stored securely in MongoDB.</p>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="setup-warning">
                ⚠️ <strong>Setup Required</strong><br><br>
                Add <code>GOOGLE_CLIENT_SECRET</code> to your <code>.env</code> file.<br>
                Get it from Google Cloud Console → Credentials → your OAuth client.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ─── Register navigation based on auth state ─────────────────────────────────
if is_authenticated():
    pg = st.navigation(
        {
            "": [
                st.Page("pages/1_Dashboard.py",        title="Dashboard",        icon="📊", default=True),
                st.Page("pages/2_New_Consultation.py", title="New Consultation", icon="🎙️"),
                st.Page("pages/3_All_Consultations.py",title="All Consultations",icon="📋"),
            ]
        },
        position="hidden",   # We use custom sidebars inside each page
    )
else:
    pg = st.navigation(
        [st.Page(login_page, title="Login", icon="🔑")],
        position="hidden",
    )

pg.run()