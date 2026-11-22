from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.errors import NotFoundError, PermissionDeniedError
from app.models import User, Collection, Document, AuditLog
from app.schemas import CollectionCreate, CollectionUpdate, CollectionResponse
from app.services.retrieval.vector_store import get_vector_store
from app.services.retrieval.bm25 import get_bm25_index

router = APIRouter(prefix="/collections", tags=["Collections"])


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    req: CollectionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    chunk_cfg = req.chunk_config.model_dump() if req.chunk_config else {"chunk_size": 700, "chunk_overlap": 100}
    collection = Collection(
        tenant_id=user.tenant_id,
        name=req.name,
        description=req.description or "",
        chunk_config=chunk_cfg
    )
    db.add(collection)
    await db.flush()

    audit = AuditLog(actor_id=user.id, tenant_id=user.tenant_id, action="COLLECTION_CREATED", resource=collection.id)
    db.add(audit)
    await db.commit()

    return CollectionResponse(
        id=collection.id,
        tenant_id=collection.tenant_id,
        name=collection.name,
        description=collection.description,
        chunk_config=collection.chunk_config,
        created_at=collection.created_at,
        document_count=0
    )


@router.get("", response_model=List[CollectionResponse])
async def list_collections(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Enforce strict tenant isolation
    query = (
        select(Collection, func.count(Document.id).label("doc_count"))
        .outerjoin(Document, Collection.id == Document.collection_id)
        .where(Collection.tenant_id == user.tenant_id)
        .group_by(Collection.id)
        .order_by(Collection.created_at.desc())
    )
    result = await db.execute(query)
    rows = result.all()

    responses = []
    for col, count in rows:
        responses.append(
            CollectionResponse(
                id=col.id,
                tenant_id=col.tenant_id,
                name=col.name,
                description=col.description,
                chunk_config=col.chunk_config or {},
                created_at=col.created_at,
                document_count=count
            )
        )
    return responses


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Collection).where(Collection.id == collection_id, Collection.tenant_id == user.tenant_id)
    result = await db.execute(query)
    col = result.scalars().first()
    if not col:
        raise NotFoundError("Collection", collection_id)

    count_q = select(func.count(Document.id)).where(Document.collection_id == collection_id)
    count = (await db.execute(count_q)).scalar() or 0

    return CollectionResponse(
        id=col.id,
        tenant_id=col.tenant_id,
        name=col.name,
        description=col.description,
        chunk_config=col.chunk_config or {},
        created_at=col.created_at,
        document_count=count
    )


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Collection).where(Collection.id == collection_id, Collection.tenant_id == user.tenant_id)
    result = await db.execute(query)
    col = result.scalars().first()
    if not col:
        raise NotFoundError("Collection", collection_id)

    # Clean from vector store and BM25 index
    vector_store = get_vector_store()
    bm25 = get_bm25_index()
    await vector_store.delete_by_collection(collection_id)
    bm25.delete_by_collection(collection_id)

    await db.delete(col)
    await db.commit()
    return None
