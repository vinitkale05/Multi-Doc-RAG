from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.errors import NotFoundError
from app.models import User, Chunk, Document, Collection

router = APIRouter(prefix="/citations", tags=["Citations"])


@router.get("/{chunk_id}")
async def get_citation_detail(
    chunk_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves full passage, page number, section path, and char highlight offsets for side-by-side document viewer."""
    query = (
        select(Chunk, Document, Collection)
        .join(Document, Chunk.document_id == Document.id)
        .join(Collection, Document.collection_id == Collection.id)
        .where(Chunk.id == chunk_id, Collection.tenant_id == user.tenant_id)
    )
    result = await db.execute(query)
    row = result.first()
    if not row:
        raise NotFoundError("Citation Chunk", chunk_id)

    chunk, doc, col = row

    return {
        "chunk_id": chunk.id,
        "document_id": doc.id,
        "filename": doc.filename,
        "mime_type": doc.mime_type,
        "storage_uri": doc.storage_uri,
        "page_start": chunk.page_start,
        "page_end": chunk.page_end,
        "section_path": chunk.section_path,
        "text": chunk.text,
        "highlight": {
            "start": chunk.char_start,
            "end": chunk.char_end
        }
    }
