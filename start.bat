@echo off
title Multi-Agent AI System
color 0A

echo.
echo  ==========================================
echo   Multi-Agent AI System - Starting Up...
echo  ==========================================
echo.

:: ── Check Ollama ──────────────────────────────────────────
echo [1/4] Checking Ollama...
ollama list >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Ollama is not running. Please start Ollama first.
    pause
    exit /b 1
)
echo  OK - Ollama is running.

:: ── Warm up the model ─────────────────────────────────────
echo [2/4] Warming up llama3.2 model (first run may take ~30s)...
for /f "delims=" %%i in ('ollama run llama3.2 "hi" 2^>nul') do (
    echo  Model ready.
    goto :model_ready
)
:model_ready

:: ── Start Backend ─────────────────────────────────────────
echo.
echo [3/4] Starting Backend (FastAPI on port 8000)...
start "AgentOS - Backend" cmd /k "cd /d %~dp0 && .venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

echo  Waiting for backend to be ready...
:wait_backend
timeout /t 2 /nobreak >nul
curl -s http://localhost:8000/api/health >nul 2>&1
if errorlevel 1 goto wait_backend
echo  OK - Backend is up at http://localhost:8000

:: ── Start Frontend ────────────────────────────────────────
echo.
echo [4/4] Starting Frontend (Vite on port 5173)...
start "AgentOS - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 4 /nobreak >nul

:: ── Done ──────────────────────────────────────────────────
echo.
echo  ==========================================
echo   All services started successfully!
echo  ==========================================
echo.
echo   Frontend : http://localhost:5173
echo   Backend  : http://localhost:8000
echo   API Docs : http://localhost:8000/docs
echo.
echo  Opening browser...
start http://localhost:5173

echo.
echo  Press any key to close this launcher (servers keep running).
pause >nul
