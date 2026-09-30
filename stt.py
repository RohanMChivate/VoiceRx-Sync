import os
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def get_api_key():
    """
    Reads Groq API key.

    Locally:
    - Reads from .env

    On Streamlit Cloud:
    - Reads from Streamlit secrets
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
    Creates Groq client.
    """
    return Groq(api_key=get_api_key())


def save_audio_file(audio_file) -> str:
    """
    Saves Streamlit recorded audio to temp folder.
    """
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)

    file_path = os.path.join(temp_dir, "doctor_recording.wav")

    with open(file_path, "wb") as f:
        f.write(audio_file.getbuffer())

    return file_path


def transcribe_audio(audio_path: str) -> str:
    """
    Sends audio file to Groq Whisper and returns text.
    """
    client = get_groq_client()

    with open(audio_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(audio_path, file.read()),
            model="whisper-large-v3",
            temperature=0,  
            response_format="verbose_json",
        )

    return transcription.text
