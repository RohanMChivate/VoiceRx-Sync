import os
import sys
import json
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from bson import ObjectId
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.stt import save_audio_file, transcribe_audio
from services.llm_extract import extract_medical_json
from services.validator import validate_medicines
from services.pid_extractor import extract_patient_id_from_transcript
from services.encryption import encrypt_patient_id
from services.fhir_builder import build_fhir_prescription
from services.pdf_generator import create_prescription_pdf
from services.database import (
    save_prescription, get_consultations_by_doctor,
    get_consultation_by_id, get_doctor_by_email,
)

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
router = APIRouter()


def _serial(obj):
    if isinstance(obj, ObjectId): return str(obj)
    if isinstance(obj, datetime):  return obj.isoformat()
    raise TypeError(f"Not serialisable: {type(obj)}")

def _jsonify(data):
    return json.loads(json.dumps(data, default=_serial))


class SaveRequest(BaseModel):
    model_config = {"extra": "ignore"}   # silently ignore any extra fields from frontend
    patient_id:      Optional[str] = None   # encrypted token, never plaintext
    age:             Optional[int] = None
    diagnosis:       Optional[str] = None
    symptoms:        list[str]          = []
    medicines:       list[dict]         = []
    safety_warnings: list[str]          = []
    advice:          Optional[str]      = None
    doctor_approved: bool               = False
    doctor_email:    str
    doctor_name:     str
    doctor_picture:  Optional[str]      = ""


@router.post("/process-audio")
async def process_audio(
    file: UploadFile = File(...),
):
    # ── 1. Save audio & transcribe ────────────────────────────────────────────
    audio_bytes = await file.read()
    audio_path  = save_audio_file(audio_bytes, file.filename or "recording.webm")

    try:
        # ── 2. STT — get the full transcript ─────────────────────────────────
        transcript = transcribe_audio(audio_path)

        # ── 3. Extract patient ID from transcript BEFORE passing to LLM ──────
        raw_pid = extract_patient_id_from_transcript(transcript)
        if not raw_pid:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Patient ID not found in recording. "
                    "Please re-record and say the patient ID clearly, e.g. "
                    "'Patient ID P1234' or 'PID 00421'."
                ),
            )

        # ── 4. Encrypt immediately — LLM never sees the plain ID ──────────────
        encrypted_pid = encrypt_patient_id(raw_pid)

        # ── 5. LLM extraction (transcript passed as-is; LLM ignores patient ID) ─
        extracted_json = extract_medical_json(transcript)

        # ── 6. Inject encrypted patient_id ────────────────────────────────────
        extracted_json["patient_id"] = encrypted_pid

        # ── 7. Validate medicines ─────────────────────────────────────────────
        validated_json = validate_medicines(extracted_json)

        return {"transcript": transcript, "prescription": validated_json}

    finally:
        try: os.remove(audio_path)
        except: pass


@router.post("/save")
def save_consultation(body: SaveRequest):
    import logging, traceback
    log = logging.getLogger(__name__)
    try:
        data = {
            "patient_id":      body.patient_id,
            "age":             body.age,
            "diagnosis":       body.diagnosis,
            "symptoms":        body.symptoms,
            "medicines":       body.medicines,
            "safety_warnings": body.safety_warnings,
            "advice":          body.advice,
            "doctor_approved": body.doctor_approved,
        }
        doctor = {
            "email":   body.doctor_email,
            "name":    body.doctor_name,
            "picture": body.doctor_picture,
        }
        fhir_json = build_fhir_prescription(data)

        # Fetch doctor's clinic profile (set once in dashboard)
        doctor_profile = get_doctor_by_email(body.doctor_email) or {}

        # Use absolute path so PDF never fails due to CWD mismatch
        pdf_dir  = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = os.path.join(pdf_dir, "digital_prescription.pdf")
        create_prescription_pdf(data, doctor=doctor_profile, doctor_info=doctor, filename=pdf_path)
        doc_id = save_prescription(data, fhir_json, doctor)
        return {"id": doc_id, "fhir_json": fhir_json}
    except Exception as exc:
        log.error("save_consultation failed: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("")
def list_consultations(doctor_email: str = Query(...)):
    docs = get_consultations_by_doctor(doctor_email)
    return _jsonify(docs)


@router.get("/{consultation_id}")
def get_consultation(consultation_id: str):
    doc = get_consultation_by_id(consultation_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Consultation not found")
    return _jsonify(doc)


@router.get("/{consultation_id}/pdf")
def download_pdf(consultation_id: str):
    doc = get_consultation_by_id(consultation_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Consultation not found")
    pdf_path = create_prescription_pdf(doc.get("medical_json", {}))
    return FileResponse(pdf_path, media_type="application/pdf",
                        filename=f"prescription_{consultation_id}.pdf")
