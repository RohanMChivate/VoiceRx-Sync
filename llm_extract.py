import os
import json
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


SYSTEM_PROMPT = """
You are a medical data extraction assistant.

Convert the doctor's English transcript into valid JSON.

Return exactly this JSON structure:
{
  "patient_name": string or null,
  "age": number or null,
  "symptoms": [string],
  "diagnosis": string or null,
  "medicines": [
    {
      "name": string,
      "dosage": string,
      "frequency": string,
      "duration": string
    }
  ],
  "advice": string or null
}

Rules:
- The input transcript will be in English only.
- Output only valid JSON.
- Do not write explanations.
- Do not include markdown.
- Do not include extra keys outside the required JSON structure.
- Use common generic medicine names when possible.
- Keep medicine names in English.
- Keep symptoms and diagnosis in English.
- If patient name is missing, use null.
- If age is missing, use null.
- If symptoms are missing, use an empty list.
- If diagnosis is unclear, use null.
- If no medicines are found, use an empty list.
- If dosage, frequency, or duration is missing for a medicine, use null for that field.
"""


def get_api_key():
    """
    Reads Groq API key from .env locally or Streamlit secrets during deployment.
    """
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        try:
            api_key = st.secrets["GROQ_API_KEY"]
        except Exception:
            api_key = None

    if not api_key:
        raise ValueError("GROQ_API_KEY not found. Add it to .env or Streamlit secrets.")

    return api_key


def get_groq_client():
    """
    Creates and returns Groq client.
    """
    return Groq(api_key=get_api_key())


def extract_medical_json(transcript: str) -> dict:
    """
    Converts an English doctor transcript into structured prescription JSON.
    """
    if not transcript or not transcript.strip():
        return {
            "patient_name": None,
            "age": None,
            "symptoms": [],
            "diagnosis": None,
            "medicines": [],
            "advice": None
        }

    client = get_groq_client()

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": transcript,
            },
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "patient_name": None,
            "age": None,
            "symptoms": [],
            "diagnosis": None,
            "medicines": [],
            "advice": None
        }