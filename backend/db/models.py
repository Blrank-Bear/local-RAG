from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Float, Integer, Boolean,
    DateTime, ForeignKey, JSON, Enum as SAEnum, Index,
)
from sqlalchemy.orm import DeclarativeBase, relationship
from pgvector.sqlalchemy import Vector
import enum
import uuid


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


# ── Enums ──────────────────────────────────────────────────────────────────────

class SessionStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    failed = "failed"


class TaskStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


# ── Auth ───────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")


# ── Session / Chat ─────────────────────────────────────────────────────────────

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(SAEnum(SessionStatus), default=SessionStatus.active)

    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="session", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=gen_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    role = Column(String, nullable=False)          # user | assistant | agent
    content = Column(Text, nullable=False)
    agent_name = Column(String, nullable=True)
    retrieved_context = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="messages")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=gen_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(SAEnum(TaskStatus), default=TaskStatus.pending)
    result = Column(Text, nullable=True)
    steps = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    session = relationship("Session", back_populates="tasks")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=gen_uuid)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)   # pdf | txt
    chunk_count = Column(Integer, default=0)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(String, primary_key=True, default=gen_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    message_id = Column(String, ForeignKey("messages.id"), nullable=True)
    rating = Column(Integer, nullable=True)        # 1-5
    comment = Column(Text, nullable=True)
    quality_score = Column(Float, nullable=True)   # auto-evaluated
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="feedbacks")


class EvaluationLog(Base):
    __tablename__ = "evaluation_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    session_id = Column(String, nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    retrieved_docs = Column(JSON, nullable=True)
    relevance_score = Column(Float, nullable=True)
    faithfulness_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── pgvector RAG store ─────────────────────────────────────────────────────────

EMBEDDING_DIM = 768  # nomic-embed-text output dimension


class DocumentChunk(Base):
    """Stores document chunks with their vector embeddings (replaces ChromaDB)."""
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, default=gen_uuid)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=True)
    content = Column(Text, nullable=False)
    source = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_hash = Column(String, nullable=True)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=True)
    chunk_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index(
            "ix_document_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
