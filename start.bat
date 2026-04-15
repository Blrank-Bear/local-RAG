@echo off
title AgentOS — Multi-Agent AI System
color 0A

echo.
echo  ============================================
echo    AgentOS - Multi-Agent AI System
echo  ============================================
echo.

:: ── Check PostgreSQL ──────────────────────────────────────
echo [1/5] Checking PostgreSQL...
set PG_BIN=C:\Program Files\PostgreSQL\13\bin
set PGPASSWORD=1234

"%PG_BIN%\pg_isready" -U postgres -q >nul 2>&1
if errorlevel 1 (
    echo  WARNING: PostgreSQL does not appear to be ready.
    echo  Make sure PostgreSQL is running before continuing.
    echo  Continuing anyway in 5 seconds...
    timeout /t 5 /nobreak >nul
) else (
    echo  OK - PostgreSQL is running.
)

:: ── Ensure database exists ────────────────────────────────
"%PG_BIN%\psql" -U postgres -tc "SELECT 1 FROM pg_database WHERE datname='agentdb'" 2>nul | find "1" >nul
if errorlevel 1 (
    echo  Creating database 'agentdb'...
    "%PG_BIN%\psql" -U postgres -c "CREATE DATABASE agentdb;" >nul 2>&1
    echo  OK - Database created.
) else (
    echo  OK - Database 'agentdb' exists.
)

:: ── Check Ollama ──────────────────────────────────────────
echo.
echo [2/5] Checking Ollama...
ollama list >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Ollama is not running or not installed.
    echo  Download from https://ollama.com and start it, then re-run this script.
    pause
    exit /b 1
)
echo  OK - Ollama is running.

:: ── Check required models ─────────────────────────────────
echo [3/5] Checking Ollama models...
ollama list | find "llama3.2" >nul 2>&1
if errorlevel 1 (
    echo  Pulling llama3.2 (this may take a few minutes)...
    ollama pull llama3.2
)
ollama list | find "nomic-embed-text" >nul 2>&1
if errorlevel 1 (
    echo  Pulling nomic-embed-text...
    ollama pull nomic-embed-text
)
echo  OK - Models ready.

:: ── Start Backend ─────────────────────────────────────────
echo.
echo [4/5] Starting Backend (FastAPI on port 8000)...
start "AgentOS - Backend" cmd /k "cd /d %~dp0 && .venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

echo  Waiting for backend to be ready...
:wait_backend
timeout /t 2 /nobreak >nul
curl -s http://localhost:8000/api/health >nul 2>&1
if errorlevel 1 goto wait_backend
echo  OK - Backend is up at http://localhost:8000

:: ── Start Frontend ────────────────────────────────────────
echo.
echo [5/5] Starting Frontend (Vite on port 5173)...
start "AgentOS - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 4 /nobreak >nul

:: ── Done ──────────────────────────────────────────────────
echo.
echo  ============================================
echo    All services started successfully!
echo  ============================================
echo.
echo    Frontend  :  http://localhost:5173
echo    Backend   :  http://localhost:8000
echo    API Docs  :  http://localhost:8000/docs
echo.
echo    Register or log in at http://localhost:5173
echo.
echo  Opening browser...
start http://localhost:5173

echo.
echo  Press any key to close this launcher (servers keep running in their windows).
pause >nul
