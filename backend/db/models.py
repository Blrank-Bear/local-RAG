from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Float, Integer, Boolean,
    DateTime, ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import DeclarativeBase, relationship
import enum
import uuid


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class SessionStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    failed = "failed"


class TaskStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=gen_uuid)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(SAEnum(SessionStatus), default=SessionStatus.active)

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
