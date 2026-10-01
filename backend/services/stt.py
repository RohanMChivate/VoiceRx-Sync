import os
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# Medical vocabulary hint fed to Whisper to bias it toward
# clinical terms, dosage units, and drug names.
_WHISPER_PROMPT = (
    "Doctor's consultation note. Medical terminology: patient name, age, symptoms, "
    "diagnosis, prescription, medicines, dosage mg, frequency twice daily, "
    "once daily, three times a day, duration days, weeks, advice rest, follow up."
)


def get_api_key() -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment.")
    return api_key


def get_groq_client() -> Groq:
    return Groq(api_key=get_api_key())


def save_audio_file(audio_bytes: bytes, filename: str = "recording.webm") -> str:
    """Saves raw audio bytes to temp folder, returns path."""
    import tempfile
    temp_dir = os.path.join(tempfile.gettempdir(), "voicerx")
    os.makedirs(temp_dir, exist_ok=True)
    path = os.path.join(temp_dir, filename)
    with open(path, "wb") as f:
        f.write(audio_bytes)
    return path


def transcribe_audio(audio_path: str) -> str:
    """Sends audio to Groq Whisper and returns transcript text."""
    client = get_groq_client()
    with open(audio_path, "rb") as f:
        audio_data = f.read()

    # Determine MIME type from extension for correct API handling
    ext = os.path.splitext(audio_path)[1].lower()
    mime_map = {
        ".webm": "audio/webm",
        ".wav":  "audio/wav",
        ".mp3":  "audio/mpeg",
        ".ogg":  "audio/ogg",
        ".m4a":  "audio/mp4",
    }
    mime_type = mime_map.get(ext, "audio/webm")
    filename  = os.path.basename(audio_path)

    model = os.getenv("GROQ_STT_MODEL", "whisper-large-v3")
    result = client.audio.transcriptions.create(
        file=(filename, audio_data, mime_type),
        model=model,
        language="en",          # pin language — prevents mis-detection
        prompt=_WHISPER_PROMPT, # primes Whisper on medical vocab
        response_format="text", # simplest accurate format
    )
    # Groq returns a string when response_format="text"
    return result if isinstance(result, str) else result.text