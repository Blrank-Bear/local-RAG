# AgentOS — Multi-Agent AI System

A voice-enabled, RAG-powered multi-agent system with user authentication, persistent conversation history, and a local Ollama LLM backend.

---

## Stack

| Layer     | Tech                                                        |
|-----------|-------------------------------------------------------------|
| Backend   | Python 3.11+ · FastAPI · WebSocket · uvicorn                |
| LLM       | Ollama (llama3.2 / any local model)                         |
| RAG       | PostgreSQL + pgvector (auto-fallback to JSON if not installed) |
| Voice     | faster-whisper (local) · sounddevice                        |
| Database  | PostgreSQL 13+ · SQLAlchemy async · asyncpg                 |
| Auth      | JWT (python-jose) · bcrypt                                  |
| Frontend  | React 18 · Vite · Zustand · CSS                             |

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.11+ | `python --version` to check |
| Node.js 20+ | `node --version` to check |
| PostgreSQL 13+ | Must be running locally |
| Ollama | Download from [ollama.com](https://ollama.com) |

---

## Quick Start (Windows)

```bat
start.bat
```

The launcher checks Ollama, starts the backend, starts the frontend, and opens the browser automatically.

---

## Manual Setup

### 1. Configure environment

```bash
copy .env.example .env
# Edit .env — set DATABASE_URL, JWT_SECRET_KEY, and Ollama model
```

### 2. Create the database

```sql
-- In psql or pgAdmin, run once:
CREATE DATABASE agentdb;
```

> The app automatically runs `CREATE TABLE` on first startup.  
> If pgvector is installed, it also enables the `vector` extension for native similarity search.  
> Without pgvector the app falls back to Python-based cosine similarity — no action needed.

### 3. Pull Ollama models

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

### 4. Backend

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — you'll land on the login/register page.

---

## pgvector (optional — for faster RAG)

pgvector enables native vector similarity search inside PostgreSQL.  
The app works without it using a Python fallback, but pgvector is faster for large document sets.

| Platform | Install |
|---|---|
| Ubuntu/Debian | `apt install postgresql-16-pgvector` |
| macOS | `brew install pgvector` |
| Windows | Use **EDB StackBuilder** (comes with PostgreSQL installer) → Add-ons → pgvector |

After installing, restart PostgreSQL. The app enables the extension automatically on next startup.

---

## Features

| Feature | Description |
|---|---|
| User Auth | Register / login with JWT tokens. All data is user-scoped. |
| Persistent History | Conversation history survives page reloads, stored in PostgreSQL. |
| Session Management | Switch between past sessions from the sidebar; delete individual sessions. |
| Clear History | Delete all messages in the current session with one click. |
| Voice Input | Push-to-talk or continuous listening via local Whisper STT. |
| RAG | Upload PDF/TXT → chunked, embedded, retrieved on query. |
| Multi-Agent Pipeline | Planner → Retriever → Analyzer → Executor → Memory. |
| Tool Registry | RAG search, file reader, calculator, HTTP API caller. |
| Autonomous Tasks | Complex requests broken into parallel/sequential steps. |
| Feedback & Evaluation | Star ratings + auto LLM-based relevance scoring. |

---

## Project Structure

```
backend/
  agents/         Planner, Retriever, Analyzer, Executor, Memory (DB-backed)
  auth/           JWT + bcrypt security utilities
  core/           Orchestrator, TaskRunner
  rag/            Ingestion pipeline, pgvector store (with JSON fallback)
  voice/          faster-whisper STT, microphone capture
  tools/          RAG search, file reader, calculator, API caller
  memory/         Feedback store, evaluation logger
  db/             SQLAlchemy models, async session, init_db
  api/
    routes/       auth, chat, voice, documents, tasks, feedback
    deps.py       Shared FastAPI dependencies (get_current_user)
frontend/
  src/
    components/   AuthPage, ChatPanel, Sidebar, VoiceInput,
                  DocumentsPanel, TasksPanel, FeedbackPanel,
                  MessageBubble, AgentStatus
    hooks/        useVoice
    services/     api.js  (axios + JWT interceptors)
    store/        useStore.js  (Zustand — auth, session, messages)
    styles/       global.css
docs/             Drop PDF/TXT files here for RAG ingestion
```

---

## API Endpoints

| Method   | Path                              | Auth | Description                    |
|----------|-----------------------------------|------|--------------------------------|
| POST     | /api/auth/register                | —    | Register new user              |
| POST     | /api/auth/login                   | —    | Login, receive JWT token       |
| GET      | /api/auth/me                      | ✓    | Current user info              |
| POST     | /api/chat/                        | ✓    | Send a message                 |
| GET      | /api/chat/sessions                | ✓    | List all sessions              |
| DELETE   | /api/chat/sessions/{id}           | ✓    | Delete a session + its messages|
| GET      | /api/chat/history/{session_id}    | ✓    | Load message history           |
| DELETE   | /api/chat/history/{session_id}    | ✓    | Clear messages in a session    |
| POST     | /api/voice/transcribe             | ✓    | Transcribe audio file          |
| POST     | /api/documents/upload             | ✓    | Upload and index PDF/TXT       |
| GET      | /api/documents/                   | ✓    | List indexed documents         |
| POST     | /api/tasks/run                    | ✓    | Run autonomous multi-step task |
| WS       | /api/tasks/ws/{session_id}        | —    | Stream task progress           |
| POST     | /api/feedback/                    | ✓    | Submit star rating             |
| POST     | /api/feedback/evaluate            | ✓    | Auto-evaluate response quality |
| GET      | /api/feedback/stats/{session_id}  | ✓    | Session quality metrics        |
| GET      | /api/health                       | —    | Health check                   |

> ✓ = requires `Authorization: Bearer <token>` header.  
> Interactive docs available at **http://localhost:8000/docs**.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:password@localhost:5432/agentdb` | PostgreSQL connection string |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | Chat model name |
| `OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model for RAG |
| `WHISPER_MODEL` | `base` | Whisper model size (`tiny`, `base`, `small`, `medium`) |
| `VOICE_MODE` | `push_to_talk` | `push_to_talk` or `continuous` |
| `DOCS_DIR` | `./docs` | Directory for uploaded documents |
| `CHUNK_SIZE` | `512` | RAG chunk size in tokens |
| `CHUNK_OVERLAP` | `64` | RAG chunk overlap in tokens |
| `JWT_SECRET_KEY` | *(change this)* | Secret for signing JWT tokens |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` | Token lifetime (7 days) |
| `SECRET_KEY` | *(change this)* | General app secret |
| `API_HOST` | `0.0.0.0` | Backend bind host |
| `API_PORT` | `8000` | Backend bind port |
