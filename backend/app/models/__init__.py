import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, ForeignKey, DateTime, JSON
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    plan = Column(String(50), default="free")
    quota_tokens = Column(Integer, default=1000000)
    quota_storage = Column(Integer, default=1073741824)  # 1 GB
    created_at = Column(DateTime(timezone=True), default=now_utc)

    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    collections = relationship("Collection", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="member")  # admin, member, viewer
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    tenant = relationship("Tenant", back_populates="users")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class Collection(Base):
    __tablename__ = "collections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    chunk_config = Column(JSON, default=lambda: {"chunk_size": 700, "chunk_overlap": 100})
    created_at = Column(DateTime(timezone=True), default=now_utc)

    tenant = relationship("Tenant", back_populates="collections")
    documents = relationship("Document", back_populates="collection", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="collection", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    collection_id = Column(String(36), ForeignKey("collections.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(512), nullable=False)
    mime_type = Column(String(128), default="application/octet-stream")
    size = Column(Integer, default=0)
    sha256 = Column(String(64), index=True, nullable=False)
    storage_uri = Column(String(1024), nullable=False)
    status = Column(String(50), default="QUEUED", index=True)  # QUEUED, PARSING, CHUNKING, EMBEDDING, READY, FAILED
    error = Column(Text, nullable=True)
    page_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    collection = relationship("Collection", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    ordinal = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    page_start = Column(Integer, default=1)
    page_end = Column(Integer, default=1)
    section_path = Column(String(512), default="")
    char_start = Column(Integer, default=0)
    char_end = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    embedding_model = Column(String(128), default="")
    created_at = Column(DateTime(timezone=True), default=now_utc)

    document = relationship("Document", back_populates="chunks")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    collection_id = Column(String(36), ForeignKey("collections.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), default="New Conversation")
    created_at = Column(DateTime(timezone=True), default=now_utc)

    user = relationship("User", back_populates="conversations")
    collection = relationship("Collection", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    citations = Column(JSON, default=list)  # structured citation list
    bibliography = Column(JSON, default=list)
    trace_id = Column(String(64), nullable=True)
    tokens_in = Column(Integer, default=0)
    tokens_out = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    grounded = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    conversation = relationship("Conversation", back_populates="messages")
    feedback = relationship("Feedback", back_populates="message", uselist=False, cascade="all, delete-orphan")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, unique=True)
    rating = Column(Integer, nullable=False)  # 1 (thumbs up) or -1 (thumbs down)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    message = relationship("Message", back_populates="feedback")


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dataset = Column(String(255), nullable=False)
    question = Column(Text, nullable=False)
    expected_answer = Column(Text, nullable=True)
    expected_sources = Column(JSON, default=list)
    metrics = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=now_utc)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    actor_id = Column(String(36), nullable=False, index=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    action = Column(String(128), nullable=False)
    resource = Column(String(255), nullable=False)
    ip = Column(String(64), default="")
    timestamp = Column(DateTime(timezone=True), default=now_utc)


class Note(Base):
    __tablename__ = "notes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    collection_id = Column(String(36), ForeignKey("collections.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    note_type = Column(String(50), default="user_note")  # user_note, audio_overview, study_guide, briefing_doc, faq, timeline
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=now_utc)
