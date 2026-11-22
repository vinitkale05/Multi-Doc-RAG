from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.errors import NotFoundError, AppError
from app.models import User, Document, Chunk, Collection, Note
from app.schemas import (
    StudioGenerateRequest,
    AudioOverviewResponse,
    StudioArtifactResponse,
    NoteCreate,
    NoteUpdate,
    NoteResponse,
)
from app.services.generation.notebook_studio import notebook_studio

router = APIRouter(prefix="/notebook", tags=["NotebookLM Studio"])


async def resolve_sources(
    req: StudioGenerateRequest, user: User, db: AsyncSession
) -> List[dict]:
    """Helper to fetch verified chunk texts from authorized documents."""
    query = (
        select(Chunk, Document)
        .join(Document, Chunk.document_id == Document.id)
        .join(Collection, Document.collection_id == Collection.id)
        .where(Collection.tenant_id == user.tenant_id)
    )

    if req.document_ids:
        query = query.where(Document.id.in_(req.document_ids))
    elif req.collection_id:
        query = query.where(Document.collection_id == req.collection_id)

    rows = (await db.execute(query)).all()
    if not rows:
        raise AppError(status_code=400, detail="No sources found for the selected scope.")

    sources = []
    for chunk, doc in rows:
        sources.append({
            "document_id": doc.id,
            "filename": doc.filename,
            "page": chunk.page_start,
            "text": chunk.text,
        })
    return sources


@router.post("/audio-overview", response_model=AudioOverviewResponse)
async def generate_audio_overview(
    req: StudioGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    sources = await resolve_sources(req, user, db)
    return await notebook_studio.generate_audio_overview(sources, req.custom_instructions)


@router.post("/study-guide", response_model=StudioArtifactResponse)
async def generate_study_guide(
    req: StudioGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    sources = await resolve_sources(req, user, db)
    return await notebook_studio.generate_study_guide(sources, req.custom_instructions)


@router.post("/briefing-doc", response_model=StudioArtifactResponse)
async def generate_briefing_doc(
    req: StudioGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    sources = await resolve_sources(req, user, db)
    return await notebook_studio.generate_briefing_doc(sources, req.custom_instructions)


@router.post("/faq", response_model=StudioArtifactResponse)
async def generate_faq(
    req: StudioGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    sources = await resolve_sources(req, user, db)
    return await notebook_studio.generate_faq(sources, req.custom_instructions)


@router.post("/timeline", response_model=StudioArtifactResponse)
async def generate_timeline(
    req: StudioGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    sources = await resolve_sources(req, user, db)
    return await notebook_studio.generate_timeline(sources, req.custom_instructions)


# ==============================================================================
# Notebook Notes API (Pin to Studio / Saved Cards)
# ==============================================================================

@router.get("/notes", response_model=List[NoteResponse])
async def list_notes(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    q = select(Note).where(Note.user_id == user.id).order_by(Note.created_at.desc())
    notes = (await db.execute(q)).scalars().all()
    return notes


@router.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    req: NoteCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    note = Note(
        user_id=user.id,
        collection_id=req.collection_id,
        title=req.title,
        content=req.content,
        note_type=req.note_type or "user_note",
        metadata_json=req.metadata_json or {}
    )
    db.add(note)
    await db.commit()
    return note


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    q = select(Note).where(Note.id == note_id, Note.user_id == user.id)
    note = (await db.execute(q)).scalars().first()
    if not note:
        raise NotFoundError("Note", note_id)
    await db.delete(note)
    await db.commit()
    return None
