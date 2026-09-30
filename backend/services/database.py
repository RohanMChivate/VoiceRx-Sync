import os
import json
from pathlib import Path
from datetime import datetime, timedelta

import certifi
import pymongo
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "voicerx")

_client = None


def get_client():
    global _client
    if _client is None:
        _client = pymongo.MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=10000,
            tlsCAFile=certifi.where(),
        )
    return _client


def get_db():
    return get_client()[MONGO_DB_NAME]


def get_prescriptions_col():
    return get_db()["prescriptions"]


def get_doctors_col():
    return get_db()["doctors"]


# ────────────────────────────────────────────
# Doctor (Auth) Operations
# ────────────────────────────────────────────

def save_doctor(doctor_info: dict):
    """
    Upserts doctor record on every login.
    """
    col = get_doctors_col()
    col.update_one(
        {"email": doctor_info["email"]},
        {
            "$set": {
                "name": doctor_info.get("name"),
                "picture": doctor_info.get("picture"),
                "last_login": datetime.now(),
            },
            "$setOnInsert": {
                "email": doctor_info["email"],
                "created_at": datetime.now(),
            },
        },
        upsert=True,
    )


def get_doctor_by_email(email: str):
    return get_doctors_col().find_one({"email": email})


def update_doctor_profile(email: str, profile: dict):
    """
    Saves clinic/hospital details for a doctor.
    Fields: hospital_name, hospital_address, hospital_phone,
            hospital_city, qualification, registration_no
    These are set once in the dashboard and reused in every PDF.
    """
    col = get_doctors_col()
    col.update_one(
        {"email": email},
        {"$set": {k: v for k, v in profile.items() if k in {
            "hospital_name", "hospital_address", "hospital_phone",
            "hospital_city", "qualification", "registration_no",
        }}},
        upsert=True,
    )


# ────────────────────────────────────────────
# Prescription Operations
# ────────────────────────────────────────────

def save_prescription(data: dict, fhir_json: dict, doctor_info: dict) -> str:
    """
    Saves full prescription + FHIR JSON into MongoDB.
    Returns the inserted document ID as string.
    patient_id is stored as an encrypted token — never plaintext.
    """
    col = get_prescriptions_col()
    doc = {
        "doctor_email":  doctor_info.get("email"),
        "doctor_name":   doctor_info.get("name"),
        "patient_id":    data.get("patient_id"),    # encrypted Fernet token
        "age":           data.get("age"),
        "symptoms":      data.get("symptoms", []),
        "diagnosis":     data.get("diagnosis"),
        "medicines":     data.get("medicines", []),
        "safety_warnings": data.get("safety_warnings", []),
        "doctor_approved": data.get("doctor_approved", False),
        "medical_json":  data,
        "fhir_json":     fhir_json,
        "created_at":    datetime.now(),
    }
    result = col.insert_one(doc)
    return str(result.inserted_id)



def get_consultations_by_doctor(doctor_email: str) -> list:
    """
    Returns all prescriptions for a specific doctor, newest first.
    """
    col = get_prescriptions_col()
    docs = list(
        col.find({"doctor_email": doctor_email}).sort("created_at", pymongo.DESCENDING)
    )
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs


def get_consultation_by_id(consultation_id: str) -> dict:
    """
    Returns a single prescription document by ID.
    """
    col = get_prescriptions_col()
    doc = col.find_one({"_id": ObjectId(consultation_id)})
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


# ────────────────────────────────────────────
# Analytics
# ────────────────────────────────────────────

def get_analytics(doctor_email: str, period: str = "month") -> dict:
    """
    Returns analytics data for a doctor.
    period: 'today' | 'week' | 'month' | 'year' | 'all'
    """
    col = get_prescriptions_col()

    now = datetime.now()
    period_starts = {
        "today": now.replace(hour=0, minute=0, second=0, microsecond=0),
        "week": now - timedelta(days=7),
        "month": now - timedelta(days=30),
        "year": now - timedelta(days=365),
        "all": datetime(2000, 1, 1),
    }
    start_date = period_starts.get(period, period_starts["month"])

    base_match = {"doctor_email": doctor_email}
    period_match = {"doctor_email": doctor_email, "created_at": {"$gte": start_date}}

    total_all = col.count_documents(base_match)
    total_period = col.count_documents(period_match)

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = col.count_documents(
        {"doctor_email": doctor_email, "created_at": {"$gte": today_start}}
    )

    approved_count = col.count_documents(
        {**period_match, "doctor_approved": True}
    )
    approval_rate = (
        round((approved_count / total_period) * 100, 1) if total_period > 0 else 0
    )

    # Top medicines
    top_meds = list(
        col.aggregate([
            {"$match": period_match},
            {"$unwind": "$medicines"},
            {"$group": {"_id": "$medicines.name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 8},
        ])
    )

    # Diagnosis distribution
    diag_dist = list(
        col.aggregate([
            {"$match": {**period_match, "diagnosis": {"$nin": [None, ""]}}},
            {"$group": {"_id": "$diagnosis", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ])
    )

    # Timeline — group by day
    timeline = list(
        col.aggregate([
            {"$match": period_match},
            {
                "$group": {
                    "_id": {
                        "y": {"$year": "$created_at"},
                        "m": {"$month": "$created_at"},
                        "d": {"$dayOfMonth": "$created_at"},
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id.y": 1, "_id.m": 1, "_id.d": 1}},
        ])
    )
    timeline_formatted = [
        {
            "date": f"{e['_id']['y']}-{e['_id']['m']:02d}-{e['_id']['d']:02d}",
            "count": e["count"],
        }
        for e in timeline
    ]

    most_prescribed = top_meds[0]["_id"] if top_meds else "—"

    return {
        "total_all": total_all,
        "total_period": total_period,
        "today_count": today_count,
        "approval_rate": approval_rate,
        "most_prescribed": most_prescribed,
        "top_medicines": top_meds,
        "diagnosis_distribution": diag_dist,
        "timeline": timeline_formatted,
    }


# ────────────────────────────────────────────
# Legacy shim — keeps old import in app.py working
# during transition (will be removed)
# ────────────────────────────────────────────

def create_tables():
    """No-op: kept for backwards compatibility, not needed with MongoDB."""
    pass


def get_all_prescriptions():
    """Legacy: returns empty list (SQLite removed)."""
    return []