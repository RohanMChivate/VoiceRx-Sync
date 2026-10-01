# 🎙️ VoiceRx Sync

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge)
![Next.js](https://img.shields.io/badge/Next.js%2015-black?style=for-the-badge&logo=next.js&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Groq](https://img.shields.io/badge/Groq%20Cloud-F05A28?style=for-the-badge)
![MongoDB](https://img.shields.io/badge/MongoDB%20Atlas-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![Firebase](https://img.shields.io/badge/Firebase%20Auth-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)

<p align="center">
  <strong>AI-Powered Clinical Voice Prescription & EHR Synchronization Platform</strong>
  <br />
  Transforms clinical voice consultations into structured, validated medical prescriptions and compliant EHR records in real time.
</p>

[Live Web App](https://voice-rx-sync.vercel.app) • [API Health](https://voicerx-sync.onrender.com/api/health) • [API Documentation](https://voicerx-sync.onrender.com/docs)

</div>

---

## ⚡ Overview

**VoiceRx Sync** automates medical documentation for healthcare practitioners. By recording doctor dictations and patient consultations directly in the browser, VoiceRx eliminates manual data entry, validates dosages and drug regimens, encrypts sensitive Patient Health Information (PHI), and compiles clinical-grade prescription PDFs ready for print or digital distribution.

---

## ✨ Key Features

- 🎙️ **Direct Audio Capture**: Browser-native recording via the MediaRecorder API with zero client-side file truncation or timeout limits.
- ⚡ **Ultra-Fast Clinical STT**: Real-time voice transcription powered by Groq-accelerated **Whisper Large v3**.
- 🧠 **Structured Clinical Entity Extraction**: Converts unstructured speech into normalized JSON schemas (patient demographics, diagnosis, symptoms, structured medications, dosages, intervals, and durations) using high-speed reasoning models.
- 🛡️ **Zero-Trust PHI Cryptography**: End-to-end field-level Fernet symmetric encryption on patient identifiable data before writing to MongoDB.
- 📄 **Dynamic Prescription PDF Generation**: Direct-to-PDF compilation via ReportLab containing clinical disclaimers, doctor signatures, and digital verification.
- 📊 **Synchronized EHR Records**: Searchable consultation history and analytics backed by MongoDB Atlas.

---

## 🏗️ Architecture

```
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│        Vercel (Frontend)        │       │         Render (Backend)        │
│       Next.js 15 + React        │──────▶│         FastAPI + Python        │
│   [https://voicerx-sync.vercel.app](https://voicerx-sync.vercel.app)│ CORS │ [https://voicerx-sync.onrender.com](https://voicerx-sync.onrender.com)│
└────────────────┬────────────────┘       └────────┬───────────────┬────────┘
                 │                                 │               │
                 ▼                                 ▼               ▼
      ┌─────────────────────┐             ┌──────────────────┐ ┌───────────────┐
      │    Firebase Auth    │             │  MongoDB Atlas   │ │    Groq AI    │
      │  (Google Sign-In)   │             │   (Database M0)  │ │ (Whisper+LLM) │
      └─────────────────────┘             └──────────────────┘ └───────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Next.js (App Router), React, Tailwind CSS, Lucide Icons, Firebase Auth SDK |
| **Backend** | Python 3, FastAPI, Uvicorn, Pydantic v2, Cryptography (Fernet), ReportLab |
| **AI / Machine Learning** | Groq Cloud API, `whisper-large-v3` (STT), `openai/gpt-oss-20b` (Entity Extraction) |
| **Database** | MongoDB Atlas (Motor async driver / PyMongo) |
| **Deployment & Hosting** | Vercel (Frontend Edge), Render (Containerized Backend Web Service) |

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.10+
- MongoDB Atlas Account & Database Cluster
- Groq Cloud Account & API Key
- Firebase Project with Google Sign-In enabled

---

### 1. Clone the Repository

```bash
git clone [https://github.com/your-username/VoiceRx-Sync.git](https://github.com/your-username/VoiceRx-Sync.git)
cd VoiceRx-Sync
```

---

### 2. Backend Setup (FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

Configure `backend/.env`:

```ini
PORT=8000
MONGO_URI=mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/voicerx?appName=Cluster0
MONGO_DB_NAME=voicerx
GROQ_API_KEY=gsk_your_groq_api_key
GROQ_LLM_MODEL=openai/gpt-oss-20b
GROQ_STT_MODEL=whisper-large-v3
JWT_SECRET=your_generated_32_byte_hex_secret
PATIENT_ENCRYPT_KEY=your_generated_fernet_key
FIREBASE_API_KEY=your_firebase_web_api_key
```

Generate cryptographic keys:
```bash
# Generate JWT_SECRET
openssl rand -hex 32

# Generate PATIENT_ENCRYPT_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Start the backend server:

```bash
uvicorn main:app --reload --port 8000
```

---

### 3. Frontend Setup (Next.js)

```bash
cd ../frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local
```

Configure `frontend/.env.local`:

```ini
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSy...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=1234567890
NEXT_PUBLIC_FIREBASE_APP_ID=1:1234567890:web:abcdef
```

Start the frontend development server:

```bash
npm run dev
```

Visit `http://localhost:3000` in your browser.

---

## 🔒 Security & Data Privacy

- **Field-Level Encryption**: All sensitive patient data (name, identification, contact) is encrypted using AES-128-CBC with SHA256 HMAC (Fernet specification) prior to insertion into MongoDB Atlas.
- **In-Memory Audio Processing**: Voice streams are handled entirely in memory buffers without leaving lingering unencrypted temporary audio files on server storage.
- **Strict Authentication**: Endpoints require verified Firebase Auth Bearer tokens or backend JWT headers.

---

## 📖 API Reference

When the backend is active, complete interactive documentation is available at:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Backend and dependency health check |
| `POST` | `/api/consultations/process-audio` | Transcribe audio stream and parse clinical JSON |
| `POST` | `/api/consultations/save` | Encrypt & commit consultation to MongoDB Atlas |
| `GET` | `/api/consultations/history` | Fetch authenticated doctor consultation records |
| `GET` | `/api/consultations/{id}/pdf` | Generate and download prescription PDF |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
