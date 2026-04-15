# Multi-Agent AI System

Voice-enabled, RAG-powered multi-agent system with Ollama LLM backend.

## Stack

| Layer     | Tech                                      |
|-----------|-------------------------------------------|
| Backend   | Python · FastAPI · WebSocket              |
| LLM       | Ollama (llama3.2 / any local model)       |
| RAG       | **pgvector** · PostgreSQL · sentence-transformers |
| Voice     | OpenAI Whisper (local) · sounddevice      |
| Database  | PostgreSQL · SQLAlchemy async             |
| Auth      | JWT (python-jose) · bcrypt (passlib)      |
| Frontend  | React · Vite · CSS                        |

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL running locally
- [Ollama](https://ollama.com) installed and running

## Setup

### 1. Clone & configure

```bash
cp .env.example .env
# Edit .env with your DB credentials and preferred Ollama model
```

### 2. Pull Ollama models

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

### 3. Enable pgvector in PostgreSQL

```sql
-- Run once in your PostgreSQL instance
CREATE EXTENSION IF NOT EXISTS vector;
```

> pgvector is available via `apt install postgresql-16-pgvector` on Ubuntu,
> or `brew install pgvector` on macOS. On Windows use the
> [pgvector releases](https://github.com/pgvector/pgvector/releases).

### 3. Backend

```bash
cd agent-project
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Features

| Feature                  | Description                                              |
|--------------------------|----------------------------------------------------------|
| Voice Input              | Push-to-talk or continuous listening via Whisper STT     |
| RAG                      | Upload PDF/TXT → chunked, embedded, retrieved on query   |
| Multi-Agent Pipeline     | Planner → Retriever → Analyzer → Executor → Memory       |
| Tool Registry            | RAG search, file reader, calculator, API caller          |
| Autonomous Tasks         | Complex requests broken into parallel/sequential steps   |
| Feedback & Evaluation    | Star ratings + auto LLM-based relevance scoring          |

## Project Structure

```
backend/
  agents/       Planner, Retriever, Analyzer, Executor, Memory
  core/         Orchestrator, TaskRunner
  rag/          Ingestion pipeline, ChromaDB vector store
  voice/        Whisper STT, microphone capture
  tools/        RAG search, file reader, calculator, API caller
  memory/       Feedback store, evaluation logger
  db/           SQLAlchemy models, async session
  api/routes/   FastAPI REST + WebSocket endpoints
frontend/
  src/
    components/ ChatPanel, VoiceInput, DocumentsPanel, TasksPanel, FeedbackPanel
    hooks/      useWebSocket, useVoice
    services/   API client
    store/      Zustand global state
docs/           Drop your PDF/TXT files here
```

## API Endpoints

| Method | Path                        | Description              |
|--------|-----------------------------|--------------------------|
| POST   | /api/auth/register          | Register new user        |
| POST   | /api/auth/login             | Login, get JWT token     |
| GET    | /api/auth/me                | Get current user info    |
| POST   | /api/chat/                  | Single-turn chat         |
| WS     | /api/chat/ws/{session_id}   | Streaming chat           |
| WS     | /api/voice/ws/{session_id}  | Voice input stream       |
| POST   | /api/documents/upload       | Upload PDF/TXT           |
| GET    | /api/documents/             | List indexed documents   |
| POST   | /api/tasks/run              | Run autonomous task      |
| WS     | /api/tasks/ws/{session_id}  | Stream task progress     |
| POST   | /api/feedback/              | Submit rating            |
| POST   | /api/feedback/evaluate      | Auto-evaluate response   |
| GET    | /api/feedback/stats/{id}    | Session quality stats    |

> All endpoints except `/api/auth/register` and `/api/auth/login` require a `Bearer` JWT token.
