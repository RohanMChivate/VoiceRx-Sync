import os
import json
import secrets
import hashlib
import base64
import requests
import streamlit as st
from google_auth_oauthlib.flow import Flow
from dotenv import load_dotenv
from database import save_doctor

load_dotenv()

# Allow OAuth over plain HTTP on localhost (dev only — remove for production HTTPS)
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501")

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

# Temp file to persist PKCE verifiers across the Google redirect
_VERIFIER_FILE = os.path.join("temp", "oauth_verifiers.json")


# ── PKCE helpers ─────────────────────────────────────────────────────────────

def _generate_pkce_pair() -> tuple[str, str]:
    """Returns (code_verifier, code_challenge) for S256 PKCE."""
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


def _store_verifier(state: str, code_verifier: str) -> None:
    """Persist the verifier keyed by OAuth state to a local file."""
    os.makedirs("temp", exist_ok=True)
    cache: dict = {}
    if os.path.exists(_VERIFIER_FILE):
        try:
            with open(_VERIFIER_FILE) as f:
                cache = json.load(f)
        except Exception:
            cache = {}
    cache[state] = code_verifier
    with open(_VERIFIER_FILE, "w") as f:
        json.dump(cache, f)


def _get_verifier(state: str) -> str:
    """Retrieve the verifier for a given OAuth state."""
    if not os.path.exists(_VERIFIER_FILE):
        return ""
    try:
        with open(_VERIFIER_FILE) as f:
            cache = json.load(f)
        return cache.get(state, "")
    except Exception:
        return ""


# ── OAuth flow ────────────────────────────────────────────────────────────────

def _is_configured() -> bool:
    return bool(
        GOOGLE_CLIENT_ID
        and GOOGLE_CLIENT_SECRET
        and GOOGLE_CLIENT_SECRET not in ("YOUR_GOOGLE_CLIENT_SECRET_HERE", "")
    )


def get_google_flow() -> Flow:
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [GOOGLE_REDIRECT_URI],
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )


def get_google_auth_url() -> str | None:
    """Generate the Google consent URL with PKCE challenge (S256)."""
    if not _is_configured():
        return None

    flow = get_google_flow()
    code_verifier, code_challenge = _generate_pkce_pair()

    auth_url, state = flow.authorization_url(
        prompt="consent",
        access_type="offline",
        code_challenge=code_challenge,
        code_challenge_method="S256",
    )

    # Persist verifier so we can retrieve it after Google's redirect
    _store_verifier(state, code_verifier)
    return auth_url


def handle_oauth_callback(code: str) -> tuple[bool, str]:
    """
    Exchange the OAuth code (+ PKCE verifier) for tokens,
    fetch the Google profile, save to MongoDB, store in session.
    Returns (True, "") on success or (False, error_message) on failure.
    """
    if not _is_configured():
        return False, "Google OAuth is not configured — add GOOGLE_CLIENT_SECRET to .env"

    try:
        state = st.query_params.get("state", "")
        code_verifier = _get_verifier(state)

        flow = get_google_flow()
        # Pass code_verifier so Google accepts the token exchange
        flow.fetch_token(code=code, code_verifier=code_verifier)
        credentials = flow.credentials

        resp = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"},
            timeout=10,
        )
        resp.raise_for_status()
        info = resp.json()

        doctor = {
            "email": info.get("email", ""),
            "name": info.get("name", "Doctor"),
            "picture": info.get("picture", ""),
        }

        save_doctor(doctor)
        st.session_state["doctor"] = doctor
        st.query_params.clear()
        return True, ""

    except Exception as e:
        st.session_state.pop("doctor", None)
        return False, str(e)


# ── Session helpers ───────────────────────────────────────────────────────────

def is_authenticated() -> bool:
    return bool(st.session_state.get("doctor"))


def require_login():
    """Guard: call at top of every protected page."""
    if not is_authenticated():
        st.set_page_config(page_title="VoiceRx Sync", page_icon="🩺")
        st.warning("🔒 You must be logged in to view this page.")
        if st.button("Go to Login →", type="primary"):
            st.switch_page("app.py")
        st.stop()
    return st.session_state["doctor"]


def logout():
    st.session_state.pop("doctor", None)
