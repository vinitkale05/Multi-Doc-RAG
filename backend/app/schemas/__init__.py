from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==============================================================================
# Auth Schemas
# ==============================================================================

class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8)
    tenant_name: Optional[str] = "Default Workspace"
    role: Optional[str] = "admin"


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    tenant_id: str
    created_at: datetime


class TenantQuotaResponse(BaseModel):
    id: str
    name: str
    plan: str
    quota_tokens: int
    quota_storage: int
    used_tokens: int = 0
    used_storage: int = 0


# ==============================================================================
# Collection Schemas
# ==============================================================================

class ChunkConfig(BaseModel):
    chunk_size: int = 700
    chunk_overlap: int = 100


class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = ""
    chunk_config: Optional[ChunkConfig] = Field(default_factory=ChunkConfig)


class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    chunk_config: Optional[ChunkConfig] = None


class CollectionResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str
    chunk_config: Dict[str, Any]
    created_at: datetime
    document_count: Optional[int] = 0


# ==============================================================================
# Document & Ingestion Schemas
# ==============================================================================

class DocumentResponse(BaseModel):
    id: str
    collection_id: str
    filename: str
    mime_type: str
    size: int
    sha256: str
    status: str
    error: Optional[str] = None
    page_count: int
    created_at: datetime


class URLIngestRequest(BaseModel):
    url: str
    title: Optional[str] = None


class IngestStatusEvent(BaseModel):
    document_id: str
    status: str
    progress: float
    message: str
    error: Optional[str] = None


# ==============================================================================
# Citation & Chat Schemas
# ==============================================================================

class CitationHighlight(BaseModel):
    start: int
    end: int


class CitationDetail(BaseModel):
    id: int  # user-facing 1, 2, ...
    document_id: str
    title: str
    page: int
    section: str
    chunk_id: str
    snippet: str
    score: float
    highlight: Optional[CitationHighlight] = None


class BibliographyItem(BaseModel):
    document_id: str
    title: str
    pages: List[int]


class ChatOptions(BaseModel):
    top_k: int = 30
    rerank_top_n: int = 8
    stream: bool = True
    temperature: Optional[float] = 0.1


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    collection_ids: List[str] = Field(default_factory=list)
    document_ids: List[str] = Field(default_factory=list)
    question: str = Field(..., min_length=1)
    options: Optional[ChatOptions] = Field(default_factory=ChatOptions)


class ChatResponse(BaseModel):
    answer: str
    citations: List[CitationDetail]
    bibliography: List[BibliographyItem]
    grounded: bool
    trace_id: str
    conversation_id: str
    message_id: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: float = 0.0


# ==============================================================================
# Conversation & Message Schemas
# ==============================================================================

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    bibliography: List[Dict[str, Any]] = Field(default_factory=list)
    trace_id: Optional[str] = None
    grounded: bool = True
    created_at: datetime


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    collection_id: Optional[str] = None
    title: str
    created_at: datetime
    messages: Optional[List[MessageResponse]] = None


# ==============================================================================
# Feedback & Admin Schemas
# ==============================================================================

class FeedbackCreate(BaseModel):
    rating: int = Field(..., description="1 for thumbs up, -1 for thumbs down")
    reason: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: str
    message_id: str
    rating: int
    reason: Optional[str] = None
    created_at: datetime


class EvalRunCreate(BaseModel):
    dataset: str = "golden_benchmark"
    eval_cases_count: Optional[int] = 100


class EvalRunResponse(BaseModel):
    id: str
    dataset: str
    total_cases: int
    metrics: Dict[str, Any]
    created_at: datetime


class UsageReportResponse(BaseModel):
    tenant_id: str
    total_documents: int
    total_chunks: int
    total_conversations: int
    total_tokens_used: int
    quota_tokens: int
    storage_used_bytes: int
    quota_storage_bytes: int


# ==============================================================================
# NotebookLM Studio & Notes Schemas
# ==============================================================================

class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str
    note_type: Optional[str] = "user_note"
    collection_id: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class NoteResponse(BaseModel):
    id: str
    user_id: str
    collection_id: Optional[str] = None
    title: str
    content: str
    note_type: str
    metadata_json: Dict[str, Any]
    created_at: datetime


class StudioGenerateRequest(BaseModel):
    collection_id: Optional[str] = None
    document_ids: List[str] = Field(default_factory=list)
    custom_instructions: Optional[str] = None


class DialogueTurn(BaseModel):
    speaker: str  # Alex or Taylor
    text: str
    timestamp: str


class AudioOverviewResponse(BaseModel):
    title: str
    summary: str
    dialogue: List[DialogueTurn]
    sources_used: List[str]


class StudioArtifactResponse(BaseModel):
    artifact_type: str  # study_guide, briefing_doc, faq, timeline
    title: str
    content_markdown: str
    sources_used: List[str]

