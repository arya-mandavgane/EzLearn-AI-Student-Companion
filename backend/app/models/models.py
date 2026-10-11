"""
SQLAlchemy models for AI Study Companion — Phase 1.
Includes Users, Inputs, Chunks, Explanations, Quizzes, Attempts, Mastery, Revisions, Feedback, and ErrorReports.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Text, Index
)
from sqlalchemy.orm import relationship

from app.models.database import Base


def _gen_uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    age = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now)

    # Daily usage tracking to control AI cost per user
    daily_requests_count = Column(Integer, default=0)
    last_request_date = Column(String(10), nullable=True)  # YYYY-MM-DD

    # Relationships
    inputs = relationship("InputRecord", back_populates="user", cascade="all, delete-orphan")
    explanations = relationship("ExplanationRecord", back_populates="user", cascade="all, delete-orphan")
    quizzes = relationship("QuizRecord", back_populates="user", cascade="all, delete-orphan")
    masteries = relationship("MasteryRecord", back_populates="user", cascade="all, delete-orphan")
    revisions = relationship("RevisionRecord", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("ConversationRecord", back_populates="user", cascade="all, delete-orphan")


class ConversationRecord(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False, default="New Conversation")
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    user = relationship("User", back_populates="conversations")
    messages = relationship("MessageRecord", back_populates="conversation", cascade="all, delete-orphan", order_by="MessageRecord.created_at")
    resources = relationship("ChatResourceRecord", back_populates="conversation", cascade="all, delete-orphan", order_by="ChatResourceRecord.created_at")


class ChatResourceRecord(Base):
    __tablename__ = "chat_resources"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)  # "text", "file", "image", "audio"
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)  # JSON for pages, mime, ocr confidence
    created_at = Column(DateTime, default=_now)

    conversation = relationship("ConversationRecord", back_populates="resources")


class MessageRecord(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" | "assistant"
    user_prompt = Column(Text, nullable=True)
    explanation_json = Column(Text, nullable=True)
    simulation_json = Column(Text, nullable=True)
    quiz_json = Column(Text, nullable=True)
    quiz_attempt_json = Column(Text, nullable=True)
    ai_suggestions = Column(Text, nullable=True)
    citations_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now)

    conversation = relationship("ConversationRecord", back_populates="messages")


class InputRecord(Base):
    __tablename__ = "inputs"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    source_type = Column(String(50), nullable=False, default="text")  # "text", "pdf", "image", "voice"
    title = Column(String(255), nullable=True)
    text = Column(Text, nullable=False)
    status = Column(String(50), default="ready")  # "queued", "processing", "ready", "failed"
    created_at = Column(DateTime, default=_now)

    user = relationship("User", back_populates="inputs")
    chunks = relationship("ChunkRecord", back_populates="input_record", cascade="all, delete-orphan")


class ChunkRecord(Base):
    __tablename__ = "chunks"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    input_id = Column(String(36), ForeignKey("inputs.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, default=1)
    content = Column(Text, nullable=False)
    embedding_id = Column(String(100), nullable=True)

    input_record = relationship("InputRecord", back_populates="chunks")


class ExplanationRecord(Base):
    __tablename__ = "explanations"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    input_id = Column(String(36), nullable=True, index=True)
    topic = Column(String(255), nullable=False)
    subtopic = Column(String(255), nullable=True)
    topic_type = Column(String(50), default="concept")
    language = Column(String(10), default="en")
    simple_explanation = Column(Text, nullable=False)
    exam_answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_now)

    user = relationship("User", back_populates="explanations")


class QuizRecord(Base):
    __tablename__ = "quizzes"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    input_id = Column(String(36), nullable=True, index=True)
    topic = Column(String(255), nullable=True)
    questions_json = Column(Text, nullable=False)  # JSON-encoded array of questions
    created_at = Column(DateTime, default=_now)

    user = relationship("User", back_populates="quizzes")
    attempts = relationship("QuizAttemptRecord", back_populates="quiz", cascade="all, delete-orphan")


class QuizAttemptRecord(Base):
    __tablename__ = "quiz_attempts"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    quiz_id = Column(String(36), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    score = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    answers_json = Column(Text, nullable=True)
    weak_topics_json = Column(Text, nullable=True)
    time_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=_now)

    quiz = relationship("QuizRecord", back_populates="attempts")


class MasteryRecord(Base):
    __tablename__ = "mastery"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic = Column(String(255), nullable=False, index=True)
    score = Column(Float, default=0.5)  # 0.0 to 1.0 (starts at 50%)
    last_tested_at = Column(DateTime, default=_now)

    user = relationship("User", back_populates="masteries")


class RevisionRecord(Base):
    __tablename__ = "revisions"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic = Column(String(255), nullable=False, index=True)
    due_date = Column(DateTime, nullable=False, index=True)
    interval_days = Column(Integer, default=1)  # 1 -> 3 -> 7
    repetitions = Column(Integer, default=0)
    ease_factor = Column(Float, default=2.5)

    user = relationship("User", back_populates="revisions")


class FeedbackRecord(Base):
    __tablename__ = "feedback"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    user_id = Column(String(36), nullable=True, index=True)
    explanation_id = Column(String(36), nullable=True, index=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now)


class ErrorReportRecord(Base):
    __tablename__ = "error_reports"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    user_id = Column(String(36), nullable=True)
    description = Column(Text, nullable=False)
    contact_email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=_now)
