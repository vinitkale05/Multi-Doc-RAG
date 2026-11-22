import asyncio
import hashlib
import io
import urllib.parse
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, status
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db, AsyncSessionLocal
from app.core.dependencies import get_current_user
from app.core.errors import NotFoundError, AppError
from app.core.events import event_bus
from app.core.config import settings
from app.models import User, Collection, Document, Chunk
from app.schemas import DocumentResponse, URLIngestRequest
from app.services.storage.storage import get_storage_service
from app.services.ingestion.pipeline import ingestion_pipeline
from app.services.ingestion.ssrf import fetch_url_safely
from app.services.retrieval.vector_store import get_vector_store
from app.services.retrieval.bm25 import get_bm25_index

router = APIRouter(tags=["Documents"])


async def run_ingestion_background(document_id: str, content_bytes: bytes, filename: str, mime_type: str, tenant_id: str):
    async with AsyncSessionLocal() as session:
        try:
            await ingestion_pipeline.ingest_document(
                db=session,
                document_id=document_id,
                content_bytes=content_bytes,
                filename=filename,
                mime_type=mime_type,
                tenant_id=tenant_id
            )
        except Exception:
            pass


@router.post("/collections/{collection_id}/documents", response_model=List[DocumentResponse], status_code=status.HTTP_202_ACCEPTED)
async def upload_documents(
    collection_id: str,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify collection ownership
    col_q = select(Collection).where(Collection.id == collection_id, Collection.tenant_id == user.tenant_id)
    collection = (await db.execute(col_q)).scalars().first()
    if not collection:
        raise NotFoundError("Collection", collection_id)

    storage_service = get_storage_service()
    responses = []

    for file in files:
        content = await file.read()
        size_mb = len(content) / (1024 * 1024)
        if size_mb > settings.MAX_UPLOAD_MB:
            raise AppError(status_code=400, detail=f"File {file.filename} exceeds max size limit of {settings.MAX_UPLOAD_MB}MB")

        sha256_hash = hashlib.sha256(content).hexdigest()

        # Check deduplication
        existing_doc_q = select(Document).where(
            Document.collection_id == collection_id,
            Document.sha256 == sha256_hash
        )
        existing = (await db.execute(existing_doc_q)).scalars().first()
        if existing and existing.status == "READY":
            responses.append(existing)
            continue
        elif existing:
            # Document previously failed or was interrupted: reset and re-ingest
            existing.status = "QUEUED"
            existing.error = None
            await db.flush()
            responses.append(existing)
            background_tasks.add_task(
                run_ingestion_background,
                document_id=existing.id,
                content_bytes=content,
                filename=existing.filename,
                mime_type=existing.mime_type,
                tenant_id=user.tenant_id
            )
            continue

        # Upload to storage
        storage_uri = await storage_service.upload(
            file_obj=io.BytesIO(content),
            filename=f"{collection_id}_{sha256_hash}_{file.filename}",
            content_type=file.content_type or "application/octet-stream"
        )

        doc = Document(
            collection_id=collection_id,
            filename=file.filename or "uploaded_file",
            mime_type=file.content_type or "application/octet-stream",
            size=len(content),
            sha256=sha256_hash,
            storage_uri=storage_uri,
            status="QUEUED"
        )
        db.add(doc)
        await db.flush()
        responses.append(doc)

        # Trigger background ingestion
        background_tasks.add_task(
            run_ingestion_background,
            document_id=doc.id,
            content_bytes=content,
            filename=doc.filename,
            mime_type=doc.mime_type,
            tenant_id=user.tenant_id
        )

    await db.commit()
    return responses


@router.post("/collections/{collection_id}/documents/url", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_url(
    collection_id: str,
    req: URLIngestRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    col_q = select(Collection).where(Collection.id == collection_id, Collection.tenant_id == user.tenant_id)
    collection = (await db.execute(col_q)).scalars().first()
    if not collection:
        raise NotFoundError("Collection", collection_id)

    content, content_type = await fetch_url_safely(req.url)
    sha256_hash = hashlib.sha256(content).hexdigest()
    parsed_url = urllib.parse.urlparse(req.url)
    filename = req.title or f"{parsed_url.netloc}{parsed_url.path}.html".strip("/") or "web_document.html"

    # Check deduplication
    existing_doc_q = select(Document).where(
        Document.collection_id == collection_id,
        Document.sha256 == sha256_hash
    )
    existing = (await db.execute(existing_doc_q)).scalars().first()
    if existing and existing.status == "READY":
        return existing
    elif existing:
        existing.status = "QUEUED"
        existing.error = None
        await db.commit()
        background_tasks.add_task(
            run_ingestion_background,
            document_id=existing.id,
            content_bytes=content,
            filename=existing.filename,
            mime_type=existing.mime_type,
            tenant_id=user.tenant_id
        )
        return existing

    storage_service = get_storage_service()
    storage_uri = await storage_service.upload(
        file_obj=io.BytesIO(content),
        filename=f"{collection_id}_{sha256_hash}_{filename}",
        content_type=content_type
    )

    doc = Document(
        collection_id=collection_id,
        filename=filename,
        mime_type=content_type,
        size=len(content),
        sha256=sha256_hash,
        storage_uri=storage_uri,
        status="QUEUED"
    )
    db.add(doc)
    await db.commit()

    background_tasks.add_task(
        run_ingestion_background,
        document_id=doc.id,
        content_bytes=content,
        filename=doc.filename,
        mime_type=doc.mime_type,
        tenant_id=user.tenant_id
    )

    return doc


@router.post("/documents/{document_id}/retry", response_model=DocumentResponse)
async def retry_document_ingestion(
    document_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    doc_q = (
        select(Document)
        .join(Collection, Document.collection_id == Collection.id)
        .where(Document.id == document_id, Collection.tenant_id == user.tenant_id)
    )
    doc = (await db.execute(doc_q)).scalars().first()
    if not doc:
        raise NotFoundError("Document", document_id)

    storage_service = get_storage_service()
    content = await storage_service.download(doc.storage_uri)
    doc.status = "QUEUED"
    doc.error = None
    await db.commit()

    background_tasks.add_task(
        run_ingestion_background,
        document_id=doc.id,
        content_bytes=content,
        filename=doc.filename,
        mime_type=doc.mime_type,
        tenant_id=user.tenant_id
    )
    return doc


@router.get("/collections/{collection_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    collection_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    col_q = select(Collection).where(Collection.id == collection_id, Collection.tenant_id == user.tenant_id)
    if not (await db.execute(col_q)).scalars().first():
        raise NotFoundError("Collection", collection_id)

    docs_q = select(Document).where(Document.collection_id == collection_id).order_by(Document.created_at.desc())
    docs = (await db.execute(docs_q)).scalars().all()
    return docs


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    doc_q = (
        select(Document)
        .join(Collection, Document.collection_id == Collection.id)
        .where(Document.id == document_id, Collection.tenant_id == user.tenant_id)
    )
    doc = (await db.execute(doc_q)).scalars().first()
    if not doc:
        raise NotFoundError("Document", document_id)
    return doc


@router.get("/documents/{document_id}/events")
async def document_progress_events(document_id: str):
    """SSE endpoint streaming live status updates for a document."""
    return StreamingResponse(
        event_bus.sse_stream(document_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    doc_q = (
        select(Document)
        .join(Collection, Document.collection_id == Collection.id)
        .where(Document.id == document_id, Collection.tenant_id == user.tenant_id)
    )
    doc = (await db.execute(doc_q)).scalars().first()
    if not doc:
        raise NotFoundError("Document", document_id)

    # Remove from vector store and BM25 index
    await get_vector_store().delete_by_document(document_id)
    get_bm25_index().delete_by_document(document_id)

    # Delete original file
    await get_storage_service().delete(doc.storage_uri)

    await db.delete(doc)
    await db.commit()
    return None
