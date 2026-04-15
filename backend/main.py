"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import chat, voice, documents, feedback, tasks
from backend.db.database import init_db
from backend.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    settings.docs_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Multi-Agent AI System",
    description="Voice-enabled RAG multi-agent system powered by Ollama",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Allow WebSocket connections from the Vite dev server
ALLOWED_WS_ORIGINS = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
}

app.include_router(chat.router, prefix="/api")
app.include_router(voice.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
