# VoiceRx Sync

**AI-powered voice-to-prescription clinical documentation assistant.**

A doctor speaks a consultation note — patient ID, symptoms, diagnosis, and medicines — and VoiceRx Sync automatically transcribes, extracts, validates, and saves a structured digital prescription. Patient identifiers are encrypted end-to-end and never processed by the LLM.

---

## Architecture

```
frontend/          Next.js 14 (App Router) — doctor UI
backend/           FastAPI — STT, LLM extraction, encryption, PDF, MongoDB
```

### Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Framer Motion |
| Backend | FastAPI, Python 3.11+ |
| AI / STT | Groq API (Whisper large-v3 + LLaMA 3) |
| Database | MongoDB Atlas |
| Auth | Firebase Google Sign-In + JWT |
| Encryption | Fernet symmetric encryption (cryptography) |
| PDF | fpdf2 |

---

## Features

- **Voice recording** — doctor narrates consultation; STT via Whisper
- **LLM extraction** — diagnosis, symptoms, multi-medicine prescriptions
- **Patient ID encryption** — ID extracted from voice, encrypted with Fernet, LLM never sees it
- **Medicine validation** — dose safety check against medications CSV
- **Colorful PDF** — clinic letterhead, ℞ section, medicines table, signature
- **Clinic profile** — set hospital name/address once in dashboard, used on every PDF
- **FHIR output** — prescription exported as FHIR R4 bundle
- **Analytics dashboard** — consultation timeline, top medicines, diagnosis distribution

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB Atlas cluster
- Groq API key (free at [console.groq.com](https://console.groq.com))
- Firebase project with Google Auth enabled

### 1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

pip install -r requirements.txt

# Copy and fill in secrets
cp .env.example .env

python -m uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install

# Copy and fill in secrets
cp .env.local.example .env.local

npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Groq API key for STT + LLM |
| `MONGO_URI` | ✅ | MongoDB Atlas connection string |
| `MONGO_DB_NAME` | ✅ | MongoDB database name (default: `voicerx`) |
| `FIREBASE_API_KEY` | ✅ | Firebase Web API key for token verification |
| `JWT_SECRET` | ✅ | Long random string for JWT signing |
| `PATIENT_ENCRYPT_KEY` | ⬜ | Optional Fernet key (derived from JWT_SECRET if absent) |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | ✅ | Backend URL (default: `http://localhost:8000`) |
| `NEXT_PUBLIC_FIREBASE_*` | ✅ | Firebase project config |

---

## How It Works

### Recording Flow

```
Doctor speaks:  "Patient ID P1042, age 35, fever 3 days, 
                 Paracetamol 500mg twice daily for 5 days..."
        │
        ▼  [WebM audio → FastAPI /process-audio]
        
1. Whisper STT  →  full transcript
2. Regex scan   →  extract "P1042" from transcript
3. Fernet.encrypt("P1042")  →  encrypted token (LLM never sees plain ID)
4. LLM (LLaMA 3)  →  {age, diagnosis, symptoms, medicines[]}
5. Inject encrypted token into result
6. Medicine dose validation vs. medications.csv
        │
        ▼  [Review UI → /save]
        
7. Fetch clinic profile from MongoDB (hospital name, doctor quals, etc.)
8. Generate PDF (decrypt patient ID only for printing)
9. Build FHIR R4 bundle
10. Save to MongoDB
```

### Security

- Patient ID is **encrypted immediately** after STT, before the LLM call
- The LLM processes only clinical text — no PII
- Encrypted token stored in MongoDB; plain ID only appears in the generated PDF
- JWT tokens expire after 72 hours

---

## Project Structure

```
voicerx-sync/
├── backend/
│   ├── main.py                  FastAPI app entry point
│   ├── requirements.txt
│   ├── .env.example
│   └── services/
│       ├── stt.py               Whisper STT via Groq
│       ├── llm_extract.py       LLaMA 3 medical JSON extraction
│       ├── pid_extractor.py     Regex patient ID extraction from transcript
│       ├── encryption.py        Fernet encrypt/decrypt
│       ├── validator.py         Medicine dose safety validation
│       ├── pdf_generator.py     Professional prescription PDF
│       ├── fhir_builder.py      FHIR R4 bundle
│       └── database.py          MongoDB operations
│   └── routers/
│       ├── auth.py              Firebase auth + clinic profile API
│       ├── consultations.py     Audio processing + save pipeline
│       └── analytics.py         Dashboard analytics
│
└── frontend/
    ├── app/
    │   ├── page.tsx             Landing / login
    │   ├── dashboard/           Analytics dashboard + clinic profile
    │   ├── consultation/new/    Voice recording + review flow
    │   └── consultations/       Consultation list
    ├── lib/
    │   ├── api.ts               Axios API client
    │   ├── auth.tsx             Firebase auth context
    │   └── firebase.ts          Firebase init
    └── components/
        └── Sidebar.tsx
```

---

## License

MIT