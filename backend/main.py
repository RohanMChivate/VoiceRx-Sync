import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, consultations, analytics

app = FastAPI(title="VoiceRx Sync API", version="2.0.0")

# CORS — configure allowed origins
# By default allows localhost and any *.vercel.app domain.
# In production, set ALLOWED_ORIGINS to your custom domains or specific URLs (comma-separated).
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,          prefix="/api/auth",          tags=["auth"])
app.include_router(consultations.router, prefix="/api/consultations",  tags=["consultations"])
app.include_router(analytics.router,     prefix="/api/analytics",      tags=["analytics"])

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "VoiceRx Sync API"}
