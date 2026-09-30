import os
import sys
import requests
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from jose import jwt
from pydantic import BaseModel
from dotenv import load_dotenv

# Ensure backend root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.database import save_doctor, get_doctor_by_email, update_doctor_profile

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

router = APIRouter()

FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "")
JWT_SECRET       = os.getenv("JWT_SECRET", "voicerx-super-secret-key")
JWT_ALGORITHM    = "HS256"
JWT_EXPIRE_HOURS = 72


class TokenRequest(BaseModel):
    id_token: str


def _verify_firebase_token(id_token: str) -> dict:
    if not FIREBASE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="FIREBASE_API_KEY is not configured in backend environment variables."
        )
    url  = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_API_KEY}"
    resp = requests.post(url, json={"idToken": id_token}, timeout=10)
    data = resp.json()
    if "error" in data:
        raise HTTPException(status_code=401, detail=data.get("error", {}).get("message", "Invalid Firebase token"))
    users = data.get("users", [])
    if not users:
        raise HTTPException(status_code=401, detail="User not found")
    return users[0]


def _create_jwt(doctor: dict) -> str:
    payload = {
        "email":   doctor["email"],
        "name":    doctor["name"],
        "picture": doctor["picture"],
        "exp":     datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.post("/verify")
def verify_token(body: TokenRequest):
    firebase_user = _verify_firebase_token(body.id_token)
    doctor = {
        "email":   firebase_user.get("email", ""),
        "name":    firebase_user.get("displayName", "Doctor"),
        "picture": firebase_user.get("photoUrl", ""),
    }
    save_doctor(doctor)
    return {"token": _create_jwt(doctor), "doctor": doctor}


# ── Doctor clinic profile ─────────────────────────────────────────────────────

from fastapi import Header

class ProfileRequest(BaseModel):
    hospital_name:    str = ""
    hospital_address: str = ""
    hospital_phone:   str = ""
    hospital_city:    str = ""
    qualification:    str = ""
    registration_no:  str = ""


def _email_from_header(authorization: str = Header(...)) -> str:
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_jwt(token)
    return payload["email"]


@router.get("/profile")
def get_profile(authorization: str = Header(...)):
    email = _email_from_header(authorization)
    doc = get_doctor_by_email(email) or {}
    return {
        "hospital_name":    doc.get("hospital_name", ""),
        "hospital_address": doc.get("hospital_address", ""),
        "hospital_phone":   doc.get("hospital_phone", ""),
        "hospital_city":    doc.get("hospital_city", ""),
        "qualification":    doc.get("qualification", ""),
        "registration_no":  doc.get("registration_no", ""),
    }


@router.put("/profile")
def update_profile(body: ProfileRequest, authorization: str = Header(...)):
    email = _email_from_header(authorization)
    update_doctor_profile(email, body.model_dump())
    return {"status": "ok"}
