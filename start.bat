@echo off
echo ============================================
echo  VoiceRx Sync  -  Development Servers
echo ============================================

echo.
echo [1/2] Starting FastAPI backend on port 8000...
start "VoiceRx Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --reload --port 8000"

timeout /t 4 /nobreak > nul

echo [2/2] Starting Next.js frontend on port 3000...
start "VoiceRx Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ============================================
echo  Backend  : http://localhost:8000
echo  Frontend : http://localhost:3000
echo  API Docs : http://localhost:8000/docs
echo ============================================
timeout /t 6 /nobreak > nul
start http://localhost:3000
